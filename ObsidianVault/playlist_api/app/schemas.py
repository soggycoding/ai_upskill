from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, model_validator


# --- Song Schemas ---
class SongBase(BaseModel):
    title: str
    artist: str
    album: Optional[str] = None
    duration_seconds: Optional[int] = None


class SongCreate(SongBase):
    pass


class SongResponse(SongBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- PlaylistSong Junction Schemas ---
class PlaylistSongItemResponse(BaseModel):
    id: int
    position: int
    added_at: datetime
    song: SongResponse

    model_config = ConfigDict(from_attributes=True)


# --- Playlist Schemas ---
class PlaylistBase(BaseModel):
    name: str
    description: Optional[str] = None


class PlaylistCreate(PlaylistBase):
    song_ids: Optional[List[int]] = None


class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PlaylistResponse(PlaylistBase):
    id: int
    created_at: datetime
    updated_at: datetime
    song_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class PlaylistDetailResponse(PlaylistBase):
    id: int
    created_at: datetime
    updated_at: datetime
    songs: List[PlaylistSongItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Add Song to Playlist Request ---
class AddSongToPlaylistRequest(BaseModel):
    song_id: Optional[int] = None
    song_data: Optional[SongCreate] = None

    @model_validator(mode="after")
    def check_song_source(self):
        if not self.song_id and not self.song_data:
            raise ValueError("Must provide either 'song_id' or 'song_data' to add a song to the playlist.")
        return self
