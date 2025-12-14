from __future__ import annotations

import logging
from openai import AsyncOpenAI

from .logging_conf import log_exception
from .settings import settings

_client_cache: AsyncOpenAI | None = None

logger = logging.getLogger("fmp.llm")


def _get_client() -> AsyncOpenAI | None:
    global _client_cache

    api_key = settings.OPENAI_API_KEY
    if not api_key:
        logger.warning("OPENAI_API_KEY non configurée, utilisation du mode mock.")
        _client_cache = None
        return None

    if _client_cache is None:
        _client_cache = AsyncOpenAI(api_key=api_key)

    return _client_cache


def _build_messages(cv_text: str, job_text: str):
    """
    Construit les messages pour le LLM.

    Objectif : produire une analyse exploitable pour Fit My Profile,
    avec un format stable et actionnable.
    """
    system = (
        "Tu es un expert en recrutement et en optimisation de candidatures. "
        "Tu aides un candidat à adapter son profil (CV, expérience, compétences) "
        "à une offre précise. Réponds en français, de façon claire, directe et utile. "
        "Ton but est que la personne sache quoi CHANGER concrètement dans son CV."
    )

    user = f"""
Voici le CV (texte brut) :

----
{cv_text}
----

Voici l'offre d'emploi :

----
{job_text}
----

Tu dois IMPÉRATIVEMENT structurer ta réponse en suivant ce format :

1. Commence par une ligne unique de la forme :
   "Score global : XX/100"
   où XX est un entier entre 0 et 100.

2. Puis, en markdown, génère les sections suivantes :

## 1. Résumé du fit global
- 3 à 5 phrases maximum
- Donne une vision honnête mais constructive

## 2. Forces principales pour ce poste
- Liste en bullet points les 5 à 7 points forts du candidat
- Mets en avant les expériences, compétences, résultats, mots-clés déjà alignés

## 3. Points faibles / risques de non-sélection
- Liste 5 à 7 points concrets qui peuvent poser problème
- Tu peux parler de manque d'expérience, de mots-clés absents, de niveau de séniorité, etc.

## 4. Plan d'action pour améliorer le CV
- Sous forme de liste numérotée (1., 2., 3., …)
- Chaque point doit être une action concrète sur le CV :
  - ajouter une ligne précise,
  - reformuler une expérience,
  - mettre en avant certains mots,
  - raccourcir une section, etc.

## 5. Titre de CV + accroche optimisée
- Propose 2 ou 3 versions de titre de CV (en une ligne)
- Propose 2 ou 3 exemples de paragraphe d'accroche (3 à 5 phrases) adaptés à cette offre

## 6. Compétences et mots-clés à ajouter ou renforcer
- Liste :
  - les hard skills à ajouter ou renforcer
  - les soft skills pertinents
  - les outils / technologies / environnements à mentionner

Respecte bien la structure, les titres et l'ordre des sections.
"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


async def analyze_profile(cv_text: str, job_text: str) -> str:
    """
    Analyse CV + offre via OpenAI.
    Si pas de clé API ou erreur, renvoie un texte explicatif + mock.
    """
    cv_text = (cv_text or "").strip()
    job_text = (job_text or "").strip()

    # Cas où on n'a pas de matière
    if not cv_text or not job_text:
        return (
            "Analyse IA indisponible : CV ou offre vides.\n"
            "Vérifie que ton fichier est bien lisible et que tu as collé l'offre."
        )

    client = _get_client()
    if client is None:
        # Mode mock si pas de clé
        return (
            "Analyse IA (mode mock – aucune clé API configurée).\n\n"
            f"CV détecté (~{len(cv_text)} caractères) et offre (~{len(job_text)} caractères).\n"
            "Quand tu auras configuré OPENAI_API_KEY, je générerai ici une analyse complète "
            "(score, forces, faiblesses, suggestions)."
        )

    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=_build_messages(cv_text, job_text),
            temperature=0.3,
            max_tokens=900,
        )
        content = completion.choices[0].message.content or ""
        return content.strip()
    except Exception as exc:  # noqa: BLE001
        log_exception(exc, logger_name="fmp.llm")
        return f"Une erreur est survenue lors de l'appel à l'IA. Détails techniques : {type(exc).__name__}"


def _build_rewrite_messages(cv_text: str, job_text: str) -> list[dict[str, str]]:
    system = (
        "Tu es un expert en optimisation de CV et en recrutement. "
        "Tu aides un candidat à adapter son CV à une offre précise. "
        "Tu écris en français, de façon claire, concise et impactante. "
        "Tu produis du texte prêt à copier-coller dans un CV moderne."
    )

    user = f"""
Voici le CV du candidat (texte brut) :

----
{cv_text}
----

Voici l'offre d'emploi ciblée :

----
{job_text}
----

Ta mission : produire une RÉÉCRITURE PRO de certaines parties du CV, adaptée à cette offre.

Réponds STRICTEMENT en markdown avec les sections suivantes :

## 1. Titre de CV – 3 variantes
- Propose 3 titres de CV percutants, en une ligne chacun.
- Ils doivent être alignés avec l'offre (niveau, scope, secteur si possible).

## 2. Paragraphe d'accroche – 3 variantes
- Propose 3 paragraphes d'accroche (3 à 5 phrases chacun).
- Style : clair, orienté résultats, sans bullshit.
- Le candidat doit pouvoir les coller tels quels en haut de son CV.

## 3. Expériences à réécrire
- Identifie 1 ou 2 expériences du CV qui sont les plus pertinentes pour l'offre.
- Pour chaque expérience, donne :
  - **Intitulé + contexte** (1–2 lignes)
  - **Version réécrite de la description** sous forme de bullet points (4 à 7 bullets)
  - Mets en avant les résultats, les responsabilités et les éléments alignés avec l'offre.

## 4. Mots-clés à insérer dans le CV
- Liste les mots-clés (techniques + business) à insérer dans :
  - le titre
  - l'accroche
  - les expériences
- Sépare les catégories si nécessaire.

Ne fais pas de blabla autour, respecte uniquement cette structure.
"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


async def rewrite_profile(cv_text: str, job_text: str) -> str:
    cv_text = (cv_text or "").strip()
    job_text = (job_text or "").strip()

    if not cv_text or not job_text:
        return (
            "Réécriture IA indisponible : CV ou offre vides.\n"
            "Vérifie que ton fichier est bien lisible et que tu as collé l'offre."
        )

    client = _get_client()
    if client is None:
        return (
            "Réécriture IA (mode mock – aucune clé API configurée).\n\n"
            f"CV détecté (~{len(cv_text)} caractères) et offre (~{len(job_text)} caractères).\n"
            "Quand tu auras configuré OPENAI_API_KEY, je proposerai ici une réécriture optimisée."
        )

    try:
        completion = await client.chat.completions.create(
            model="gpt-4o",
            messages=_build_rewrite_messages(cv_text, job_text),
            temperature=0.4,
            max_tokens=900,
        )
        content = completion.choices[0].message.content or ""
        return content.strip()
    except Exception as exc:  # noqa: BLE001
        log_exception(exc, logger_name="fmp.llm")
        return f"Une erreur est survenue lors de l'appel à l'IA. Détails techniques : {type(exc).__name__}"
