# Fit My Profile (FMP)

Fit My Profile (FMP) est un MVP qui permet d’optimiser ton profil de candidature
(CV, contenu) pour une offre précise.

Tu fournis :

- ton CV (PDF/DOCX),
- la description du poste,

et FMP t’aide à générer une version ciblée, plus claire et plus alignée avec ce que
les recruteurs – humains ou algos – attendent.

---

## ⚙️ Stack

- FastAPI (backend)
- Jinja2 + HTML/CSS (frontend minimal)
- HTMX (plus tard pour les interactions dynamiques)
- OpenRouter (LLM) – plus tard
- Docker + Railway/Render (déploiement)

Les specs complètes : voir [`SPEC.md`](./SPEC.md).

---

## 🚀 Démarrer en local

```bash
python -m venv .venv
# Windows :
# .venv\Scripts\activate
# macOS / Linux :
# source .venv/bin/activate

pip install -r requirements.txt

uvicorn backend.main:app --reload
```

---

## Run en local avec Docker

```bash
# build + run
docker-compose up --build
# puis ouvrir http://localhost:8000/app
```

---

## Variables d'environnement (prod)

Définis ces variables dans un fichier `.env` (chargé aussi par `docker-compose` ou ta plateforme) :

- `OPENAI_API_KEY` : clé OpenAI.
- `ENV` : `prod` en production, `dev` sinon.
- `LOG_LEVEL` : INFO/DEBUG/ERROR.
- `USE_FAKE_CHECKOUT` : `false` en prod (sinon bypass paiement).
- `PRICE_EUR` : prix affiché.
- `MAX_UPLOAD_MB` : taille max upload CV.
- `RATE_LIMIT_PER_MIN`, `RATE_LIMIT_BURST` : protection anti-abus.
- `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID` : pour Stripe Checkout en prod.
- `ANALYTICS_DOMAIN` : domaine Plausible (ou laisse vide pour désactiver).
- Optionnel : `OPENROUTER_BASE_URL` (hérité de l’ancien setup, ignoré si non utilisé).

Sur Render / Railway : fournis ces variables dans le dashboard, ou laisse la plateforme construire l’image à partir du `Dockerfile`. Expose le port 8000, et définis la commande `uvicorn backend.main:app --host 0.0.0.0 --port 8000` si la plateforme ne lit pas le `CMD` du Dockerfile.
