"""Abstract interfaces (protocols) for YouTube search/playlist operations.

This module provides the `VideoSearcher` abstract base class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional


class VideoSearcher(ABC):
    """Abstract Base Class for video search operations."""

    @abstractmethod
    def search_video(self, query: str) -> Optional[Dict[str, str]]:
        """Returns the most relevant video ID for the given query."""
        raise NotImplementedError

    @abstractmethod
    def create_playlist(self, title: str, description: str = "") -> Optional[str]:
        """Creates a new playlist in the user's account and returns its ID."""
        raise NotImplementedError

    @abstractmethod
    def add_video_to_playlist(self, playlist_id: str, video_id: str) -> bool:
        """Adds a single video ID to the specified playlist."""
        raise NotImplementedError
