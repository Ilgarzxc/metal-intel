from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class Release(Base):
        __tablename__ = "releases"

        id = Column(Integer, primary_key=True, index=True)
        artist = Column(String(255))
        title = Column(String(255))
        release_date = Column(Date)
        genre = Column(String(100))
        country = Column(String(100))
        label = Column(String(255))

        # mbid for connection with MusicBrainz
        mbid = Column(UUID(as_uuid=True), unique=True, nullable=True)
        