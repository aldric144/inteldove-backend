from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    FEDERAL_AGENT = "federal_agent"
    LAW_ENFORCEMENT = "law_enforcement"
    ADVOCATE = "advocate"
    RESEARCHER = "researcher"
    PUBLIC = "public"

class CaseType(str, enum.Enum):
    DV_HOMICIDE = "dv_homicide"
    MURDER_SUICIDE = "murder_suicide"
    ATTEMPTED_HOMICIDE = "attempted_homicide"
    MISSING = "missing"
    THREAT_ASSESSMENT = "threat_assessment"

class RiskLevel(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    organization = Column(String)
    badge_number = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    case_type = Column(Enum(CaseType), nullable=False)
    description = Column(Text)
    location_city = Column(String)
    location_state = Column(String)
    location_coordinates = Column(String)
    incident_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    
    extracted_text = Column(Text)
    key_entities = Column(Text)  # JSON string of extracted entities
    
    risk_score = Column(Float)
    risk_level = Column(Enum(RiskLevel))
    ai_analysis = Column(Text)  # JSON string of AI analysis results
    
    created_by = relationship("User")
    suspects = relationship("Suspect", back_populates="case")
    victims = relationship("Victim", back_populates="case")
    documents = relationship("Document", back_populates="case")
    profiles = relationship("Profile", back_populates="case")

class Suspect(Base):
    __tablename__ = "suspects"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    race = Column(String)
    relationship_to_victim = Column(String)
    criminal_history = Column(Text)
    mental_health_history = Column(Text)
    substance_abuse = Column(Boolean)
    firearm_access = Column(Boolean)
    employment_status = Column(String)
    
    case = relationship("Case", back_populates="suspects")

class Victim(Base):
    __tablename__ = "victims"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    race = Column(String)
    relationship_to_suspect = Column(String)
    children_involved = Column(Boolean)
    financial_dependence = Column(Boolean)
    isolation_level = Column(String)
    prior_dv_reports = Column(Integer)
    protection_order_history = Column(Text)
    
    case = relationship("Case", back_populates="victims")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    filename = Column(String, nullable=False)
    file_type = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"))
    
    extracted_text = Column(Text)
    processing_status = Column(String, default="pending")
    
    case = relationship("Case", back_populates="documents")
    uploaded_by = relationship("User")

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    profile_type = Column(String)  # "suspect" or "victim"
    psychological_profile = Column(Text)
    behavioral_patterns = Column(Text)
    risk_factors = Column(Text)
    warning_signs = Column(Text)
    recommendations = Column(Text)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    case = relationship("Case", back_populates="profiles")

class LethalityAssessment(Base):
    __tablename__ = "lethality_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    assessment_data = Column(Text)  # JSON string of assessment responses
    lethality_score = Column(Float)
    risk_level = Column(Enum(RiskLevel))
    recommendations = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    
    created_by = relationship("User")

class PatternMatch(Base):
    __tablename__ = "pattern_matches"
    
    id = Column(Integer, primary_key=True, index=True)
    source_case_id = Column(Integer, ForeignKey("cases.id"))
    matched_case_id = Column(Integer, ForeignKey("cases.id"))
    similarity_score = Column(Float)
    matching_factors = Column(Text)  # JSON string of factors that matched
    created_at = Column(DateTime, default=datetime.utcnow)

class EmergencyVault(Base):
    __tablename__ = "emergency_vault"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    encrypted_data = Column(Text)
    vault_type = Column(String)  # "threat_screenshots", "audio", "photos", "documents"
    dead_man_switch_active = Column(Boolean, default=False)
    last_checkin = Column(DateTime, default=datetime.utcnow)
    emergency_contacts = Column(Text)  # JSON string of emergency contacts
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
