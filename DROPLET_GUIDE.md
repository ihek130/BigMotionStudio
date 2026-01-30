# Droplet Deployment Guide

## Your Droplet Info

- **IP Address:** 158.55.67.189
- **OS:** Ubuntu 22.04 (LTS) x64
- **Specs:** 2 GB RAM / 1 vCPU / 70 GB Disk
- **Region:** SFO2 (San Francisco)

## Step 1: Connect to Your Droplet

### On Windows (PowerShell):

```powershell
ssh root@158.55.67.189
```

When prompted:
- Type `yes` to accept fingerprint
- Enter the password from your email

### First Login:

You'll be asked to change your password:
1. Enter current password (from email)
2. Enter new password (twice)

## Step 2: Run Setup Script

Once connected to your droplet, run these commands:

```bash
# Download setup script
curl -o setup.sh https://raw.githubusercontent.com/ihek130/BigMotionStudio/main/deploy/droplet-setup.sh

# Make it executable
chmod +x setup.sh

# Run setup (takes 5-10 minutes)
./setup.sh
```

**OR manually paste the script:**

```bash
# Create and edit setup script
nano setup.sh

# Paste the entire contents of deploy/droplet-setup.sh
# Press Ctrl+X, then Y, then Enter to save

# Make executable and run
chmod +x setup.sh
./setup.sh
```

## Step 3: Configure Environment Variables

After setup completes:

```bash
# Edit .env file
nano /var/www/bigmotion-studio/.env

# Add your API keys (from your local .env file)
# Press Ctrl+X, then Y, then Enter to save
```

## Step 4: Start Services

```bash
cd /var/www/bigmotion-studio
pm2 start ecosystem.config.js
pm2 save
pm2 status
```

## Step 5: Test Your App

Open in browser:
- **Frontend:** http://158.55.67.189
- **Backend API:** http://158.55.67.189/api/docs

## Useful Commands

### Check service status:
```bash
pm2 status
```

### View logs:
```bash
pm2 logs          # All services
pm2 logs frontend # Frontend only
pm2 logs backend  # Backend only
pm2 logs scheduler # Scheduler only
```

### Restart services:
```bash
pm2 restart all
pm2 restart frontend
pm2 restart backend
```

### Update from GitHub:
```bash
cd /var/www/bigmotion-studio
git pull
npm install && npm run build
source venv/bin/activate
pip install -r requirements.txt
pm2 restart all
```

### Check Nginx:
```bash
systemctl status nginx
nginx -t  # Test config
systemctl restart nginx
```

## Setup Custom Domain (Optional)

### 1. Point DNS to droplet:
```
Type: A Record
Name: @
Value: 158.55.67.189
```

### 2. Update Nginx config:
```bash
nano /etc/nginx/sites-available/bigmotion-studio

# Change:
server_name _;
# To:
server_name yourdomain.com www.yourdomain.com;

# Save and restart
nginx -t && systemctl restart nginx
```

### 3. Setup SSL (HTTPS):
```bash
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Troubleshooting

### Frontend not loading:
```bash
pm2 logs frontend
cd /var/www/bigmotion-studio
npm run build
pm2 restart frontend
```

### Backend errors:
```bash
pm2 logs backend
# Check .env has all required keys
nano /var/www/bigmotion-studio/.env
pm2 restart backend
```

### Videos not generating:
```bash
pm2 logs scheduler
# Check MongoDB connection
# Check API keys in .env
```

### Port already in use:
```bash
pm2 delete all
pm2 start ecosystem.config.js
```

## Security Checklist

- [ ] Changed root password
- [ ] Setup firewall: `ufw allow 22,80,443/tcp && ufw enable`
- [ ] Created non-root user (optional but recommended)
- [ ] Setup SSL with certbot
- [ ] Configured MongoDB IP whitelist
- [ ] Backup .env file securely

## Monitoring

### Server resources:
```bash
htop           # CPU/RAM usage
df -h          # Disk space
du -sh temp/   # Temp folder size
du -sh output/ # Output folder size
```

### Cleanup logs:
```bash
tail -f logs/cleanup.log
```

## Cost: $18/month

That's it! Your SaaS is now live on the droplet.
