import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Lead
from schemas.lead import LeadCreate, LeadUpdate


async def get_all(db: AsyncSession) -> list[Lead]:
    result = await db.execute(select(Lead))
    return result.scalars().all()


async def get_by_id(db: AsyncSession, lead_id: uuid.UUID) -> Lead | None:
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    return result.scalar_one_or_none()


async def get_by_partner(db: AsyncSession, partner_id: uuid.UUID) -> list[Lead]:
    result = await db.execute(
        select(Lead).where(Lead.partner_id == partner_id)
    )
    return result.scalars().all()


async def create(db: AsyncSession, data: LeadCreate) -> Lead:
    lead = Lead(**data.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead


async def update(db: AsyncSession, lead: Lead, data: LeadUpdate) -> Lead:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    await db.commit()
    await db.refresh(lead)
    return lead


async def delete(db: AsyncSession, lead: Lead) -> None:
    await db.delete(lead)
    await db.commit()
