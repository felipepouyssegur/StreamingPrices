import json
from datetime import datetime
from typing import List
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import get_settings
from app.models import PriceRecord, ServiceMeta
from scrapers.base import ScrapedPlan

_engine = None

# Default service catalogue (id, name, website, pricing_url, logo_url, category)
_SERVICES = [
    # Cine, Series y TV
    ("netflix",       "Netflix",               "https://www.netflix.com/ar",                    "https://www.netflix.com/ar/signup/planform",                     "https://cdn.worldvectorlogo.com/logos/netflix-4.svg",                  "Cine, Series y TV"),
    ("disney",        "Disney+",               "https://www.disneyplus.com/es-ar",              "https://www.disneyplus.com/es-ar/subscribe",                     "https://cdn.worldvectorlogo.com/logos/disney-plus-1.svg",             "Cine, Series y TV"),
    ("max",           "Max",                   "https://www.max.com/ar/es",                     "https://www.max.com/ar/es/plans",                                "https://cdn.worldvectorlogo.com/logos/hbo-max-1.svg",                  "Cine, Series y TV"),
    ("amazon",        "Amazon Prime Video",    "https://www.amazon.com.ar/prime",               "https://www.amazon.com.ar/amazonprime",                          "https://cdn.worldvectorlogo.com/logos/prime-video-1.svg",             "Cine, Series y TV"),
    ("paramount",     "Paramount+",            "https://www.paramountplus.com/ar",              "https://www.paramountplus.com/ar/account/signup/",               "https://cdn.worldvectorlogo.com/logos/paramount-plus-1.svg",          "Cine, Series y TV"),
    ("appletv",       "Apple TV+",             "https://www.apple.com/ar/apple-tv-plus/",       "https://www.apple.com/ar/apple-tv-plus/",                        "https://cdn.worldvectorlogo.com/logos/apple-tv-plus-logo.svg",        "Cine, Series y TV"),
    ("crunchyroll",   "Crunchyroll",           "https://www.crunchyroll.com",                   "https://www.crunchyroll.com/es/welcome",                         "",                                                                    "Cine, Series y TV"),
    ("kick",          "Kick",                  "https://kick.com",                              "https://kick.com",                                               "",                                                                    "Cine, Series y TV"),
    ("mercadolibre",  "Mercado Libre",         "https://www.mercadolibre.com.ar",               "https://www.mercadolibre.com.ar/suscripciones",                  "",                                                                    "Cine, Series y TV"),
    ("mubi",          "Mubi",                  "https://mubi.com/es/ar",                        "https://mubi.com/es/ar/plans",                                   "",                                                                    "Cine, Series y TV"),
    ("plex",          "Plex Pass",             "https://www.plex.tv",                           "https://www.plex.tv/es/plex-pass/",                              "",                                                                    "Cine, Series y TV"),
    ("viki",          "Rakuten Viki Pass",     "https://www.viki.com",                          "https://www.viki.com/vikipass",                                  "",                                                                    "Cine, Series y TV"),
    ("stremio",       "Stremio",               "https://www.stremio.com",                       "https://www.stremio.com/stremio-plus",                           "",                                                                    "Cine, Series y TV"),
    ("twitch",        "Twitch",                "https://www.twitch.tv",                         "https://www.twitch.tv/subs",                                     "",                                                                    "Cine, Series y TV"),
    ("vix",           "ViX Premium",           "https://www.vix.com",                           "https://www.vix.com/es/premium",                                 "",                                                                    "Cine, Series y TV"),
    ("youtube",       "YouTube Premium",       "https://www.youtube.com/premium",               "https://www.youtube.com/premium",                                "",                                                                    "Cine, Series y TV"),
    # Música
    ("applemusic",    "Apple Music",           "https://www.apple.com/ar/apple-music/",         "https://www.apple.com/ar/apple-music/",                          "",                                                                    "Música"),
    ("deezer",        "Deezer",                "https://www.deezer.com/es",                     "https://www.deezer.com/es/offers",                               "",                                                                    "Música"),
    ("amazonmusic",   "Amazon Music Unlimited","https://music.amazon.com.ar",                   "https://www.amazon.com.ar/music/unlimited",                      "",                                                                    "Música"),
    ("spotify",       "Spotify",               "https://www.spotify.com/ar",                    "https://www.spotify.com/ar/premium/",                            "",                                                                    "Música"),
    ("tidal",         "Tidal",                 "https://tidal.com",                             "https://tidal.com/plans",                                        "",                                                                    "Música"),
    ("yandexmusic",   "Yandex Music",          "https://music.yandex.com",                      "https://music.yandex.com/pay",                                   "",                                                                    "Música"),
    ("youtubemusic",  "YouTube Music",         "https://music.youtube.com",                     "https://music.youtube.com/premium",                              "",                                                                    "Música"),
    # Videojuegos
    ("applearcade",   "Apple Arcade",          "https://www.apple.com/ar/apple-arcade/",        "https://www.apple.com/ar/apple-arcade/",                         "",                                                                    "Videojuegos"),
    ("chess",         "Chess.com",             "https://www.chess.com",                         "https://www.chess.com/membership",                               "",                                                                    "Videojuegos"),
    ("eaplay",        "EA Play",               "https://www.ea.com/es-es/ea-play",              "https://www.ea.com/es-es/ea-play/buy",                           "",                                                                    "Videojuegos"),
    ("exitlag",       "ExitLag",               "https://www.exitlag.com",                       "https://www.exitlag.com/es/pricing",                             "",                                                                    "Videojuegos"),
    ("faceit",        "FACEIT",                "https://www.faceit.com",                        "https://www.faceit.com/es/membership",                           "",                                                                    "Videojuegos"),
    ("ffxiv",         "Final Fantasy XIV",     "https://www.finalfantasyxiv.com",               "https://www.finalfantasyxiv.com/es/product/",                    "",                                                                    "Videojuegos"),
    ("geforcenow",    "GeForce Now",           "https://www.nvidia.com/es-la/geforce-now/",     "https://www.nvidia.com/es-la/geforce-now/plans/",                "",                                                                    "Videojuegos"),
    ("geoguessr",     "Geoguessr",             "https://www.geoguessr.com",                     "https://www.geoguessr.com/pro",                                  "",                                                                    "Videojuegos"),
    ("iracing",       "iRacing",               "https://www.iracing.com",                       "https://www.iracing.com/membership/",                            "",                                                                    "Videojuegos"),
    ("justdance",     "Just Dance Now",        "https://justdancenow.com",                      "https://justdancenow.com/subscription",                          "",                                                                    "Videojuegos"),
    ("minecraft",     "Minecraft Realms",      "https://www.minecraft.net",                     "https://www.minecraft.net/es-es/realms",                         "",                                                                    "Videojuegos"),
    ("nintendo",      "Nintendo Switch Online","https://www.nintendo.com/es-ar/",               "https://www.nintendo.com/es-ar/nintendo-switch-online/",         "",                                                                    "Videojuegos"),
    ("playstation",   "PlayStation Plus",      "https://www.playstation.com/es-ar/",            "https://www.playstation.com/es-ar/ps-plus/",                     "",                                                                    "Videojuegos"),
    ("ubisoft",       "Ubisoft+",              "https://store.ubisoft.com/es",                  "https://store.ubisoft.com/es/ubisoftplus",                       "",                                                                    "Videojuegos"),
    ("wow",           "World of Warcraft",     "https://worldofwarcraft.blizzard.com",          "https://worldofwarcraft.blizzard.com/es-es/shop/subscription",  "",                                                                    "Videojuegos"),
    ("xbox",          "Xbox Game Pass",        "https://www.xbox.com/es-AR/",                   "https://www.xbox.com/es-AR/xbox-game-pass",                      "",                                                                    "Videojuegos"),
    # Deportes
    ("f1tv",          "F1 TV",                 "https://f1tv.formula1.com",                     "https://f1tv.formula1.com/page/plans",                           "",                                                                    "Deportes"),
    ("nba",           "NBA League Pass",       "https://www.nba.com",                           "https://www.nba.com/league-pass-register",                       "",                                                                    "Deportes"),
    ("nfl",           "NFL Game Pass",         "https://www.nfl.com",                           "https://www.nfl.com/network/watch/nfl-game-pass",                "",                                                                    "Deportes"),
    ("trillertv",     "Triller TV+",           "https://trillertv.com",                         "https://trillertv.com/subscribe",                                "",                                                                    "Deportes"),
    ("ufc",           "UFC Fight Pass",        "https://www.ufc.com",                           "https://ufcfightpass.com/",                                      "",                                                                    "Deportes"),
    ("wwe",           "WWE Network",           "https://network.wwe.com",                       "https://network.wwe.com",                                        "",                                                                    "Deportes"),
    # Chatbots IA
    ("chatgpt",       "ChatGPT",               "https://chatgpt.com",                           "https://chatgpt.com/",                                           "",                                                                    "Chatbots IA"),
    ("claude",        "Claude",                "https://claude.ai",                             "https://claude.ai/upgrade",                                      "",                                                                    "Chatbots IA"),
    ("copilot",       "Copilot",               "https://copilot.microsoft.com",                 "https://copilot.microsoft.com/",                                 "",                                                                    "Chatbots IA"),
    ("gemini",        "Gemini",                "https://gemini.google.com",                     "https://gemini.google.com/advanced",                             "",                                                                    "Chatbots IA"),
    ("grok",          "Grok",                  "https://grok.com",                              "https://grok.com/",                                              "",                                                                    "Chatbots IA"),
    ("perplexity",    "Perplexity",            "https://www.perplexity.ai",                     "https://www.perplexity.ai/pro",                                  "",                                                                    "Chatbots IA"),
    ("t3chat",        "T3.chat",               "https://t3.chat",                               "https://t3.chat/",                                               "",                                                                    "Chatbots IA"),
    # Asistentes de Código IA
    ("cursor",        "Cursor",                "https://www.cursor.com",                        "https://www.cursor.com/pricing",                                 "",                                                                    "Asistentes de Código IA"),
    ("githubcopilot", "GitHub Copilot",        "https://github.com/features/copilot",           "https://github.com/features/copilot/plans",                     "",                                                                    "Asistentes de Código IA"),
    ("jetbrains",     "JetBrains",             "https://www.jetbrains.com",                     "https://www.jetbrains.com/store/",                               "",                                                                    "Asistentes de Código IA"),
    ("tabnine",       "Tabnine",               "https://www.tabnine.com",                       "https://www.tabnine.com/pricing",                                "",                                                                    "Asistentes de Código IA"),
    ("traeai",        "TRAE AI",               "https://www.trae.ai",                           "https://www.trae.ai/pricing",                                    "",                                                                    "Asistentes de Código IA"),
    ("windsurf",      "Windsurf",              "https://codeium.com/windsurf",                  "https://codeium.com/windsurf/pricing",                           "",                                                                    "Asistentes de Código IA"),
    # Vibe Coding
    ("bolt",          "Bolt",                  "https://bolt.new",                              "https://bolt.new/pricing",                                       "",                                                                    "Vibe Coding"),
    ("lovable",       "Lovable",               "https://lovable.dev",                           "https://lovable.dev/pricing",                                    "",                                                                    "Vibe Coding"),
    ("v0",            "v0",                    "https://v0.dev",                                "https://v0.dev/pricing",                                         "",                                                                    "Vibe Coding"),
    # Generación Visual IA
    ("krea",          "Krea AI",               "https://www.krea.ai",                           "https://www.krea.ai/pricing",                                    "",                                                                    "Generación Visual IA"),
    ("midjourney",    "Midjourney",            "https://www.midjourney.com",                    "https://www.midjourney.com/account/",                            "",                                                                    "Generación Visual IA"),
    # Hosting, Cloud y Otros
    ("bubble",        "Bubble.io",             "https://bubble.io",                             "https://bubble.io/pricing",                                      "",                                                                    "Hosting, Cloud y Otros"),
    ("github",        "GitHub",                "https://github.com",                            "https://github.com/pricing",                                     "",                                                                    "Hosting, Cloud y Otros"),
    ("nicar",         "Nic.ar",                "https://nic.ar",                                "https://nic.ar/es/dominios/buscar",                              "",                                                                    "Hosting, Cloud y Otros"),
    ("sanity",        "Sanity",                "https://www.sanity.io",                         "https://www.sanity.io/pricing",                                  "",                                                                    "Hosting, Cloud y Otros"),
    ("starlink",      "Starlink",              "https://www.starlink.com",                      "https://www.starlink.com/service-plans",                         "",                                                                    "Hosting, Cloud y Otros"),
    ("supabase",      "Supabase",              "https://supabase.com",                          "https://supabase.com/pricing",                                   "",                                                                    "Hosting, Cloud y Otros"),
    ("vercel",        "Vercel",                "https://vercel.com",                            "https://vercel.com/pricing",                                     "",                                                                    "Hosting, Cloud y Otros"),
    ("webflow",       "Webflow",               "https://webflow.com",                           "https://webflow.com/pricing",                                    "",                                                                    "Hosting, Cloud y Otros"),
    # Diseño
    ("adobe",         "Adobe Creative Cloud",  "https://www.adobe.com/es/creativecloud.html",   "https://www.adobe.com/es/creativecloud/plans.html",              "",                                                                    "Diseño"),
    ("canva",         "Canva",                 "https://www.canva.com",                         "https://www.canva.com/pricing/",                                 "",                                                                    "Diseño"),
    ("clipchamp",     "Clipchamp",             "https://clipchamp.com",                         "https://clipchamp.com/es/pricing/",                              "",                                                                    "Diseño"),
    ("figjam",        "FigJam",                "https://www.figma.com/figjam/",                 "https://www.figma.com/pricing/",                                 "",                                                                    "Diseño"),
    ("figma",         "Figma",                 "https://www.figma.com",                         "https://www.figma.com/pricing/",                                 "",                                                                    "Diseño"),
    ("framer",        "Framer",                "https://www.framer.com",                        "https://www.framer.com/pricing/",                                "",                                                                    "Diseño"),
    ("picsart",       "Picsart",               "https://picsart.com",                           "https://picsart.com/pricing",                                    "",                                                                    "Diseño"),
    # Seguridad
    ("onepassword",   "1Password",             "https://1password.com",                         "https://1password.com/sign-up/",                                 "",                                                                    "Seguridad"),
    ("bitwarden",     "Bitwarden",             "https://bitwarden.com",                         "https://bitwarden.com/pricing/",                                 "",                                                                    "Seguridad"),
    ("nordvpn",       "NordVPN",               "https://nordvpn.com/es/",                       "https://nordvpn.com/es/pricing/",                                "",                                                                    "Seguridad"),
    # Productividad
    ("appleone",      "Apple One",             "https://www.apple.com/ar/apple-one/",           "https://www.apple.com/ar/apple-one/",                            "",                                                                    "Productividad"),
    ("capcut",        "CapCut",                "https://www.capcut.com",                        "https://www.capcut.com/pricing",                                 "",                                                                    "Productividad"),
    ("elevenlabs",    "ElevenLabs",            "https://elevenlabs.io",                         "https://elevenlabs.io/pricing",                                  "",                                                                    "Productividad"),
    ("gastipro",      "Gasti Pro (ARS)",       "https://gasti.app",                             "https://gasti.app/pricing",                                      "",                                                                    "Productividad"),
    ("gastitprousd",  "Gasti Pro (USD)",       "https://gasti.app",                             "https://gasti.app/pricing",                                      "",                                                                    "Productividad"),
    ("gworkspace",    "Google Workspace",      "https://workspace.google.com/intl/es-419/",     "https://workspace.google.com/intl/es-419/pricing/",              "",                                                                    "Productividad"),
    ("ifttt",         "IFTTT",                 "https://ifttt.com",                             "https://ifttt.com/plans",                                        "",                                                                    "Productividad"),
    ("linkedin",      "LinkedIn Premium",      "https://www.linkedin.com",                      "https://www.linkedin.com/premium/products/",                     "",                                                                    "Productividad"),
    ("microsoft365",  "Microsoft 365",         "https://www.microsoft.com/es-ar/microsoft-365", "https://www.microsoft.com/es-ar/microsoft-365/compare-all-microsoft-365-products", "",                                               "Productividad"),
    ("notion",        "Notion",                "https://www.notion.so",                         "https://www.notion.so/pricing",                                  "",                                                                    "Productividad"),
    ("obsidian",      "Obsidian",              "https://obsidian.md",                           "https://obsidian.md/pricing",                                    "",                                                                    "Productividad"),
    ("proton",        "Proton",                "https://proton.me",                             "https://proton.me/pricing",                                      "",                                                                    "Productividad"),
    ("tradingview",   "TradingView",           "https://www.tradingview.com",                   "https://www.tradingview.com/pricing/",                           "",                                                                    "Productividad"),
    ("zoom",          "Zoom",                  "https://zoom.us",                               "https://zoom.us/pricing",                                        "",                                                                    "Productividad"),
    # Almacenamiento
    ("icloud",        "Apple iCloud",          "https://www.apple.com/ar/icloud/",              "https://www.apple.com/ar/icloud/",                               "",                                                                    "Almacenamiento"),
    ("dropbox",       "Dropbox",               "https://www.dropbox.com",                       "https://www.dropbox.com/plans",                                  "",                                                                    "Almacenamiento"),
    ("googleone",     "Google One",            "https://one.google.com/about",                  "https://one.google.com/about/plans",                             "",                                                                    "Almacenamiento"),
    ("onedrive",      "OneDrive",              "https://www.microsoft.com/es-ar/microsoft-365/onedrive/compare-onedrive-plans", "https://www.microsoft.com/es-ar/microsoft-365/onedrive/compare-onedrive-plans", "",                  "Almacenamiento"),
    ("yandex360",     "Yandex 360",            "https://360.yandex.com",                        "https://360.yandex.com/pricing/",                                "",                                                                    "Almacenamiento"),
    # Redes Sociales y Chat
    ("discord",       "Discord",               "https://discord.com",                           "https://discord.com/nitro",                                      "",                                                                    "Redes Sociales y Chat"),
    ("metaverified",  "Meta Verified",         "https://about.meta.com/technologies/meta-verified/", "https://about.meta.com/technologies/meta-verified/",       "",                                                                    "Redes Sociales y Chat"),
    ("slack",         "Slack",                 "https://slack.com/intl/es-419",                 "https://slack.com/intl/es-419/pricing",                          "",                                                                    "Redes Sociales y Chat"),
    ("streamlabs",    "Streamlabs",            "https://streamlabs.com",                        "https://streamlabs.com/pricing",                                 "",                                                                    "Redes Sociales y Chat"),
    ("telegram",      "Telegram",              "https://telegram.org",                          "https://telegram.org/faq_premium",                               "",                                                                    "Redes Sociales y Chat"),
    ("twitter",       "X (Twitter)",           "https://twitter.com",                           "https://twitter.com/i/premium_sign_up",                          "",                                                                    "Redes Sociales y Chat"),
    # Aprendizaje
    ("audible",       "Amazon Audible",        "https://www.audible.com.ar",                    "https://www.audible.com.ar/ep/membership",                       "",                                                                    "Aprendizaje"),
    ("brilliant",     "Brilliant",             "https://brilliant.org",                         "https://brilliant.org/premium/",                                 "",                                                                    "Aprendizaje"),
    ("busuu",         "Busuu",                 "https://www.busuu.com/es",                      "https://www.busuu.com/es/premium",                               "",                                                                    "Aprendizaje"),
    ("duolingo",      "Duolingo",              "https://www.duolingo.com",                      "https://www.duolingo.com/subscribe",                             "",                                                                    "Aprendizaje"),
    ("kindle",        "Kindle Unlimited",      "https://www.amazon.com.ar/kindle-dbs/ku/kuExperience", "https://www.amazon.com.ar/kindle-dbs/ku/kuExperience",   "",                                                                    "Aprendizaje"),
    ("mimo",          "Mimo",                  "https://getmimo.com",                           "https://getmimo.com/pricing",                                    "",                                                                    "Aprendizaje"),
]


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
        _engine = create_engine(settings.database_url, connect_args=connect_args)
    return _engine


def init_db():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for sid, name, website, pricing, logo, category in _SERVICES:
            if not session.get(ServiceMeta, sid):
                session.add(ServiceMeta(
                    id=sid, name=name, website_url=website,
                    pricing_url=pricing, logo_url=logo, category=category,
                ))
        session.commit()


def get_session():
    with Session(get_engine()) as session:
        yield session


def save_scrape_results(service_id: str, plans: List[ScrapedPlan], is_manual: bool = False):
    with Session(get_engine()) as session:
        # Mark old records as not current
        old = session.exec(
            select(PriceRecord).where(
                PriceRecord.service_id == service_id,
                PriceRecord.is_current == True,
            )
        ).all()
        for rec in old:
            rec.is_current = False

        now = datetime.utcnow()
        for plan in plans:
            session.add(PriceRecord(
                service_id=service_id,
                plan_name=plan.plan_name,
                price=plan.price,
                currency=plan.currency,
                billing_period=plan.billing_period,
                features=json.dumps(plan.features, ensure_ascii=False),
                is_current=True,
                is_manual=is_manual,
                scraped_at=now,
            ))

        meta = session.get(ServiceMeta, service_id)
        if meta:
            meta.last_scraped_at = now
            meta.scrape_status = "ok"
            meta.last_error = ""

        session.commit()


def mark_scrape_error(service_id: str, error: str):
    with Session(get_engine()) as session:
        meta = session.get(ServiceMeta, service_id)
        if meta:
            meta.scrape_status = "error"
            meta.last_error = error[:500]
            meta.last_scraped_at = datetime.utcnow()
        session.commit()
