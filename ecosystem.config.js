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
      args: 'scheduler.py --mode service',
      cwd: '/var/www/bigmotion-studio',
      interpreter: 'none',
      autorestart: true,
      max_restarts: 10,
      restart_delay: 60000
    }
  ]
};
