from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum


# Enums for status tracking
class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MedicationType(str, Enum):
    TABLET = "tablet"
    CAPSULE = "capsule"
    SYRUP = "syrup"
    INJECTION = "injection"
    DROPS = "drops"
    CREAM = "cream"
    OINTMENT = "ointment"
    OTHER = "other"


# Persistent models (stored in database)
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    email: str = Field(unique=True, max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    prescription_images: List["PrescriptionImage"] = Relationship(back_populates="user")
    analysis_sessions: List["AnalysisSession"] = Relationship(back_populates="user")


class PrescriptionImage(SQLModel, table=True):
    __tablename__ = "prescription_images"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(max_length=255)
    original_filename: str = Field(max_length=255)
    file_path: str = Field(max_length=500)
    file_size: int = Field(gt=0)  # File size in bytes
    mime_type: str = Field(max_length=100)
    width: Optional[int] = Field(default=None, ge=0)
    height: Optional[int] = Field(default=None, ge=0)
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Foreign keys
    user_id: int = Field(foreign_key="users.id")

    # Relationships
    user: User = Relationship(back_populates="prescription_images")
    prescriptions: List["Prescription"] = Relationship(back_populates="image")
    analysis_sessions: List["AnalysisSession"] = Relationship(back_populates="image")


class AnalysisSession(SQLModel, table=True):
    __tablename__ = "analysis_sessions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    status: AnalysisStatus = Field(default=AnalysisStatus.PENDING)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    processing_time_seconds: Optional[Decimal] = Field(default=None, decimal_places=3)

    # AI model information
    model_name: str = Field(default="gemini-flash", max_length=100)
    model_version: Optional[str] = Field(default=None, max_length=50)

    # Error handling
    error_message: Optional[str] = Field(default=None, max_length=1000)
    error_code: Optional[str] = Field(default=None, max_length=50)

    # Raw AI response for debugging/audit
    raw_response: Optional[Dict[str, Any]] = Field(default={}, sa_column=Column(JSON))
    confidence_score: Optional[Decimal] = Field(default=None, decimal_places=3, ge=0.0, le=1.0)

    # Foreign keys
    user_id: int = Field(foreign_key="users.id")
    image_id: int = Field(foreign_key="prescription_images.id")

    # Relationships
    user: User = Relationship(back_populates="analysis_sessions")
    image: PrescriptionImage = Relationship(back_populates="analysis_sessions")
    prescriptions: List["Prescription"] = Relationship(back_populates="analysis_session")


class Prescription(SQLModel, table=True):
    __tablename__ = "prescriptions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)

    # Doctor and patient information
    doctor_name: Optional[str] = Field(default=None, max_length=200)
    doctor_license: Optional[str] = Field(default=None, max_length=100)
    clinic_name: Optional[str] = Field(default=None, max_length=200)
    clinic_address: Optional[str] = Field(default=None, max_length=500)

    patient_name: Optional[str] = Field(default=None, max_length=200)
    patient_age: Optional[int] = Field(default=None, ge=0, le=150)
    patient_gender: Optional[str] = Field(default=None, max_length=20)

    # Prescription details
    prescription_date: Optional[datetime] = Field(default=None)
    prescription_number: Optional[str] = Field(default=None, max_length=100)
    diagnosis: Optional[str] = Field(default=None, max_length=1000)
    notes: Optional[str] = Field(default=None, max_length=2000)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Foreign keys
    image_id: int = Field(foreign_key="prescription_images.id")
    analysis_session_id: int = Field(foreign_key="analysis_sessions.id")

    # Relationships
    image: PrescriptionImage = Relationship(back_populates="prescriptions")
    analysis_session: AnalysisSession = Relationship(back_populates="prescriptions")
    medications: List["Medication"] = Relationship(back_populates="prescription")


class Medication(SQLModel, table=True):
    __tablename__ = "medications"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)

    # Basic medication information
    name: str = Field(max_length=200)
    generic_name: Optional[str] = Field(default=None, max_length=200)
    brand_name: Optional[str] = Field(default=None, max_length=200)
    medication_type: Optional[MedicationType] = Field(default=None)

    # Dosage information
    strength: Optional[str] = Field(default=None, max_length=100)  # e.g., "500mg", "5mg/ml"
    dosage_form: Optional[str] = Field(default=None, max_length=100)  # e.g., "tablet", "capsule"

    # Administration instructions
    dosage_instructions: Optional[str] = Field(default=None, max_length=500)
    frequency: Optional[str] = Field(default=None, max_length=200)  # e.g., "twice daily", "every 8 hours"
    duration: Optional[str] = Field(default=None, max_length=200)  # e.g., "7 days", "until finished"
    quantity: Optional[str] = Field(default=None, max_length=100)  # e.g., "30 tablets", "100ml"

    # Special instructions
    before_after_meal: Optional[str] = Field(default=None, max_length=100)  # e.g., "after meal", "empty stomach"
    special_instructions: Optional[str] = Field(default=None, max_length=1000)

    # Metadata
    order_index: int = Field(default=0, ge=0)  # Order in which medications appear in prescription
    confidence_score: Optional[Decimal] = Field(default=None, decimal_places=3, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Foreign key
    prescription_id: int = Field(foreign_key="prescriptions.id")

    # Relationships
    prescription: Prescription = Relationship(back_populates="medications")


# Non-persistent schemas (for validation, forms, API requests/responses)
class UserCreate(SQLModel, table=False):
    name: str = Field(max_length=100)
    email: str = Field(max_length=255)


class UserResponse(SQLModel, table=False):
    id: int
    name: str
    email: str
    is_active: bool
    created_at: str  # Will be converted from datetime using .isoformat()


class PrescriptionImageUpload(SQLModel, table=False):
    filename: str = Field(max_length=255)
    file_size: int = Field(gt=0)
    mime_type: str = Field(max_length=100)
    width: Optional[int] = Field(default=None, ge=0)
    height: Optional[int] = Field(default=None, ge=0)


class PrescriptionImageResponse(SQLModel, table=False):
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    width: Optional[int]
    height: Optional[int]
    upload_timestamp: str


class AnalysisSessionCreate(SQLModel, table=False):
    image_id: int
    model_name: str = Field(default="gemini-flash", max_length=100)
    model_version: Optional[str] = Field(default=None, max_length=50)


class AnalysisSessionResponse(SQLModel, table=False):
    id: int
    status: AnalysisStatus
    started_at: str
    completed_at: Optional[str]
    processing_time_seconds: Optional[Decimal]
    model_name: str
    confidence_score: Optional[Decimal]
    error_message: Optional[str]


class MedicationCreate(SQLModel, table=False):
    name: str = Field(max_length=200)
    generic_name: Optional[str] = Field(default=None, max_length=200)
    brand_name: Optional[str] = Field(default=None, max_length=200)
    medication_type: Optional[MedicationType] = Field(default=None)
    strength: Optional[str] = Field(default=None, max_length=100)
    dosage_form: Optional[str] = Field(default=None, max_length=100)
    dosage_instructions: Optional[str] = Field(default=None, max_length=500)
    frequency: Optional[str] = Field(default=None, max_length=200)
    duration: Optional[str] = Field(default=None, max_length=200)
    quantity: Optional[str] = Field(default=None, max_length=100)
    before_after_meal: Optional[str] = Field(default=None, max_length=100)
    special_instructions: Optional[str] = Field(default=None, max_length=1000)
    order_index: int = Field(default=0, ge=0)
    confidence_score: Optional[Decimal] = Field(default=None, decimal_places=3, ge=0.0, le=1.0)


class MedicationResponse(SQLModel, table=False):
    id: int
    name: str
    generic_name: Optional[str]
    brand_name: Optional[str]
    medication_type: Optional[MedicationType]
    strength: Optional[str]
    dosage_form: Optional[str]
    dosage_instructions: Optional[str]
    frequency: Optional[str]
    duration: Optional[str]
    quantity: Optional[str]
    before_after_meal: Optional[str]
    special_instructions: Optional[str]
    order_index: int
    confidence_score: Optional[Decimal]


class PrescriptionCreate(SQLModel, table=False):
    doctor_name: Optional[str] = Field(default=None, max_length=200)
    doctor_license: Optional[str] = Field(default=None, max_length=100)
    clinic_name: Optional[str] = Field(default=None, max_length=200)
    clinic_address: Optional[str] = Field(default=None, max_length=500)
    patient_name: Optional[str] = Field(default=None, max_length=200)
    patient_age: Optional[int] = Field(default=None, ge=0, le=150)
    patient_gender: Optional[str] = Field(default=None, max_length=20)
    prescription_date: Optional[datetime] = Field(default=None)
    prescription_number: Optional[str] = Field(default=None, max_length=100)
    diagnosis: Optional[str] = Field(default=None, max_length=1000)
    notes: Optional[str] = Field(default=None, max_length=2000)
    image_id: int
    analysis_session_id: int
    medications: List[MedicationCreate] = Field(default=[])


class PrescriptionResponse(SQLModel, table=False):
    id: int
    doctor_name: Optional[str]
    doctor_license: Optional[str]
    clinic_name: Optional[str]
    clinic_address: Optional[str]
    patient_name: Optional[str]
    patient_age: Optional[int]
    patient_gender: Optional[str]
    prescription_date: Optional[str]  # Will be converted from datetime using .isoformat()
    prescription_number: Optional[str]
    diagnosis: Optional[str]
    notes: Optional[str]
    created_at: str
    medications: List[MedicationResponse] = Field(default=[])


class PrescriptionAnalysisResult(SQLModel, table=False):
    """Complete analysis result including session info, prescription, and medications"""

    session: AnalysisSessionResponse
    prescription: Optional[PrescriptionResponse]
    image: PrescriptionImageResponse
