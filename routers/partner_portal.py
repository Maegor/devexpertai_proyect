import uuid

import bcrypt as _bcrypt
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
import repositories.partner as partner_repo
import repositories.invoice as invoice_repo

router = APIRouter(prefix="/partners", tags=["partner-portal"])
templates = Jinja2Templates(directory="templates")


def _verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def get_current_partner_id(request: Request) -> str | None:
    return request.session.get("partner_id")


# ── Auth ───────────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def portal_root(request: Request):
    if get_current_partner_id(request):
        return RedirectResponse(url="/partners/dashboard", status_code=302)
    return RedirectResponse(url="/partners/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    if get_current_partner_id(request):
        return RedirectResponse(url="/partners/dashboard", status_code=302)
    return templates.TemplateResponse(request, "partners/login.html", {"error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    partner = await partner_repo.get_by_email(db, email.strip())
    if not partner or not partner.password_hash:
        return templates.TemplateResponse(
            request, "partners/login.html",
            {"error": "Email o contraseña incorrectos."},
            status_code=401,
        )
    if not _verify_password(password, partner.password_hash):
        return templates.TemplateResponse(
            request, "partners/login.html",
            {"error": "Email o contraseña incorrectos."},
            status_code=401,
        )
    request.session["partner_id"] = str(partner.id)
    request.session["partner_name"] = partner.name
    return RedirectResponse(url="/partners/dashboard", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    request.session.pop("partner_id", None)
    request.session.pop("partner_name", None)
    return RedirectResponse(url="/partners/login", status_code=302)


# ── Dashboard shell ────────────────────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not get_current_partner_id(request):
        return RedirectResponse(url="/partners/login", status_code=302)
    return templates.TemplateResponse(
        request,
        "partners/dashboard.html",
        {"partner_name": request.session.get("partner_name", "")},
    )


# ── Partials ───────────────────────────────────────────────────────────────────

@router.get("/dashboard/profile", response_class=HTMLResponse)
async def profile_partial(request: Request, db: AsyncSession = Depends(get_db)):
    partner_id = get_current_partner_id(request)
    if not partner_id:
        return RedirectResponse(url="/partners/login", status_code=302)
    partner = await partner_repo.get_by_id(db, uuid.UUID(partner_id))
    return templates.TemplateResponse(
        request, "partners/partials/profile.html", {"partner": partner}
    )


@router.get("/dashboard/invoices", response_class=HTMLResponse)
async def invoices_partial(request: Request, db: AsyncSession = Depends(get_db)):
    partner_id = get_current_partner_id(request)
    if not partner_id:
        return RedirectResponse(url="/partners/login", status_code=302)
    invoices = await invoice_repo.get_by_partner(db, uuid.UUID(partner_id))
    invoices_sorted = sorted(invoices, key=lambda i: i.created_at, reverse=True)
    return templates.TemplateResponse(
        request, "partners/partials/invoices.html", {"invoices": invoices_sorted}
    )


@router.get("/dashboard/invoices/{invoice_id}", response_class=HTMLResponse)
async def invoice_detail_partial(
    request: Request,
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    partner_id = get_current_partner_id(request)
    if not partner_id:
        return RedirectResponse(url="/partners/login", status_code=302)
    invoice = await invoice_repo.get_by_id(db, invoice_id)
    if not invoice or str(invoice.partner_id) != partner_id:
        return HTMLResponse("<p class='text-danger'>Factura no encontrada.</p>", status_code=404)
    return templates.TemplateResponse(
        request, "partners/partials/invoice_detail.html", {"invoice": invoice}
    )
