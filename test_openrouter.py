import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # lit ton .env

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

print("API KEY:", api_key[:10] + "..." if api_key else "AUCUNE")
print("BASE URL:", base_url)

client = OpenAI(api_key=api_key, base_url=base_url)

try:
    # appel tout simple : on liste les modèles dispos
    models = client.models.list()
    print("OK, modèles récupérés :", len(models.data), "modèles trouvés.")
except Exception as e:
    print("ERREUR lors de l'appel à OpenRouter :")
    print(type(e), e)
