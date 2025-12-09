import asyncio
import scrapy
from scrapy_playwright.page import PageMethod
from src.models.data_classes import SongInfo, PlaylistSource

class SpotifyPlaylistSpider(scrapy.Spider):
    name = 'spotify_spider'

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 1,
        'LOG_LEVEL': 'ERROR',
        'PLAYWRIGHT_ABORT_REQUEST': lambda req: req.resource_type in ["image", "font", "media"],
        'ITEM_PIPELINES': {
            'src.scraper.pipelines.FalkordbPipeline': 300,
        },
    }

    def start_requests(self):
        url = getattr(self, 'playlist_url', None)
        if url:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_context_kwargs': {
                        'viewport': {'width': 1280, 'height': 800},
                        'java_script_enabled': True,
                        'ignore_https_errors': True,
                    },
                    'playwright_page_methods': [
                        PageMethod(
                            "add_init_script",
                            script=(
                                "Object.defineProperty(navigator, 'webdriver', "
                                "{get: () => undefined})"
                            )
                        ),
                    ],
                }
            )

    async def parse(self, response):
        """Parses the Spotify playlist page."""
        page = response.meta.get("playwright_page")

        # Check URL: Album or Playlist?
        is_album = "/album/" in response.url

        playlist_title, default_artist = await self._extract_playlist_info(page)

        print(f"📘 PLAYLIST NAME: {playlist_title}")
        if is_album and default_artist != "Unknown":
            print(f"🎤 ALBUM ARTIST: {default_artist}")

        yield PlaylistSource(name=playlist_title)

        await self._scroll_page(page)

        songs_data = await self._extract_songs_js(page, default_artist, is_album)

        count = 0
        seen = set()

        for i, s in enumerate(songs_data, start=1):
            key = f"{s['title']}-{s['artist']}"
            if key not in seen:
                seen.add(key)
                count += 1
                print(f"🎵 Song Found: {s['title']} - {s['artist']}")
                yield SongInfo(title=s['title'], artist=s['artist'], album="", index=i)

        if count == 0:
            async for item in self._fallback_parse(page):
                yield item
                count += 1

        print(f"✅ TOTAL {count} SONGS SCRAPED.")
        try:
            # Try to close page, but don't force if stuck (2 second timeout)
            await asyncio.wait_for(page.close(), timeout=2.0)
        except (asyncio.TimeoutError, Exception): # pylint: disable=broad-exception-caught
            pass

    async def _extract_playlist_info(self, page):
        """Extracts playlist title and default artist."""
        playlist_title = "Spotify Playlist"
        default_artist = "Unknown"
        try:
            await page.wait_for_selector('h1', timeout=7000)
            title_el = await page.query_selector('h1')
            if title_el:
                playlist_title = (await title_el.inner_text()).strip()

            # Try to find artist
            default_artist = await self._find_artist(page)

        except Exception: # pylint: disable=broad-exception-caught
            pass
        return playlist_title, default_artist

    async def _find_artist(self, page):
        """Tries to find the artist using multiple methods."""
        # 1. Creator Link
        artist_el = await page.query_selector('a[data-testid="creator-link"]')
        if artist_el:
            return (await artist_el.inner_text()).strip()

        # 2. Header Artist Link
        header_artist = await page.query_selector(
            'div[data-testid="entity-header"] a[href*="/artist/"]'
        )
        if header_artist:
            return (await header_artist.inner_text()).strip()

        # 3. Meta Tag
        meta_desc = await page.query_selector('meta[property="og:description"]')
        if meta_desc:
            content = await meta_desc.get_attribute("content")
            if content:
                parts = content.split('·')
                if len(parts) > 0:
                    candidate = parts[0].strip()
                    if "Listen to" not in candidate and "Spotify" not in candidate:
                        return candidate

        # 4. Page Title
        page_title = await page.title()
        if " by " in page_title:
            try:
                return page_title.split(" by ")[1].split(" |")[0].strip()
            except IndexError:
                pass

        return "Unknown"

    async def _scroll_page(self, page):
        """Scrolls the page to load lazy content."""
        try:
            await page.evaluate("""async () => {
                for (let i = 0; i < 10; i++) {
                    window.scrollBy(0, document.body.scrollHeight);
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
            }""")
        except Exception: # pylint: disable=broad-exception-caught
            pass

    async def _extract_songs_js(self, page, default_artist, is_album):
        """Extracts songs using JavaScript execution."""
        return await page.evaluate("""({default_artist, is_album}) => {
            // 1. Scope Definition: Get songs only from the main list
            let container = document.querySelector('div[data-testid="playlist-tracklist"]');
            if (!container) container = document.querySelector('div[data-testid="album-tracklist"]');

            const root = container || document;

            let rows = Array.from(root.querySelectorAll(
                'div[role="row"], div[data-testid="tracklist-row"], div[data-testid="track-row"]'
            ));

            if (!container) {
                rows = rows.filter(row => {
                    let parent = row.parentElement;
                    while (parent && parent !== document.body) {
                        const testId = parent.getAttribute('data-testid') || "";
                        const label = parent.getAttribute('aria-label') || "";
                        // Filter out recommendations
                        if (testId.includes('recommend') || label.includes('Recommended') || label.includes('Önerilenler')) return false;
                        parent = parent.parentElement;
                    }
                    return true;
                });
            }

            return rows.map(row => {
                let title = "";
                const titleEl = row.querySelector('a[data-testid="internal-track-link"], div[dir="auto"], a[href*="/track/"]');

                if (titleEl) {
                    title = titleEl.innerText.trim();
                } else {
                    const rowLabel = row.getAttribute('aria-label');
                    if (rowLabel) {
                        if (rowLabel.includes(" by ")) {
                            title = rowLabel.split(" by ")[0].trim();
                        } else {
                            title = rowLabel;
                        }
                    }
                }

                if (!title || title === "Title" || title === "#") return null;

                let artist = "";

                const artistEls = Array.from(row.querySelectorAll('a[href*="/artist/"]'));
                if (artistEls.length > 0) {
                    artist = artistEls.map(el => el.innerText.trim()).join(", ");
                }

                if (!artist || artist === "") {
                    if (titleEl) {
                        const container = titleEl.parentElement;
                        if (container) {
                            const texts = Array.from(container.querySelectorAll('span[data-encore-id="text"], div'))
                                .map(el => el.innerText.trim())
                                .filter(t => t !== title && t !== "" && t !== "E" && t !== "•");

                            if (texts.length > 0) {
                                artist = texts[0];
                            }
                        }
                    }
                }

                if ((!artist || artist === "") && row.getAttribute('aria-label')) {
                    const rowLabel = row.getAttribute('aria-label');
                    if (rowLabel.includes(" by ")) {
                        const parts = rowLabel.split(" by ");
                        if (parts.length > 1) artist = parts[parts.length - 1].trim();
                    }
                }

                if ((!artist || artist === "") && is_album && default_artist !== "Unknown") {
                    artist = default_artist;
                }

                if (!artist) artist = "Unknown";

                return { title, artist };
            }).filter(item => item !== null && item.title);

        }""", {'default_artist': default_artist, 'is_album': is_album})

    async def _fallback_parse(self, page):
        """Fallback parsing using meta tags."""
        try:
            meta_urls = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('meta[name="music:song"]'))
                    .map(m => m.content);
            }""")

            if meta_urls:
                oembed_results = await page.evaluate("""async (urls) => {
                    const promises = urls.map(u => 
                        fetch('https://open.spotify.com/oembed?url=' + encodeURIComponent(u))
                            .then(r => r.json())
                            .catch(() => null)
                    );
                    return await Promise.all(promises);
                }""", meta_urls)

                for i, data in enumerate(oembed_results, start=1):
                    if data and 'title' in data:
                        t = data.get('title', 'Unknown')
                        a = data.get('author_name', 'Unknown')
                        print(f"🎵 Song Found: {t} - {a}")
                        yield SongInfo(title=t, artist=a, album="", index=i)
        except Exception: # pylint: disable=broad-exception-caught
            pass
