from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Fit My Profile (FMP)")

# Dossiers static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    """
    Page d'accueil très simple pour vérifier que tout fonctionne.
    """
    return templates.TemplateResponse(
        "landing.html",
        {"request": request}
    )

# Commande de lancement :
# uvicorn backend.main:app --reload
