"""
Corré este script desde tu PC (en Argentina) una vez por semana.
Scrapea los precios y los sube a la API desplegada en Render.

Uso:
    python run_scraper_local.py

Configuración:
    Editá DEPLOYED_API_URL y API_KEY antes de correrlo.
"""

import asyncio
import httpx
from scrapers import ALL_SCRAPERS

DEPLOYED_API_URL = "https://streamingprices.onrender.com"
API_KEY = "tu-api-key-secreta"  # <-- la misma que pusiste en Render en la variable API_KEY


async def scrape_and_push():
    async with httpx.AsyncClient(timeout=60) as client:
        for scraper in ALL_SCRAPERS:
            print(f"\n[{scraper.service_name}] Scrapeando...")
            try:
                plans = await scraper.scrape(headless=True)
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
