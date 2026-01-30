#!/bin/bash
# Digital Ocean Droplet Setup Script for ReelFlow SaaS
# Run this script on a fresh Ubuntu 22.04 droplet

set -e

echo "==================================="
echo "ReelFlow Droplet Setup"
echo "==================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential tools
echo "🔧 Installing essential tools..."
sudo apt install -y curl wget git build-essential software-properties-common

# Install Node.js 20
echo "📦 Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node --version
npm --version

# Install Python 3.11
echo "🐍 Installing Python 3.11..."
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
python3 --version

# Install pip for Python 3.11
echo "📦 Installing pip..."
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
python3.11 -m pip --version

# Install Nginx
echo "🌐 Installing Nginx..."
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Install PM2
echo "⚙️ Installing PM2 process manager..."
sudo npm install -g pm2
pm2 startup systemd -u $USER --hp $HOME
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp $HOME

# Install FFmpeg (for video processing)
echo "🎬 Installing FFmpeg..."
sudo apt install -y ffmpeg
ffmpeg -version

# Install ImageMagick (for image processing)
echo "🖼️ Installing ImageMagick..."
sudo apt install -y imagemagick
convert -version

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /var/www/reelflow
sudo chown -R $USER:$USER /var/www/reelflow

# Setup firewall
echo "🔥 Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Clone repository
echo "📥 Cloning repository..."
cd /var/www/reelflow
if [ ! -d ".git" ]; then
    git clone https://github.com/ihek130/BigMotionStudio.git .
else
    git pull origin main
fi

# Setup Python virtual environment
echo "🐍 Setting up Python virtual environment..."
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Create .env file
echo "📝 Creating .env file..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Database
MONGODB_URL=your_mongodb_connection_string

# JWT Secret
JWT_SECRET_KEY=your_super_secret_jwt_key_change_this

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# DeepInfra
DEEPINFRA_API_KEY=your_deepinfra_api_key

# ElevenLabs TTS
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Pexels
PEXELS_API_KEY=your_pexels_api_key

# YouTube OAuth
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret

# TikTok OAuth
TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret

# Instagram OAuth
INSTAGRAM_APP_ID=your_instagram_app_id
INSTAGRAM_APP_SECRET=your_instagram_app_secret

# Storage Directories
OUTPUT_DIR=output
TEMP_DIR=temp
LOGS_DIR=logs

# AI Models
OPENAI_MODEL=gpt-4o
IMAGE_MODEL=black-forest-labs/FLUX-1-schnell

# Next.js
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=production
EOF
    echo "⚠️  IMPORTANT: Edit /var/www/reelflow/.env with your actual API keys!"
fi

# Create required directories
echo "📁 Creating required directories..."
mkdir -p output temp logs

# Build Next.js frontend
echo "🏗️ Building Next.js frontend..."
npm run build

# Setup Nginx configuration
echo "🌐 Configuring Nginx..."
sudo bash -c 'cat > /etc/nginx/sites-available/reelflow << "EOF"
server {
    listen 80;
    server_name _;  # Replace with your domain or droplet IP

    client_max_body_size 500M;

    # Frontend (Next.js)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend (FastAPI)
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for video streaming
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
EOF'

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/reelflow /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# Setup PM2 ecosystem
echo "⚙️ Setting up PM2 processes..."
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'frontend',
      script: 'npm',
      args: 'start',
      cwd: '/var/www/reelflow',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      error_file: '/var/www/reelflow/logs/frontend-error.log',
      out_file: '/var/www/reelflow/logs/frontend-out.log',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M'
    },
    {
      name: 'backend',
      script: '/var/www/reelflow/.venv/bin/uvicorn',
      args: 'api:app --host 0.0.0.0 --port 8000',
      cwd: '/var/www/reelflow',
      interpreter: 'none',
      error_file: '/var/www/reelflow/logs/backend-error.log',
      out_file: '/var/www/reelflow/logs/backend-out.log',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    },
    {
      name: 'scheduler',
      script: '/var/www/reelflow/.venv/bin/python',
      args: 'scheduler.py',
      cwd: '/var/www/reelflow',
      interpreter: 'none',
      error_file: '/var/www/reelflow/logs/scheduler-error.log',
      out_file: '/var/www/reelflow/logs/scheduler-out.log',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    }
  ]
};
EOF

# Start PM2 processes
echo "🚀 Starting applications with PM2..."
pm2 delete all 2>/dev/null || true
pm2 start ecosystem.config.js
pm2 save

# Setup cron job for cleanup
echo "⏰ Setting up cleanup cron job..."
(crontab -l 2>/dev/null; echo "0 * * * * cd /var/www/reelflow && /var/www/reelflow/.venv/bin/python cleanup_old_files.py >> /var/www/reelflow/logs/cleanup.log 2>&1") | crontab -

echo ""
echo "==================================="
echo "✅ Setup Complete!"
echo "==================================="
echo ""
echo "📝 Next Steps:"
echo "1. Edit your API keys: nano /var/www/reelflow/.env"
echo "2. Restart services: pm2 restart all"
echo "3. Check status: pm2 status"
echo "4. View logs: pm2 logs"
echo "5. Access your app: http://$(curl -s ifconfig.me)"
echo ""
echo "📊 Useful Commands:"
echo "  pm2 status          - Check app status"
echo "  pm2 logs            - View all logs"
echo "  pm2 logs frontend   - View frontend logs"
echo "  pm2 logs backend    - View backend logs"
echo "  pm2 logs scheduler  - View scheduler logs"
echo "  pm2 restart all     - Restart all apps"
echo "  pm2 monit           - Monitor resources"
echo ""
echo "🔄 To deploy updates:"
echo "  cd /var/www/reelflow"
echo "  ./deploy/update.sh"
echo ""
