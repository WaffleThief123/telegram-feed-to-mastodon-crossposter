import os
from dotenv import load_dotenv
from telegram.ext import Updater, MessageHandler, Filters
from mastodon import Mastodon
import ffmpeg

# Load environment variables
load_dotenv(dotenv_path='./data/.env')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
MASTODON_API_BASE_URL = os.getenv('MASTODON_API_BASE_URL')
MASTODON_ACCESS_TOKEN = os.getenv('MASTODON_ACCESS_TOKEN')

# Initialize Mastodon API
mastodon = Mastodon(
    access_token=MASTODON_ACCESS_TOKEN,
    api_base_url=MASTODON_API_BASE_URL
)

# Transcode video
def transcode_video(video_path):
    output_path = './data/transcoded_video.mp4'
    try:
        stream = ffmpeg.input(video_path)
        stream = ffmpeg.output(stream, output_path, vf='scale=-2:720', audio_bitrate='96k')
        ffmpeg.run(stream, overwrite_output=True)
        return output_path
    except ffmpeg.Error as e:
        print(e.stderr.decode())
        return None

# Telegram message handler
def telegram_message_handler(update, context):
    message = update.message
    if message.video:
        video_file = message.video.get_file()
        video_path = video_file.download('./data/original_video.mp4')
        transcoded_video_path = transcode_video(video_path)
        if transcoded_video_path:
            mastodon.media_post(media_file=transcoded_video_path, description='Posted from Telegram')
            os.remove(video_path)
            os.remove(transcoded_video_path)
        else:
            mastodon.status_post(status='Failed to transcode video', visibility='unlisted')
    else:
        mastodon.status_post(status=message.text, visibility='unlisted')

# Initialize Telegram bot
updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(MessageHandler(Filters.all, telegram_message_handler))
updater.start_polling()
updater.idle()
