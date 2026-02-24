from pydantic import BaseModel
from typing import Optional
from datetime import date

class ReleaseCreate(BaseModel):
	artist: str
	title: str
	release_date: Optional[date] = None
	genre: Optional[str] = None
	country: Optional[str] = None
	label: Optional[str] = None

class ReleaseUpdate(BaseModel):
	artist: Optional[str] = None
	title: Optional[str] = None
	release_date: Optional[date] = None
	genre: Optional[str] = None
	country: Optional[str] = None
	label: Optional[str] = None
