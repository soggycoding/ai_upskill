from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models, schemas


# --- Song CRUD ---
def create_song(db: Session, song: schemas.SongCreate) -> models.Song:
    db_song = models.Song(
        title=song.title,
        artist=song.artist,
        album=song.album,
        duration_seconds=song.duration_seconds,
    )
    db.add(db_song)
    db.commit()
    db.refresh(db_song)
    return db_song


def get_song(db: Session, song_id: int) -> Optional[models.Song]:
    return db.query(models.Song).filter(models.Song.id == song_id).first()


def get_songs(db: Session, skip: int = 0, limit: int = 100) -> List[models.Song]:
    return db.query(models.Song).offset(skip).limit(limit).all()


# --- Playlist CRUD ---
def create_playlist(db: Session, playlist: schemas.PlaylistCreate) -> models.Playlist:
    db_playlist = models.Playlist(
        name=playlist.name,
        description=playlist.description,
    )
    db.add(db_playlist)
    db.commit()
    db.refresh(db_playlist)

    if playlist.song_ids:
        position = 1
        for song_id in playlist.song_ids:
            song = get_song(db, song_id)
            if song:
                ps = models.PlaylistSong(
                    playlist_id=db_playlist.id,
                    song_id=song.id,
                    position=position,
                )
                db.add(ps)
                position += 1
        db.commit()
        db.refresh(db_playlist)

    return db_playlist


def get_playlists(db: Session, skip: int = 0, limit: int = 100) -> List[dict]:
    playlists = db.query(models.Playlist).offset(skip).limit(limit).all()
    results = []
    for p in playlists:
        song_count = len(p.playlist_songs)
        results.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "song_count": song_count,
        })
    return results


def get_playlist(db: Session, playlist_id: int) -> Optional[models.Playlist]:
    playlist = db.query(models.Playlist).filter(models.Playlist.id == playlist_id).first()
    if playlist:
        db.expire(playlist)
    return playlist


def update_playlist(
    db: Session, playlist_id: int, playlist_update: schemas.PlaylistUpdate
) -> Optional[models.Playlist]:
    db_playlist = get_playlist(db, playlist_id)
    if not db_playlist:
        return None

    if playlist_update.name is not None:
        db_playlist.name = playlist_update.name
    if playlist_update.description is not None:
        db_playlist.description = playlist_update.description

    db.commit()
    db.refresh(db_playlist)
    return db_playlist


def delete_playlist(db: Session, playlist_id: int) -> bool:
    db_playlist = get_playlist(db, playlist_id)
    if not db_playlist:
        return False
    db.delete(db_playlist)
    db.commit()
    return True


# --- Playlist Song Management ---
def add_song_to_playlist(
    db: Session, playlist_id: int, song_id: int
) -> Optional[models.PlaylistSong]:
    playlist = get_playlist(db, playlist_id)
    song = get_song(db, song_id)

    if not playlist or not song:
        return None

    # Calculate next position
    max_pos = (
        db.query(func.max(models.PlaylistSong.position))
        .filter(models.PlaylistSong.playlist_id == playlist_id)
        .scalar()
    )
    next_position = (max_pos or 0) + 1

    ps = models.PlaylistSong(
        playlist_id=playlist_id,
        song_id=song_id,
        position=next_position,
    )
    db.add(ps)
    db.commit()
    db.refresh(ps)
    db.expire_all()
    return ps


def remove_song_from_playlist(db: Session, playlist_id: int, song_id: int) -> bool:
    ps = (
        db.query(models.PlaylistSong)
        .filter(
            models.PlaylistSong.playlist_id == playlist_id,
            models.PlaylistSong.song_id == song_id,
        )
        .first()
    )
    if not ps:
        return False

    db.delete(ps)
    db.commit()
    db.expire_all()
    return True
