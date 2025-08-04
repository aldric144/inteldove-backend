from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, CaseType, RiskLevel

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    organization: Optional[str] = None
    badge_number: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    organization: Optional[str]
    badge_number: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class CaseCreate(BaseModel):
    title: str
    case_type: CaseType
    description: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    incident_date: Optional[datetime] = None

class CaseResponse(BaseModel):
    id: int
    case_number: str
    title: str
    case_type: CaseType
    description: Optional[str]
    location_city: Optional[str]
    location_state: Optional[str]
    incident_date: Optional[datetime]
    risk_score: Optional[float]
    risk_level: Optional[RiskLevel]
    created_at: datetime
    created_by: UserResponse
    
    class Config:
        from_attributes = True

class SuspectCreate(BaseModel):
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    race: Optional[str] = None
    relationship_to_victim: Optional[str] = None
    criminal_history: Optional[str] = None
    mental_health_history: Optional[str] = None
    substance_abuse: Optional[bool] = None
    firearm_access: Optional[bool] = None
    employment_status: Optional[str] = None

class VictimCreate(BaseModel):
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    race: Optional[str] = None
    relationship_to_suspect: Optional[str] = None
    children_involved: Optional[bool] = None
    financial_dependence: Optional[bool] = None
    isolation_level: Optional[str] = None
    prior_dv_reports: Optional[int] = None
    protection_order_history: Optional[str] = None

class DocumentUpload(BaseModel):
    filename: str
    file_type: str

class LethalityAssessmentCreate(BaseModel):
    case_id: int
    assessment_data: dict
    
class LethalityAssessmentResponse(BaseModel):
    id: int
    lethality_score: float
    risk_level: RiskLevel
    recommendations: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class AIAnalysisRequest(BaseModel):
    case_id: int
    analysis_type: str  # "suspect_profile", "victim_profile", "risk_assessment"

class AIAnalysisResponse(BaseModel):
    analysis_type: str
    results: dict
    confidence_score: float
    recommendations: List[str]
