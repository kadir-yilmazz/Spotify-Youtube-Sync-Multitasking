# sync_cli.py
import sys
import subprocess
import click
from datetime import datetime
from src.db.falkordb_manager import db_manager 
from src.youtube.youtube_manager import YouTubeManager 

# Windows freeze fix
if sys.platform == "win32":
    try:
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        sys.stdout.reconfigure(encoding='utf-8')
    except: pass

@click.command()
def main_menu():
    """Spotify Sync Tool - Main Menu"""
    while True:
        try:
            click.clear()
            click.echo("="*50)
            click.echo("🎵 SPOTIFY -> YOUTUBE SYNC")
            click.echo("="*50)
            click.echo("1. Scrape (Fetch from Spotify)")
            click.echo("2. Match (Sync with YouTube)")
            click.echo("3. Create (Create Playlist)")
            click.echo("4. Clean (Reset DB)")
            click.echo("0. Exit")
            click.echo("-" * 50)
            
            choice = click.prompt("Your Choice", type=str)

            if choice == '1':
                url = click.prompt("👉 Spotify Link", type=str)
                click.echo(f"\n🚀 Starting scraping process...")
                try:
                    # Run scraping as a separate process (Prevents freezing)
                    subprocess.run([sys.executable, "-m", "src.scraper.runner", url], check=True)
                    click.echo("\n✅ Scraping completed.")
                except subprocess.CalledProcessError:
                    click.echo("\n❌ Error during scraping.")
                click.pause(info="Press any key to continue...")

            elif choice == '2':
                run_match()
                click.pause(info="Press any key to continue...")

            elif choice == '3':
                run_create_playlist()
                if click.confirm('Do you want to delete temporary data?', default=True):
                    db_manager.clear_database()
                click.pause(info="Press any key to continue...")

            elif choice == '4':
                if click.confirm('All data will be deleted. Are you sure?'): db_manager.clear_database()
                click.pause()

            elif choice == '0':
                break
        except Exception as e:
            click.echo(f"Error: {e}")
            click.pause()

def run_match():
    click.echo("\n🔄 YouTube matching started...")
    pending_songs = db_manager.find_pending_songs()
    
    if not pending_songs:
        click.echo("ℹ️ No songs to match.")
        return

    youtube = YouTubeManager()
    success_count = 0
    not_found_list = []
    
    with click.progressbar(pending_songs, label='Processing') as bar:
        for song in bar:
            query = f"{song['title']} {song['artist']}"
            match = youtube.search_video(query)
            if match:
                db_manager.update_song_with_youtube_match(song['song_id'], match['video_id'], query)
                success_count += 1
            else:
                not_found_list.append(f"{song['title']} - {song['artist']}")

    click.echo(f"\n✨ Total {success_count} songs matched successfully.")
    if not_found_list:
        click.echo("\n⚠️ NOT FOUND:")
        for item in not_found_list: click.echo(f" ❌ {item}")

def run_create_playlist():
    video_ids = db_manager.get_all_matched_video_ids()
    if not video_ids:
        click.echo("❌ No videos to add.")
        return

    try:
        youtube = YouTubeManager()
        # Logic to create playlist would go here (not fully implemented in previous context, but keeping structure)
        # Assuming youtube_manager has create_playlist and add_video_to_playlist
        
        playlist_name = db_manager.get_playlist_name()
        click.echo(f"Creating playlist: {playlist_name}")
        
        playlist_id = youtube.create_playlist(playlist_name, "Created by Spotify-Youtube Sync")
        
        if playlist_id:
            click.echo(f"Playlist created with ID: {playlist_id}")
            with click.progressbar(video_ids, label='Adding videos') as bar:
                for vid in bar:
                    youtube.add_video_to_playlist(playlist_id, vid)
            click.echo("✅ Playlist creation completed.")
        else:
            click.echo("❌ Failed to create playlist.")

    except Exception as e:
        click.echo(f"Error: {e}")

if __name__ == "__main__":
    main_menu()
