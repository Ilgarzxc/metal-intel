import asyncio
import logging
from datetime import datetime
from app.db import init_pool, get_connection, execute_batch, execute
from app.services.musicbrainz import search_releases_group

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def transform_release(item):
    """Преобразует релиз из API в формат для базы"""
    mbid = item.get("id")
    title = item.get("title")
    artist_credit = item.get("artist-credit", [])
    artist = "".join(a.get("name", "") for a in artist_credit)

    raw_date = item.get("first-release-date", "")
    parts = raw_date.split("-") if raw_date else []
    # Приведение даты к формату YYYY-MM-DD
    while 0 < len(parts) < 3:
        parts.append("01")
    clean_date = "-".join(parts) if parts else None

    tags = item.get("tags", [])
    genres = [t.get("name") for t in tags] if tags else []

    return {
        "mbid": mbid,
        "title": title,
        "artist": artist,
        "release_date": clean_date,
        "genres": genres
    }


async def save_releases(conn, releases):
    """Сохраняет релизы в БД с проверкой на уникальность mbid"""
    if not releases:
        return

    query = """
    INSERT INTO releases (artist, title, release_date, mbid)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (mbid) DO NOTHING
    """

    params = [(r["artist"], r["title"], r["release_date"], r["mbid"]) for r in releases]
    await execute_batch(query, params)


async def save_genres(conn, releases):
    """Сохраняет все жанры и связывает с релизами"""
    if not releases:
        return

    # Собираем все уникальные жанры из батча
    genre_set = set()
    for r in releases:
        for g in r["genres"]:
            genre_set.add(g)

    if not genre_set:
        return

    # Вставка новых жанров
    genre_params = [(g,) for g in genre_set]
    await execute_batch("INSERT INTO genres (name) VALUES ($1) ON CONFLICT (name) DO NOTHING", genre_params)

    # Связывание релизов с жанрами
    for r in releases:
        for g in r["genres"]:
            # Получаем id жанра
            genre_row = await conn.fetchrow("SELECT id FROM genres WHERE name = $1", g)
            if not genre_row:
                continue
            genre_id = genre_row["id"]

            # Получаем id релиза
            release_row = await conn.fetchrow("SELECT id FROM releases WHERE mbid = $1", r["mbid"])
            if not release_row:
                continue
            release_id = release_row["id"]

            await execute(
                "INSERT INTO release_genres (release_id, genre_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                release_id, genre_id
            )


async def fetch_all_metal(batch_size=100, max_pages=None):
    """Постраничная загрузка релизов с MusicBrainz"""
    offset = 0
    page = 0
    conn = await get_connection()

    try:
        while True:
            await asyncio.sleep(1)  # Соблюдение Rate Limit MusicBrainz

            data = await search_releases_group("metal", batch_size, offset)
            releases = data.get("release-groups")
            
            if not releases:
                logger.info("No more releases found")
                break

            clean_releases = []
            for item in releases:
                # Оставляем только полноформатные альбомы
                if item.get("primary-type") != "Album":
                    continue
                
                clean = transform_release(item)
                
                # Сохраняем альбом, если у него есть хотя бы один любой жанр/тег
                if clean["genres"]:
                    clean_releases.append(clean)

            if clean_releases:
                await save_releases(conn, clean_releases)
                await save_genres(conn, clean_releases)
                logger.info(f"Fetched offset {offset} – {len(clean_releases)} albums saved")
            else:
                logger.info(f"Fetched offset {offset} – No albums with tags found in this batch")

            offset += batch_size
            page += 1

            if max_pages and page >= max_pages:
                logger.info("Reached max pages limit")
                break
    finally:
        await conn.close()


async def main():
    await init_pool()
    await fetch_all_metal(batch_size=100, max_pages=None)


if __name__ == "__main__":
    asyncio.run(main())