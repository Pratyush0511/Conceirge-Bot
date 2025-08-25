# 🚀 Deploy to Render - Complete Guide

This guide walks you through deploying your AI Customer Service System to [Render](https://render.com) with zero configuration.

## 📋 Prerequisites

- [ ] Git repository (GitHub/GitLab/Bitbucket)
- [ ] Render account (free tier available)
- [ ] OpenAI API key
- [ ] Basic Git knowledge

## 🎯 Quick Deploy (5 minutes)

### 1. **Connect Repository**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Web Service"
3. Connect your Git repository
4. Render will auto-detect `render.yaml`

### 2. **Environment Variables**
Add these in Render dashboard:

```bash
# Critical Variables
OPENAI_API_KEY=your-openai-api-key-here
FLASK_ENV=production

# Optional Variables (with defaults)
SECRET_KEY=auto-generated-by-render
DATABASE_URL=auto-configured-by-render
REDIS_URL=auto-configured-by-render
CELERY_BROKER_URL=auto-configured-by-render
CELERY_RESULT_BACKEND=auto-configured-by-render
```

### 3. **Deploy**
Click "Deploy" - Render handles everything automatically!

## 🔧 Manual Configuration (Alternative)

If not using `render.yaml`, configure manually:

### **Web Service Settings**
- **Name**: `ai-customer-service`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT start:app`

### **Worker Service Settings**
- **Name**: `ai-customer-service-worker`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `celery -A celery_worker.celery worker --loglevel=info`

### **Database**
- **Type**: PostgreSQL
- **Plan**: Starter (free tier available)
- **Name**: `postgres`

### **Redis**
- **Type**: Redis
- **Plan**: Starter (free tier available)
- **Name**: `redis`

## 📁 Required Files Checklist

Ensure these files exist in your repository:

```
├── render.yaml          ✅ (created)
├── requirements.txt     ✅ (exists)
├── start.py            ✅ (exists)
├── celery_worker.py    ✅ (exists)
├── .env.example        ✅ (exists)
└── Dockerfile          ✅ (exists - optional for Render)
```

## 🔐 Security Setup

### **Environment Variables in Render**
1. Go to your service settings
2. Navigate to "Environment" tab
3. Add variables:
   - `OPENAI_API_KEY` (required)
   - `SECRET_KEY` (auto-generated recommended)
   - `FLASK_ENV=production`

### **Database Security**
- Render automatically manages database credentials
- Connection strings are injected automatically
- SSL/TLS enabled by default

## 🚀 Deployment Commands

### **Push to Deploy**
```bash
git add .
git commit -m "Deploy to Render"
git push origin main
```

### **Monitor Deployment**
- Check Render dashboard logs
- View real-time build progress
- Monitor service health

## 📊 Service URLs

After deployment, you'll get:
- **Web App**: `https://ai-customer-service.onrender.com`
- **API**: `https://ai-customer-service.onrender.com/api`
- **Health Check**: `https://ai-customer-service.onrender.com/health`

## 🔍 Troubleshooting

### **Build Fails**
- Check `requirements.txt` for conflicts
- Verify Python version compatibility
- Review build logs in Render dashboard

### **Service Won't Start**
- Ensure all environment variables are set
- Check database connection
- Verify Redis connectivity

### **Celery Worker Issues**
- Check worker service logs
- Ensure Redis is running
- Verify database connectivity

### **Database Connection**
- Render provides `DATABASE_URL` automatically
- No manual configuration needed
- SSL required (handled automatically)

## 📈 Scaling

### **Vertical Scaling**
- Upgrade service plan in dashboard
- Increase CPU/memory as needed
- Auto-scaling available

### **Horizontal Scaling**
- Add multiple web service instances
- Load balancing handled automatically
- Database connections scale automatically

## 🔄 Continuous Deployment

- **Auto-deploy**: Enabled by default on push to main
- **Manual deploy**: Use "Manual Deploy" button
- **Rollback**: Previous versions available in dashboard

## 🆓 Free Tier Limits

- **Web Service**: 512 MB RAM, 100 GB bandwidth
- **Worker**: 512 MB RAM
- **Database**: 1 GB storage, 100 connections
- **Redis**: 25 MB storage

## 📞 Support

- **Render Docs**: [docs.render.com](https://docs.render.com)
- **Community**: [community.render.com](https://community.render.com)
- **Status**: [status.render.com](https://status.render.com)

## ✅ Deployment Success Checklist

- [ ] Web service responds to `/health`
- [ ] Database migrations complete
- [ ] Celery worker starts successfully
- [ ] Redis connection established
- [ ] OpenAI API calls working
- [ ] Frontend loads correctly

**Your app is now live on Render!** 🎉