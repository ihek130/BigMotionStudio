#!/bin/bash
# Droplet Setup Script for BigMotion Studio SaaS
# Run this on your fresh Ubuntu 22.04 droplet

set -e  # Exit on error

echo "🚀 Starting BigMotion Studio Setup..."

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install essential tools
echo "🔧 Installing essential tools..."
apt install -y curl git nginx certbot python3-certbot-nginx build-essential

# Install Node.js 20
echo "📦 Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Install Python 3.11
echo "🐍 Installing Python 3.11..."
apt install -y python3.11 python3.11-venv python3-pip python3.11-dev

# Install PM2 (process manager)
echo "⚙️ Installing PM2..."
npm install -g pm2

# Install FFmpeg (for video processing)
echo "🎬 Installing FFmpeg..."
apt install -y ffmpeg imagemagick

# Setup frontend (repo already cloned)
cd /var/www/bigmotion-studio
echo "🎨 Setting up frontend..."
npm install
npm run build

# Setup backend
echo "🔧 Setting up backend..."
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
echo "📝 Creating .env file (you'll need to edit this)..."
cat > .env << 'EOF'
# MongoDB
MONGODB_URL=your-mongodb-connection-string

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o

# DeepInfra (Image Generation)
DEEPINFRA_API_KEY=your-deepinfra-api-key
IMAGE_MODEL=black-forest-labs/FLUX-1-schnell

# ElevenLabs (TTS)
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# Pexels (Stock Videos)
PEXELS_API_KEY=your-pexels-api-key

# YouTube OAuth
YOUTUBE_CLIENT_ID=your-youtube-client-id
YOUTUBE_CLIENT_SECRET=your-youtube-client-secret

# TikTok OAuth
TIKTOK_CLIENT_KEY=your-tiktok-client-key
TIKTOK_CLIENT_SECRET=your-tiktok-client-secret

# Instagram OAuth
INSTAGRAM_APP_ID=your-instagram-app-id
INSTAGRAM_APP_SECRET=your-instagram-app-secret

# Storage
OUTPUT_DIR=output
TEMP_DIR=temp
LOGS_DIR=logs
EOF

echo "⚠️  IMPORTANT: Edit /var/www/bigmotion-studio/.env with your API keys!"

# Configure Nginx
echo "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/bigmotion-studio << 'EOF'
server {
    listen 80;
    server_name _;

    # Frontend (Next.js)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend (FastAPI)
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for video uploads
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }

    # Increase max upload size for videos
    client_max_body_size 500M;
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/bigmotion-studio /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Create PM2 ecosystem file
echo "📋 Creating PM2 ecosystem..."
cat > /var/www/bigmotion-studio/ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'frontend',
      script: 'npm',
      args: 'start',
      cwd: '/var/www/bigmotion-studio',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      }
    },
    {
      name: 'backend',
      script: '/var/www/bigmotion-studio/venv/bin/uvicorn',
      args: 'api:app --host 0.0.0.0 --port 8000',
      cwd: '/var/www/bigmotion-studio',
      interpreter: 'none'
    },
    {
      name: 'scheduler',
      script: '/var/www/bigmotion-studio/venv/bin/python',
      args: 'scheduler.py',
      cwd: '/var/www/bigmotion-studio',
      interpreter: 'none'
    }
  ]
};
EOF

# Setup PM2 startup
echo "🔄 Setting up PM2 auto-restart..."
pm2 startup systemd -u root --hp /root
env PATH=$PATH:/usr/bin pm2 startup systemd -u root --hp /root

# Setup cleanup cron job
echo "⏰ Setting up hourly cleanup cron..."
(crontab -l 2>/dev/null; echo "0 * * * * cd /var/www/bigmotion-studio && /var/www/bigmotion-studio/venv/bin/python cleanup_old_files.py >> /var/www/bigmotion-studio/logs/cleanup.log 2>&1") | crontab -

# Create necessary directories
echo "📁 Creating storage directories..."
mkdir -p /var/www/bigmotion-studio/temp
mkdir -p /var/www/bigmotion-studio/output
mkdir -p /var/www/bigmotion-studio/logs

echo "✅ Setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 NEXT STEPS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Edit your environment variables:"
echo "   nano /var/www/bigmotion-studio/.env"
echo ""
echo "2. Start all services:"
echo "   cd /var/www/bigmotion-studio"
echo "   pm2 start ecosystem.config.js"
echo "   pm2 save"
echo ""
echo "3. Check status:"
echo "   pm2 status"
echo "   pm2 logs"
echo ""
echo "4. Your app will be available at:"
echo "   http://158.55.67.189"
echo ""
echo "5. Optional - Setup domain & SSL:"
echo "   Update server_name in /etc/nginx/sites-available/bigmotion-studio"
echo "   certbot --nginx -d yourdomain.com"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
