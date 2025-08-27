from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import json
import tempfile
from datetime import datetime, timedelta
import schedule
import threading
import time

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Google OAuth2 configuration
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']
CLIENT_SECRETS_FILE = 'client_secret.json'

# Global variables for scheduled uploads
scheduled_uploads = []

def create_flow():
    """Create OAuth2 flow"""
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=os.environ.get('REDIRECT_URI', 'http://localhost:5000/callback')
    )
    return flow

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/login')
def login():
    """Initiate Google OAuth2 login"""
    try:
        flow = create_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        session['state'] = state
        return redirect(authorization_url)
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/callback')
def callback():
    """Handle OAuth2 callback"""
    try:
        state = session['state']
        flow = create_flow()
        flow.fetch_token(authorization_response=request.url)
        
        if not state or state != request.args.get('state'):
            return jsonify({'error': 'Invalid state parameter'}), 400
        
        credentials = flow.credentials
        session['credentials'] = credentials_to_dict(credentials)
        
        return redirect(url_for('upload_page'))
    except Exception as e:
        return jsonify({'error': f'Callback failed: {str(e)}'}), 500

@app.route('/upload')
def upload_page():
    """Upload page - only accessible after authentication"""
    if 'credentials' not in session:
        return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/upload_video', methods=['POST'])
def upload_video():
    """Handle video upload"""
    if 'credentials' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        tags = request.form.get('tags', '').split(',')
        privacy_status = request.form.get('privacy_status', 'private')
        schedule_time = request.form.get('schedule_time')
        
        # Get uploaded file
        if 'video_file' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        video_file = request.files['video_file']
        if video_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, video_file.filename)
        video_file.save(temp_file_path)
        
        # Prepare video metadata
        video_metadata = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': [tag.strip() for tag in tags if tag.strip()],
                'categoryId': '22'  # People & Blogs category
            },
            'status': {
                'privacyStatus': privacy_status
            }
        }
        
        if schedule_time:
            # Schedule the upload
            schedule_datetime = datetime.fromisoformat(schedule_time.replace('T', ' '))
            scheduled_upload = {
                'video_metadata': video_metadata,
                'file_path': temp_file_path,
                'schedule_time': schedule_datetime,
                'credentials': session['credentials']
            }
            scheduled_uploads.append(scheduled_upload)
            
            return jsonify({
                'message': f'Video scheduled for upload at {schedule_time}',
                'scheduled': True
            })
        else:
            # Upload immediately
            credentials = Credentials(**session['credentials'])
            youtube = build('youtube', 'v3', credentials=credentials)
            
            media = MediaFileUpload(temp_file_path, chunksize=-1, resumable=True)
            
            request_body = youtube.videos().insert(
                part='snippet,status',
                body=video_metadata,
                media_body=media
            )
            
            response = request_body.execute()
            
            # Clean up temp file
            os.remove(temp_file_path)
            os.rmdir(temp_dir)
            
            return jsonify({
                'message': 'Video uploaded successfully!',
                'video_id': response['id'],
                'video_url': f'https://youtube.com/watch?v={response["id"]}'
            })
            
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/scheduled_uploads')
def get_scheduled_uploads():
    """Get list of scheduled uploads"""
    if 'credentials' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    uploads = []
    for upload in scheduled_uploads:
        uploads.append({
            'title': upload['video_metadata']['snippet']['title'],
            'schedule_time': upload['schedule_time'].isoformat(),
            'status': 'scheduled'
        })
    
    return jsonify({'scheduled_uploads': uploads})

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('index'))

def credentials_to_dict(credentials):
    """Convert credentials to dictionary for session storage"""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def upload_scheduled_video(upload_data):
    """Upload a scheduled video"""
    try:
        credentials = Credentials(**upload_data['credentials'])
        youtube = build('youtube', 'v3', credentials=credentials)
        
        media = MediaFileUpload(upload_data['file_path'], chunksize=-1, resumable=True)
        
        request_body = youtube.videos().insert(
            part='snippet,status',
            body=upload_data['video_metadata'],
            media_body=media
        )
        
        response = request_body.execute()
        print(f"Scheduled video uploaded: {response['id']}")
        
        # Clean up temp file
        os.remove(upload_data['file_path'])
        
    except Exception as e:
        print(f"Failed to upload scheduled video: {str(e)}")

def check_scheduled_uploads():
    """Check and process scheduled uploads"""
    current_time = datetime.now()
    uploads_to_remove = []
    
    for i, upload in enumerate(scheduled_uploads):
        if current_time >= upload['schedule_time']:
            upload_scheduled_video(upload)
            uploads_to_remove.append(i)
    
    # Remove processed uploads
    for i in reversed(uploads_to_remove):
        scheduled_uploads.pop(i)

def schedule_checker():
    """Background thread to check scheduled uploads"""
    while True:
        check_scheduled_uploads()
        time.sleep(60)  # Check every minute

if __name__ == '__main__':
    # Start background scheduler only in development
    if app.debug:
        scheduler_thread = threading.Thread(target=schedule_checker, daemon=True)
        scheduler_thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
