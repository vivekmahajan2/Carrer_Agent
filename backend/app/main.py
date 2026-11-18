from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.core.config import get_settings
from backend.app.core.database import engine, Base
from backend.app.core.logging import logger
# Import all models so Base.metadata knows about them
import backend.app.models  # noqa
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.onboarding import router as onboarding_router
from backend.app.api.v1.resumes import router as resumes_router
from backend.app.api.v1.jobs import router as jobs_router
from backend.app.api.v1.companies import router as companies_router
from backend.app.api.v1.recruiters import router as recruiters_router
from backend.app.api.v1.matching import router as matching_router
from backend.app.api.v1.outreach import router as outreach_router
from backend.app.api.v1.approvals import router as approvals_router
from backend.app.api.v1.applications import router as applications_router
from backend.app.api.v1.followups import router as followups_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.billing import router as billing_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    yield
    logger.info("Shutting down CareerPilot AI backend...")


app = FastAPI(
    title=settings.APP_NAME,
    description="CareerPilot AI - Multi-Tenant AI-powered Job Discovery, Networking and Outreach Agent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": settings.DATABASE_URL.split("://")[0]
    }


# Include All API Routers under /api/v1
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(onboarding_router, prefix=f"{settings.API_V1_STR}/onboarding", tags=["User Onboarding"])
app.include_router(resumes_router, prefix=f"{settings.API_V1_STR}/resumes", tags=["Resume Management"])
app.include_router(jobs_router, prefix=f"{settings.API_V1_STR}/jobs", tags=["Job Discovery"])
app.include_router(companies_router, prefix=f"{settings.API_V1_STR}/companies", tags=["Companies"])
app.include_router(recruiters_router, prefix=f"{settings.API_V1_STR}/recruiters", tags=["Recruiter Intelligence"])
app.include_router(matching_router, prefix=f"{settings.API_V1_STR}/matching", tags=["AI Matching"])
app.include_router(outreach_router, prefix=f"{settings.API_V1_STR}/outreach", tags=["Outreach Agent"])
app.include_router(approvals_router, prefix=f"{settings.API_V1_STR}/approvals", tags=["Approval Center"])
app.include_router(applications_router, prefix=f"{settings.API_V1_STR}/applications", tags=["Application CRM"])
app.include_router(followups_router, prefix=f"{settings.API_V1_STR}/followups", tags=["Follow-up Manager"])
app.include_router(analytics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["Real-time Analytics"])
app.include_router(billing_router, prefix=f"{settings.API_V1_STR}/billing", tags=["SaaS Billing & Quotas"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."}
    )
