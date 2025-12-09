"""Unit tests for data models."""

from src.models.data_classes import SongInfo, PlaylistSource

def test_song_info_creation():
    """Test creating a SongInfo instance."""
    song = SongInfo(title="Bohemian Rhapsody", artist="Queen", album="A Night at the Opera")
    assert song.title == "Bohemian Rhapsody"
    assert song.artist == "Queen"
    assert song.album == "A Night at the Opera"

def test_playlist_source_creation():
    """Test creating a PlaylistSource instance."""
    playlist = PlaylistSource(name="My Awesome Playlist")
    assert playlist.name == "My Awesome Playlist"
