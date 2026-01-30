#!/bin/bash
# Update script for ReelFlow - Run this to deploy updates

set -e

echo "🔄 Updating ReelFlow..."

# Navigate to app directory
cd /var/www/reelflow

# Pull latest code
echo "📥 Pulling latest code from GitHub..."
git pull origin main

# Update Python dependencies
echo "🐍 Updating Python dependencies..."
source .venv/bin/activate
pip install --upgrade -r requirements.txt

# Update Node.js dependencies
echo "📦 Updating Node.js dependencies..."
npm install

# Build Next.js
echo "🏗️ Building Next.js..."
npm run build

# Restart services
echo "♻️ Restarting services..."
pm2 restart all

echo "✅ Update complete!"
echo "📊 Status:"
pm2 status
