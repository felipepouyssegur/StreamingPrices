"""
Corré este script una vez por semana para scrapear los precios y subirlos
a la API desplegada en Render.

Uso:
    python run_scraper_local.py

Configuración (variables de entorno, o en el archivo .env):
    DEPLOYED_API_URL   URL de la API (default: https://streamingprices.onrender.com)
    API_KEY            clave de admin para el header X-API-Key (requerida)
"""

import os
import sys
import asyncio
import httpx
from dotenv import load_dotenv

from scrapers import ALL_SCRAPERS

load_dotenv()

DEPLOYED_API_URL = os.environ.get("DEPLOYED_API_URL", "https://streamingprices.onrender.com")
API_KEY = os.environ.get("API_KEY")

if not API_KEY:
    sys.exit(
        "ERROR: falta la variable de entorno API_KEY.\n"
        "Definila antes de correr el script, por ejemplo:\n"
        "  PowerShell:  $env:API_KEY = 'tu-clave'\n"
        "  Bash:        export API_KEY='tu-clave'\n"
        "o agregala al archivo .env como API_KEY=tu-clave"
    )


async def scrape_and_push():
    async with httpx.AsyncClient(timeout=60) as client:
        for scraper in ALL_SCRAPERS:
            print(f"\n[{scraper.service_name}] Scrapeando...")
            try:
                plans = await scraper.scrape()
                if not plans:
                    print(f"  Sin resultados — revisá los selectores en scrapers/{scraper.service_id}.py")
                    continue

                payload = [
                    {
                        "plan_name": p.plan_name,
                        "price": p.price,
                        "currency": p.currency,
                        "billing_period": p.billing_period,
                        "features": p.features,
                    }
                    for p in plans
                ]

                response = await client.put(
                    f"{DEPLOYED_API_URL}/api/v1/prices/{scraper.service_id}",
                    json=payload,
                    headers={"X-API-Key": API_KEY},
                )
                response.raise_for_status()
                print(f"  OK — {len(plans)} planes guardados:")
                for p in plans:
                    print(f"     {p.plan_name}: ${p.price:,.0f} ARS")

            except httpx.HTTPStatusError as e:
                print(f"  ERROR HTTP {e.response.status_code}: {e.response.text}")
            except Exception as e:
                print(f"  ERROR: {e}")

    print("\nListo.")


if __name__ == "__main__":
    asyncio.run(scrape_and_push())
