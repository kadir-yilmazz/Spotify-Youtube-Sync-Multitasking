"""Unit tests for YouTube Manager (Mocked)."""

from unittest.mock import MagicMock, patch
import pytest
from src.youtube.youtube_manager import YouTubeManager

@pytest.fixture
def mock_youtube_build():
    """Mocks the googleapiclient.discovery.build function."""
    with patch('src.youtube.youtube_manager.build') as mock_build:
        yield mock_build

@pytest.fixture
def mock_creds():
    """Mocks the credentials."""
    with patch('src.youtube.youtube_manager.Credentials') as mock_creds_cls:
        mock_creds_cls.from_authorized_user_file.return_value = MagicMock(valid=True)
        yield mock_creds_cls

def test_search_video_success(mock_youtube_build, mock_creds): # pylint: disable=unused-argument
    """Test searching for a video successfully."""
    # Setup mock response
    mock_service = MagicMock()
    mock_youtube_build.return_value = mock_service
    
    mock_search = mock_service.search.return_value.list.return_value
    mock_search.execute.return_value = {
        "items": [
            {
                "id": {"videoId": "12345"},
                "snippet": {
                    "title": "Test Video",
                    "channelTitle": "Test Channel"
                }
            }
        ]
    }

    # Initialize manager (will use mocks)
    with patch('os.path.exists', return_value=True):
        manager = YouTubeManager()
        result = manager.search_video("Test Query")

    assert result is not None
    assert result["video_id"] == "12345"
    assert result["title"] == "Test Video"

def test_search_video_no_results(mock_youtube_build, mock_creds): # pylint: disable=unused-argument
    """Test searching for a video with no results."""
    mock_service = MagicMock()
    mock_youtube_build.return_value = mock_service
    
    mock_search = mock_service.search.return_value.list.return_value
    mock_search.execute.return_value = {"items": []}

    with patch('os.path.exists', return_value=True):
        manager = YouTubeManager()
        result = manager.search_video("Nonexistent Video")

    assert result is None
