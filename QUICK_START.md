# QUICK START GUIDE

## Local Development (5 minutes)

### 1. Setup Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set:
```env
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=dev-secret-key-only
ALLOWED_HOSTS=localhost,127.0.0.1
# DATABASE_URL not needed - uses SQLite by default
REDIS_URL=redis://localhost:6379/0
```

### 4. Setup Database

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_data
```

### 5. Start Services

**Terminal 1 - Redis:**
```bash
redis-server
```

**Terminal 2 - Django:**
```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

Or use:
```bash
python manage.py runserver 0.0.0.0:8000
```

### 6. Access the App

- **Public Dashboard**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/manager/
- **Admin Login**: `admin` / `admin123`
- **Score Manager Login**: `scoremanager` / `manager123`
- **Django Admin**: http://localhost:8000/admin/

---

## Docker Compose (Recommended for Dev)

```bash
# Start all services (PostgreSQL, Redis, Django)
docker-compose up

# In another terminal, run migrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py seed_data

# Access app at http://localhost:8000
# Stop all services
docker-compose down
```

---

## Production Deployment to Koyeb

### Prerequisites
- Koyeb account (free tier available)
- Supabase PostgreSQL database
- Redis service (Upstash or managed)

### Step 1: Prepare Repository

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/username/sports-gala.git
git push -u origin main
```

### Step 2: Create Supabase Database

1. Go to https://supabase.com
2. Create new project (get `DATABASE_URL`)

### Step 3: Create Redis Instance

- Option 1: Upstash (https://upstash.com) - free tier
- Option 2: Koyeb managed Redis
- Get `REDIS_URL`

### Step 4: Deploy to Koyeb

1. Go to https://koyeb.com
2. Click "Create Application"
3. Connect GitHub repository
4. Configure build:
   - Builder: Dockerfile
   - Run command: `daphne -b 0.0.0.0 -p 8000 config.asgi:application`

5. Set Environment Variables:
```env
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<generate-secure-key-32-chars>
ALLOWED_HOSTS=<your-app>.koyeb.app,yourdomain.com
CSRF_TRUSTED_ORIGINS=https://<your-app>.koyeb.app,https://yourdomain.com,wss://<your-app>.koyeb.app,wss://yourdomain.com
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://user:pass@host:port
```

6. Click "Deploy"

### Step 5: Run Migrations

After deployment starts:

```bash
# Via Koyeb dashboard terminal
python manage.py migrate
python manage.py seed_data
python manage.py collectstatic --noinput
```

Or via SSH:
```bash
koyeb service exec sports-gala -- python manage.py migrate
koyeb service exec sports-gala -- python manage.py seed_data
```

### Step 6: Verify Deployment

- Visit: https://<your-app>.koyeb.app
- Login: admin / admin123
- Check WebSockets work by updating a score

---

## Testing

### Run Unit Tests

```bash
python manage.py test
```

### Test Specific Module

```bash
python manage.py test core.tests.GameModelTest
```

### Test with Coverage

```bash
pip install coverage
coverage run --source='core' manage.py test
coverage report
coverage html  # generates htmlcov/index.html
```

---

## Common Issues & Fixes

### Redis Connection Error

```bash
# Check if Redis is running
redis-cli PING

# If not running:
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# macOS: brew install redis
# Linux: sudo apt-get install redis-server
```

### Port 8000 Already in Use

```bash
# Use different port
daphne -b 0.0.0.0 -p 8001 config.asgi:application

# Or kill existing process
# Windows: netstat -ano | findstr :8000
# macOS/Linux: lsof -i :8000
```

### WebSocket Connection Failed

1. Check ALLOWED_HOSTS in settings
2. Ensure WebSocket URL uses correct protocol (ws:// for dev, wss:// for production)
3. Check CSRF_TRUSTED_ORIGINS includes WebSocket origin
4. Verify Redis is running

### Database Migrations Failed

```bash
# Reset database (dev only)
rm db.sqlite3
python manage.py migrate

# Or check migration status
python manage.py showmigrations
```

---

## Project Structure Reference

```
sports_gala/
├── config/              # Project configuration
│   ├── settings/
│   │   ├── base.py      # Base settings
│   │   ├── development.py
│   │   └── production.py
│   ├── asgi.py          # WebSocket routing
│   └── urls.py          # URL patterns
├── core/                # Main app
│   ├── models.py        # Database models
│   ├── views.py         # Views & API
│   ├── forms.py         # Django forms
│   ├── consumers.py     # WebSocket handlers
│   ├── admin.py         # Django admin
│   ├── templates/       # HTML templates
│   └── management/
│       └── commands/
│           └── seed_data.py  # Sample data
├── static/              # CSS, JS
├── templates/           # Base templates
├── Dockerfile           # Container config
├── docker-compose.yml   # Dev environment
├── requirements.txt     # Python dependencies
└── manage.py           # Django CLI
```

---

## Useful Commands

```bash
# Database
python manage.py migrate              # Run migrations
python manage.py makemigrations       # Create new migrations
python manage.py showmigrations       # List migrations

# Data
python manage.py seed_data            # Load sample data
python manage.py shell                # Django shell

# Static files
python manage.py collectstatic        # Collect static files

# Admin
python manage.py createsuperuser      # Create admin user
python manage.py changepassword user  # Change user password

# Testing
python manage.py test                 # Run all tests
python manage.py test core.tests      # Run specific app tests

# Server
python manage.py runserver            # Dev server (HTTP only)
daphne -b 0.0.0.0 -p 8000 config.asgi:application  # ASGI with WebSocket
```

---

## Support & Documentation

- **Full Documentation**: See [README.md](README.md)
- **API Documentation**: See [API_DOCS.md](docs/API_DOCS.md) (if created)
- **Contributing**: See [CONTRIBUTING.md](docs/CONTRIBUTING.md) (if created)

---

## Next Steps

1. ✅ Local development running? Test features
2. ✅ Tests passing? Push to GitHub
3. ✅ Ready for production? Deploy to Koyeb
4. ✅ Domain configured? Enable HTTPS
5. ✅ Monitoring setup? Setup logging

---

**Happy coding! 🚀**
