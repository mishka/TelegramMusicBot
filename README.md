## Features
- **Exceptional Speed**  
  - Uploads music files in approximately 3-5 seconds on average.  
  - I host it on a Raspberry Pi 4 with a LAN connection supporting up to 70Mbps download and 10Mbps upload speeds.
- **Memory-Only Operation**  
  - Downloads and processes data entirely in memory, without writing to disk.  
  - Ideal for Raspberry Pi or ARM-based boards.  
  - Prevents excessive wear on SD cards by avoiding unnecessary writes.  
  - Benefits from faster read/write speeds by using RAM.
- **Efficient Query Handling**  
  - Performs regex checks to ensure only valid YouTube links are processed.  
  - Includes robust error handling, ignoring livestreams and files larger than 50MB.

## Usage
You can use the bot by sending the youtube video URLs in the Telegram bot chat.

# Requirements
- **Don't forget to replace the `token` in `TelegramMusicBot.py` with your Telegram bot token.**
  - If you haven't created a bot on Telegram before, you can simply message [BotFather](https://t.me/botfather) and type `/newbot`.
  - Follow the steps to complete your bot configuration. Upon completion, you will receive a bot token.
- **FFmpeg**
  - Follow [this guide](https://www.hostinger.com/tutorials/how-to-install-ffmpeg) and install it on your system. Make sure to always download the latest stable version.
  - If you're using Windows, you can simply download the binary files and place them in the same folder as the script if you prefer not to add them to the environment.
- **yt-dlp**
  - My program will automatically download and update to the latest version on every launch.
- **[TelegramAPI](https://github.com/mishka/TelegramAPI)**
  - This is my own Telegram API for Python. Compared to all the bloatware libraries out there, it is simple, effective, and fast. :)
  - To use it, just download the files and place the `.py` files into the same folder as this script.
  - I don't have a pip installer for it yet, but I'll create one when I find some free time.

## Note on the `old` Folder
Please ignore the `old` folder. It contains the ancestor bot I initially created as a JavaScript practice project. Due to dependency rewrites and updates, the project eventually stopped working, and I didn't get around to fixing it.

I started from scratch and built a new version of the tool, inspired by this old project. Although it no longer functions, I've kept it in the repository for sentimental reasons. It served as a valuable learning experience and inspiration for the tool I've developed today, so I'll let it remain a testament to that journey.
