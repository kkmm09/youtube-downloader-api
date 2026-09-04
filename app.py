import os
import json
from flask import Flask, request, jsonify
import yt_dlp
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)

@app.route('/', methods=['POST'])
def download_video():
data = request.json
url = data.get('url')
if not url:
return jsonify({"status": "error", "message": "URL is required"}), 400

output_path = '/tmp/%(title)s.%(ext)s'
ydl_opts = {
'outtmpl': output_path,
'format': 'bestvideo[height<=1080]+bestaudio/best',
'merge_output_format': 'mp4',
}

try:
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
info = ydl.extract_info(url, download=True)
filename = ydl.prepare_filename(info).replace('.webm', '.mp4').replace('.mkv', '.mp4')

file_title = os.path.basename(filename)
folder_id = os.environ.get('DRIVE_FOLDER_ID')
key_json = json.loads(os.environ.get('GCP_SERVICE_ACCOUNT_KEY'))

creds = service_account.Credentials.from_service_account_info(
key_json, scopes=['https://googleapis.com']
)
drive_service = build('drive', 'v3', credentials=creds)

file_metadata = {'name': file_title, 'parents': [folder_id]}
media = MediaFileUpload(filename, mimetype='video/mp4', resumable=True, chunksize=10*1024*1024)
request_api = drive_service.files().create(body=file_metadata, media_body=media, fields='id')

response = None
while response is None:
status, response = request_api.next_chunk()

if os.path.exists(filename):
os.remove(filename)

return jsonify({"status": "success", "fileId": response.get('id')})
except Exception as e:
return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
app.run(host='0.0.0.0', port=10000)
