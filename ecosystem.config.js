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
      },
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: '/var/www/bigmotion-studio/logs/frontend-error.log',
      out_file: '/var/www/bigmotion-studio/logs/frontend-out.log',
      max_size: '50M',
      retain: 5,
      compress: true
    },
    {
      name: 'backend',
      script: '/var/www/bigmotion-studio/venv/bin/uvicorn',
      args: 'api:app --host 0.0.0.0 --port 8000 --workers 2 --timeout-keep-alive 120',
      cwd: '/var/www/bigmotion-studio',
      interpreter: 'none',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: '/var/www/bigmotion-studio/logs/backend-error.log',
      out_file: '/var/www/bigmotion-studio/logs/backend-out.log',
      max_size: '50M',
      retain: 5,
      compress: true
    },
    {
      name: 'scheduler',
      script: '/var/www/bigmotion-studio/venv/bin/python',
      args: 'scheduler.py --mode service',
      cwd: '/var/www/bigmotion-studio',
      interpreter: 'none',
      autorestart: true,
      max_restarts: 10,
      restart_delay: 60000,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: '/var/www/bigmotion-studio/logs/scheduler-error.log',
      out_file: '/var/www/bigmotion-studio/logs/scheduler-out.log',
      max_size: '50M',
      retain: 5,
      compress: true
    }
  ]
};
