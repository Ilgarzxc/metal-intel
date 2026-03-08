import asyncio
import logging
from datetime import datetime, date

import httpx

from app.db import init_pool, execute_batch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = "https://musicbrainz.org/ws/2/release/"


def parse_date(date_str: str | None) -> date | None:
    """Преобразует строку даты в datetime.date"""
    if not date_str:
        return None

    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    return None


async def fetch_releases(genre: str, limit: int = 5):
    """Загружает релизы по жанру"""

    params = {
        "query": f"tag:{genre}",
        "fmt": "json",
        "limit": limit,
    }

    async with httpx.AsyncClient(timeout=30, headers={
        "User-Agent": "metal-intel/0.1 (contact: ilgar.gurbanov.90@gmail.com)"
    }
    ) as client:
        r = await client.get(API_URL, params=params)
        r.raise_for_status()
        data = r.json()

    releases = data.get("releases", [])
    logger.info(f"Fetched {len(releases)} releases for genre '{genre}'")

    clean = []

    for r in releases:
        clean.append(
            (
                r.get("id"),
                r.get("title"),
                parse_date(r.get("date")),
                genre,
            )
        )

    return clean


async def save_releases(releases):

    if not releases:
        logger.warning("No releases to save")
        return

    query = """
    INSERT INTO releases (
        musicbrainz_id,
        title,
        release_date,
        genre
    )
    VALUES ($1,$2,$3,$4)
    ON CONFLICT (musicbrainz_id) DO NOTHING
    """

    await execute_batch(query, releases)

    logger.info(f"Saved {len(releases)} releases to DB")


async def fetch_and_store(genre: str, limit: int = 5):

    releases = await fetch_releases(genre, limit)

    await save_releases(releases)


async def main():

    genre = "metal"

    logger.info(f"Starting fetch for genre: {genre}")

    # Инициализация пула соединений
    await init_pool()

    await fetch_and_store(
        genre=genre,
        limit=5,
    )

    logger.info("Finished")


if __name__ == "__main__":
    asyncio.run(main())

'''import asyncio
import logging

from app.services.musicbrainz import search_releases_group
from app.db import get_connection, execute_batch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="fetcher.log",
)

logger = logging.getLogger(__name__)


ALLOWED_GENRES = {
    "Black Metal", "Death Metal", "Doom Metal",
    "Heavy Metal", "Thrash Metal", "Power Metal",
    "Folk Metal", "Progressive Metal", "Symphonic Metal",
    "Alternative Metal", "Avant-garde Metal",
    "Blackened Death Metal", "Drone Metal",
    "Gothic Metal", "Grunge", "Industrial Metal",
    "Post-metal", "Mathcore", "Metalcore",
    "Deathcore", "Stoner Metal"
}


# -----------------------------
# Transform API data
# -----------------------------
def transform_release(item):

    mbid = item.get("id")
    title = item.get("title")

    artists_credits = item.get("artist-credit", [])
    artist_name = "".join(a.get("name", "") for a in artists_credits)

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
        "genres": genres
    }


# -----------------------------
# Save releases
# -----------------------------
async def save_releases(conn, releases):

    if not releases:
        return

    query = """
    INSERT INTO releases (artist, title, release_date, mbid)
    VALUES ($1,$2,$3,$4)
    ON CONFLICT (mbid) DO NOTHING
    """

    params = [
        (
            r["artist"],
            r["title"],
            r["release_date"],
            r["mbid"]
        )
        for r in releases
    ]

    await execute_batch(query, params)


# -----------------------------
# Save genres
# -----------------------------
async def save_genres(conn, releases):

    genre_set = set()

    for r in releases:
        for g in r["genres"]:
            if g in ALLOWED_GENRES:
                genre_set.add(g)

    if not genre_set:
        return

    query = """
    INSERT INTO genres (name)
    VALUES ($1)
    ON CONFLICT (name) DO NOTHING
    """

    params = [(g,) for g in genre_set]

    await execute_batch(query, params)


# -----------------------------
# Main fetch loop
# -----------------------------
async def fetch_all_metal(batch_size=100, max_pages=None):

    offset = 0
    page = 0

    conn = await get_connection()

    try:

        while True:

            await asyncio.sleep(1)  # MusicBrainz rate limit

            data = await search_releases_group("metal", batch_size, offset)
            releases = data.get("release-groups")

            if not releases:
                logger.info("No more releases found")
                break

            clean_releases = []

            for item in releases:

                if item.get("primary-type") != "Album":
                    continue

                clean = transform_release(item)

                genres = [g for g in clean["genres"] if g in ALLOWED_GENRES]

                if not genres:
                    continue

                clean["genres"] = genres

                clean_releases.append(clean)

            await save_releases(conn, clean_releases)
            await save_genres(conn, clean_releases)

            logger.info(f"Fetched offset {offset} – {len(clean_releases)} albums saved")

            offset += batch_size
            page += 1

            if max_pages and page >= max_pages:
                logger.info("Reached test page limit")
                break

    finally:
        await conn.close()


# -----------------------------
# Entry point
# -----------------------------
async def main():

    # для теста можно ограничить
    await fetch_all_metal(
        batch_size=100,
        max_pages=1
    )


if __name__ == "__main__":
    asyncio.run(main())'''