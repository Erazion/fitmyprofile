from __future__ import annotations

import os
import re

import markdown
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .upload_guard import validate_and_read_upload
from .parse_cv import extract_text_from_validated_upload, clean_text
from .llm_client import analyze_profile, rewrite_profile
from .logging_conf import configure_logging
from .rate_limit import RateLimitMiddleware

# Charger les variables d'environnement depuis .env si présent
load_dotenv()

# Configurer les logs
log_level = os.getenv("LOG_LEVEL", "INFO")
configure_logging(log_level)

app = FastAPI(title="Fit My Profile (FMP)")

# Static & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Rate limiting (simple, en mémoire)
rate_per_minute = int(os.getenv("RATE_LIMIT_PER_MIN", "120"))
rate_burst = int(os.getenv("RATE_LIMIT_BURST", "40"))
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
    return templates.TemplateResponse(
        "landing.html",
        {"request": request},
    )


@app.get("/app", response_class=HTMLResponse)
async def app_index(request: Request):
    return templates.TemplateResponse(
        "app_index.html",
        {"request": request},
    )


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

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
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
    """
    Réécriture Pro : réutilise la même logique de parsing que /analyze,
    mais appelle le moteur de réécriture.
    """

    # 1. Valider + lire le fichier CV
    file_bytes = await validate_and_read_upload(cv_file)

    # 2. Extraire le texte du CV
    cv_text = await extract_text_from_validated_upload(cv_file, file_bytes)

    # 3. Nettoyer l’offre
    job_text = clean_text(job_offer)

    # Extraits pour affichage
    cv_excerpt = cv_text[:800] + ("…" if len(cv_text) > 800 else "")
    job_excerpt = job_text[:800] + ("…" if len(job_text) > 800 else "")

    # 4. Appel LLM pour la réécriture Pro
    rewrite_md = rewrite_profile(cv_text, job_text)
    rewrite_html = markdown.markdown(rewrite_md, extensions=["extra"])

    return templates.TemplateResponse(
        "pro_result.html",
        {
            "request": request,
            "cv_excerpt": cv_excerpt,
            "job_excerpt": job_excerpt,
            "rewrite_html": rewrite_html,
        },
    )


@app.get("/pro", response_class=HTMLResponse)
async def pro_page(request: Request):
    return templates.TemplateResponse(
        "pro.html",
        {"request": request},
    )


@app.get("/pro/rewrite", response_class=HTMLResponse)
async def pro_rewrite_form(request: Request):
    return templates.TemplateResponse(
        "pro_rewrite.html",
        {"request": request},
    )


# Point d'entrée :
# uvicorn backend.main:app --reload
