from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import json
import tempfile
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    print("Warning: schedule module not available. Scheduling features will be disabled.")
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
    # Auto-detect the correct redirect URI based on environment
    if os.environ.get('RENDER_EXTERNAL_URL'):
        # We're on Render
        base_url = os.environ.get('RENDER_EXTERNAL_URL')
        redirect_uri = f"{base_url}/callback"
        logger.info(f"Using Render redirect URI: {redirect_uri}")
    else:
        # Local development
        redirect_uri = os.environ.get('REDIRECT_URI', 'http://localhost:5000/callback')
        logger.info(f"Using local redirect URI: {redirect_uri}")
    
    logger.info(f"Creating OAuth2 flow with redirect URI: {redirect_uri}")
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    return flow

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'environment': {
            'render_external_url': os.environ.get('RENDER_EXTERNAL_URL'),
            'redirect_uri': os.environ.get('REDIRECT_URI'),
            'flask_env': os.environ.get('FLASK_ENV'),
            'schedule_available': SCHEDULE_AVAILABLE
        }
    })

@app.route('/')
def index():
    """Main page"""
    no_channel_error = session.pop('no_channel_error', False)
    return render_template('index.html', no_channel_error=no_channel_error)

@app.route('/login')
def login():
    """Initiate Google OAuth2 login"""
    try:
        logger.info("Starting OAuth2 login process")
        flow = create_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        session['state'] = state
        logger.info(f"Generated authorization URL: {authorization_url}")
        logger.info(f"Generated state: {state}")
        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/callback')
def callback():
    """Handle OAuth2 callback"""
    try:
        logger.info(f"OAuth2 callback received. URL: {request.url}")
        logger.info(f"Request args: {dict(request.args)}")
        
        state = session.get('state')
        logger.info(f"Session state: {state}")
        logger.info(f"Request state: {request.args.get('state')}")
        
        flow = create_flow()
        flow.fetch_token(authorization_response=request.url)
        
        if not state or state != request.args.get('state'):
            logger.error(f"State mismatch. Session: {state}, Request: {request.args.get('state')}")
            return jsonify({'error': 'Invalid state parameter'}), 400
        
        credentials = flow.credentials
        session['credentials'] = credentials_to_dict(credentials)
        logger.info("OAuth2 authentication successful")
        
        # Check if user has YouTube channels
        try:
            youtube = build('youtube', 'v3', credentials=credentials)
            channels_request = youtube.channels().list(part='snippet', mine=True)
            channels_response = channels_request.execute()
            
            if not channels_response.get('items'):
                logger.warning("No YouTube channels found for user")
                session['no_channel_error'] = True
                return redirect(url_for('index'))
            
            logger.info(f"Found {len(channels_response['items'])} YouTube channel(s)")
            
        except Exception as channel_error:
            logger.error(f"Failed to check YouTube channels: {str(channel_error)}")
            session['no_channel_error'] = True
            return redirect(url_for('index'))
        
        return redirect(url_for('publish_page'))
    except Exception as e:
        logger.error(f"Callback failed: {str(e)}")
        return jsonify({'error': f'Callback failed: {str(e)}'}), 500

@app.route('/publish')
def publish_page():
    """Main publish page - only accessible after authentication"""
    if 'credentials' not in session:
        return redirect(url_for('index'))
    return render_template('publish.html')

@app.route('/upload')
def upload_page():
    """Upload page - only accessible after authentication"""
    if 'credentials' not in session:
        return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/upload_video', methods=['POST'])
def upload_video():
    """Handle video upload"""
    logger.info("=== UPLOAD VIDEO REQUEST STARTED ===")
    
    if 'credentials' not in session:
        logger.error("Upload failed: User not authenticated")
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        tags = request.form.get('tags', '').split(',')
        privacy_status = request.form.get('privacy_status', 'private')
        schedule_time = request.form.get('schedule_time')
        
        logger.info(f"Form data received - Title: {title}, Privacy: {privacy_status}, Schedule: {schedule_time}")
        
        # Get uploaded file
        if 'video_file' not in request.files:
            logger.error("Upload failed: No video file in request")
            return jsonify({'error': 'No video file provided'}), 400
        
        video_file = request.files['video_file']
        if video_file.filename == '':
            logger.error("Upload failed: Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        logger.info(f"Video file received: {video_file.filename}, Size: {video_file.content_length} bytes")
        
        # Validate file size (128GB = 137438953472 bytes)
        if video_file.content_length and video_file.content_length > 137438953472:
            logger.error(f"Upload failed: File too large - {video_file.content_length} bytes")
            return jsonify({'error': f'File size ({video_file.content_length} bytes) exceeds 128GB limit'}), 400
        
        # Save file temporarily
        try:
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, video_file.filename)
            video_file.save(temp_file_path)
            logger.info(f"File saved temporarily: {temp_file_path}")
        except Exception as save_error:
            logger.error(f"Failed to save file: {str(save_error)}")
            return jsonify({'error': f'Failed to save file: {str(save_error)}'}), 500
        
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
        
        logger.info(f"Video metadata prepared: {video_metadata}")
        
        if schedule_time:
            logger.info(f"Scheduling video for: {schedule_time}")
            # Check if scheduling is available
            if not SCHEDULE_AVAILABLE:
                logger.error("Scheduling not available in this environment")
                return jsonify({'error': 'Scheduling is not available in this environment. Please upload immediately.'}), 400
            
            # Schedule the upload
            try:
                schedule_datetime = datetime.fromisoformat(schedule_time.replace('T', ' '))
                scheduled_upload = {
                    'video_metadata': video_metadata,
                    'file_path': temp_file_path,
                    'schedule_time': schedule_datetime,
                    'credentials': session['credentials']
                }
                scheduled_uploads.append(scheduled_upload)
                logger.info(f"Video scheduled successfully for {schedule_time}")
                
                return jsonify({
                    'message': f'Video scheduled for upload at {schedule_time}',
                    'scheduled': True
                })
            except Exception as schedule_error:
                logger.error(f"Failed to schedule video: {str(schedule_error)}")
                return jsonify({'error': f'Failed to schedule video: {str(schedule_error)}'}), 500
        else:
            logger.info("Starting immediate upload to YouTube")
            # Upload immediately
            try:
                credentials = Credentials(**session['credentials'])
                logger.info("Credentials loaded successfully")
                
                youtube = build('youtube', 'v3', credentials=credentials)
                logger.info("YouTube API client created")
                
                media = MediaFileUpload(temp_file_path, chunksize=-1, resumable=True)
                logger.info("Media file upload object created")
                
                logger.info("Executing YouTube upload request...")
                request_body = youtube.videos().insert(
                    part='snippet,status',
                    body=video_metadata,
                    media_body=media
                )
                
                response = request_body.execute()
                logger.info(f"YouTube upload successful! Video ID: {response['id']}")
                
                # Clean up temp file
                try:
                    os.remove(temp_file_path)
                    os.rmdir(temp_dir)
                    logger.info("Temporary files cleaned up")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp files: {str(cleanup_error)}")
                
                return jsonify({
                    'message': 'Video uploaded successfully!',
                    'video_id': response['id'],
                    'video_url': f'https://youtube.com/watch?v={response["id"]}'
                })
                
            except Exception as upload_error:
                logger.error(f"YouTube upload failed: {str(upload_error)}")
                logger.error(f"Error type: {type(upload_error).__name__}")
                
                # Clean up temp file on error
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    if os.path.exists(temp_dir):
                        os.rmdir(temp_dir)
                    logger.info("Temporary files cleaned up after error")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp files after error: {str(cleanup_error)}")
                
                return jsonify({'error': f'YouTube upload failed: {str(upload_error)}'}), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in upload_video: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {e}")
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
    # Start background scheduler only in development and if schedule is available
    if app.debug and SCHEDULE_AVAILABLE:
        scheduler_thread = threading.Thread(target=schedule_checker, daemon=True)
        scheduler_thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
