"""Data models (dataclasses)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SongInfo:
    """Carries song information."""

    title: str
    artist: str
    album: str
    index: int


@dataclass(frozen=True)
class PlaylistSource:
    """Carries the playlist name."""

    name: str
