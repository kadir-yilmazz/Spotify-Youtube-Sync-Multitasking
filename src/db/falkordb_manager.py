"""FalkorDB connection manager.

This module provides access to the FalkorDB graph using a simple singleton pattern
and includes helper methods for adding/updating data.
"""

import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()


class FalkordbManager:
    """Simple FalkorDB manager (singleton-like behavior).

    Note: `FALKORDB_PORT` environment variable is read as string and converted to int
    to prevent pylint's env default type warning.
    """

    _instance: Optional[FalkorDB] = None
    _graph_name = "spotify_sync_graph"

    def __init__(self) -> None:
        host = os.getenv("FALKORDB_HOST", "localhost")
        port = int(os.getenv("FALKORDB_PORT", "6379"))

        if FalkordbManager._instance is None:
            try:
                db = FalkorDB(host=host, port=port)
                FalkordbManager._instance = db.select_graph(FalkordbManager._graph_name)
            except Exception as exc:  # pylint: disable=broad-except
                print(f"Error: Could not establish FalkorDB connection. {exc}")

    @property
    def graph(self) -> Optional[FalkorDB]:
        """Returns the FalkorDB graph object (or None)."""
        return FalkordbManager._instance

    def _sanitize(self, text: str) -> str:
        """Escapes single quotes in the text.

        Emojis are preserved; only single quotes are escaped.
        """
        if not text:
            return ""
        return str(text).replace("'", "\\'")

    def save_song_info(self, title: str, artist: str, index: int = 0) -> None:
        """Creates or updates a `Song` node."""
        if not self.graph:
            return

        t = self._sanitize(title)
        a = self._sanitize(artist)

        query = f"""
        MERGE (s:Song {{title: '{t}', artist: '{a}'}})
        ON CREATE SET s.scraped_at = timestamp(), 
                      s.match_status = 'PENDING', 
                      s.playlist_index = {index}
        ON MATCH SET s.playlist_index = {index}
        MERGE (art:Artist {{name: '{a}'}})
        MERGE (s)-[:PERFORMED_BY]->(art)
        """
        self.graph.query(query)

    def save_playlist_name(self, name: str) -> None:
        """Saves playlist metadata."""
        if not self.graph:
            return

        n = self._sanitize(name)
        query = f"MERGE (p:PlaylistMeta {{id: 1}}) SET p.name = '{n}'"
        self.graph.query(query)

    def get_playlist_name(self) -> str:
        """Returns the saved playlist name (returns default if not found)."""
        if not self.graph:
            return "Spotify Playlist"
        try:
            res = self.graph.query("MATCH (p:PlaylistMeta) RETURN p.name LIMIT 1")
            return res.result_set[0][0] if res.result_set else "Spotify Playlist"
        except Exception:  # pylint: disable=broad-except
            return "Spotify Playlist"

    def find_pending_songs(self) -> List[Dict[str, str]]:
        """Returns a list of pending songs as dictionaries."""
        if not self.graph:
            return []

        query = (
            "MATCH (s:Song) WHERE s.match_status = 'PENDING' "
            "RETURN s.title, s.artist, ID(s) "
            "ORDER BY s.playlist_index ASC"
        )
        try:
            result = self.graph.query(query)
            return [
                {"title": r[0], "artist": r[1], "song_id": r[2]}
                for r in result.result_set
            ]
        except Exception: # pylint: disable=broad-except
            return []

    def update_song_with_youtube_match(self, song_id: int, video_id: str, query_used: str) -> None:
        """Updates the song with the matched YouTube video ID."""
        if not self.graph:
            return

        q = self._sanitize(query_used)
        query = f"""
        MATCH (s:Song) WHERE ID(s) = {song_id}
        SET s.match_status = 'MATCHED', 
            s.youtube_id = '{video_id}', 
            s.query_used = '{q}',
            s.matched_at = timestamp()
        """
        self.graph.query(query)

    def get_all_matched_video_ids(self) -> List[str]:
        """Returns a list of all matched YouTube video IDs."""
        if not self.graph:
            return []
        
        query = (
            "MATCH (s:Song) WHERE s.match_status = 'MATCHED' "
            "RETURN s.youtube_id "
            "ORDER BY s.playlist_index ASC"
        )
        try:
            result = self.graph.query(query)
            return [r[0] for r in result.result_set]
        except Exception: # pylint: disable=broad-except
            return []

    def clear_database(self) -> None:
        """Deletes all nodes and relationships in the graph."""
        if not self.graph:
            return
        try:
            self.graph.query("MATCH (n) DETACH DELETE n")
            print("Database cleared.")
        except Exception as exc: # pylint: disable=broad-except
            print(f"Error clearing database: {exc}")

# Global instance
db_manager = FalkordbManager()
