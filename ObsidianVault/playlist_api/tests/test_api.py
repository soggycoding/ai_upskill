import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

# Ensure project folder is in sys.path for importing app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, get_db
from app.main import app

# Setup in-memory SQLite database for testing with StaticPool
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_and_read_song():
    response = client.post(
        "/songs",
        json={
            "title": "Bohemian Rhapsody",
            "artist": "Queen",
            "album": "A Night at the Opera",
            "duration_seconds": 354,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Bohemian Rhapsody"
    assert data["id"] == 1

    # Read song back
    get_res = client.get(f"/songs/{data['id']}")
    assert get_res.status_code == 200
    assert get_res.json()["artist"] == "Queen"


def test_playlist_crud():
    # 1. Create Playlist
    create_res = client.post(
        "/playlists",
        json={"name": "Rock Classics", "description": "Best rock hits of all time"},
    )
    assert create_res.status_code == 201
    playlist_id = create_res.json()["id"]

    # 2. Read Playlists list
    list_res = client.get("/playlists")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["name"] == "Rock Classics"

    # 3. Read single playlist
    get_res = client.get(f"/playlists/{playlist_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Rock Classics"
    assert get_res.json()["songs"] == []

    # 4. Update Playlist
    update_res = client.put(
        f"/playlists/{playlist_id}",
        json={"name": "Ultimate Rock Classics", "description": "Updated description"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Ultimate Rock Classics"

    # 5. Delete Playlist
    del_res = client.delete(f"/playlists/{playlist_id}")
    assert del_res.status_code == 200

    # Verify deleted
    get_after_del = client.get(f"/playlists/{playlist_id}")
    assert get_after_del.status_code == 404


def test_multiple_playlists_share_same_song_without_duplication():
    """Test that multiple playlists can contain the exact same song without creating duplicate song records."""
    # Create 1 song
    song_res = client.post(
        "/songs",
        json={"title": "Hotel California", "artist": "Eagles", "album": "Hotel California"},
    )
    song_id = song_res.json()["id"]

    # Create 2 distinct playlists
    p1_res = client.post("/playlists", json={"name": "70s Rock"})
    p1_id = p1_res.json()["id"]

    p2_res = client.post("/playlists", json={"name": "Road Trip Hits"})
    p2_id = p2_res.json()["id"]

    # Add the SAME song to Playlist 1
    add1 = client.post(f"/playlists/{p1_id}/songs", json={"song_id": song_id})
    assert add1.status_code == 201
    assert len(add1.json()["songs"]) == 1
    assert add1.json()["songs"][0]["song"]["id"] == song_id

    # Add the SAME song to Playlist 2
    add2 = client.post(f"/playlists/{p2_id}/songs", json={"song_id": song_id})
    assert add2.status_code == 201
    assert len(add2.json()["songs"]) == 1
    assert add2.json()["songs"][0]["song"]["id"] == song_id

    # Verify song catalog still only has 1 song record
    songs_catalog = client.get("/songs").json()
    assert len(songs_catalog) == 1
    assert songs_catalog[0]["id"] == song_id

    # Delete Playlist 1
    client.delete(f"/playlists/{p1_id}")

    # Verify Playlist 2 still has the song
    p2_get = client.get(f"/playlists/{p2_id}").json()
    assert len(p2_get["songs"]) == 1
    assert p2_get["songs"][0]["song"]["id"] == song_id

    # Verify the song still exists in song catalog
    songs_catalog_after = client.get("/songs").json()
    assert len(songs_catalog_after) == 1
    assert songs_catalog_after[0]["id"] == song_id


def test_remove_song_from_playlist():
    # Create song
    song = client.post("/songs", json={"title": "Stairway to Heaven", "artist": "Led Zeppelin"}).json()
    # Create playlist
    p = client.post("/playlists", json={"name": "Acoustic Favorites"}).json()

    # Add song to playlist
    client.post(f"/playlists/{p['id']}/songs", json={"song_id": song["id"]})

    # Remove song from playlist
    rem_res = client.delete(f"/playlists/{p['id']}/songs/{song['id']}")
    assert rem_res.status_code == 200
    assert len(rem_res.json()["songs"]) == 0

    # Song catalog still has the song
    assert len(client.get("/songs").json()) == 1
