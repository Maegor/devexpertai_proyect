import uuid

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt as _bcrypt

from database import get_db
from models import Partner, PartnerStatus, PartnerDealStatus
import repositories.internal_user as user_repo
import repositories.partner as partner_repo
import repositories.invoice as invoice_repo
import repositories.reward as reward_repo
import repositories.partner_deal as deal_repo
import repositories.lead as lead_repo
from schemas.partner import PartnerUpdate

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


def _verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def get_current_user_id(request: Request) -> str | None:
    return request.session.get("admin_user_id")


async def _get_partner_kpis(db: AsyncSession) -> dict:
    result = await db.execute(
        select(Partner.status, func.count(Partner.id).label("n")).group_by(Partner.status)
    )
    counts = {row.status: row.n for row in result.all()}
    total = sum(counts.values())
    return {
        "total": total,
        "active": counts.get(PartnerStatus.Active, 0),
        "inactive": counts.get(PartnerStatus.Inactive, 0),
        "pending_review": counts.get(PartnerStatus.PendingReview, 0),
        "suspended": counts.get(PartnerStatus.Suspended, 0),
        "rejected": counts.get(PartnerStatus.Rejected, 0),
    }


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def admin_root(request: Request):
    if get_current_user_id(request):
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    return RedirectResponse(url="/admin/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    if get_current_user_id(request):
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    return templates.TemplateResponse(request, "admin/login.html", {"error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    user = await user_repo.get_by_email(db, email.strip())
    if not user or not _verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request, "admin/login.html",
            {"error": "Email o contraseña incorrectos."},
            status_code=401,
        )
    if not user.is_active:
        return templates.TemplateResponse(
            request, "admin/login.html",
            {"error": "Tu cuenta está inactiva."},
            status_code=403,
        )
    request.session["admin_user_id"] = str(user.id)
    request.session["admin_user_name"] = user.name
    return RedirectResponse(url="/admin/dashboard", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=302)


# ── Shell ─────────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not get_current_user_id(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {"user_name": request.session.get("admin_user_name", "")},
    )


# ── Partners section ──────────────────────────────────────────────────────────

@router.get("/partners-section", response_class=HTMLResponse)
async def partners_section(request: Request, db: AsyncSession = Depends(get_db)):
    if not get_current_user_id(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    kpis = await _get_partner_kpis(db)
    return templates.TemplateResponse(
        request, "admin/partials/partners_section.html",
        {"kpis": kpis, "active_sub": "dashboard"},
    )


@router.get("/partners/dashboard", response_class=HTMLResponse)
async def partners_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    if not get_current_user_id(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    kpis = await _get_partner_kpis(db)
    return templates.TemplateResponse(
        request, "admin/partials/partners_dashboard.html", {"kpis": kpis}
    )


@router.get("/partners", response_class=HTMLResponse)
async def partners_list(request: Request, db: AsyncSession = Depends(get_db)):
    if not get_current_user_id(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    partners = await partner_repo.get_all(db)
    return templates.TemplateResponse(
        request, "admin/partials/partners_list.html", {"partners": partners}
    )


@router.get("/partners/{partner_id}/detail", response_class=HTMLResponse)
async def partner_detail(
    request: Request,
    partner_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    if not get_current_user_id(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    partner = await partner_repo.get_by_id(db, partner_id)
    if not partner:
        return HTMLResponse("<p style='color:#e85454;'>Partner not found.</p>", status_code=404)
    invoices = await invoice_repo.get_by_partner(db, partner_id)
    invoices_sorted = sorted(invoices, key=lambda i: i.created_at, reverse=True)
    rewards = await reward_repo.get_by_partner(db, partner_id)
    rewards_sorted = sorted(rewards, key=lambda r: r.transaction_date, reverse=True)
    leads = await lead_repo.get_by_partner(db, partner_id)
    leads_sorted = sorted(leads, key=lambda l: l.created_at, reverse=True)
    return templates.TemplateResponse(
        request, "admin/partials/partner_detail.html",
        {"partner": partner, "invoices": invoices_sorted, "rewards": rewards_sorted, "leads": leads_sorted},
    )


@router.get("/partners/{partner_id}/edit", response_class=HTMLResponse)
async def partner_edit_get(
    request: Request,
    partner_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    if not get_current_user_id(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    partner = await partner_repo.get_by_id(db, partner_id)
    if not partner:
        return HTMLResponse("<p style='color:#e85454;'>Partner not found.</p>", status_code=404)
    return templates.TemplateResponse(
        request, "admin/partials/partner_edit.html",
        {"partner": partner, "status_options": [s.value for s in PartnerStatus], "error": None},
    )


@router.post("/partners/{partner_id}/edit", response_class=HTMLResponse)
async def partner_edit_post(
    request: Request,
    partner_id: uuid.UUID,
    name: str = Form(...),
    email: str = Form(...),
    company_name: str = Form(""),
    website: str = Form(""),
    country: str = Form(""),
    status: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    if not get_current_user_id(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    partner = await partner_repo.get_by_id(db, partner_id)
    if not partner:
        return HTMLResponse("<p style='color:#e85454;'>Partner not found.</p>", status_code=404)

    try:
        partner_status = PartnerStatus(status)
    except ValueError:
        return templates.TemplateResponse(
            request, "admin/partials/partner_edit.html",
            {"partner": partner, "status_options": [s.value for s in PartnerStatus], "error": "Invalid status value."},
        )

    await partner_repo.update(db, partner, PartnerUpdate(
        name=name.strip(),
        email=email.strip(),
        company_name=company_name.strip() or None,
        website=website.strip() or None,
        country=country.strip() or None,
        status=partner_status,
    ))

    partner = await partner_repo.get_by_id(db, partner_id)
    invoices = await invoice_repo.get_by_partner(db, partner_id)
    invoices_sorted = sorted(invoices, key=lambda i: i.created_at, reverse=True)
    rewards = await reward_repo.get_by_partner(db, partner_id)
    rewards_sorted = sorted(rewards, key=lambda r: r.transaction_date, reverse=True)
    leads = await lead_repo.get_by_partner(db, partner_id)
    leads_sorted = sorted(leads, key=lambda l: l.created_at, reverse=True)
    return templates.TemplateResponse(
        request, "admin/partials/partner_detail.html",
        {"partner": partner, "invoices": invoices_sorted, "rewards": rewards_sorted, "leads": leads_sorted},
    )


@router.get("/partners/{partner_id}/invoices/{invoice_id}", response_class=HTMLResponse)
async def partner_invoice_detail(
    request: Request,
    partner_id: uuid.UUID,
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    if not get_current_user_id(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    invoice = await invoice_repo.get_by_id(db, invoice_id)
    if not invoice or invoice.partner_id != partner_id:
        return HTMLResponse("<p style='color:#e85454;'>Invoice not found.</p>", status_code=404)
    rewards = await reward_repo.get_by_invoice(db, invoice_id)
    rewards_sorted = sorted(rewards, key=lambda r: r.transaction_date, reverse=True)
    return templates.TemplateResponse(
        request, "partners/partials/invoice_detail.html",
        {
            "invoice": invoice,
            "rewards": rewards_sorted,
            "back_url": f"/admin/partners/{partner_id}/detail",
            "back_target": "#partners-main",
        },
    )


@router.get("/partners/{partner_id}/leads/{lead_id}", response_class=HTMLResponse)
async def partner_lead_detail(
    request: Request,
    partner_id: uuid.UUID,
    lead_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    if not get_current_user_id(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    lead = await lead_repo.get_by_id(db, lead_id)
    if not lead or lead.partner_id != partner_id:
        return HTMLResponse("<p style='color:#e85454;'>Lead not found.</p>", status_code=404)
    partner = await partner_repo.get_by_id(db, partner_id)
    return templates.TemplateResponse(
        request, "admin/partials/lead_detail.html",
        {
            "lead": lead,
            "partner": partner,
            "back_url": f"/admin/partners/{partner_id}/detail",
        },
    )


# ── Internal users section ────────────────────────────────────────────────────

@router.get("/internal_users", response_class=HTMLResponse)
async def internal_users_list(request: Request, db: AsyncSession = Depends(get_db)):
    if not get_current_user_id(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    users = await user_repo.get_all(db)
    return templates.TemplateResponse(
        request, "admin/partials/internal_users.html", {"users": users}
    )


# ── Deals section ────────────────────────────────────────────────────────────

@router.get("/deals", response_class=HTMLResponse)
async def deals_list(request: Request, db: AsyncSession = Depends(get_db)):
    if not get_current_user_id(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    deals = await deal_repo.get_all(db)
    partners = await partner_repo.get_all(db)
    partner_map = {str(p.id): p.name for p in partners}
    return templates.TemplateResponse(
        request, "admin/partials/deals_section.html",
        {
            "deals": deals,
            "partner_map": partner_map,
            "partners": sorted(partners, key=lambda p: p.name),
            "status_options": [s.value for s in PartnerDealStatus],
        },
    )


@router.get("/deals/{deal_id}/detail", response_class=HTMLResponse)
async def deal_detail(
    request: Request,
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    if not get_current_user_id(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    deal = await deal_repo.get_by_id(db, deal_id)
    if not deal:
        return HTMLResponse("<p style='color:#e85454;'>Deal not found.</p>", status_code=404)
    partner = await partner_repo.get_by_id(db, deal.partner_id)
    return templates.TemplateResponse(
        request, "admin/partials/deal_detail.html",
        {"deal": deal, "partner": partner},
    )
