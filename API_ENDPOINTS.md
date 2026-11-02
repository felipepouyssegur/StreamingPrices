# API Endpoints — Streaming Prices AR

Documentación de todas las URLs de la API para testear manualmente.

**Base URL (producción):** `https://streamingprices.onrender.com`
**Base URL (local):** `http://localhost:8000`

**API Key:** `streaming-ar-secret-2024`
> ⚠️ La API key protege los endpoints de administración. Cambiala en `.env` (`API_KEY`) para producción.

**Swagger UI interactivo:** [`https://streamingprices.onrender.com/docs`](https://streamingprices.onrender.com/docs)
> Desde ahí podés probar todos los endpoints con botones, sin escribir comandos.

---

## 🟢 Endpoints públicos (sin autenticación)

Estos los podés abrir directamente en el navegador.

### 1. Todos los precios

```
GET /api/v1/prices
```

Devuelve los precios actuales de los 112 servicios, cada uno con su categoría.

**Probar en el navegador:**
```
https://streamingprices.onrender.com/api/v1/prices
```

**Respuesta (ejemplo):**
```json
{
  "generated_at": "2026-07-17T15:11:08.633273",
  "services": [
    {
      "id": "netflix",
      "name": "Netflix",
      "category": "Cine, Series y TV",
      "website_url": "https://www.netflix.com/ar",
      "logo_url": "https://cdn.worldvectorlogo.com/logos/netflix-4.svg",
      "last_scraped_at": "2026-07-17T03:00:00",
      "scrape_status": "ok",
      "plans": [
        {
          "plan_name": "Netflix Básico",
          "price": 11069.0,
          "currency": "ARS",
          "billing_period": "monthly",
          "features": [],
          "is_manual": false,
          "scraped_at": "2026-07-17T03:00:00"
        }
      ]
    }
  ]
}
```

---

### 2. Precios de un servicio específico

```
GET /api/v1/prices/{service_id}
```

**Probar en el navegador:**
```
https://streamingprices.onrender.com/api/v1/prices/netflix
https://streamingprices.onrender.com/api/v1/prices/spotify
https://streamingprices.onrender.com/api/v1/prices/disney
```

> Ver la [tabla de service IDs](#-lista-de-service-ids) abajo para todos los valores válidos.

---

### 3. Historial de precios de un servicio

```
GET /api/v1/history/{service_id}?limit=50
```

Devuelve todos los registros históricos (no solo el actual), ordenados del más reciente al más viejo. El parámetro `limit` es opcional (default: 50).

**Probar en el navegador:**
```
https://streamingprices.onrender.com/api/v1/history/netflix
https://streamingprices.onrender.com/api/v1/history/spotify?limit=10
```

---

### 4. Health check

```
GET /health
```

Verifica que la API esté viva. Usado por el cron job de keep-alive.

**Probar en el navegador:**
```
https://streamingprices.onrender.com/health
```

**Respuesta:**
```json
{ "status": "ok", "timestamp": "2026-07-17T15:11:08.633273" }
```

---

## 🔴 Endpoints de administración (requieren API Key)

Estos **no** se pueden probar solo con el navegador porque necesitan el header `X-API-Key` (o body). Usá `curl`, PowerShell, o el Swagger UI (`/docs`).

### 5. Disparar scraping de TODOS los servicios

```
POST /api/v1/scrape
Header: X-API-Key: streaming-ar-secret-2024
```

Corre el scraping de los 112 servicios en background y devuelve inmediatamente.

**curl:**
```bash
curl -X POST "https://streamingprices.onrender.com/api/v1/scrape" \
  -H "X-API-Key: streaming-ar-secret-2024"
```

**PowerShell:**
```powershell
Invoke-RestMethod -Method Post -Uri "https://streamingprices.onrender.com/api/v1/scrape" -Headers @{ "X-API-Key" = "streaming-ar-secret-2024" }
```

---

### 6. Disparar scraping de UN servicio (espera el resultado)

```
POST /api/v1/scrape/{service_id}
Header: X-API-Key: streaming-ar-secret-2024
```

A diferencia del anterior, este **espera** a que termine y devuelve cuántos planes encontró.

**curl:**
```bash
curl -X POST "https://streamingprices.onrender.com/api/v1/scrape/netflix" \
  -H "X-API-Key: streaming-ar-secret-2024"
```

**PowerShell:**
```powershell
Invoke-RestMethod -Method Post -Uri "https://streamingprices.onrender.com/api/v1/scrape/netflix" -Headers @{ "X-API-Key" = "streaming-ar-secret-2024" }
```

**Respuesta:**
```json
{ "service_id": "netflix", "status": "ok", "plans_saved": 8, "error": null }
```

---

### 7. Cargar precios manualmente (override)

```
PUT /api/v1/prices/{service_id}
Header: X-API-Key: streaming-ar-secret-2024
Body: JSON con lista de planes
```

Sirve para cargar precios a mano cuando el scraper falla. Reemplaza los precios actuales del servicio.

**curl:**
```bash
curl -X PUT "https://streamingprices.onrender.com/api/v1/prices/netflix" \
  -H "X-API-Key: streaming-ar-secret-2024" \
  -H "Content-Type: application/json" \
  -d '[{"plan_name":"Premium","price":15000,"currency":"ARS","billing_period":"monthly","features":["4K","4 pantallas"]}]'
```

**PowerShell:**
```powershell
$body = '[{"plan_name":"Premium","price":15000,"currency":"ARS","billing_period":"monthly","features":["4K","4 pantallas"]}]'
Invoke-RestMethod -Method Put -Uri "https://streamingprices.onrender.com/api/v1/prices/netflix" -Headers @{ "X-API-Key" = "streaming-ar-secret-2024"; "Content-Type" = "application/json" } -Body $body
```

---

### 8. Cron trigger (GET con api_key en la URL)

```
GET /cron/scrape?api_key=streaming-ar-secret-2024
```

Versión GET del scraping masivo, pensada para cron jobs externos (cron-job.org) sin necesidad de configurar headers. Dispara el scraping en background.

**Probar en el navegador:**
```
https://streamingprices.onrender.com/cron/scrape?api_key=streaming-ar-secret-2024
```

**Respuesta:**
```json
{ "status": "queued", "services": 112 }
```

---

## 📋 Resumen de endpoints

| # | Método | URL | Auth | Navegador |
|---|--------|-----|------|-----------|
| 1 | GET  | `/api/v1/prices` | No | ✅ |
| 2 | GET  | `/api/v1/prices/{service_id}` | No | ✅ |
| 3 | GET  | `/api/v1/history/{service_id}` | No | ✅ |
| 4 | GET  | `/health` | No | ✅ |
| 5 | POST | `/api/v1/scrape` | Sí (header) | ❌ |
| 6 | POST | `/api/v1/scrape/{service_id}` | Sí (header) | ❌ |
| 7 | PUT  | `/api/v1/prices/{service_id}` | Sí (header) | ❌ |
| 8 | GET  | `/cron/scrape?api_key=...` | Sí (query) | ✅ |

---

## 🗂️ Lista de service IDs

Usá estos IDs en las URLs `{service_id}` (ej. `/api/v1/prices/netflix`).

### Cine, Series y TV
| Servicio | ID |
|----------|-----|
| Netflix | `netflix` |
| Disney+ | `disney` |
| Max | `max` |
| Amazon Prime Video | `amazon` |
| Paramount+ | `paramount` |
| Apple TV+ | `appletv` |
| Crunchyroll | `crunchyroll` |
| Kick | `kick` |
| Mercado Libre | `mercadolibre` |
| Mubi | `mubi` |
| Plex Pass | `plex` |
| Rakuten Viki Pass | `viki` |
| Stremio | `stremio` |
| Twitch | `twitch` |
| ViX Premium | `vix` |
| YouTube Premium | `youtube` |

### Música
| Servicio | ID |
|----------|-----|
| Apple Music | `applemusic` |
| Deezer | `deezer` |
| Amazon Music Unlimited | `amazonmusic` |
| Spotify | `spotify` |
| Tidal | `tidal` |
| Yandex Music | `yandexmusic` |
| YouTube Music | `youtubemusic` |

### Videojuegos
| Servicio | ID |
|----------|-----|
| Apple Arcade | `applearcade` |
| Chess.com | `chess` |
| EA Play | `eaplay` |
| ExitLag | `exitlag` |
| FACEIT | `faceit` |
| Final Fantasy XIV | `ffxiv` |
| GeForce Now | `geforcenow` |
| Geoguessr | `geoguessr` |
| iRacing | `iracing` |
| Just Dance Now | `justdance` |
| Minecraft Realms | `minecraft` |
| Nintendo Switch Online | `nintendo` |
| PlayStation Plus | `playstation` |
| Ubisoft+ | `ubisoft` |
| World of Warcraft | `wow` |
| Xbox Game Pass | `xbox` |

### Deportes
| Servicio | ID |
|----------|-----|
| F1 TV | `f1tv` |
| NBA League Pass | `nba` |
| NFL Game Pass | `nfl` |
| Triller TV+ | `trillertv` |
| UFC Fight Pass | `ufc` |
| WWE Network | `wwe` |

### Chatbots IA
| Servicio | ID |
|----------|-----|
| ChatGPT | `chatgpt` |
| Claude | `claude` |
| Copilot | `copilot` |
| Gemini | `gemini` |
| Grok | `grok` |
| Perplexity | `perplexity` |
| T3.chat | `t3chat` |

### Asistentes de Código IA
| Servicio | ID |
|----------|-----|
| Cursor | `cursor` |
| GitHub Copilot | `githubcopilot` |
| JetBrains | `jetbrains` |
| Tabnine | `tabnine` |
| TRAE AI | `traeai` |
| Windsurf | `windsurf` |

### Vibe Coding
| Servicio | ID |
|----------|-----|
| Bolt | `bolt` |
| Lovable | `lovable` |
| v0 | `v0` |

### Generación Visual IA
| Servicio | ID |
|----------|-----|
| Krea AI | `krea` |
| Midjourney | `midjourney` |

### Hosting, Cloud y Otros
| Servicio | ID |
|----------|-----|
| Bubble.io | `bubble` |
| GitHub | `github` |
| Nic.ar | `nicar` |
| Sanity | `sanity` |
| Starlink | `starlink` |
| Supabase | `supabase` |
| Vercel | `vercel` |
| Webflow | `webflow` |

### Diseño
| Servicio | ID |
|----------|-----|
| Adobe Creative Cloud | `adobe` |
| Canva | `canva` |
| Clipchamp | `clipchamp` |
| FigJam | `figjam` |
| Figma | `figma` |
| Framer | `framer` |
| Picsart | `picsart` |

### Seguridad
| Servicio | ID |
|----------|-----|
| 1Password | `onepassword` |
| Bitwarden | `bitwarden` |
| NordVPN | `nordvpn` |

### Productividad
| Servicio | ID |
|----------|-----|
| Apple One | `appleone` |
| CapCut | `capcut` |
| ElevenLabs | `elevenlabs` |
| Gasti Pro (ARS) | `gastipro` |
| Gasti Pro (USD) | `gastitprousd` |
| Google Workspace | `gworkspace` |
| IFTTT | `ifttt` |
| LinkedIn Premium | `linkedin` |
| Microsoft 365 | `microsoft365` |
| Notion | `notion` |
| Obsidian | `obsidian` |
| Proton | `proton` |
| TradingView | `tradingview` |
| Zoom | `zoom` |

### Almacenamiento
| Servicio | ID |
|----------|-----|
| Apple iCloud | `icloud` |
| Dropbox | `dropbox` |
| Google One | `googleone` |
| OneDrive | `onedrive` |
| Yandex 360 | `yandex360` |

### Redes Sociales y Chat
| Servicio | ID |
|----------|-----|
| Discord | `discord` |
| Meta Verified | `metaverified` |
| Slack | `slack` |
| Streamlabs | `streamlabs` |
| Telegram | `telegram` |
| X (Twitter) | `twitter` |

### Aprendizaje
| Servicio | ID |
|----------|-----|
| Amazon Audible | `audible` |
| Brilliant | `brilliant` |
| Busuu | `busuu` |
| Duolingo | `duolingo` |
| Kindle Unlimited | `kindle` |
| Mimo | `mimo` |

---

## ⚙️ Cómo funciona la actualización automática

1. **cron-job.org** hace `GET /health` cada 10 minutos → mantiene la app despierta en Render (que apaga el servicio tras 15 min de inactividad).
2. La app despierta corre un **APScheduler interno** que dispara el scraping de los 112 servicios **cada 24 horas** (`SCRAPE_INTERVAL_HOURS` en `.env`).
3. Si la DB arranca vacía (típico tras un redeploy de Render), la app hace un **scraping inicial automático** al arrancar.

El endpoint `/cron/scrape` es opcional — solo para forzar una actualización manual.
