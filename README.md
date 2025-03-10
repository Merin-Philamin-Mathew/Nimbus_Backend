# Nimbus Weather Tracking - Backend

Django-based backend for the Nimbus Weather Tracking application, providing weather data management and authentication services.

## 🚀 Features

- Weather data API integration
- Google OAuth authentication
- Role-based access control
- Weather analytics API endpoints
- Location-based data fetching

## 💻 Tech Stack

- Django
- Django REST Framework
- PostgreSQL
- Gunicorn
- Nginx

## 🛠️ AWS Deployment Setup

1. **System Updates and Python Installation**
```bash
sudo apt update
sudo apt install python3-pip python3-dev
```

2. **Create Virtual Environment**
```bash
sudo apt install python3-virtualenv
git clone <your-backend-repo>
cd nimbus-backend
virtualenv venv
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
pip install django gunicorn whitenoise
```

4. **Configure Django**
```python
# settings.py
ALLOWED_HOSTS = ['api.your-domain.com']
INSTALLED_APPS += ['whitenoise']
MIDDLEWARE += ['whitenoise.middleware.WhiteNoiseMiddleware']
```

5. **Database Setup**
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
```

6. **Configure Gunicorn**

Create `/etc/systemd/system/gunicorn.socket`:
```ini
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

Create `/etc/systemd/system/gunicorn.service`:
```ini
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/nimbus-backend
ExecStart=/home/ubuntu/nimbus-backend/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          project.wsgi:application

[Install]
WantedBy=multi-user.target
```

7. **Nginx Configuration**

Add to your nginx configuration:
```nginx
server {
    listen 80;
    server_name api.your-domain.com;

    location /staticfiles/ {
        alias /home/ubuntu/nimbus-backend/static;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header X-Forwarded-Protocol ssl;
    }

    client_max_body_size 10M;
}
```

8. **Start Services**
```bash
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
sudo systemctl restart nginx
```

## ⚙️ Environment Variables

Create `.env` file:
```env
DEBUG=False
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=api.your-domain.com
WEATHER_API_KEY=your_weather_api_key
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
```

## 🔍 Monitoring

Check service status:
```bash
sudo systemctl status nginx
sudo systemctl status gunicorn
```

View logs:
```bash
sudo tail -f /var/log/nginx/error.log
```

