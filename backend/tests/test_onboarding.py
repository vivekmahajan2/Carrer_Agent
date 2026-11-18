import pytest

def test_get_and_update_profile(client, test_user):
    # Fetch initial profile
    res = client.get("/api/v1/onboarding/profile", headers=test_user["headers"])
    assert res.status_code == 200
    
    # Update profile
    update_payload = {
        "headline": "Lead AI Architect & Full-Stack Specialist",
        "target_role": "Staff AI Engineer",
        "location": "San Francisco, CA",
        "bio": "Experienced architect building agentic SaaS platforms.",
        "linkedin_url": "https://linkedin.com/in/testuser"
    }
    update_res = client.put("/api/v1/onboarding/profile", json=update_payload, headers=test_user["headers"])
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["headline"] == "Lead AI Architect & Full-Stack Specialist"
    assert updated_data["target_role"] == "Staff AI Engineer"
    assert updated_data["location"] == "San Francisco, CA"


def test_get_and_update_preferences(client, test_user):
    pref_payload = {
        "employment_type": "full-time",
        "target_roles": ["AI Engineer", "Full Stack Engineer"],
        "desired_locations": ["Bangalore", "San Francisco", "Remote"],
        "remote_preference": "remote",
        "min_salary_annual": 150000,
        "preferred_skills": ["Python", "FastAPI", "Next.js", "LangGraph"],
        "target_industries": ["Artificial Intelligence", "SaaS"]
    }
    update_res = client.put("/api/v1/onboarding/preferences", json=pref_payload, headers=test_user["headers"])
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["remote_preference"] == "remote"
    assert "LangGraph" in data["preferred_skills"]
    assert data["min_salary_annual"] == 150000


def test_unauthorized_access_rejected(client):
    res = client.get("/api/v1/onboarding/profile")
    assert res.status_code == 401

