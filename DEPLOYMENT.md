# Deployment Guide - Multi-Channel AI Customer Service System

## Quick Start

1. **Clone and Setup**
   ```bash
   cd wind
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start the System**
   ```bash
   python start.py
   ```

## Manual Setup

### Prerequisites

- Python 3.8+
- Redis Server
- Google Gemini API Key
- Twilio Account (for voice features)

### Step-by-Step Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   Create `.env` file with:
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   REDIS_URL=redis://localhost:6379/0
   MONGODB_URI=mongodb+srv://username:password@cluster0.mongodb.net/hotel_service?retryWrites=true&w=majority
   SECRET_KEY=your_secret_key
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   ```

3. **Start Redis Server**
   ```bash
   redis-server
   ```

4. **MongoDB Setup**
   ```bash
   # For local development, ensure MongoDB is running
   # For production, set up MongoDB Atlas account and create a cluster
   # Update MONGODB_URI in .env with your connection string
   ```

5. **Start Services**
   
   **Terminal 1 - Celery Worker:**
   ```bash
   celery -A celery_worker.celery worker --loglevel=info
   ```
   
   **Terminal 2 - Flask Application:**
   ```bash
   python run.py
   ```

## Production Deployment

### Using Docker

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   
   EXPOSE 5000
   CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "run:app"]
   ```

2. **Docker Compose**
   ```yaml
   version: '3.8'
   services:
     web:
       build: .
       ports:
         - "5000:5000"
       environment:
         - REDIS_URL=redis://redis:6379/0
         - DATABASE_URL=postgresql://user:pass@db:5432/hotel_service
       depends_on:
         - redis
         - db
     
     redis:
       image: redis:alpine
     
     db:
       image: postgres:13
       environment:
         POSTGRES_DB: hotel_service
         POSTGRES_USER: user
         POSTGRES_PASSWORD: pass
     
     celery:
       build: .
       command: celery -A celery_worker.celery worker --loglevel=info
       depends_on:
         - redis
         - db
   ```

### Using Heroku

1. **Create Procfile**
   ```
   web: gunicorn --worker-class eventlet -w 1 run:app
   worker: celery -A celery_worker.celery worker --loglevel=info
   ```

2. **Deploy**
   ```bash
   heroku create your-hotel-ai-service
   heroku addons:create heroku-redis:hobby-dev
   heroku addons:create heroku-postgresql:hobby-dev
   heroku config:set GOOGLE_API_KEY=your_key
   git push heroku main
   ```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | Yes |
| `REDIS_URL` | Redis connection URL | Yes |
| `DATABASE_URL` | Database connection URL | Yes |
| `SECRET_KEY` | Flask secret key | Yes |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | For voice |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | For voice |
| `HOTEL_NAME` | Hotel name | Optional |
| `HOTEL_PHONE` | Hotel phone number | Optional |

### Database Configuration

**Development:** SQLite (default)
**Production:** PostgreSQL recommended

### Redis Configuration

Used for:
- Session management
- Celery message broker
- Real-time data caching

## Monitoring

### Health Checks

- **Application:** `GET /api/health`
- **Database:** Check connection in admin dashboard
- **Redis:** Monitor connection status
- **Celery:** Monitor worker status

### Logs

- Application logs: Check Flask logs
- Celery logs: Monitor worker output
- Error tracking: Implement Sentry for production

## Security

### Production Security Checklist

- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS
- [ ] Secure API keys in environment variables
- [ ] Implement rate limiting
- [ ] Use database connection pooling
- [ ] Enable CORS properly
- [ ] Implement input validation
- [ ] Use secure session cookies

### API Security

- Input sanitization for all user inputs
- SQL injection prevention via SQLAlchemy ORM
- XSS protection in templates
- CSRF protection for forms

## Scaling

### Horizontal Scaling

- Multiple Flask app instances behind load balancer
- Multiple Celery workers
- Redis cluster for high availability
- Database read replicas

### Performance Optimization

- Enable Redis caching for frequent queries
- Use CDN for static assets
- Implement database indexing
- Monitor and optimize slow queries
- Use connection pooling

## Troubleshooting

### Common Issues

1. **Redis Connection Error**
   - Ensure Redis server is running
   - Check REDIS_URL configuration

2. **Database Migration Issues**
   - Delete migrations folder and reinitialize
   - Check database permissions

3. **Gemini API Errors**
   - Verify API key is correct
   - Check API quota and billing

4. **Socket.IO Connection Issues**
   - Ensure eventlet is installed
   - Check firewall settings

### Debug Mode

Enable debug mode for development:
```bash
export FLASK_DEBUG=1
python run.py
```

## Backup and Recovery

### Database Backup

**SQLite:**
```bash
cp hotel_service.db hotel_service_backup.db
```

**PostgreSQL:**
```bash
pg_dump hotel_service > backup.sql
```

### Redis Backup

```bash
redis-cli BGSAVE
```

## Support

For issues and support:
1. Check logs for error messages
2. Verify all services are running
3. Test API endpoints individually
4. Check environment variable configuration
