# Sports Gala - Django WebSocket Application

A production-ready Django application for managing university department sports events with real-time dashboards, WebSocket updates, and role-based access control.

## Features

✨ **Core Features:**
- 🎯 Public real-time dashboard (no authentication required)
- 👥 Role-based access control (Admin, Score Manager)
- 🔄 Real-time updates via Django Channels + WebSockets
- 📊 Live leaderboards with auto-rotating slideshow
- 📢 Scheduled announcements panel
- 🏆 Dynamic award/results management
- 🎨 Sci-fi themed UI with neon styling

## Tech Stack

- **Framework**: Django 5.0+
- **ASGI Server**: Daphne (or Uvicorn)
- **WebSockets**: Django Channels 4.0
- **Database**: PostgreSQL (Supabase compatible)
- **Cache/Channels Layer**: Redis
- **Frontend**: TailwindCSS with custom sci-fi styling
- **Charts**: Chart.js for data visualization

## Project Structure

```
sports_gala/
├── config/                 # Django configuration
│   ├── settings/
│   │   ├── base.py         # Base settings
│   │   ├── development.py  # Dev settings (SQLite option)
│   │   └── production.py   # Production settings
│   ├── asgi.py            # ASGI configuration
│   ├── wsgi.py            # WSGI configuration
│   └── urls.py            # URL routing
├── core/                   # Main application
│   ├── models.py          # Database models
│   ├── views.py           # Views and API endpoints
│   ├── forms.py           # Django forms
│   ├── admin.py           # Django admin configuration
│   ├── consumers.py       # WebSocket consumers
│   ├── routing.py         # WebSocket routing
│   ├── signals.py         # Django signals for real-time updates
│   ├── tests.py           # Unit and integration tests
│   ├── templates/core/    # HTML templates
│   └── management/commands/
│       └── seed_data.py   # Sample data creation
├── static/                # CSS, JavaScript, images
├── assets/                # Department/Society logos
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Local development environment
├── requirements.txt       # Python dependencies
├── manage.py             # Django management script
└── README.md             # This file
```

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 13+ (or use Supabase)
- Redis 6+
- Docker & Docker Compose (optional)

### Local Development Setup

1. **Clone and setup:**
```bash
cd sports_gala
python -m venv venv

# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

2. **Environment Configuration:**
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```env
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://user:password@localhost:5432/sports_gala
REDIS_URL=redis://localhost:6379/0
```

3. **Database Setup:**
```bash
python manage.py migrate
python manage.py createsuperuser  # Create admin user
python manage.py seed_data        # Load sample data
```

4. **Run Local Development Server:**
```bash
# Using Daphne (recommended for WebSockets)
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Or using Uvicorn
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload
```

Visit: http://localhost:8000

### Docker Compose Setup

```bash
# Start services (PostgreSQL, Redis, Django)
docker-compose up

# Run migrations and seed data
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py seed_data

# Stop services
docker-compose down
```

Visit: http://localhost:8000

## Testing

```bash
# Run all tests
python manage.py test

# Run specific test
python manage.py test core.tests.GameModelTest

# With coverage
coverage run --source='core' manage.py test
coverage report
```

## Data Models

### Core Entities

**Game**
- Represents a sport/event (Cricket, Badminton, Football, etc.)
- Statuses: upcoming, ongoing, completed
- display_order for slideshow ordering

**Team**
- Belongs to one Game
- Has a required captain (enforced via validation)
- Can have multiple members

**TeamMember**
- Belongs to one Team
- Role: captain or member
- Captain required per team

**Match**
- Two teams competing in a game
- Scoring and match result tracking
- Optional winner_team (nullable for ongoing)

**ScoreManagerProfile**
- One-to-One with User
- Links users to games they can manage
- Many-to-Many with Games (assigned_games)

**GameAward**
- Dynamic award types per game
- Can be team-based or individual
- Examples: 1st Position, Best Catcher, etc.

**ScheduledMessage**
- Announcements visible on public dashboard
- Time-bounded (start_time, end_time)
- Real-time broadcast via WebSocket

**LeaderboardCache**
- Denormalized cache of team points
- Updated on match completion
- Prevents expensive aggregation queries
- Points system: Win=3, Loss=0

## API Endpoints

### Public Endpoints (No Auth Required)

- `GET /` - Public dashboard
- `GET /api/games/<id>/` - Game details with teams
- `GET /api/games/<id>/matches/` - Game matches
- `GET /api/games/<id>/leaderboard/` - Game leaderboard
- `GET /login/` - Login page
- `POST /login/` - Login form submission

### Authenticated Endpoints

**Admin Only:**
- `GET /manager/` - Admin panel
- `GET /admin/` - Django admin interface
- CRUD endpoints for games, teams, members, matches, awards, messages, score managers

**Score Manager Only:**
- `GET /score-manager/` - Score manager panel
- `POST /score-manager/game/<id>/match/<match_id>/update/` - Update match scores
- Cannot modify completed games or teams

## WebSocket Implementation

### Connection Points

1. **Public Dashboard**: `ws://localhost:8000/ws/dashboard/`
   - Broadcasts match updates, messages, awards
   - Groups: "dashboard", "game_<id>"

2. **Game Slideshow**: `ws://localhost:8000/ws/game/<game_id>/`
   - Real-time leaderboard and match updates for specific game

### Message Format

```javascript
// Match Update
{
    type: "match_update",
    match_id: 1,
    game_id: 1,
    score_a: 50,
    score_b: 45,
    status: "ongoing",
    winner_id: null
}

// Message Update
{
    type: "message_update",
    message_id: 1,
    title: "Update Title",
    message: "Update content"
}

// Award Update
{
    type: "award_update",
    award_id: 1,
    game_id: 1,
    label: "1st Position"
}
```

### Client Implementation

```javascript
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const socket = new WebSocket(`${protocol}//${window.location.host}/ws/dashboard/`);

socket.onopen = function(e) {
    console.log('Connected');
    socket.send(JSON.stringify({
        action: 'subscribe_game',
        game_id: 1
    }));
};

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
## Features
        updateLeaderboard(data);
    }
};
```

## Permissions Model

### Superuser (Admin)

- ✅ Full CRUD on all models
- ✅ Create/edit/delete games, teams, members
- ✅ Update match scores and results
- ✅ Manage awards and announcements
- ✅ Assign score managers to games
- ✅ Access Django admin panel

### Score Manager

- ✅ View assigned games
- ✅ Update scores for assigned games
- ✅ Mark matches as complete
- ✅ Set winners for completed matches
- ❌ Cannot create/delete games, teams, members
- ❌ Cannot modify games marked as "completed"
- ❌ Cannot create score managers

### Public Users

- ✅ View public dashboard
- ✅ See live leaderboards
- ✅ Read announcements
- ✅ View final results/awards
- ❌ No authentication required
- ❌ Cannot modify any data

## Production Deployment

### Option 1: Koyeb + Supabase + Redis

#### Prerequisites
- Koyeb account (https://koyeb.com)
- Supabase PostgreSQL database
- Redis service (Koyeb, Upstash, or managed Redis)

#### Step 1: Prepare for Deployment

Update `config/settings/production.py`:

```python
# Ensure all production settings are configured
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda x: [s.strip() for s in x.split(',')])
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='').split(',')
```

#### Step 2: Set Environment Variables on Koyeb

```bash
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<generate-secure-key>
ALLOWED_HOSTS=your-app.koyeb.app,yourdomain.com
CSRF_TRUSTED_ORIGINS=https://your-app.koyeb.app,https://yourdomain.com
DATABASE_URL=postgresql://user:password@db.host:5432/dbname
REDIS_URL=redis://user:password@redis.host:6379/0
```

#### Step 3: Create Koyeb Service

```yaml
# koyeb.yml
name: sports-gala
services:
  api:
    image:
      builder: dockerfile
    ports:
      - protocol: http
        port: 8000
    routes:
      - path: /
    env:
      - key: DJANGO_SETTINGS_MODULE
        value: config.settings.production
      - key: DJANGO_DEBUG
        value: "false"
      - key: DATABASE_URL
        scope: service
      - key: REDIS_URL
        scope: service
```

#### Step 4: Deployment

```bash
# Install Koyeb CLI
brew install koyeb/tap/koyeb  # macOS
# Or download from https://github.com/koyeb/koyeb-cli

# Login to Koyeb
koyeb auth login

# Deploy
koyeb service deploy <app-name> --git-repository https://github.com/username/sports-gala --git-branch main

# Or deploy from Docker image
docker build -t sports-gala .
docker tag sports-gala:latest registry.koyeb.io/username/sports-gala:latest
docker push registry.koyeb.io/username/sports-gala:latest
koyeb service deploy sports-gala --docker registry.koyeb.io/username/sports-gala:latest
```

#### Step 5: Run Migrations

```bash
koyeb service exec <app-name> -- python manage.py migrate
koyeb service exec <app-name> -- python manage.py seed_data
koyeb service exec <app-name> -- python manage.py collectstatic --noinput
```

### Option 2: Traditional Server (VPS, AWS EC2, DigitalOcean)

#### Installation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql redis-server nginx

# Clone repository
git clone https://github.com/username/sports-gala.git
cd sports-gala

# Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup database
sudo -u postgres createdb sports_gala
sudo -u postgres createuser sports_user
# Configure user password and permissions in PostgreSQL

# Setup Django
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

#### Systemd Service Files

**`/etc/systemd/system/sports-gala.service`**
```ini
[Unit]
Description=Sports Gala Django Application
After=network.target

[Service]
Type=notify
User=appuser
WorkingDirectory=/opt/sports-gala
ExecStart=/opt/sports-gala/venv/bin/daphne -b 0.0.0.0 -p 8000 config.asgi:application
EnvironmentFile=/opt/sports-gala/.env
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**`/etc/systemd/system/sports-gala-worker.service`** (for background tasks)
```ini
[Unit]
Description=Sports Gala Celery Worker
After=network.target

[Service]
Type=simple
User=appuser
WorkingDirectory=/opt/sports-gala
ExecStart=/opt/sports-gala/venv/bin/celery -A config worker --loglevel=info
EnvironmentFile=/opt/sports-gala/.env
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Nginx Configuration

**`/etc/nginx/sites-available/sports-gala`**
```nginx
upstream daphne {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    client_max_body_size 10M;

    location / {
        proxy_pass http://daphne;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /opt/sports-gala/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /opt/sports-gala/media/;
        expires 7d;
    }
}

# Redirect HTTP to HTTPS (after SSL setup)
# server {
#     listen 443 ssl http2;
#     server_name your-domain.com;
#     ssl_certificate /path/to/cert.pem;
#     ssl_certificate_key /path/to/key.pem;
#     ...
# }
```

#### SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --standalone -d your-domain.com
# Update nginx config with SSL paths
```

#### Service Management

```bash
# Start services
sudo systemctl start sports-gala
sudo systemctl start sports-gala-worker
sudo systemctl start nginx

# Enable on boot
sudo systemctl enable sports-gala
sudo systemctl enable sports-gala-worker
sudo systemctl enable nginx

# View logs
sudo journalctl -u sports-gala -f
```

## Environment Variables

### Development

```env
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=dev-key-only
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://localhost/sports_gala (optional, uses SQLite)
REDIS_URL=redis://localhost:6379/0
```

### Production

```env
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<secure-random-string>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,wss://yourdomain.com
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://user:password@host:6379/0
LOG_LEVEL=INFO
```

## Logging

### Development
Console logging via StreamHandler

### Production
Both file and console logging:
- File: `logs/django.log`
- Console: CloudWatch / Docker logs

Configure log level via `LOG_LEVEL` env var (default: INFO)

## Monitoring and Maintenance

### Health Check Endpoint

```bash
curl http://localhost:8000/admin/login/
```

### Database Backups

```bash
# Postgres backup
pg_dump -U postgres sports_gala > backup.sql

# Restore
psql -U postgres sports_gala < backup.sql
```

### Clear Cache

```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

### Statistics

```bash
python manage.py shell
>>> from core.models import Game, Match
>>> Game.objects.count()
>>> Match.objects.filter(status='completed').count()
```

## Troubleshooting

### WebSocket Connection Issues

1. **Check Redis connection:**
```bash
redis-cli PING
```

2. **Verify ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS:**
```python
# settings/production.py
ALLOWED_HOSTS = ['yourdomain.com']
CSRF_TRUSTED_ORIGINS = ['https://yourdomain.com', 'wss://yourdomain.com']
```

3. **HTTPS Required:**
WebSockets need WSS (WebSocket Secure) on production. Ensure HTTPS is configured.

### Database Connection

```bash
# Test connection
psql postgresql://user:password@host:5432/dbname

# Check logs
docker logs postgres  # if using Docker
tail -f /var/log/postgresql/postgresql.log  # if using system postgres
```

### Static Files Not Loading

```bash
python manage.py collectstatic --clear --noinput
```

### Permissions Errors

```bash
# Django admin
python manage.py createsuperuser

# Grant score manager role
python manage.py shell
>>> from django.contrib.auth.models import User
>>> from core.models import ScoreManagerProfile
>>> user = User.objects.get(username='manager')
>>> ScoreManagerProfile.objects.create(user=user)
```

## Performance Optimization

1. **Database indexing:** Configured on high-query fields
2. **Leaderboard caching:** LeaderboardCache table prevents aggregation queries
3. **Static file compression:** WhiteNoise handles gzipped assets
4. **Redis caching:** Cache frequently accessed data
5. **Connection pooling:** Use psycopg connection pooling

## Security

✅ **Implemented:**
- CSRF protection via Django's middleware
- SQL injection prevention (ORM queries)
- XSS protection (template auto-escaping)
- Secure password hashing (Django default)
- Role-based access control
- HTTPS enforcement (production)
- Secure cookie settings (production)

⚠️ **Production Checklist:**
- [ ] Change SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Enable HTTPS/SSL
- [ ] Setup firewall rules
- [ ] Regularly update dependencies
- [ ] Monitor logs for suspicious activity
- [ ] Backup database regularly

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: https://github.com/username/sports-gala/issues
- Email: support@sportsgala.local

## Credits

**Managed by**: afzalhussainj

**Technologies**: Django, Channels, PostgreSQL, Redis, TailwindCSS

## Changelog

### v1.0.0 (Initial Release)
- ✨ Public dashboard with real-time leaderboards
- 🔐 Admin and Score Manager roles
- 🔄 WebSocket real-time updates
- 📊 Game management with matches and awards
- 🎨 Sci-fi themed UI
- 🚀 Production-ready with Docker support

---

**Last Updated**: January 2026
