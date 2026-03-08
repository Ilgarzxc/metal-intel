# app/api/releases.py

from fastapi import APIRouter, HTTPException
from app.db import fetch_all, execute
from app.api.schemas import ReleaseCreate, ReleaseUpdate

router = APIRouter()


# -------------------------
# DB Health Check
# -------------------------
@router.get("/db-check")
async def db_check():
    try:
        result = await fetch_all("SELECT 1;")
        return {"db_status": "ok", "result": result[0][0]}
    except Exception as e:
        return {"db_status": "error", "details": str(e)}


# -------------------------
# Get all releases
# -------------------------
@router.get("/releases")
async def get_releases():
    query = """
    SELECT 
        r.id, r.artist, r.title, r.release_date, r.country, r.label,
        STRING_AGG(g.name, ', ') as genres
    FROM releases r
    LEFT JOIN release_genres rg ON r.id = rg.release_id
    LEFT JOIN genres g ON rg.genre_id = g.id
    GROUP BY r.id;
    """
    rows = await fetch_all(query)
    releases = [
        {
            "id": r["id"],
            "artist": r["artist"],
            "title": r["title"],
            "release_date": r["release_date"],
            "country": r["country"],
            "label": r["label"],
            "genres": r["genres"],
        }
        for r in rows
    ]
    return {"releases": releases}


# -------------------------
# Add a release
# -------------------------
@router.post("/releases/add")
async def add_release(data: ReleaseCreate):
    try:
        # Insert main release
        insert_release = """
        INSERT INTO releases (artist, title, release_date, country, label)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id;
        """
        new_id_row = await fetch_all(insert_release, data.artist, data.title, data.release_date, data.country, data.label)
        new_id = new_id_row[0]["id"]

        # Insert genres and link
        if data.genre:
            for genre_name in data.genre:
                genre_row = await fetch_all("""
                    INSERT INTO genres (name) VALUES ($1)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id;
                """, genre_name)
                genre_id = genre_row[0]["id"]
                await execute("INSERT INTO release_genres (release_id, genre_id) VALUES ($1, $2);", new_id, genre_id)

        return {"id": new_id, **data.dict()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# Delete a release
# -------------------------
@router.delete("/releases/{release_id}")
async def delete_release(release_id: int):
    try:
        deleted = await fetch_all("DELETE FROM releases WHERE id = $1 RETURNING id;", release_id)
        if not deleted:
            return {"status": "not_found", "id": release_id}
        return {"status": "deleted", "id": deleted[0]["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# Update a release
# -------------------------
@router.put("/releases/{release_id}")
async def update_release(release_id: int, data: ReleaseUpdate):
    try:
        update_fields = []
        update_params = []

        for field, value in data.dict(exclude={'genre'}, exclude_unset=True).items():
            update_fields.append(f"{field} = ${len(update_params)+1}")
            update_params.append(value)

        if update_fields:
            # Add release_id at the end for WHERE clause
            update_params.append(release_id)
            query = f"UPDATE releases SET {', '.join(update_fields)} WHERE id = ${len(update_params)} RETURNING id;"
            updated = await fetch_all(query, *update_params)
            if not updated:
                return {"status": "not_found", "id": release_id}

        # Update genres with "delete and replace" strategy
        if data.genre is not None:
            await execute("DELETE FROM release_genres WHERE release_id = $1;", release_id)
            for genre_name in data.genre:
                genre_row = await fetch_all("""
                    INSERT INTO genres (name) VALUES ($1)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id;
                """, genre_name)
                genre_id = genre_row[0]["id"]
                await execute("INSERT INTO release_genres (release_id, genre_id) VALUES ($1, $2);", release_id, genre_id)

        return {"status": "updated", "id": release_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))