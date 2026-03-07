import asyncio
import logging
from app.services.musicbrainz import search_releases_group
from app.db import get_connection, execute_batch

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  - %(levelname)s - %(message)s',
    filename='fetcher.log'
    )
logger = logging.getLogger(__name__)

# Белый список жанров
ALLOWED_GENRES = {
    "Black Metal", "Death Metal", "Doom Metal",
    "Heavy Metal", "Thrash Metal", "Power Metal",
    "Folk Metal", "Progressive Metal", "Symphonic Metal",
    "Alternative Metal", "Avant-garde Metal", "Blackened Death Metal", 
    "Drone Metal", "Gothic Metal", "Grunge",
    "Industrial Metal", "Post-metal", "Mathcore",
    "Metalcore", "Deathcore", "Stoner Metal"
}

async def fetch_all_metal(batch_size=5):
    offset = 0
    all_releases = []

    while True:
        await asyncio.sleep(1)  # rate limit
        data = await search_releases_group("metal", batch_size, offset)
        releases = data.get("release-groups")
        if not releases:
            break

        for item in releases:
            if item.get("primary-type") != "Album":
                continue
            clean = transform_release(item)

            # Фильтр по жанрам
            genres = [g for g in clean["genre"] if g in ALLOWED_GENRES]
            if not genres:
                continue
            clean["genre"] = genres

            all_releases.append(clean)

        logger.info(f"Fetched offset {offset} – {len(releases)} items")
        # offset += batch_size // commented out to test

    return all_releases


def transform_release(item):
    mbid = item.get("id")
    title = item.get("title")
    artists_credits = item.get("artist-credit", [])
    artist_name = "".join([a.get("name", "") for a in artists_credits])
    raw_date = item.get("first-release-date", "")
    parts = raw_date.split("-") if raw_date else []
    while 0 < len(parts) < 3:
        parts.append("01")
    clean_date = "-".join(parts) if parts else None
    tags = item.get("tags", [])
    genres = [t.get("name") for t in tags] if tags else []
    return {
        "mbid": mbid,
        "title": title,
        "artist": artist_name,
        "release_date": clean_date,
        "genre": genres
    }

async def save_releases(all_releases):
    """Асинхронная батч-вставка с ON CONFLICT DO NOTHING"""
    if not all_releases:
        return

    query = """
    INSERT INTO releases (artist, title, release_date, country, label, mbid)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (mbid) DO NOTHING
    """
    params = [
        (
            r["artist"],
            r["title"],
            r["release_date"],
            r.get("country"),
            r.get("label"),
            r["mbid"]
        )
        for r in all_releases
    ]

    conn = await get_connection()
    try:
        await execute_batch(query, params)
    finally:
        await conn.close()

# Пример использования
async def main():
    releases = await fetch_all_metal()
    await save_releases(releases)

if __name__ == "__main__":
    asyncio.run(main())