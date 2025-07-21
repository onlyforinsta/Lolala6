
import os, time, shutil
import dropbox
from instagrapi import Client
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ENV VARIABLES
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
DROPBOX_REELS_FOLDER = "/reels_queue"
DROPBOX_UPLOADED_FOLDER = "/uploaded"
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Setup clients
dbx = dropbox.Dropbox(DROPBOX_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
cl = Client()
cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

# Temp folder
TEMP_FOLDER = "downloads"
os.makedirs(TEMP_FOLDER, exist_ok=True)

def list_reels():
    res = dbx.files_list_folder(DROPBOX_REELS_FOLDER)
    return res.entries

def download_from_dropbox(entry):
    local_path = os.path.join(TEMP_FOLDER, entry.name)
    with open(local_path, "wb") as f:
        _, res = dbx.files_download(entry.path_lower)
        f.write(res.content)
    return local_path

def move_to_uploaded(entry):
    src = entry.path_lower
    dst = f"{DROPBOX_UPLOADED_FOLDER}/{entry.name}"
    dbx.files_move_v2(src, dst, allow_shared_folder=True, autorename=True)

def generate_caption():
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content("Write a short, fun Instagram reel caption with 2 hashtags.")
        return response.text.strip()
    except Exception as e:
        print("Gemini error:", e)
        return "🔥 Auto-posted #reels #trending"

def main():
    files = list_reels()
    if not files:
        print("No video found in Dropbox.")
        return
    video = files[0]
    print("📥 Downloading:", video.name)
    local_file = download_from_dropbox(video)
    caption = generate_caption()
    print("📤 Uploading to Instagram...")
    try:
        cl.clip_upload(local_file, caption)
        print("✅ Uploaded successfully!")
        move_to_uploaded(video)
    except Exception as e:
        print("❌ Upload failed:", e)
    finally:
        os.remove(local_file)

if __name__ == "__main__":
    main()
