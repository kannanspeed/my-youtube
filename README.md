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

## Deployment Options

### 🚀 Quick Deploy to Render (Recommended)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. **Fork this repository** to your GitHub account

2. **Set up Google OAuth2** (if not done already):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable YouTube Data API v3
   - Create OAuth2 credentials (Web application)
   - Add your Render URL to authorized redirect URIs: `https://your-app-name.onrender.com/callback`
   - Download the `client_secret.json` file

3. **Deploy to Render**:
   - Sign up/Login to [Render](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your forked GitHub repository
   - Configure the service:
     - **Name**: `youtube-video-uploader`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`

4. **Add Environment Variables** in Render dashboard:
   ```
   SECRET_KEY=your-secure-random-string-here
   FLASK_ENV=production
   REDIRECT_URI=https://your-app-name.onrender.com/callback
   ```

5. **Upload OAuth2 Credentials**:
   - In Render dashboard, go to your service → Environment tab
   - Upload your `client_secret.json` file

6. **Deploy**: Render will automatically build and deploy your application

### 🐳 Docker Deployment

You can also deploy using Docker:

```bash
# Build the image
docker build -t youtube-uploader .

# Run with environment variables
docker run -p 5000:5000 \
  -e SECRET_KEY="your-secret-key" \
  -e REDIRECT_URI="http://localhost:5000/callback" \
  -v $(pwd)/client_secret.json:/app/client_secret.json:ro \
  youtube-uploader
```

Or use docker-compose:
```bash
# Copy environment template
cp env.example .env
# Edit .env with your values
docker-compose up -d
```

### ☁️ Other Deployment Platforms

#### Heroku
1. Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Create a new Heroku app:
   ```bash
   heroku create your-app-name
   ```
3. Set environment variables:
   ```bash
   heroku config:set SECRET_KEY="your-secret-key"
   heroku config:set FLASK_ENV="production"
   heroku config:set REDIRECT_URI="https://your-app-name.herokuapp.com/callback"
   ```
4. Deploy:
   ```bash
   git push heroku main
   ```

#### Railway
1. Connect your GitHub repository to [Railway](https://railway.app)
2. Set environment variables in Railway dashboard
3. Deploy automatically on push to main branch

#### Vercel
1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel` in your project directory
3. Set environment variables in Vercel dashboard

### 🔧 Manual Server Deployment

For deployment on your own server:

1. **Clone and setup**:
   ```bash
   git clone https://github.com/yourusername/youtube-video-uploader.git
   cd youtube-video-uploader
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your values
   ```

3. **Run with gunicorn**:
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 2 app:app
   ```

4. **Set up reverse proxy** (nginx example):
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
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

## 🚀 Quick GitHub Deployment

### Step 1: Fork & Setup
```bash
# Fork this repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/usa-open-data.git
cd usa-open-data

# Commit any changes
git add .
git commit -m "Ready for deployment"
git push origin main
```

### Step 2: Choose Your Platform
- **Render**: Best for beginners (free tier available)
- **Heroku**: Popular platform (free tier discontinued)
- **Railway**: Modern platform with good free tier
- **Vercel**: Great for static sites with serverless functions
- **Docker**: For custom server deployment

### Step 3: Deploy
Follow the platform-specific instructions above. Most platforms will:
1. Connect to your GitHub repository
2. Detect the Python app automatically
3. Set environment variables
4. Deploy with automatic builds on push

## 🔧 Development & Testing

### Local Development
```bash
pip install -r requirements.txt
export SECRET_KEY="dev-secret-key"
export REDIRECT_URI="http://localhost:5000/callback"
python app.py
```

### Docker Development
```bash
cp env.example .env  # Edit with your values
docker-compose up -d
```

### Testing
The GitHub Actions workflow will automatically test your code on every push.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test locally
5. Push to your fork
6. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/usa-open-data/issues)
- 📖 **Documentation**: See deployment sections above
- 💡 **Feature Requests**: Open an issue with the "enhancement" label

---

**🎉 Ready to deploy?** Your YouTube Video Uploader is now ready for GitHub deployment! Choose your preferred platform and get started in minutes.

