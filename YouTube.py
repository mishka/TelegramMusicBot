from os import getcwd
from os.path import join, isfile
from shutil import which
from platform import system

from io import BytesIO
from requests import get

import re, subprocess, yt_dlp


class YouTube:
    def __init__(self, update: bool = True):
        # try to install/update yt-dlp on each run
        if update:
            try:
                subprocess.check_call(['pip', 'install', '-U', 'yt-dlp'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print('yt-dlp updated successfully.')
            except subprocess.CalledProcessError as e:
                print(f'There was an error while updating yt-dlp: {e}')

        self.options = {
            'logtostderr': True,
            'quiet': True,
            'no-part': True,
            'format': 'bestaudio/best'
        }
        
        # Check if the platform is Windows
        if system() == 'Windows':
            ffmpeg_executable = join(getcwd(), '')
            if isfile(ffmpeg_executable):
                self.ffmpeg_location = join(getcwd(), '')
            elif which('ffmpeg') is None:
                raise SystemExit('FFmpeg is required but not found. Exiting.')
            else:
                self.ffmpeg_location = 'ffmpeg'
        else:
            # For macOS and Linux, check if ffmpeg is available globally
            if which('ffmpeg') is None:
                raise SystemExit('FFmpeg is required but not found. Exiting.')
            self.ffmpeg_location = 'ffmpeg'

        # Create YoutubeDL instance for info extraction
        self.ydl = yt_dlp.YoutubeDL(self.options)
        self.filter = re.compile(r'^.*(youtu\.be/|v/|u/\w/|embed/|watch\?v=|\&v=)([^#\&\?]*).*')


    def extract_url(self, url: str):
        try:
            match = self.filter.match(url)
            vid_id = match.group(2) if match else None
            if vid_id and len(vid_id) == 11:
                return f'https://youtube.com/watch?v={vid_id}'
            return False
        except Exception as e:
            print(f'Error extracting URL: {e}')
            return False


    def download(self, url: str):
        try:
            if any(x in url.lower() for x in ['ytimg.com', '.jpg', '.jpeg', '.png', '.webp', 'maxresdefault', 'hqdefault', 'sddefault']):
                print('Downloading thumbnail...')
                r = get(url)
                if r.status_code == 200:
                    print('Thumbnail downloaded.')
                    return r.content
                else:
                    print(f'Failed to download thumbnail: {r.status_code}')
                    return None
            else:
                print('Downloading and converting to MP3 in memory...')
                
                # Use yt-dlp to download best audio to stdout
                ytdlp_cmd = [
                    'yt-dlp',
                    '-f', 'bestaudio',
                    '-o', '-',  # Output to stdout
                    '--quiet',
                    '--no-warnings',
                    url
                ]
                
                # Pipe yt-dlp output directly to FFmpeg for MP3 conversion
                ffmpeg_cmd = [
                    self.ffmpeg_location,
                    '-i', 'pipe:0',  # Read from stdin
                    '-vn',  # No video
                    '-acodec', 'libmp3lame',  # MP3 codec
                    '-b:a', '192k',  # Bitrate
                    '-f', 'mp3',  # Format
                    'pipe:1'  # Write to stdout
                ]
                
                # Start both processes and pipe them together
                ytdlp_process = subprocess.Popen(
                    ytdlp_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                ffmpeg_process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdin=ytdlp_process.stdout,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Allow ytdlp_process to receive a SIGPIPE if ffmpeg_process exits
                ytdlp_process.stdout.close()
                
                # Get the MP3 data from FFmpeg's stdout
                mp3_data, ffmpeg_err = ffmpeg_process.communicate()
                
                # Wait for yt-dlp to finish and get its stderr
                ytdlp_process.wait()
                
                if ffmpeg_process.returncode == 0 and mp3_data:
                    print('Download and conversion complete.')
                    return mp3_data
                else:
                    print(f'Conversion failed. FFmpeg return code: {ffmpeg_process.returncode}')
                    print(f'yt-dlp return code: {ytdlp_process.returncode}')
                    if ffmpeg_err:
                        print(f'FFmpeg error: {ffmpeg_err.decode("utf-8", errors="ignore")[:500]}')
                    return None
                            
        except Exception as e:
            print(f'Download error: {e}')
            import traceback
            traceback.print_exc()
            return None
                    
                
    def get_size(self, info):
        # Find the highest opus (audio only) entry and get the filesize
        max_opus = None
        max_filesize = 0

        if 'formats' in info and info['formats']:
            for format_entry in info['formats']:
                if format_entry.get('acodec') == 'opus' and format_entry.get('filesize'):
                    filesize = format_entry['filesize']
                    if filesize > max_filesize:
                        max_filesize = filesize
                        max_opus = format_entry

        return (max_opus.get('filesize') / (1024 ** 2)) if max_opus else False


    def is_livestream(self, info):
        return bool(info.get('is_live'))
        

    def get_info(self, url: str):
        try:
            info = self.ydl.extract_info(url, download = False)
        except Exception as e: # In case if the video does not exist
            print(f'Failed to extract video info: {e}')
            return False
        # Try to get the metadata song title / artist name
        # If they are not available, use the video title / channel name
        parsed_info = {
            'title': info.get('track', info.get('title', None)),
            'artist': info.get('artist', None),
            'thumbnail': info.get('thumbnail', None),
            'duration': info.get('duration', None),
            'filesize': self.get_size(info),
            'is_live': self.is_livestream(info)
        }
        
        return parsed_info


