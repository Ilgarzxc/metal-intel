import asyncio
import logging

from app.services.musicbrainz import search_releases_group
from app.db import get_connection, execute_batch, init_pool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="fetcher.log",
)

logger = logging.getLogger(__name__)


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


async def save_releases(conn, releases):

    if not releases:
        logger.info("No releases to save")
        return

    query = """
    INSERT INTO releases (artist, title, release_date, mbid)
    VALUES ($1,$2,$3,$4)
    ON CONFLICT (mbid) DO NOTHING
    """

    params = [
        (r["artist"], r["title"], r["release_date"], r["mbid"])
        for r in releases
    ]

    logger.info(f"Inserting {len(params)} releases")

    await execute_batch(query, params)


async def fetch_all_metal(batch_size=5, max_pages=1):

    offset = 0
    page = 0

    conn = await get_connection()

    try:

        while True:

            await asyncio.sleep(1)

            data = await search_releases_group("metal", batch_size, offset)

            releases = data.get("release-groups")

            logger.info(f"MusicBrainz returned {len(releases)} items")

            if not releases:
                break

            clean_releases = []

            for item in releases:

                if item.get("primary-type") != "Album":
                    continue

                clean = transform_release(item)

                logger.info(f"Parsed release: {clean}")

                clean_releases.append(clean)

            await save_releases(conn, clean_releases)

            offset += batch_size
            page += 1

            if max_pages and page >= max_pages:
                logger.info("Reached test limit")
                break

    finally:
        await conn.close()


async def main():

    # 🔴 critical line
    await init_pool()

    await fetch_all_metal(
        batch_size=5,
        max_pages=1
    )


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