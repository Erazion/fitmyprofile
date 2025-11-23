from __future__ import annotations

import logging
import os

from openai import OpenAI

from .logging_conf import log_exception

logger = logging.getLogger("fmp.llm")


def _get_client() -> OpenAI | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY non configurée, utilisation du mode mock.")
        return None

    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


def _build_messages(cv_text: str, job_text: str):
    """
    Construit les messages pour le LLM.
    On vise un output structuré mais lisible.
    """
    system = (
        "Tu es un expert en recrutement et en optimisation de candidatures. "
        "Tu aides un candidat à adapter son profil (CV, expérience, compétences) "
        "à une offre précise. Réponds en français, de façon claire et directe."
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

1. Donne un score de fit global entre 0 et 100.
2. Résume en 5 bullet points les forces du candidat pour ce poste.
3. Liste les 5 gaps ou points faibles principaux pour cette offre.
4. Propose une version retravaillée du titre de CV + 3 phrases d'accroche
   pour l'entête du CV adaptées à cette offre.
5. Suggère 5 mots-clés ou compétences à faire ressortir dans le CV.

Format attendu (sections claires avec titres en markdown).
"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def analyze_profile(cv_text: str, job_text: str) -> str:
    """
    Analyse CV + offre via LLM (OpenRouter/OpenAI).
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
            "Quand tu auras configuré OPENAI_API_KEY + OPENAI_BASE_URL/OPENROUTER_MODEL, "
            "je générerai ici une analyse complète (score, forces, faiblesses, suggestions)."
        )

    model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3-8b-instruct")

    try:
        messages = _build_messages(cv_text, job_text)
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=900,
        )
        content = completion.choices[0].message.content or ""
        return content.strip()
    except Exception as exc:  # noqa: BLE001
        log_exception(exc, logger_name="fmp.llm")
        return (
            "Une erreur est survenue lors de l'appel à l'IA.\n\n"
            "Détails techniques (pour le dev, à masquer côté front) :\n"
            f"{exc}"
        )
