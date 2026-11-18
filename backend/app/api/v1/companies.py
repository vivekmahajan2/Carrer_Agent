import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.company import Company
from backend.app.models.user import User
from backend.app.schemas.company import CompanyCreate, CompanyResponse
from backend.app.api.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=List[CompanyResponse])
def get_companies(
    query: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """List discovered startups and hiring companies."""
    q = db.query(Company)
    if query:
        q = q.filter(Company.name.ilike(f"%{query}%"))
    if industry:
        q = q.filter(Company.industry.ilike(f"%{industry}%"))

    return q.order_by(Company.name.asc()).offset(skip).limit(limit).all()


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    company_in: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Company).filter(Company.name.ilike(company_in.name.strip())).first()
    if existing:
        return existing

    company = Company(
        name=company_in.name.strip(),
        domain=company_in.domain,
        website=company_in.website,
        industry=company_in.industry,
        size=company_in.size,
        headquarters=company_in.headquarters,
        description=company_in.description,
        tech_stack=company_in.tech_stack,
        hiring_signals=company_in.hiring_signals
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

