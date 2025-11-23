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
