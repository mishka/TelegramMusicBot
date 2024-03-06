from TelegramAPI import TelegramAPI
from YouTube import YouTube

youtube = YouTube()
telegram = TelegramAPI('Your Token Here')

for message in telegram.poll_updates():
    if message.text:
        user = message.chat_id
        msg_id = message.message_id

        print(f'Processing message: {message.text}')
        telegram.send_message(chat_id = user, reply_to_message_id = msg_id, parse_mode = 'Markdown', text = '`Processing...`')
        url = youtube.extract_url(message.text)

        if not url:
            print('Invalid URL. Skipping..')
            telegram.edit_message(chat_id = user, message_id = int(msg_id) + 1, parse_mode = 'Markdown', text = '*Invalid ID.*')
            continue

        info = youtube.get_info(url)
        title = info['title']
        
        print(f'Found: {title}\nDownload started!')
        telegram.edit_message(chat_id = user, message_id = int(msg_id) + 1, parse_mode = 'Markdown', text = f'*Found:* `{title}`\n*Download started!*')

        audio = youtube.download(url)
        thumbnail = youtube.download(info['thumbnail'])
        
        print('Uploading...')
        telegram.edit_message(chat_id = user, message_id = int(msg_id) + 1, parse_mode = 'Markdown', text = '`Uploading...`')
        try:
            telegram.send_audio(
                chat_id = user,
                audio = audio,
                thumbnail = thumbnail,
                title = title,
                performer = info['artist'],
                duration = info['duration'],
                byte = True,
                reply_to_message_id = msg_id
            )
        except Exception as e:
            print(f'Error while uploading {e}')
            telegram.edit_message(chat_id = user, message_id = int(msg_id) + 1, parse_mode = 'Markdown', text = '_Something went wrong while uploading the audio file, maybe try again later?_')
        telegram.delete_message(chat_id = user, message_id = msg_id + 1)