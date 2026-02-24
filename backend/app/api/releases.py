from fastapi import APIRouter
from app.db import get_connection
from app.db import fetch_all, execute
from app.api.schemas import ReleaseCreate, ReleaseUpdate

router = APIRouter()

@router.get("/releases")
def get_releases():
	rows = fetch_all("SELECT id, artist, title, release_date, genre, country, label FROM releases;")
	releases = [
		{
			"id": r[0],
			"artist": r[1],
			"title": r[2],
			"release_date": r[3],
			"genre": r[4],
			"country": r[5],
			"label": r[6],
		}
		for r in rows
	]
	return {"releases": releases}

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

@router.post("/releases/add")
def add_release(data: ReleaseCreate):
	query = """
		INSERT INTO releases (artist, title, release_date, genre, country, label)
		VALUES (%s, %s, %s, %s, %s, %s)
		RETURNING id;
	"""
	params = (
		data.artist,
		data.title,
		data.release_date,
		data.genre,
		data.country,
		data.label,
	)

	conn = get_connection()
	cur = conn.cursor()
	cur.execute(query, params)
	new_id = cur.fetchone()[0]
	conn.commit()
	cur.close()
	conn.close()

	return {
		"id": new_id,
		"artist": data.artist,
		"title": data.title,
		"release_date": data.release_date,
		"genre": data.genre,
		"country": data.country,
		"label": data.label,
	}

@router.delete("/releases/{release_id}")
def delete_release(release_id: int):
	query = "DELETE FROM releases WHERE id = %s RETURNING id;"
	params = (release_id,)

	conn = get_connection()
	cur = conn.cursor()
	cur.execute(query, params)
	deleted = cur.fetchone()
	conn.commit()
	cur.close()
	conn.close()

	if deleted is None:
		return {"status": "not_found", "id": release_id}

	return {"status": "deleted", "id": deleted[0]}

@router.put("/releases/{release_id}")
def update_release(release_id: int, data: ReleaseUpdate):
	fields = []
	params = []

	if data.artist is not None:
		fields.append("artist = %s")
		params.append(data.artist)

	if data.title is not None:
		fields.append("title = %s")
		params.append(data.title)

	if data.release_date is not None:
		fields.append("release_date = %s")
		params.append(data.release_date)

	if data.genre is not None:
		fields.append("genre = %s")
		params.append(data.genre)

	if data.country is not None:
		fields.appends("country = %s")
		params.append(data.country)

	if data.label is not None:
		fields.append("label = %s")
		params.append(data.label)

	if not fields:
		return {"status": "no_changes"}

	query = f"UPDATE releases SET {', '.join(fields)} WHERE id = %s RETURNING id;"
	params.append(release_id)

	conn = get_connection()
	cur = conn.cursor()
	cur.execute(query, tuple(params))
	updated = cur.fetchone()
	conn.commit()
	cur.close()
	conn.close()

	if updated is None:
		return {"status": "not_found", "id": release_id}

	return {"status": "updated", "id": updated[0]}
