import os
import re
import logging
import requests
import instaloader
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
import yt_dlp as youtube_dl

# Load credentials from .env
load_dotenv()
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

def extract_links(text):
    return re.findall(r"https?://\S+", text)

def detect_platform(url):
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "instagram.com" in url:
        return "instagram"
    elif "facebook.com" in url:
        return "facebook"
    return "unknown"

def download_youtube(url):
    try:
        ydl_opts = {'quiet': True, 'format': 'best', 'noplaylist': True}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return [info['url']]
    except Exception as e:
        logging.error(f"[YouTube ERROR] {e}")
    return []

def download_instagram(url):
    try:
        loader = instaloader.Instaloader(download_videos=False, download_video_thumbnails=False)
        loader.login(IG_USERNAME, IG_PASSWORD)
        shortcode = re.search(r"/(p|reel|tv)/([\w-]+)/", url)
        if not shortcode:
            return []
        post = instaloader.Post.from_shortcode(loader.context, shortcode.group(2))
        return [post.video_url] if post.is_video else [post.url]
    except Exception as e:
        logging.error(f"[Instagram ERROR] {e}")
    return []

def download_facebook(url):
    try:
        ydl_opts = {'quiet': True, 'format': 'best', 'noplaylist': True}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return [info['url']]
    except Exception as e:
        logging.error(f"[Facebook yt_dlp ERROR] {e}")
    return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send a YouTube, Instagram, or Facebook link.")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    links = extract_links(text)
    for link in links:
        platform = detect_platform(link)
        await update.message.reply_text(f"🔍 Fetching media from {platform}...")
        media_urls = []

        if platform == "youtube":
            media_urls = download_youtube(link)
        elif platform == "instagram":
            media_urls = download_instagram(link)
        elif platform == "facebook":
            media_urls = download_facebook(link)

        if not media_urls:
            await update.message.reply_text(
                f"❌ Could not fetch media from {platform.title()}.\nTry manually: {link}"
            )
        else:
            for media in media_urls:
                try:
                    if media.endswith(".mp4") or "googlevideo.com" in media:
                        await update.message.reply_video(media)
                    else:
                        await update.message.reply_photo(media)
                except Exception as e:
                    logging.warning(f"[SEND FAIL] {e}")
                    await update.message.reply_text(f"⚠️ Failed to send media. Try manually:\n{media}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("✅ Bot is running...")
    app.run_polling()
