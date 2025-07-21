
import os
import time
import shutil
import dropbox
from apscheduler.schedulers.blocking import BlockingScheduler
from instagrapi import Client
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

# Load env vars
load_dotenv()

DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
DROPBOX_FOLDER = "/AutoUpload"
LOCAL_TEMP_FOLDER = "temp"
UPLOADED_FOLDER = "uploaded"

INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
FIXED_CAPTION = "🔥 Auto-posted! #reels #trending"

EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_PASS = os.getenv("EMAIL_PASS")  # Gmail app password

os.makedirs(LOCAL_TEMP_FOLDER, exist_ok=True)
os.makedirs(UPLOADED_FOLDER, exist_ok=True)

def send_email_notification(subject, body):
    if not EMAIL_TO or not EMAIL_FROM or not EMAIL_PASS:
        print("📭 Email not configured. Skipping email.")
        return
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_FROM, EMAIL_PASS)
            smtp.send_message(msg)
        print("📧 Notification sent.")
    except Exception as e:
        print("❌ Failed to send email:", e)

def upload_reel():
    dbx = dropbox.Dropbox(DROPBOX_TOKEN)
    entries = dbx.files_list_folder(DROPBOX_FOLDER).entries

    video_files = [e for e in entries if isinstance(e, dropbox.files.FileMetadata) and e.name.endswith(".mp4")]

    if not video_files:
        print("😴 No videos to upload.")
        send_email_notification("Instagram Bot", "Boss, I am waiting for your orders 😎")
        return

    file = video_files[0]
    local_path = os.path.join(LOCAL_TEMP_FOLDER, file.name)

    with open(local_path, "wb") as f:
        metadata, res = dbx.files_download(file.path_lower)
        f.write(res.content)

    print(f"📥 Downloaded: {file.name}")

    try:
        cl = Client()
        cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        cl.clip_upload(local_path, FIXED_CAPTION)
        print(f"✅ Uploaded to Instagram: {file.name}")

        dbx.files_move_v2(file.path_lower, f"/{UPLOADED_FOLDER}/{file.name}")
        os.remove(local_path)

    except Exception as e:
        print(f"❌ Upload failed: {e}")

# Scheduler
scheduler = BlockingScheduler()
scheduler.add_job(upload_reel, "interval", hours=10)

print("🤖 Running every 10 hours...")
upload_reel()  # Run once at start
scheduler.start()
