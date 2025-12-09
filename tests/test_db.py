"""Unit tests for FalkorDB Manager (Mocked)."""

from unittest.mock import MagicMock, patch
import pytest
from src.db.falkordb_manager import FalkordbManager

@pytest.fixture
def mock_falkordb():
    """Mocks the FalkorDB connection."""
    with patch('src.db.falkordb_manager.FalkorDB') as mock_db_cls:
        mock_instance = MagicMock()
        mock_db_cls.return_value = mock_instance
        mock_instance.select_graph.return_value = MagicMock()
        yield mock_instance

def test_singleton_pattern(mock_falkordb): # pylint: disable=unused-argument
    """Ensure FalkordbManager acts as a singleton."""
    # Reset instance for test
    FalkordbManager._instance = None
    
    manager1 = FalkordbManager()
    manager2 = FalkordbManager()
    
    assert manager1.graph is not None
    assert manager1.graph == manager2.graph

def test_sanitize_string():
    """Test the string sanitization helper."""
    manager = FalkordbManager()
    # pylint: disable=protected-access
    assert manager._sanitize("O'Reilly") == "O\\'Reilly"
    assert manager._sanitize("Normal String") == "Normal String"
    assert manager._sanitize("") == ""

def test_save_song_info(mock_falkordb): # pylint: disable=unused-argument
    """Test saving a song generates the correct query."""
    FalkordbManager._instance = None
    manager = FalkordbManager()
    manager._instance = MagicMock() # Force mock graph
    
    manager.save_song_info("Test Song", "Test Artist")
    
    # Verify query was called
    manager.graph.query.assert_called_once()
    args, _ = manager.graph.query.call_args
    query = args[0]
    
    assert "MERGE (s:Song {title: 'Test Song', artist: 'Test Artist'})" in query
    assert "MERGE (art:Artist {name: 'Test Artist'})" in query
