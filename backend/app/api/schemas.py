from pydantic import BaseModel
from typing import Optional
from datetime import date

'''
A problem to fix (?) in the future:
--- YYYYMMDD date format. Might be not so useful, depends on musicbrainz data. 
Have to check their data.
'''

class ReleaseCreate(BaseModel):
	artist: str
	title: str
	release_date: Optional[date] = None
	genre: Optional[list[str]] = None
	country: Optional[str] = None
	label: Optional[str] = None

class ReleaseUpdate(BaseModel):
	artist: Optional[str] = None
	title: Optional[str] = None
	release_date: Optional[date] = None
	genre: Optional[list[str]] = None
	country: Optional[str] = None
	label: Optional[str] = None
