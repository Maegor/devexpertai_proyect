import enum
import uuid
from datetime import datetime, date

from sqlalchemy import String, Text, Boolean, Enum as PgEnum, DateTime, Date, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class InternalRole(str, enum.Enum):
    Sales = "Sales"
    Finance = "Finance"
    Admin = "Admin"


internal_role_enum = PgEnum(
    InternalRole,
    name="internal_role",
    create_type=True,
)



class InternalUser(Base):
    __tablename__ = "internal_users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    totp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    role: Mapped[InternalRole] = mapped_column(
        internal_role_enum, nullable=False, default=InternalRole.Sales
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), onupdate=func.now()
    )


class PartnerStatus(str, enum.Enum):
    PendingReview = "Pending Review"
    Active = "Active"
    Suspended = "Suspended"
    Inactive = "Inactive"
    Rejected = "Rejected"


partner_status_enum = PgEnum(
    PartnerStatus,
    name="partner_status",
    create_type=True,
)


class Partner(Base):
    __tablename__ = "partners"

    # System Identifiers
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    fp_promoter_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent_partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id"), nullable=True
    )

    # Profile and Basic Data
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    collaboration_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_sales_rep_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("internal_users.id"), nullable=True
    )
    language_preference: Mapped[str] = mapped_column(String(10), default="en")

    # Operational and Commercial Configuration
    referral_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    deals_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[PartnerStatus] = mapped_column(
        partner_status_enum, nullable=False, default=PartnerStatus.PendingReview
    )

    # Terms and Conditions
    tc_version_accepted: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tc_acceptance_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    tc_acceptance_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    tc_accepted_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Billing and Accounting
    qb_account_referral: Mapped[str | None] = mapped_column(String(255), nullable=True)
    qb_account_fixed: Mapped[str | None] = mapped_column(String(255), nullable=True)
    self_billing_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Audit Trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    parent: Mapped["Partner | None"] = relationship("Partner", remote_side="Partner.id", foreign_keys=[parent_partner_id])
    assigned_sales_rep: Mapped["InternalUser | None"] = relationship("InternalUser", foreign_keys=[assigned_sales_rep_id])
    billing_entities: Mapped[list["BillingEntity"]] = relationship("BillingEntity", back_populates="partner", cascade="all, delete-orphan")
    partner_campaigns: Mapped[list["PartnerCampaign"]] = relationship("PartnerCampaign", back_populates="partner", cascade="all, delete-orphan")
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="partner", cascade="all, delete-orphan")


class InvoiceType(str, enum.Enum):
    Variable = "Variable"
    Fixed    = "Fixed"


invoice_type_enum = PgEnum(InvoiceType, name="invoice_type", create_type=True)


class InvoiceStatus(str, enum.Enum):
    Sent           = "Sent"
    UnderReview    = "Under review"
    Approved       = "Approved"
    PendingPayment = "Pending payment"
    Paid           = "Paid"
    Rejected       = "Rejected"
    Cancelled      = "Cancelled"


invoice_status_enum = PgEnum(InvoiceStatus, name="invoice_status", create_type=True)


class BillingEntity(Base):
    __tablename__ = "billing_entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False
    )

    # Legal Data
    entity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    tax_identification_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vat_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Banking Details
    banking_details: Mapped[str | None] = mapped_column(Text, nullable=True)

    # History Control
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Audit Trail
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now()
    )

    # Relationships
    partner: Mapped["Partner"] = relationship("Partner", back_populates="billing_entities")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False
    )
    billing_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("billing_entities.id"), nullable=True
    )

    invoice_type: Mapped[InvoiceType] = mapped_column("type", invoice_type_enum, nullable=False)
    invoice_reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    period_from: Mapped[date] = mapped_column(Date, nullable=False)
    period_to: Mapped[date] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)

    net_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    vat_amount: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    gross_total: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[str | None] = mapped_column(String(50), nullable=True)

    pdf_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        invoice_status_enum, nullable=False, default=InvoiceStatus.Sent
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    partner: Mapped["Partner"] = relationship("Partner", foreign_keys=[partner_id])
    billing_entity: Mapped["BillingEntity | None"] = relationship("BillingEntity", foreign_keys=[billing_entity_id])


class RewardStatus(str, enum.Enum):
    Pending  = "Pending"
    Paid     = "Paid"
    Rejected = "Rejected"


reward_status_enum = PgEnum(RewardStatus, name="reward_status", create_type=True)


class Reward(Base):
    __tablename__ = "rewards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False
    )
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False
    )
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    reward_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[RewardStatus] = mapped_column(
        reward_status_enum, nullable=False, default=RewardStatus.Pending
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    partner: Mapped["Partner"] = relationship("Partner", foreign_keys=[partner_id])
    invoice: Mapped["Invoice | None"] = relationship("Invoice", foreign_keys=[invoice_id])


# ── Partner Deal ──────────────────────────────────────────────────────────────

class PartnerDealStatus(str, enum.Enum):
    Proposal       = "Proposal"
    PendingClosure = "Pending closure"
    Closed         = "Closed"
    Active         = "Active"
    Completed      = "Completed"


partner_deal_status_enum = PgEnum(
    PartnerDealStatus, name="partner_deal_status", create_type=True
)


class PartnerDeal(Base):
    __tablename__ = "partner_deals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[PartnerDealStatus] = mapped_column(
        partner_deal_status_enum, nullable=False, default=PartnerDealStatus.Proposal
    )
    start_month: Mapped[date] = mapped_column(Date, nullable=False)
    end_month: Mapped[date] = mapped_column(Date, nullable=False)
    total_cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    partner: Mapped["Partner"] = relationship("Partner", foreign_keys=[partner_id])


# ── Lead ──────────────────────────────────────────────────────────────────────

class LeadStatus(str, enum.Enum):
    New       = "New"
    Contacted = "Contacted"
    Qualified = "Qualified"
    Proposal  = "Proposal"
    Won       = "Won"
    Lost      = "Lost"


lead_status_enum = PgEnum(LeadStatus, name="lead_status", create_type=True)


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[LeadStatus] = mapped_column(
        lead_status_enum, nullable=False, default=LeadStatus.New
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    partner: Mapped["Partner"] = relationship("Partner", back_populates="leads")


# ── Campaign ──────────────────────────────────────────────────────────────────

class CampaignStatus(str, enum.Enum):
    pending   = "pending"
    active    = "active"
    cancelled = "cancelled"
    finished  = "finished"


campaign_status_enum = PgEnum(CampaignStatus, name="campaign_status", create_type=True)


class PartnerCampaignStatus(str, enum.Enum):
    pending   = "pending"
    active    = "active"
    cancelled = "cancelled"
    finished  = "finished"


partner_campaign_status_enum = PgEnum(
    PartnerCampaignStatus, name="partner_campaign_status", create_type=True
)


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    coupon: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(campaign_status_enum, nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    partner_campaigns: Mapped[list["PartnerCampaign"]] = relationship(
        "PartnerCampaign", back_populates="campaign", cascade="all, delete-orphan"
    )


class PartnerCampaign(Base):
    __tablename__ = "partner_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    coupon: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[PartnerCampaignStatus] = mapped_column(
        partner_campaign_status_enum, nullable=False
    )
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    partner: Mapped["Partner"] = relationship("Partner", back_populates="partner_campaigns")
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="partner_campaigns")
