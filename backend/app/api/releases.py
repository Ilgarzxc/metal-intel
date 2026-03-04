'''
Simple API layer.
1) Receive a request from user
2) Connect to the database
3) Obtain and provide formatted data (JSON)
'''


from fastapi import APIRouter
# Import function for connection to the database
from app.db import get_connection
# Import functions for executing queries and scripts 
from app.db import fetch_all, execute
# Import class of object for releases processing
'''
Should be agjusted according to the recent changes that we applied to the database.
No more 'genre' in the releases schema.
'''
from app.api.schemas import ReleaseCreate, ReleaseUpdate

# Encapsulated application to sort and group the endpoints
router = APIRouter()

# Get a list. Create a dictionary from tuples provided by the database.
@router.get("/releases")
def get_releases():
	rows = fetch_all("""SELECT 
	r.id, r.artist, r.title, r.release_date, r.country, r.label,
	STRING_AGG(g.name, ', ') as genres
FROM releases r
LEFT JOIN release_genres rg ON r.id = rg.release_id
LEFT JOIN genres g ON rg.genre_id = g.id
GROUP BY r.id;""")
	releases = [
		{
			"id": r[0],
			"artist": r[1],
			"title": r[2],
			"release_date": r[3],
			"country": r[4],
			"label": r[5],
			"genres": r[6],
		}
		for r in rows
	]
	return {"releases": releases}

# Function for health check.
@router.get("/db-check")
def db_check():
	try:
		conn = get_connection()
		cur = conn.cursor()
		cur.execute("SELECT 1;")
		result = cur.fetchone()
		cur.close()
		conn.close()
		return {"db_status": "ok", "result": result[0]}
	except Exception as e:
		return {"db_status": "error", "details": str(e)}

# Endpoint for creation of a new album via FastAPI interface
@router.post("/releases/add")
def add_release(data: ReleaseCreate):
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # 1. Insert the main release record into the 'releases' table
        cur.execute("""
            INSERT INTO releases (artist, title, release_date, country, label)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """, (data.artist, data.title, data.release_date, data.country, data.label))
        
        # Get the newly generated ID for the release
        new_id = cur.fetchone()[0]

        # 2. Process genres if the list is provided in the request
        if data.genre:
            for genre_name in data.genre:
                # Insert genre into 'genres' table or find the existing one by name
                # 'ON CONFLICT' ensures we don't get errors for duplicate names
                cur.execute("""
                    INSERT INTO genres (name) VALUES (%s)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id;
                """, (genre_name,))
                genre_id = cur.fetchone()[0]

                # 3. Create a link in the 'release_genres' junction table
                cur.execute("""
                    INSERT INTO release_genres (release_id, genre_id)
                    VALUES (%s, %s);
                """, (new_id, genre_id))

        # Commit the transaction: all changes are saved at once
        conn.commit()
        
        # Return the created object for the frontend/client
        return {"id": new_id, **data.dict()}

    except Exception as e:
        # If any step fails, roll back the entire transaction to keep DB clean
        conn.rollback()
        raise e
    finally:
        # Always close the cursor and connection to prevent memory leaks
        cur.close()
        conn.close()

# Endpoint for deletion of a release via FastAPI interface
@router.delete("/releases/{release_id}")
def delete_release(release_id: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Delete from 'releases'. 'release_genres' rows will be deleted automatically due to CASCADE
        query = "DELETE FROM releases WHERE id = %s RETURNING id;"
        cur.execute(query, (release_id,))
        deleted = cur.fetchone()
        conn.commit()

        if deleted is None:
            return {"status": "not_found", "id": release_id}
        return {"status": "deleted", "id": deleted[0]}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

# Endpoint for update of a release via FastAPI interface
@router.put("/releases/{release_id}")
def update_release(release_id: int, data: ReleaseUpdate):
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # 1. Update basic release fields if they are provided
        update_fields = []
        update_params = []
        
        # Mapping Pydantic model to SQL columns (excluding 'genre')
        for field, value in data.dict(exclude={'genre'}, exclude_unset=True).items():
            update_fields.append(f"{field} = %s")
            update_params.append(value)

        if update_fields:
            query = f"UPDATE releases SET {', '.join(update_fields)} WHERE id = %s RETURNING id;"
            update_params.append(release_id)
            cur.execute(query, tuple(update_params))
            if cur.fetchone() is None:
                return {"status": "not_found", "id": release_id}

        # 2. Update genres: "Delete and Replace" strategy
        if data.genre is not None:
            # Remove all old genre links for this release
            cur.execute("DELETE FROM release_genres WHERE release_id = %s;", (release_id,))
            
            # Add new genre links
            for genre_name in data.genre:
                # Get or create genre ID
                cur.execute("""
                    INSERT INTO genres (name) VALUES (%s)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id;
                """, (genre_name,))
                genre_id = cur.fetchone()[0]

                # Link release with the new genre ID
                cur.execute("""
                    INSERT INTO release_genres (release_id, genre_id)
                    VALUES (%s, %s);
                """, (release_id, genre_id))

        conn.commit()
        return {"status": "updated", "id": release_id}

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
