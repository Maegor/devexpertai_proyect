import uuid
from datetime import datetime

from pydantic import BaseModel

from models import LeadStatus


class LeadCreate(BaseModel):
    partner_id: uuid.UUID
    name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    status: LeadStatus = LeadStatus.New
    notes: str | None = None


class LeadUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    status: LeadStatus | None = None
    notes: str | None = None


class LeadResponse(BaseModel):
    id: uuid.UUID
    partner_id: uuid.UUID
    name: str
    email: str | None
    phone: str | None
    company: str | None
    status: LeadStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
