# YouTube Video Uploader

A Flask web application that allows users to upload and schedule videos to YouTube using Google OAuth2 authentication.

## Features

- 🔐 Google OAuth2 authentication
- 📤 Direct video upload to YouTube
- ⏰ Schedule video uploads for later
- 🎨 Modern, responsive UI
- 📱 Mobile-friendly design
- 🔒 Secure credential handling

## Prerequisites

- Python 3.9+
- Google Cloud Platform account
- YouTube Data API v3 enabled
- OAuth2 credentials

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd youtube-video-uploader
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google OAuth2**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable YouTube Data API v3
   - Create OAuth2 credentials
   - Download the `client_secret.json` file
   - Place it in the project root directory

4. **Set environment variables**
   ```bash
   export SECRET_KEY="your-secret-key-here"
   export REDIRECT_URI="http://localhost:5000/callback"
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open http://localhost:5000 in your browser

## Deployment to Render

### Method 1: Using Render Dashboard

1. **Fork/Clone this repository** to your GitHub account

2. **Sign up/Login to Render**
   - Go to [render.com](https://render.com)
   - Sign up with your GitHub account

3. **Create a new Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository

4. **Configure the service**
   - **Name**: `youtube-video-uploader` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

5. **Add Environment Variables**
   - `SECRET_KEY`: Generate a secure random string
   - `REDIRECT_URI`: `https://your-app-name.onrender.com/callback`
   - `FLASK_ENV`: `production`

6. **Upload OAuth2 Credentials**
   - In the Render dashboard, go to your service
   - Navigate to "Environment" tab
   - Add a file environment variable:
     - **Key**: `CLIENT_SECRETS_FILE`
     - **Value**: Upload your `client_secret.json` file

7. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application

### Method 2: Using render.yaml (Infrastructure as Code)

1. **Ensure your repository has the required files**:
   - `app.py`
   - `requirements.txt`
   - `render.yaml`
   - `Procfile`
   - `templates/` directory
   - `client_secret.json`

2. **Set up environment variables in Render**:
   - `SECRET_KEY`: Your secret key
   - `REDIRECT_URI`: Your Render app URL + `/callback`
   - `CLIENT_SECRETS_FILE`: Upload your OAuth2 credentials

3. **Deploy using Blueprint**:
   - In Render dashboard, click "New +" → "Blueprint"
   - Connect your repository
   - Render will use the `render.yaml` configuration

## Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key for sessions | Yes | `your-secret-key-here` |
| `REDIRECT_URI` | OAuth2 redirect URI | Yes | `https://app.onrender.com/callback` |
| `CLIENT_SECRETS_FILE` | Google OAuth2 credentials file | Yes | Upload `client_secret.json` |
| `FLASK_ENV` | Flask environment | No | `production` |
| `PORT` | Port to run the application | No | `10000` (Render sets this) |

## Google OAuth2 Setup

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project

2. **Enable YouTube Data API v3**
   - Go to "APIs & Services" → "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"

3. **Create OAuth2 Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:5000/callback` (for local development)
     - `https://your-app-name.onrender.com/callback` (for production)
   - Download the JSON file and rename it to `client_secret.json`

## Security Considerations

- ✅ Use environment variables for sensitive data
- ✅ Generate a strong SECRET_KEY
- ✅ Use HTTPS in production
- ✅ Keep OAuth2 credentials secure
- ✅ Regularly update dependencies

## Troubleshooting

### Common Issues

1. **OAuth2 Error**: Ensure redirect URIs match exactly
2. **Upload Fails**: Check file size limits and format
3. **Session Issues**: Verify SECRET_KEY is set
4. **Build Fails**: Check requirements.txt and Python version

### Render-Specific Issues

1. **Build Timeout**: Optimize requirements.txt
2. **Memory Issues**: Consider upgrading plan
3. **Cold Starts**: Use Render's persistent disk if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review Render's documentation

