from __future__ import annotations

import logging
import re

import markdown
import stripe
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .settings import settings
from .upload_guard import validate_and_read_upload
from .parse_cv import extract_text_from_validated_upload, clean_text
from .llm_client import analyze_profile, rewrite_profile
from .logging_conf import configure_logging
from .rate_limit import RateLimitMiddleware

# Configurer les logs
configure_logging(settings.LOG_LEVEL)

logger = logging.getLogger("fmp.api")

app = FastAPI(title="Fit My Profile (FMP)")

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY

# Static & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def render_template(
    name: str,
    request: Request,
    context: dict | None = None,
    status_code: int = status.HTTP_200_OK,
):
    ctx = {"request": request, "analytics_domain": settings.ANALYTICS_DOMAIN}
    if context:
        ctx.update(context)
    return templates.TemplateResponse(name, ctx, status_code=status_code)

# Rate limiting (simple, en mémoire)
rate_per_minute = settings.RATE_LIMIT_PER_MIN
rate_burst = settings.RATE_LIMIT_BURST
app.add_middleware(
    RateLimitMiddleware,
    rate_per_minute=rate_per_minute,
    burst=rate_burst,
)


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    """
    Page d'accueil très simple pour vérifier que tout fonctionne.
    """
    return render_template("landing.html", request)


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


@app.get("/app", response_class=HTMLResponse)
async def app_index(request: Request):
    return render_template("app_index.html", request)


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    cv_file: UploadFile = File(...),
    job_offer: str = Form(...),
):
    """
    - sécurise et lit le fichier
    - extrait le texte (pdf/docx)
    - appelle l'IA (ou mock si pas configurée)
    - retourne un résultat structuré
    """

    # 1. Valider + lire le fichier CV
    file_bytes = await validate_and_read_upload(cv_file)

    # 2. Extraire le texte du CV
    cv_text = await extract_text_from_validated_upload(cv_file, file_bytes)

    # 3. Nettoyer l’offre
    job_text = clean_text(job_offer)

    # 4. Appel LLM (ou mock)
    analysis_md = analyze_profile(cv_text, job_text)

    # Extraction du score global (si présent dans le texte)
    match = re.search(r"Score global\s*:\s*(\d{1,3})", analysis_md)
    score: int | None = None
    if match:
        try:
            raw = int(match.group(1))
            score = max(0, min(raw, 100))  # clamp 0-100
        except ValueError:
            score = None

    # Convertir le markdown en HTML
    analysis_html = markdown.markdown(analysis_md, extensions=["extra"])

    # On affiche seulement les 800 premiers caractères de chaque texte
    cv_excerpt = cv_text[:800] + ("…" if len(cv_text) > 800 else "")
    job_excerpt = job_text[:800] + ("…" if len(job_text) > 800 else "")

    return render_template(
        "result.html",
        request,
        {
            "cv_excerpt": cv_excerpt,
            "job_excerpt": job_excerpt,
            "analysis_html": analysis_html,
            "score": score,
        },
    )


@app.post("/pro/rewrite", response_class=HTMLResponse)
async def pro_rewrite(
    request: Request,
    cv_file: UploadFile = File(...),
    job_offer: str = Form(...),
):
    access_granted = settings.USE_FAKE_CHECKOUT or request.query_params.get("paid") == "1"
    if not access_granted:
        return render_template(
            "pro_rewrite.html",
            request,
            {
                "access_granted": False,
                "use_fake_checkout": settings.USE_FAKE_CHECKOUT,
            },
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
        )

    # 🔥 Validation & lecture fichier (comme /analyze)
    file_bytes = await validate_and_read_upload(cv_file)
    cv_text = await extract_text_from_validated_upload(cv_file, file_bytes)
    job_text = clean_text(job_offer)

    # 🔥 Appel modèle Pro (réécriture)
    rewrite_md = rewrite_profile(cv_text, job_text)
    rewrite_html = markdown.markdown(rewrite_md, extensions=["extra"])

    # Extraits affichés UI
    cv_excerpt = cv_text[:800] + ("…" if len(cv_text) > 800 else "")
    job_excerpt = job_text[:800] + ("…" if len(job_text) > 800 else "")

    return render_template(
        "pro_result.html",
        request,
        {
            "cv_excerpt": cv_excerpt,
            "job_excerpt": job_excerpt,
            "rewrite_html": rewrite_html,
            "access_granted": True,
            "use_fake_checkout": settings.USE_FAKE_CHECKOUT,
        },
    )


@app.get("/pro", response_class=HTMLResponse)
async def pro_page(request: Request):
    return render_template("pro.html", request)


@app.get("/pro/rewrite", response_class=HTMLResponse)
async def pro_rewrite_form(request: Request):
    access_granted = settings.USE_FAKE_CHECKOUT or request.query_params.get("paid") == "1"
    return render_template(
        "pro_rewrite.html",
        request,
        {
            "access_granted": access_granted,
            "use_fake_checkout": settings.USE_FAKE_CHECKOUT,
        },
    )


# Point d'entrée :
# uvicorn backend.main:app --reload


@app.exception_handler(Exception)
async def internal_error_handler(request: Request, exc: Exception):
    return render_template("error_500.html", request, status_code=500)


@app.post("/pro/checkout")
async def pro_checkout(request: Request):
    if settings.USE_FAKE_CHECKOUT:
        return RedirectResponse(
            url=str(request.url_for("pro_rewrite_form")),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PRICE_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Paiement indisponible : configuration Stripe manquante.",
        )

    base = (settings.PUBLIC_BASE_URL or str(request.base_url).rstrip("/")).rstrip("/")
    success_url = f"{base}{request.url_for('pro_rewrite_form').path}?paid=1"
    cancel_url = f"{base}{request.url_for('pro_page').path}"

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": settings.STRIPE_PRICE_ID, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return RedirectResponse(
            url=session.url,
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Erreur lors de la création de session Stripe: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Paiement indisponible : erreur Stripe.",
        ) from exc
