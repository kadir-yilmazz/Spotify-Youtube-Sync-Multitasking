"""Scrapy pipeline: saves scraped items to FalkorDB."""

from typing import Any

from src.db.falkordb_manager import db_manager
from src.models.data_classes import PlaylistSource, SongInfo


class FalkordbPipeline:  # pylint: disable=too-few-public-methods
    """Pipeline to process scraped items and save them to FalkorDB."""

    def process_item(self, item: Any, _spider) -> Any:
        """Processes the item coming from the spider and saves it to FalkorDB.

        The `_spider` parameter is provided by the Scrapy pipeline API but is unused here.
        """
        if isinstance(item, SongInfo):
            db_manager.save_song_info(title=item.title, artist=item.artist, index=item.index)

        elif isinstance(item, PlaylistSource):
            db_manager.save_playlist_name(item.name)

        return item
