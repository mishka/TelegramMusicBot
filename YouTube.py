from os import getcwd
from os.path import join

from io import BytesIO
from contextlib import redirect_stdout
from requests import get

import re, subprocess, yt_dlp


class YouTube:
    def __init__(self, update: bool = False):
        # try to install/update yt-dlp on each run
        if update:
            try:
                subprocess.check_call(['pip', 'install', '-U', 'yt-dlp'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print('yt-dlp updated successfully.')
            except subprocess.CalledProcessError as e:
                print(f'There was an error while updating yt-dlp: {e}')

        self.options = {
            'outtmpl': '-',
            'logtostderr': True,
            'quiet': True,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
            'ffmpeg_location': join(getcwd(), '')
        }

        self.ydl = yt_dlp.YoutubeDL(self.options)
        self.filter = re.compile(r'^.*(youtu\.be/|v/|u/\w/|embed/|watch\?v=|\&v=)([^#\&\?]*).*')


    def extract_url(self, url: str):
        match = self.filter.match(url)
        vid_id = match.group(2) if match else False
        return f'https://youtube.com/watch?v={vid_id}' if vid_id and len(vid_id) == 11 else False


    def download(self, url: str):
        if 'maxresdefault' in url:
            with BytesIO() as buffer:
                r = get(url)
                if r.status_code == 200:
                    buffer.write(r.content)
                    return buffer.getvalue()
                else:
                    print(f'Failed to download thumbnail: {r.status_code}')
                    return None
        else:
            with BytesIO() as buffer:
                with redirect_stdout(buffer), self.ydl as ugh:
                    ugh.download([url])
                    return buffer.getvalue()
                
                
    def get_size(self, info):
        # find the highest opus (audio only) entry and get the filesize
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
        if info.get('is_live') is not None:
            return True if info.get('is_live') else False
        

    def get_info(self, url: str):
        info = self.ydl.extract_info(url, download = False)
        # try to get the metadata song title / artist name
        # if they are not available, use the video title / channel name
        parsed_info = {
            'title': info.get('track', info.get('title', None)),
            'artist': info.get('artist', None),
            'thumbnail': info.get('thumbnail', None),
            'duration': info.get('duration', None),
            'filesize': self.get_size(info),
            'is_live': self.is_livestream(info)
        }
        
        return parsed_info