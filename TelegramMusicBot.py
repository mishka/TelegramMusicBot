from queue import Queue
from threading import Thread
from datetime import datetime
from TelegramAPI import TelegramAPI
from YouTube import YouTube

class Responses:
    processing = '`Processing...`'
    invalid_url = '*Invalid URL.*'
    large_file = '*Sorry, file size exceeds Telegram\'s limit.*'
    uploading = '`Uploading...`'
    livestream = '*Livestreams aren\'t supported.*'
    upload_error = '_Something went wrong while uploading the audio file, maybe try again later?_'
    error = '_An unexpected error occurred while processing your request._'

    @staticmethod
    def found(title, artist = None):
        if artist:
            return f'*Downloading:* `{title} - {artist}`'
        return f'*Downloading:* `{title}`'


class MusicBot:
    def __init__(self, update_ytdlp : bool, telegram_token : str):
        self.log('Starting the bot...')
        self.task_queue = Queue()
        self.running = True

        try:
            self.telegram = TelegramAPI(telegram_token)
            self.youtube = YouTube(update = update_ytdlp)
        except Exception as e:
            self.log(f'Error setting up YouTube/Telegram: {e}')

        # Single worker thread for sequential processing
        self.worker_thread = Thread(target = self.worker, daemon=True)
        self.worker_thread.start()

    def log(self, message):
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        print(f'[{timestamp}] - {str(message)}')

    def run(self):
        updates = self.telegram.poll_updates()
        for message in updates:
            self.log(f'Adding to the queue --> {message.from_first_name} | @{message.from_username} | {message.from_id} | {str(message.text)}')
            self.task_queue.put(message)

    def worker(self):
        """
        Single worker thread that processes messages one at a time.
        This ensures no concurrent Telegram API requests because Telegram API doesn't like that.
        """
        while self.running:
            try:
                # Wait for a message from the queue (blocking)
                message = self.task_queue.get(timeout=1)
                
                # Process the message completely before moving to the next one
                self.process_message(message)
                
                # Mark task as done
                self.task_queue.task_done()
            except:
                # Timeout or empty queue, continue loop
                continue

    def process_message(self, message):
        """
        Process a single message from start to finish.
        Includes: validation, downloading, converting, and uploading.
        All steps are sequential to avoid concurrent Telegram API calls.
        """
        chat_id = message.chat_id
        msg_id = message.message_id

        self.log(f'Processing --> {message.from_first_name} | @{message.from_username} | {message.from_id} | {str(message.text)}')

        if not message.text:
            self.log('This request wasn\'t a text message.')
            return

        bot_response = self.telegram.send_message(
            chat_id = chat_id,
            reply_to_message_id = msg_id,
            parse_mode = 'Markdown',
            text = Responses.processing
        )
        own_response = bot_response.message_id

        # Extract and validate URL
        url = self.youtube.extract_url(message.text)
        
        if not url:
            self.log(Responses.invalid_url)
            self.telegram.edit_message(
                chat_id = chat_id,
                message_id = own_response,
                parse_mode = 'Markdown',
                text = Responses.invalid_url
            )
            return

        # Get video info
        info = self.youtube.get_info(url)

        if info['is_live']:
            self.log(Responses.livestream)
            self.telegram.edit_message(
                chat_id = chat_id,
                message_id = own_response,
                parse_mode = 'Markdown',
                text = Responses.livestream
            )
            return

        if info['filesize'] and info['filesize'] > 50:
            self.log(Responses.large_file)
            self.telegram.edit_message(
                chat_id = chat_id,
                message_id = own_response,
                parse_mode = 'Markdown',
                text = Responses.large_file
            )
            return

        self.log(Responses.found(info["title"], info["artist"]))
        self.telegram.edit_message(
            chat_id = chat_id,
            message_id = own_response,
            parse_mode = 'Markdown',
            text = Responses.found(info['title'], info['artist'])
        )

        audio = self.youtube.download(url)
        
        if not audio:
            self.log('Download failed!')
            self.telegram.edit_message(
                chat_id = chat_id,
                message_id = own_response,
                parse_mode = 'Markdown',
                text = Responses.upload_error
            )
            return
        
        thumbnail = self.youtube.download(info['thumbnail'])

        self.log('Uploading...')
        self.telegram.edit_message(
            chat_id = chat_id,
            message_id = own_response,
            parse_mode = 'Markdown',
            text = Responses.uploading
        )

        self.telegram.send_audio(
            byte = True,
            audio = audio,
            title = info['title'],
            chat_id = chat_id,
            thumbnail = thumbnail,
            performer = info['artist'],
            duration = info['duration'],
            reply_to_message_id = msg_id
        )
        
        self.telegram.delete_message(chat_id = chat_id, message_id = own_response)
        
        self.log(f'Completed processing for {message.from_first_name}')


if __name__ == '__main__':
    musicbot = MusicBot(update_ytdlp = True, telegram_token = '')
    
    # Continuously poll for updates
    try:
        while True:
            musicbot.run()
    except KeyboardInterrupt:
        musicbot.log('Bot stopped by user.')
        musicbot.running = False