from queue import Queue
from threading import Thread, Event
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
            return f'*Downloading:* `{title}` - {artist}`'
        return f'*Downloading:* `{title}`'

class MusicBot:
    def __init__(self, update_ytdlp : bool, telegram_token : str):
        self.log('Starting the bot...')
        self.task_queue = Queue()
        self.stop_event = Event()

        try:
            self.youtube = YouTube(update_ytdlp)
            self.telegram = TelegramAPI(telegram_token)
        except Exception as e:
            self.log(f'Error setting up YouTube/Telegram: {e}')

        self.worker_thread = Thread(target = self.worker)
        self.worker_thread.start()

    def log(self, message : str):
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        print(f'[{timestamp}] - {message}')

    def run(self):
        while not self.stop_event.is_set():
            try:
                updates = self.telegram.poll_updates()
                for message in updates:
                    self.log(f'Adding to the queue --> {message.from_first_name} | @{message.from_username} | {message.from_id} | {str(message.text)}')
                    self.task_queue.put(message)
            except Exception as e:
                self.log(f'Error in main loop: {e}')

    def worker(self):
        while not self.stop_event.is_set():
            try:
                message = self.task_queue.get()
                self.process_message(message)
                self.task_queue.task_done()
            except Exception as e:
                self.log(f'Error in worker: {e}')

    def process_message(self, message):
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

        try:
            url = self.youtube.extract_url(message.text)
            if not url:
                self.log(Responses.invalid_url)
                self.handle_error(chat_id, own_response, Responses.invalid_url)
                return

            info = self.youtube.get_info(url)

            if info['is_live']:
                self.log(Responses.livestream)
                self.handle_error(chat_id, own_response, Responses.livestream)
                return

            if info['filesize'] and info['filesize'] > 50:
                self.log(Responses.large_file)
                self.handle_error(chat_id, own_response, Responses.large_file)
                return

            title = info['title']
            artist = info['artist']
            self.log(f'Downloading: {title} - {artist}')
            self.telegram.edit_message(
                chat_id = chat_id,
                message_id = own_response,
                parse_mode = 'Markdown',
                text = Responses.found(title, artist)
            )

            audio = self.youtube.download(url)
            thumbnail = self.youtube.download(info['thumbnail'])

            self.log('Uploading...')
            self.telegram.edit_message(
                chat_id = chat_id,
                message_id = own_response,
                parse_mode = 'Markdown',
                text = Responses.uploading
            )

            self.upload_audio(chat_id, msg_id, own_response, audio, thumbnail, info)
        except Exception as e:
            self.log(f'Error processing message: {e}')
            self.log(Responses.error)
            self.handle_error(chat_id, own_response, Responses.error)

    def handle_error(self, chat_id : int, message_id : int, error_text : str):
        self.telegram.edit_message(
            chat_id = chat_id,
            message_id = message_id,
            parse_mode = 'Markdown',
            text = error_text,
        )

    def upload_audio(self, chat_id : int, msg_id : int, own_response : int, audio, thumbnail, info):
        try:
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
        except Exception as e:
            self.log(f'Error uploading audio: {e}')
            self.log(Responses.upload_error)
            self.handle_error(chat_id, own_response, Responses.upload_error)

    def stop(self):
        self.stop_event.set()
        self.worker_thread.join()

        while not self.stop_event.is_set():
            try:
                message = self.task_queue.get(timeout=1)
                self.process_message(message)
                self.task_queue.task_done()
            except Exception as e:
                self.log(f'Error in worker: {e}')