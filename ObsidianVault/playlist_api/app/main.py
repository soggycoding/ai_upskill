from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas, crud
from app.database import engine, get_db

# Create database tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Playlist API",
    description="A RESTful API for managing playlists and shared song collections without duplication.",
    version="1.0.0",
)


@app.get("/", tags=["Health"])
def read_root():
    return {"message": "Welcome to the Playlist API. Visit /docs for interactive Swagger API documentation."}


# --- Song Catalog Endpoints ---
@app.post("/songs", response_model=schemas.SongResponse, status_code=status.HTTP_201_CREATED, tags=["Songs"])
def create_song(song: schemas.SongCreate, db: Session = Depends(get_db)):
    """Add a new song to the global catalog."""
    return crud.create_song(db=db, song=song)


@app.get("/songs", response_model=List[schemas.SongResponse], tags=["Songs"])
def list_songs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all songs in the catalog."""
    return crud.get_songs(db=db, skip=skip, limit=limit)


@app.get("/songs/{song_id}", response_model=schemas.SongResponse, tags=["Songs"])
def get_song(song_id: int, db: Session = Depends(get_db)):
    """Get details of a specific song."""
    db_song = crud.get_song(db=db, song_id=song_id)
    if not db_song:
        raise HTTPException(status_code=404, detail=f"Song with ID {song_id} not found.")
    return db_song


# --- Playlist Endpoints ---
@app.post("/playlists", response_model=schemas.PlaylistDetailResponse, status_code=status.HTTP_201_CREATED, tags=["Playlists"])
def create_playlist(playlist: schemas.PlaylistCreate, db: Session = Depends(get_db)):
    """Create a new playlist with optional existing song IDs."""
    db_playlist = crud.create_playlist(db=db, playlist=playlist)
    return db_playlist


@app.get("/playlists", response_model=List[schemas.PlaylistResponse], tags=["Playlists"])
def list_playlists(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all playlists with song counts."""
    return crud.get_playlists(db=db, skip=skip, limit=limit)


@app.get("/playlists/{playlist_id}", response_model=schemas.PlaylistDetailResponse, tags=["Playlists"])
def get_playlist(playlist_id: int, db: Session = Depends(get_db)):
    """Get a playlist by ID including all contained songs."""
    db_playlist = crud.get_playlist(db=db, playlist_id=playlist_id)
    if not db_playlist:
        raise HTTPException(status_code=404, detail=f"Playlist with ID {playlist_id} not found.")
    return db_playlist


@app.put("/playlists/{playlist_id}", response_model=schemas.PlaylistDetailResponse, tags=["Playlists"])
def update_playlist(playlist_id: int, playlist_update: schemas.PlaylistUpdate, db: Session = Depends(get_db)):
    """Update playlist metadata (name, description)."""
    db_playlist = crud.update_playlist(db=db, playlist_id=playlist_id, playlist_update=playlist_update)
    if not db_playlist:
        raise HTTPException(status_code=404, detail=f"Playlist with ID {playlist_id} not found.")
    return db_playlist


@app.delete("/playlists/{playlist_id}", status_code=status.HTTP_200_OK, tags=["Playlists"])
def delete_playlist(playlist_id: int, db: Session = Depends(get_db)):
    """Delete a playlist. Songs contained in the playlist remain intact in the catalog."""
    success = crud.delete_playlist(db=db, playlist_id=playlist_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Playlist with ID {playlist_id} not found.")
    return {"message": f"Playlist with ID {playlist_id} deleted successfully."}


# --- Playlist Song Management ---
@app.post("/playlists/{playlist_id}/songs", response_model=schemas.PlaylistDetailResponse, status_code=status.HTTP_201_CREATED, tags=["Playlist Songs"])
def add_song_to_playlist(playlist_id: int, request: schemas.AddSongToPlaylistRequest, db: Session = Depends(get_db)):
    """Add a song to a playlist.
    Can pass an existing `song_id` OR provide new `song_data` to create and add in one step.
    """
    db_playlist = crud.get_playlist(db=db, playlist_id=playlist_id)
    if not db_playlist:
        raise HTTPException(status_code=404, detail=f"Playlist with ID {playlist_id} not found.")

    target_song_id = request.song_id

    if request.song_data:
        new_song = crud.create_song(db=db, song=request.song_data)
        target_song_id = new_song.id
    else:
        existing_song = crud.get_song(db=db, song_id=target_song_id)
        if not existing_song:
            raise HTTPException(status_code=404, detail=f"Song with ID {target_song_id} not found in catalog.")

    crud.add_song_to_playlist(db=db, playlist_id=playlist_id, song_id=target_song_id)
    return crud.get_playlist(db=db, playlist_id=playlist_id)


@app.delete("/playlists/{playlist_id}/songs/{song_id}", response_model=schemas.PlaylistDetailResponse, tags=["Playlist Songs"])
def remove_song_from_playlist(playlist_id: int, song_id: int, db: Session = Depends(get_db)):
    """Remove a song from a playlist. The song itself remains in the catalog."""
    db_playlist = crud.get_playlist(db=db, playlist_id=playlist_id)
    if not db_playlist:
        raise HTTPException(status_code=404, detail=f"Playlist with ID {playlist_id} not found.")

    success = crud.remove_song_from_playlist(db=db, playlist_id=playlist_id, song_id=song_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Song with ID {song_id} is not in playlist {playlist_id}.")

    return crud.get_playlist(db=db, playlist_id=playlist_id)
