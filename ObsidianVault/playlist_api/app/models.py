from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    artist = Column(String, nullable=False, index=True)
    album = Column(String, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    playlist_songs = relationship(
        "PlaylistSong", back_populates="song", cascade="all, delete-orphan"
    )


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships - deleting playlist deletes PlaylistSong mappings, NOT the Songs
    playlist_songs = relationship(
        "PlaylistSong",
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="PlaylistSong.position",
    )

    @property
    def songs(self):
        return self.playlist_songs


class PlaylistSong(Base):
    """Junction table associating Playlists and Songs.
    Allows multiple playlists to reference the same song without duplicating song data.
    """
    __tablename__ = "playlist_songs"

    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(
        Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    song_id = Column(
        Integer, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position = Column(Integer, default=1)
    added_at = Column(DateTime, default=utc_now)

    # Relationships
    playlist = relationship("Playlist", back_populates="playlist_songs")
    song = relationship("Song", back_populates="playlist_songs")
