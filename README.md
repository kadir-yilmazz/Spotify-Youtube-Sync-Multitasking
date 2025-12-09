# Spotify to YouTube Sync

A high-performance CLI tool to synchronize Spotify playlists to YouTube.

This application automates the process of migrating music libraries by scraping Spotify data, resolving metadata via a graph database, and creating synchronized playlists on YouTube.

## 🚀 Features

*   **Advanced Scraping:** Uses **Scrapy** + **Playwright** to handle Spotify's dynamic, JavaScript-heavy frontend.
*   **Graph Database:** Stores song relationships (Artist-Song) using **FalkorDB** for efficient data modeling.
*   **Smart Matching:** Resolves Spotify tracks to YouTube videos using the YouTube Data API.
*   **Type-Safe:** Built with modern Python practices, including **Dataclasses**, **Abstract Base Classes**, and full type hinting.
*   **Robust CLI:** Interactive command-line interface for easy operation.

## 🛠️ Architecture

The project follows a modular, object-oriented architecture:

*   **`src/scraper`**: Handles data extraction. Uses a custom Scrapy spider with Playwright integration to render the DOM and extract metadata (Song Title, Artist, Album).
*   **`src/db`**: Manages data persistence. Uses a Singleton pattern to interface with FalkorDB, storing data as a graph (`(:Song)-[:PERFORMED_BY]->(:Artist)`).
*   **`src/youtube`**: Handles external API integration. Implements a strict `VideoSearcher` interface to decouple business logic from the API implementation.
*   **`src/models`**: Defines immutable data structures (`SongInfo`, `PlaylistSource`) to ensure data integrity across the pipeline.

## 📦 Installation

### Prerequisites
*   Python 3.8+
*   Docker (for FalkorDB)
*   Google Cloud Project (YouTube Data API v3 enabled)

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/kadir-yilmazz/Spotify-Youtube-Sync-Multitasking.git
    cd Spotify-Youtube-Sync-Multitasking
    ```

2.  **Create Virtual Environment:**

    **Windows:**
    ```bash
    py -m venv .venv
    .\.venv\Scripts\Activate
    ```

    **Linux/Mac:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    playwright install
    ```

4.  **Start Database:**
    ```bash
    # Run in background (-d)
    docker run -d -p 6379:6379 --rm --name falkordb falkordb/falkordb
    ```
    > **Note:** If you encounter `Bind for 0.0.0.0:6379 failed: port is already allocated`, the database is likely already running. You can skip this step or restart it:
    ```bash
    docker stop falkordb
    docker rm falkordb
    # Then run the start command again
    ```

5.  **Configuration:**
    *   Copy `.env.example` to `.env`.
    *   **Google API Setup:**
        1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
        2.  Create a new project and enable the **YouTube Data API v3**.
        3.  Configure the **OAuth Consent Screen** (External -> Add Test Users if needed).
        4.  Go to **Credentials** -> **Create Credentials** -> **OAuth Client ID** (Desktop App).
        5.  Download the JSON file, rename it to `client_secrets.json`, and place it in the project root.

## 💻 Usage

Start the CLI application:

If you activated the project's virtual environment (recommended):

```bash
# With venv active (safest)
python ./sync_cli.py
```

If you don't use a virtual environment or `python` points to an older Python on your system, run explicitly with `py` (Windows) or `python3` (Linux/Mac):

```bash
# Windows
py -u ./sync_cli.py

# Linux/Mac
python3 -u ./sync_cli.py
```

If you get errors like `ModuleNotFoundError: No module named 'src'`, make sure you run the command from the project root (where `src/` exists). As a workaround you can set PYTHONPATH so Python can find the `src` package:

```bash
PYTHONPATH=. python3 -u ./sync_cli.py
```

### Workflow
1.  Select **Scrape** and paste a Spotify playlist URL.
2.  Select **Match** to find corresponding YouTube videos.
3.  Select **Create** to generate the playlist on your YouTube account.

## 🧪 Development

**Run Unit Tests:**
```bash
pytest tests/
```

**Check Code Quality:**
```bash
pylint src
```

## ⚠️ Limitations
*   **Spotify UI Updates:** The scraper relies on specific DOM structures. Significant UI changes by Spotify may require updating the selectors in `spotify_spider.py`.
*   **API Quotas:** Large playlists may hit the daily YouTube Data API quota.

## 📄 License
MIT
