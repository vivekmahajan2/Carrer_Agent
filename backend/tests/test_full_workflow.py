import io
import uuid
import pytest
import fitz  # PyMuPDF


def test_resume_upload_and_parsing(client, test_user):
    # Create an authentic PDF document using PyMuPDF
    doc = fitz.open()
    page = doc.new_page()
    resume_text = (
        "Jane Doe\n"
        "jane.doe@example.com | (555) 123-4567 | San Francisco, CA\n\n"
        "Summary:\n"
        "Lead Full Stack & AI Engineer specializing in Python, FastAPI, React, and LangGraph.\n\n"
        "Experience:\n"
        "Senior Software Engineer at AlphaTech (2021-2024)\n"
        "- Built scalable REST APIs using FastAPI and PostgreSQL.\n"
        "- Deployed multi-agent systems using LangGraph and Qdrant.\n"
        "- Developed responsive dashboard interfaces with Next.js and Tailwind CSS.\n\n"
        "Skills:\n"
        "Python, FastAPI, Next.js, Docker, Kubernetes, PostgreSQL, Qdrant, LangGraph, TypeScript\n\n"
        "Education:\n"
        "B.S. in Computer Science, University of California, Berkeley\n"
    )
    page.insert_text((50, 50), resume_text)
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("jane_doe_cv.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    response = client.post("/api/v1/resumes/upload", files=files, headers=test_user["headers"])
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "jane_doe_cv.pdf"
    assert data["is_master"] is True
    assert "skills" in data["parsed_json"]
    
    # Check that skills like Python and FastAPI were extracted
    extracted_names = [s["skill_name"] for s in data["parsed_json"]["skills"]]
    assert "Python" in extracted_names or "FastAPI" in extracted_names


def test_job_discovery_sync(client, test_user):
    # Run sync
    sync_res = client.post("/api/v1/jobs/sync", headers=test_user["headers"])
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["status"] == "success"

    # Fetch jobs
    jobs_res = client.get("/api/v1/jobs/")
    assert jobs_res.status_code == 200
    jobs = jobs_res.json()
    assert len(jobs) > 0
    first_job = jobs[0]
    assert "title" in first_job
    assert "company_name" in first_job


def test_ai_matching_and_outreach_approval_workflow(client, test_user):
    # 1. Sync jobs
    client.post("/api/v1/jobs/sync", headers=test_user["headers"])
    jobs = client.get("/api/v1/jobs/").json()
    assert len(jobs) > 0
    target_job = jobs[0]

    # 2. Upload resume
    cv_doc = fitz.open()
    cv_p = cv_doc.new_page()
    cv_p.insert_text((50, 50), "John Smith\nSkills: Python, FastAPI, LangGraph, Qdrant, PostgreSQL, Next.js")
    cv_bytes = cv_doc.tobytes()
    cv_doc.close()
    files = {"file": ("cv.pdf", io.BytesIO(cv_bytes), "application/pdf")}
    res_upload = client.post("/api/v1/resumes/upload", files=files, headers=test_user["headers"])
    assert res_upload.status_code == 201
    resume_id = res_upload.json()["id"]

    # 3. Evaluate match
    eval_res = client.post(
        "/api/v1/matching/evaluate",
        json={"job_id": target_job["id"], "resume_id": resume_id},
        headers=test_user["headers"]
    )
    assert eval_res.status_code == 200
    match_data = eval_res.json()
    assert match_data["overall_score"] > 0
    assert "summary" in match_data["explanation"]

    # 4. Generate Outreach Draft via LangGraph Agent
    outreach_res = client.post(
        "/api/v1/outreach/generate",
        json={"job_id": target_job["id"], "channel": "cold_email"},
        headers=test_user["headers"]
    )
    assert outreach_res.status_code == 201
    outreach_data = outreach_res.json()
    assert outreach_data["status"] == "pending_approval"
    outreach_id = outreach_data["id"]

    # 5. Check Pending Approvals
    pending_res = client.get("/api/v1/approvals/pending", headers=test_user["headers"])
    assert pending_res.status_code == 200
    pending_list = pending_res.json()
    assert any(m["id"] == outreach_id for m in pending_list)

    # 6. Approve the outreach
    approval_res = client.post(
        f"/api/v1/approvals/{outreach_id}/decision",
        json={"decision": "approved"},
        headers=test_user["headers"]
    )
    assert approval_res.status_code == 200
    assert approval_res.json()["status"] == "approved"

    # 7. Check Dashboard Analytics
    analytics_res = client.get("/api/v1/analytics/dashboard", headers=test_user["headers"])
    assert analytics_res.status_code == 200
    metrics = analytics_res.json()["metrics"]
    assert metrics["jobs_discovered"] > 0
    assert metrics["total_outreach_drafts"] >= 1


def test_strict_multi_tenant_isolation(client, test_user):
    """Verify that User B cannot view or modify User A's private data."""
    # Register User B
    user_b_payload = {
        "email": "userb@example.com",
        "password": "PasswordUserB123!",
        "full_name": "User B"
    }
    res_b = client.post("/api/v1/auth/register", json=user_b_payload)
    assert res_b.status_code == 201
    user_b_token = res_b.json()["access_token"]
    user_b_headers = {"Authorization": f"Bearer {user_b_token}"}

    # User A uploads a resume
    files_a = {"file": ("user_a_secret_cv.pdf", io.BytesIO(b"User A Private CV"), "application/pdf")}
    res_a = client.post("/api/v1/resumes/upload", files=files_a, headers=test_user["headers"])
    assert res_a.status_code == 201
    resume_a_id = res_a.json()["id"]

    # User B attempts to access User A's resume directly -> Must be 404
    cross_access_res = client.get(f"/api/v1/resumes/{resume_a_id}", headers=user_b_headers)
    assert cross_access_res.status_code == 404

    # User B lists resumes -> Must only see User B's resumes (0 items)
    user_b_list = client.get("/api/v1/resumes/", headers=user_b_headers).json()
    assert len(user_b_list) == 0
