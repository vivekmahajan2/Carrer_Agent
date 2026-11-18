# CareerPilot AI — Autonomous Job Discovery, Networking & Outreach Agent

CareerPilot AI is a production-oriented, multi-tenant SaaS platform where job seekers ingest their master CV, define preferences, discover opportunities across 6 platforms, match listings with explainable AI scores, synthesize personalized outreach messages via LangGraph multi-agent workflows, and approve every single action through a human-in-the-loop Approval Center before any external execution.

### 6. LLM Configuration (Optional)
To use Groq's high-speed inference in `.env`:
```ini
DEFAULT_LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```
Supported models: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`.

---

## Architecture & Tech Stack

- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide icons (inspired by Linear & Stripe).
- **Backend:** Python FastAPI, Pydantic v2, SQLAlchemy 2.0 with tenant isolation.
- **Database:** PostgreSQL (Supabase-ready) / SQLite automatic local developer fallback.
- **Vector DB:** Qdrant client (local in-memory mode supported out of the box).
- **Agent Orchestration:** LangGraph multi-agent StateGraph with checkpointing and human-in-the-loop interruption.
- **CV Intelligence:** PyMuPDF & python-docx with structured skill and experience extraction.
- **LLM Abstraction:** Multi-provider interface supporting **Groq** (ultra-fast LPU inference via Llama 3.3/3.1), **Gemini**, **OpenAI**, **Ollama**, and offline deterministic Mock.

### 6. LLM Configuration (Optional)
To use Groq's high-speed inference in `.env`:
```ini
DEFAULT_LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```
Supported models: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`.

---

## Supported Discovery Sources

CareerPilot AI implements separate connector interfaces with rate limiting and terms-of-service compliance (no prohibited scraping or unauthorized botting):
- **LinkedIn** (Verified feed partner / export adapter)
- **Naukri** (Enterprise software listings)
- **Indeed** (Verified public listings)
- **Internshala** (Paid tech internships & PPO tracks)
- **Wellfound / AngelList** (High-growth startups)
- **Company Career Pages** (Direct portals)
- **Manual / Custom Listings** (Direct user submission)

### 6. LLM Configuration (Optional)
To use Groq's high-speed inference in `.env`:
```ini
DEFAULT_LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```
Supported models: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`.

---

## Quickstart Guide (Windows PowerShell in VS Code)

### 1. Prerequisites
- Python 3.12+
- Node.js 18+ and npm
- Windows PowerShell

### 2. Backend Setup & Run

Open a PowerShell terminal in VS Code:
```powershell
# Navigate to workspace root
cd d:\carreragent

# Activate Python virtual environment
.\backend\.venv\Scripts\Activate.ps1

# (Optional) Run the database seeder to populate demo candidates & startup jobs
python -m backend.scripts.seed_data

# Start the FastAPI server (Runs on http://localhost:8000)
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation is immediately available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 3. Run Backend Automated Test Suite
In PowerShell:
```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\tests -v
```
All 16 unit, integration, LLM, workflow, and tenant-isolation tests run with 100% pass rate.

### 4. Frontend Setup & Run
In a second PowerShell terminal:
```powershell
cd d:\carreragent\frontend

# Start Next.js development server
npm run dev
```
Open your browser at **[http://localhost:3000](http://localhost:3000)**.

### 5. Instant Demo Credentials
- **Email:** `demo@careerpilot.ai`
- **Password:** `DemoPilot2026!`
*(Or click the 1-Click Demo Login button in the authentication modal).*

### 6. LLM Configuration (Optional)
To use Groq's high-speed inference in `.env`:
```ini
DEFAULT_LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```
Supported models: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`.

---

## 13 Navigation Modules

1. **Overview:** Mission control with real database metrics, jobs discovered, active matches, and pending approvals.
2. **Discover Jobs:** Search and filter listings by remote policy, employment type (internship/full-time), with 1-click fit evaluation.
3. **Companies:** Startups and enterprises with tech stack chips and active hiring signals.
4. **Recruiters:** Publicly verified hiring leads with public source URLs and provenance grounding (never hallucinated).
5. **My Resume:** Upload PDF/DOCX resumes, inspect PyMuPDF text extractions, edit technical competencies, and designate master CVs.
6. **Job Matches:** 0-100% match score radar, semantic fit, skill overlap ratio, missing skill breakdown, and AI explainability narratives.
7. **Outreach Inbox:** LinkedIn notes (<=300 chars), cold emails, and cover letters strictly grounded in verified CV claims.
8. **Approval Center:** Human-in-the-loop safety gate where every message must be inspected, edited, or approved prior to dispatch.
9. **Applications CRM:** Track candidates across 8 lifecycle stages: Saved, Draft, Approved, Submitted, Replied, Interview, Rejected, and Offer.
10. **Follow-ups:** Scheduled touchpoints, smart reminders, and suggested follow-up drafts.
11. **Analytics:** Funnel conversion visualizations and response rates derived from real database records.
12. **Settings:** Profile headline, locations, compensation minimums, and preferred employment types.
13. **Billing & Plans:** Quota tiers (Free vs Pro vs Enterprise) with monthly match and outreach limits.

