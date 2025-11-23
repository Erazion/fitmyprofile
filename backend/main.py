from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from fastapi import Form, UploadFile, File

from .upload_guard import validate_and_read_upload
from .parse_cv import extract_text_from_validated_upload, clean_text
from .llm_client import analyze_profile

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
    analysis = analyze_profile(cv_text, job_text)

    # On affiche seulement les 800 premiers caractères de chaque texte
    cv_excerpt = cv_text[:800] + ("…" if len(cv_text) > 800 else "")
    job_excerpt = job_text[:800] + ("…" if len(job_text) > 800 else "")

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "cv_excerpt": cv_excerpt,
            "job_excerpt": job_excerpt,
            "analysis": analysis,
        },
    )


# Point d'entrée :
# uvicorn backend.main:app --reload
