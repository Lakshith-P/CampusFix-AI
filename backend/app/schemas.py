from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
class LoginIn(BaseModel):
    email: EmailStr
    password: str
class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    specialization: str = ""
    available: bool = True
    model_config = ConfigDict(from_attributes=True)
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
class ComplaintIn(BaseModel):
    title: str = Field(min_length=4, max_length=180)
    description: str = Field(min_length=8, max_length=8000)
    location: str = Field(min_length=2, max_length=180)
    ai_mode: str = "auto"
    ai_provider: str = "auto"
    ai_model: str = "auto"
    ai_second_provider: str = "groq"
    ai_second_model: str = ""
class ComplaintUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    category: str | None = None
    assigned_to_id: int | None = None
    resolution_note: str | None = Field(default=None, max_length=3000)
class ComplaintOut(BaseModel):
    id: int
    title: str
    description: str
    category: str
    priority: str
    status: str
    location: str
    reporter_id: int
    assigned_to_id: int | None
    ai_provider: str
    ai_model: str
    ai_confidence: float
    ai_review_required: bool
    resolution_note: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
