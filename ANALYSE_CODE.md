# Analyse du Code - Fit My Profile (FMP)

## 📋 Vue d'ensemble

**Fit My Profile (FMP)** est un MVP (Minimum Viable Product) qui permet d'optimiser un profil de candidature (CV) pour une offre d'emploi spécifique. L'application utilise l'IA (OpenAI) pour analyser le CV et générer des recommandations personnalisées.

---

## 🏗️ Architecture du Projet

### Structure des fichiers

```
fitmyprofile-1/
├── backend/              # Code backend Python
│   ├── main.py          # Point d'entrée FastAPI (routes principales)
│   ├── settings.py       # Configuration via variables d'environnement
│   ├── llm_client.py    # Client OpenAI pour les appels IA
│   ├── parse_cv.py      # Extraction de texte (PDF/DOCX)
│   ├── upload_guard.py  # Validation des fichiers uploadés
│   ├── rate_limit.py    # Middleware de limitation de débit
│   └── logging_conf.py  # Configuration des logs avec masquage PII
├── templates/           # Templates Jinja2 (HTML)
│   ├── base.html
│   ├── landing.html
│   ├── app_index.html
│   ├── result.html
│   ├── pro.html
│   ├── pro_rewrite.html
│   └── pro_result.html
├── static/              # Fichiers statiques (CSS)
│   └── style.css
├── docker-compose.yml   # Configuration Docker Compose
├── Dockerfile           # Image Docker
├── requirements.txt     # Dépendances Python
└── README.md            # Documentation utilisateur
```

---

## 🔧 Stack Technique

### Backend

- **FastAPI** : Framework web moderne et performant
- **Uvicorn** : Serveur ASGI pour FastAPI
- **Jinja2** : Moteur de templates HTML
- **OpenAI** (>=1.6.0) : Client pour appels à l'API GPT
- **PyMuPDF (fitz)** : Extraction de texte depuis PDF
- **python-docx** : Extraction de texte depuis DOCX
- **Stripe** : Intégration paiement (version Pro)
- **pydantic-settings** : Gestion des paramètres de configuration

### Frontend

- **HTML/CSS** : Interface minimaliste
- **JavaScript vanilla** : Interactions utilisateur (overlay de chargement)
- **Plausible Analytics** : Analytics (optionnel, via variable d'environnement)

### Déploiement

- **Docker** : Containerisation
- **Docker Compose** : Orchestration locale
- Compatible avec **Railway/Render** pour le déploiement

---

## 🎯 Fonctionnalités Principales

### 1. Analyse Gratuite (`/analyze`)

- **Entrée** : CV (PDF/DOCX) + description du poste
- **Traitement** :
  1. Validation du fichier (extension, MIME type, taille max 5 Mo)
  2. Extraction du texte (PDF via PyMuPDF, DOCX via python-docx)
  3. Nettoyage du texte (normalisation des espaces)
  4. Appel à l'IA (GPT-4.1-mini) pour analyse
- **Sortie** : Analyse structurée en markdown avec :
  - Score global (0-100)
  - Résumé du fit global
  - Forces principales
  - Points faibles / risques
  - Plan d'action pour améliorer le CV
  - Titre de CV + accroche optimisée
  - Compétences et mots-clés à ajouter

### 2. Version Pro (`/pro/rewrite`)

- **Fonctionnalité** : Réécriture complète de sections du CV
- **Modèle** : GPT-4.1 (plus puissant que la version gratuite)
- **Paiement** : Intégration Stripe Checkout (ou mode fake pour dev)
- **Sortie** : Réécriture avec :
  - 3 variantes de titre de CV
  - 3 variantes de paragraphe d'accroche
  - Expériences réécrites (1-2 expériences les plus pertinentes)
  - Mots-clés à insérer

---

## 🔐 Sécurité et Validation

### Validation des Uploads (`upload_guard.py`)

- ✅ Vérification de l'extension (`.pdf`, `.docx`)
- ✅ Vérification du MIME type
- ✅ Limitation de taille (configurable, défaut 5 Mo)
- ✅ Protection contre les fichiers vides
- ✅ Lecture par chunks pour éviter la surcharge mémoire

### Rate Limiting (`rate_limit.py`)

- **Algorithme** : Token Bucket
- **Configuration** :
  - `RATE_LIMIT_PER_MIN` : 120 requêtes/minute (défaut)
  - `RATE_LIMIT_BURST` : 40 requêtes en rafale (défaut)
- **Implémentation** : Middleware FastAPI par IP
- **Limitation** : En mémoire (perdue au redémarrage)

### Logging Sécurisé (`logging_conf.py`)

- ✅ Masquage automatique des clés API dans les logs
- ✅ Filtrage des tokens Bearer
- ✅ Format structuré avec timestamp, niveau, nom du logger
- ✅ Gestion des exceptions avec stacktrace

---

## ⚙️ Configuration (`settings.py`)

Toutes les configurations sont gérées via variables d'environnement (fichier `.env` ou variables système) :

| Variable             | Description                | Défaut |
| -------------------- | -------------------------- | ------ |
| `ENV`                | Environnement (dev/prod)   | `dev`  |
| `OPENAI_API_KEY`     | Clé API OpenAI             | `None` |
| `PRICE_EUR`          | Prix version Pro           | `4.90` |
| `USE_FAKE_CHECKOUT`  | Bypass paiement (dev)      | `True` |
| `MAX_UPLOAD_MB`      | Taille max upload          | `5`    |
| `RATE_LIMIT_PER_MIN` | Limite requêtes/min        | `120`  |
| `RATE_LIMIT_BURST`   | Capacité rafale            | `40`   |
| `LOG_LEVEL`          | Niveau de log              | `INFO` |
| `STRIPE_SECRET_KEY`  | Clé secrète Stripe         | `None` |
| `STRIPE_PRICE_ID`    | ID prix Stripe             | `None` |
| `ANALYTICS_DOMAIN`   | Domaine Plausible          | `None` |
| `PUBLIC_BASE_URL`    | URL publique (pour Stripe) | `None` |

---

## 🛣️ Routes API

### Routes Publiques

- `GET /` : Page d'accueil (landing)
- `GET /health` : Health check (retourne `{"status": "ok"}`)
- `GET /app` : Formulaire d'analyse gratuite
- `POST /analyze` : Traitement de l'analyse (CV + offre)

### Routes Pro (Payantes)

- `GET /pro` : Page de présentation version Pro
- `GET /pro/rewrite` : Formulaire de réécriture Pro
- `POST /pro/rewrite` : Traitement de la réécriture Pro
- `POST /pro/checkout` : Création session Stripe Checkout

### Gestion d'Erreurs

- `Exception Handler` : Capture toutes les exceptions non gérées et affiche `error_500.html`

---

## 🤖 Intégration IA (`llm_client.py`)

### Analyse (`analyze_profile`)

- **Modèle** : `gpt-4.1-mini`
- **Temperature** : `0.3` (réponses plus déterministes)
- **Max tokens** : `900`
- **Format** : Markdown structuré avec score global

### Réécriture (`rewrite_profile`)

- **Modèle** : `gpt-4.1`
- **Temperature** : `0.4` (légèrement plus créatif)
- **Max tokens** : `900`
- **Format** : Markdown avec variantes de titres, accroches, expériences

### Gestion des Erreurs

- ✅ Mode mock si pas de clé API configurée
- ✅ Gestion gracieuse des erreurs OpenAI
- ✅ Messages d'erreur utilisateur-friendly

---

## 📄 Extraction de Texte (`parse_cv.py`)

### Formats Supportés

- **PDF** : Via PyMuPDF (`fitz`)
- **DOCX** : Via `python-docx`

### Fonctionnalités

- Extraction de texte brut depuis les deux formats
- Nettoyage automatique :
  - Suppression des retours chariot multiples
  - Normalisation des espaces
  - Trim des lignes

---

## 🎨 Interface Utilisateur

### Design

- **Thème** : Dark mode (fond `#0b1020`, texte `#f7f7ff`)
- **Couleur principale** : Cyan (`#1ccad8`)
- **Style** : Minimaliste, moderne, centré sur l'utilisateur

### Expérience Utilisateur

- ✅ Overlay de chargement avec progression visuelle
- ✅ Messages de progression dynamiques pendant l'analyse
- ✅ Désactivation du bouton pendant le traitement (anti double-clic)
- ✅ Affichage d'extraits (800 caractères) du CV et de l'offre
- ✅ Conversion markdown → HTML pour l'affichage

---

## 🐳 Déploiement

### Docker

- **Image de base** : `python:3.13-slim`
- **Port exposé** : `8000`
- **Commande** : `uvicorn backend.main:app --host 0.0.0.0 --port 8000`

### Docker Compose

- Service unique `web`
- Montage du fichier `.env` pour les variables d'environnement
- Port mapping `8000:8000`

### Compatibilité

- ✅ Railway
- ✅ Render
- ✅ Tout hébergeur supportant Docker

---

## 🔍 Points d'Attention / Améliorations Possibles

### Points Forts

1. ✅ Architecture claire et modulaire
2. ✅ Sécurité : validation uploads, rate limiting, masquage PII
3. ✅ Gestion d'erreurs robuste
4. ✅ Configuration flexible via variables d'environnement
5. ✅ Mode mock pour développement sans clé API
6. ✅ Code bien structuré avec séparation des responsabilités

### Points à Améliorer

1. **Rate Limiting** : Actuellement en mémoire (perdu au redémarrage)
   - 💡 Suggestion : Utiliser Redis pour un rate limiting distribué
2. **Gestion des Sessions** : Pas de système de session utilisateur
   - 💡 Suggestion : Ajouter des sessions pour suivre les analyses
3. **Base de Données** : Aucune persistance
   - 💡 Suggestion : Ajouter une DB pour historiser les analyses
4. **Tests** : Aucun test unitaire ou d'intégration visible
   - 💡 Suggestion : Ajouter pytest avec tests pour chaque module
5. **Cache** : Pas de cache pour les appels IA coûteux
   - 💡 Suggestion : Mettre en cache les résultats pour CV/offre identiques
6. **Validation Offre** : Pas de validation de la longueur de l'offre
   - 💡 Suggestion : Limiter la taille de l'offre d'emploi
7. **Modèles IA** : Modèles hardcodés (`gpt-4.1-mini`, `gpt-4.1`)
   - 💡 Suggestion : Rendre les modèles configurables
8. **HTMX** : Mentionné dans le README mais pas implémenté
   - 💡 Suggestion : Implémenter HTMX pour interactions dynamiques sans JS

---

## 📊 Flux de Données

### Analyse Gratuite

```
Utilisateur → Upload CV + Offre
    ↓
Validation (extension, MIME, taille)
    ↓
Extraction texte (PDF/DOCX)
    ↓
Nettoyage texte
    ↓
Appel OpenAI (GPT-4.1-mini)
    ↓
Conversion Markdown → HTML
    ↓
Affichage résultat (score, forces, faiblesses, plan d'action)
```

### Version Pro

```
Utilisateur → Clic "Version Pro"
    ↓
Stripe Checkout (ou fake checkout en dev)
    ↓
Upload CV + Offre
    ↓
Validation + Extraction
    ↓
Appel OpenAI (GPT-4.1) - Réécriture
    ↓
Affichage réécriture (titres, accroches, expériences)
```

---

## 📝 Résumé Exécutif

**Fit My Profile** est une application web bien structurée qui utilise l'IA pour optimiser les CV selon des offres d'emploi spécifiques. Le code est propre, modulaire, et suit les bonnes pratiques de sécurité. L'application est prête pour un déploiement en production, avec quelques améliorations possibles pour la scalabilité (cache, DB, rate limiting distribué) et la maintenabilité (tests).

**Points Clés** :

- ✅ MVP fonctionnel avec analyse gratuite et version payante
- ✅ Sécurité : validation uploads, rate limiting, masquage PII
- ✅ Architecture modulaire et extensible
- ✅ Configuration flexible via variables d'environnement
- ✅ Prêt pour déploiement Docker

