from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid
from datetime import datetime, timedelta

from app.database import get_db, create_tables
from app.models import User, Case, Suspect, Victim, Document, Profile, LethalityAssessment, UserRole, CaseType
from app.schemas import (
    UserCreate, UserResponse, LoginRequest, TokenResponse,
    CaseCreate, CaseResponse, SuspectCreate, VictimCreate,
    LethalityAssessmentCreate, LethalityAssessmentResponse,
    AIAnalysisRequest, AIAnalysisResponse
)
from app.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, require_role
)
from app.ai_services import AIAnalysisService
from app.ocr_service import OCRService

app = FastAPI(title="INTELDOVE™ API", description="Intelligence for Domestic Violence Events")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

ai_service = None
ocr_service = None

def get_ai_service():
    global ai_service
    if ai_service is None:
        ai_service = AIAnalysisService()
    return ai_service

def get_ocr_service():
    global ocr_service
    if ocr_service is None:
        ocr_service = OCRService()
    return ocr_service

@app.on_event("startup")
async def startup_event():
    create_tables()

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        organization=user_data.organization,
        badge_number=user_data.badge_number
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@app.post("/auth/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/cases", response_model=CaseResponse)
async def create_case(
    case_data: CaseCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.FEDERAL_AGENT, UserRole.LAW_ENFORCEMENT, UserRole.ADVOCATE])),
    db: Session = Depends(get_db)
):
    case_number = f"INTELDOVE-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    case = Case(
        case_number=case_number,
        title=case_data.title,
        case_type=case_data.case_type,
        description=case_data.description,
        location_city=case_data.location_city,
        location_state=case_data.location_state,
        incident_date=case_data.incident_date,
        created_by_id=current_user.id
    )
    
    db.add(case)
    db.commit()
    db.refresh(case)
    
    return case

@app.get("/cases", response_model=List[CaseResponse])
async def get_cases(
    skip: int = 0,
    limit: int = 100,
    case_type: Optional[CaseType] = None,
    state: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Case)
    
    if current_user.role == UserRole.PUBLIC:
        query = query.filter(Case.risk_level.isnot(None))
    
    if case_type:
        query = query.filter(Case.case_type == case_type)
    
    if state:
        query = query.filter(Case.location_state == state)
    
    cases = query.offset(skip).limit(limit).all()
    return cases

@app.get("/cases/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if current_user.role == UserRole.PUBLIC:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return case

@app.post("/cases/{case_id}/suspects")
async def add_suspect(
    case_id: int,
    suspect_data: SuspectCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.FEDERAL_AGENT, UserRole.LAW_ENFORCEMENT])),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    suspect = Suspect(case_id=case_id, **suspect_data.dict())
    db.add(suspect)
    db.commit()
    db.refresh(suspect)
    
    return suspect

@app.post("/cases/{case_id}/victims")
async def add_victim(
    case_id: int,
    victim_data: VictimCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.FEDERAL_AGENT, UserRole.LAW_ENFORCEMENT, UserRole.ADVOCATE])),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    victim = Victim(case_id=case_id, **victim_data.dict())
    db.add(victim)
    db.commit()
    db.refresh(victim)
    
    return victim

@app.post("/cases/{case_id}/documents")
async def upload_document(
    case_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.FEDERAL_AGENT, UserRole.LAW_ENFORCEMENT, UserRole.ADVOCATE])),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    file_content = await file.read()
    
    document = Document(
        case_id=case_id,
        filename=file.filename,
        file_type=file.content_type,
        file_size=len(file_content),
        uploaded_by_id=current_user.id
    )
    
    if file.content_type and file.content_type.startswith('image/'):
        extracted_text = get_ocr_service().extract_text_from_image(file_content)
        document.extracted_text = extracted_text
        document.processing_status = "completed"
        
        entities = get_ocr_service().extract_entities_from_text(extracted_text)
        case.key_entities = str(entities)  # Store as JSON string
        
        analysis = get_ocr_service().analyze_document_content(extracted_text)
        case.extracted_text = extracted_text
        
    else:
        document.processing_status = "pending"
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return {"document_id": document.id, "status": document.processing_status}

@app.post("/ai/analyze", response_model=AIAnalysisResponse)
async def run_ai_analysis(
    analysis_request: AIAnalysisRequest,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.FEDERAL_AGENT, UserRole.LAW_ENFORCEMENT, UserRole.ADVOCATE])),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == analysis_request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if analysis_request.analysis_type == "suspect_profile":
        suspects = db.query(Suspect).filter(Suspect.case_id == case.id).all()
        if not suspects:
            raise HTTPException(status_code=400, detail="No suspects found for analysis")
        
        analysis = await get_ai_service().analyze_suspect_profile(case, suspects[0])
        
        profile = Profile(
            case_id=case.id,
            profile_type="suspect",
            psychological_profile=analysis.get("psychological_profile", ""),
            behavioral_patterns=str(analysis.get("behavioral_patterns", [])),
            risk_factors=str(analysis.get("risk_factors", [])),
            warning_signs=str(analysis.get("warning_signs", [])),
            recommendations=str(analysis.get("recommendations", [])),
            confidence_score=analysis.get("confidence_score", 0.0)
        )
        db.add(profile)
        
    elif analysis_request.analysis_type == "victim_profile":
        victims = db.query(Victim).filter(Victim.case_id == case.id).all()
        if not victims:
            raise HTTPException(status_code=400, detail="No victims found for analysis")
        
        analysis = await get_ai_service().analyze_victim_vulnerability(case, victims[0])
        
        profile = Profile(
            case_id=case.id,
            profile_type="victim",
            psychological_profile=analysis.get("vulnerability_profile", ""),
            behavioral_patterns=str(analysis.get("trauma_indicators", [])),
            risk_factors=str(analysis.get("risk_factors", [])),
            warning_signs=str(analysis.get("protective_factors", [])),
            recommendations=str(analysis.get("safety_recommendations", [])),
            confidence_score=analysis.get("confidence_score", 0.0)
        )
        db.add(profile)
        
    else:
        raise HTTPException(status_code=400, detail="Invalid analysis type")
    
    db.commit()
    
    return {
        "analysis_type": analysis_request.analysis_type,
        "results": analysis,
        "confidence_score": analysis.get("confidence_score", 0.0),
        "recommendations": analysis.get("recommendations", [])
    }

@app.post("/lethality-assessment", response_model=LethalityAssessmentResponse)
async def create_lethality_assessment(
    assessment_data: LethalityAssessmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == assessment_data.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    score, risk_level = get_ai_service().calculate_lethality_score(assessment_data.assessment_data)
    
    recommendations = []
    if risk_level.value == "extreme":
        recommendations = [
            "Immediate law enforcement notification",
            "Emergency safety planning",
            "Consider emergency relocation",
            "24/7 safety monitoring"
        ]
    elif risk_level.value == "high":
        recommendations = [
            "Comprehensive safety planning",
            "Law enforcement notification",
            "Increased support services",
            "Regular check-ins"
        ]
    elif risk_level.value == "moderate":
        recommendations = [
            "Safety planning",
            "Resource connection",
            "Regular monitoring"
        ]
    else:
        recommendations = [
            "Basic safety planning",
            "Resource information"
        ]
    
    assessment = LethalityAssessment(
        case_id=assessment_data.case_id,
        assessment_data=str(assessment_data.assessment_data),
        lethality_score=score,
        risk_level=risk_level,
        recommendations="; ".join(recommendations),
        created_by_id=current_user.id
    )
    
    case.risk_score = score
    case.risk_level = risk_level
    
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    return assessment

@app.get("/cases/{case_id}/similar")
async def find_similar_cases(
    case_id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.FEDERAL_AGENT, UserRole.LAW_ENFORCEMENT, UserRole.RESEARCHER])),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    all_cases = db.query(Case).filter(Case.id != case_id).all()
    
    matches = get_ai_service().find_pattern_matches(case, all_cases)
    
    return {"similar_cases": matches}

@app.get("/statistics/overview")
async def get_statistics_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_cases = db.query(Case).count()
    high_risk_cases = db.query(Case).filter(Case.risk_level.in_(["high", "extreme"])).count()
    recent_cases = db.query(Case).filter(
        Case.created_at >= datetime.utcnow() - timedelta(days=30)
    ).count()
    
    return {
        "total_cases": total_cases,
        "high_risk_cases": high_risk_cases,
        "recent_cases": recent_cases,
        "risk_distribution": {
            "low": db.query(Case).filter(Case.risk_level == "low").count(),
            "moderate": db.query(Case).filter(Case.risk_level == "moderate").count(),
            "high": db.query(Case).filter(Case.risk_level == "high").count(),
            "extreme": db.query(Case).filter(Case.risk_level == "extreme").count()
        }
    }

@app.get("/statistics/heatmap")
async def get_heatmap_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cases_by_state = db.query(Case.location_state, func.count(Case.id)).group_by(Case.location_state).all()
    
    heatmap_data = []
    for state, count in cases_by_state:
        if state:
            heatmap_data.append({
                "state": state,
                "case_count": count,
                "high_risk_count": db.query(Case).filter(
                    Case.location_state == state,
                    Case.risk_level.in_(["high", "extreme"])
                ).count()
            })
    
    return {"heatmap_data": heatmap_data}
