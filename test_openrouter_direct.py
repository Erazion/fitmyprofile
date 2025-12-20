#!/usr/bin/env python3
"""
Script de test pour vérifier la connexion à OpenRouter directement.
"""
import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


async def test_openrouter():
    """Test direct de l'API OpenRouter."""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    app_name = os.getenv("OPENROUTER_APP_NAME", "Fit My Profile")
    public_url = os.getenv("PUBLIC_BASE_URL", "https://fitmyprofile.com")

    if not api_key:
        print("[ERREUR] OPENAI_API_KEY non definie dans .env")
        return

    print(f"[INFO] Cle API: {api_key[:20]}...{api_key[-10:]}")
    print(f"[INFO] Base URL: {base_url}")
    print(f"[INFO] App Name: {app_name}")
    print(f"[INFO] Public URL: {public_url}")
    print()

    # Configuration des headers pour OpenRouter
    default_headers = {
        "HTTP-Referer": public_url,
        "X-Title": app_name,
    }

    print("[INFO] Headers envoyes:")
    for key, value in default_headers.items():
        print(f"   {key}: {value}")
    print()

    try:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers=default_headers,
        )

        print("[TEST] Appel a l'API OpenRouter...")
        print("   Modele: gpt-4o-mini")
        print("   Message: 'Bonjour, peux-tu repondre avec juste OK?'")
        print()

        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un assistant utile."},
                {"role": "user", "content": "Bonjour, peux-tu repondre avec juste OK?"},
            ],
            temperature=0.3,
            max_tokens=50,
        )

        response = completion.choices[0].message.content
        print(f"[SUCCES] Reponse recue: {response}")
        print()
        print("[DETAILS] Details de la reponse:")
        print(f"   Modele utilise: {completion.model}")
        print(
            f"   Tokens utilises: {completion.usage.total_tokens if completion.usage else 'N/A'}"
        )

    except Exception as e:
        print(f"[ERREUR] Erreur lors de l'appel API:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        print()
        print("[DEBUG] Stack trace complete:")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_openrouter())
