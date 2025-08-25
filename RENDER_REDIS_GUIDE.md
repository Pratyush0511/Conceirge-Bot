# Redis Configuration Guide for Render Deployment

## Overview

This guide addresses the Redis connection issue when deploying the AI Customer Service System on Render. The error `Redis is not running. Please start Redis server.` occurs because the application is not properly connecting to the Redis service provided by Render.

## Solution

### 1. Code Changes (Already Applied)

The following changes have been made to the codebase to fix the Redis connection issue:

1. **Updated `start.py`**:
   - Now properly checks for `REDIS_URL` environment variable
   - Falls back to localhost only for local development
   - Continues execution in production even if Redis check fails

2. **Updated `config.py`**:
   - Modified Celery configuration to prioritize the `REDIS_URL` environment variable:
   ```python
   # Celery Configuration
   CELERY_BROKER_URL = os.getenv('REDIS_URL') or os.getenv('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
   CELERY_RESULT_BACKEND = os.getenv('REDIS_URL') or os.getenv('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
   ```
   - Ensures consistent Redis configuration across the application

3. **Updated `app/__init__.py`**:
   - Modified Celery configuration in the Flask app factory to prioritize `REDIS_URL`:
   ```python
   app.config['CELERY_BROKER_URL'] = os.getenv('REDIS_URL') or os.getenv('CELERY_BROKER_URL', 'memory://')
   app.config['CELERY_RESULT_BACKEND'] = os.getenv('REDIS_URL') or os.getenv('CELERY_RESULT_BACKEND', 'cache+memory://')
   ```
   - Ensures consistent Redis configuration in the Flask application

### 2. Deployment Steps

Follow these steps to deploy your application on Render with proper Redis configuration:

1. **Push the updated code to your GitHub repository**

2. **Deploy using the Blueprint (render.yaml)**:
   - The `render.yaml` file already includes the Redis service configuration
   - Render will automatically create and link the Redis service

3. **Manual Deployment (if not using Blueprint)**:
   - Create a Redis service in Render
   - Create your web service and worker service
   - Link the Redis service to both web and worker services
   - Set the environment variables as specified below

### 3. Required Environment Variables

Ensure these environment variables are set in your Render dashboard:

```
REDIS_URL: [Automatically set by Render when linking Redis service]
CELERY_BROKER_URL: [Same as REDIS_URL]
CELERY_RESULT_BACKEND: [Same as REDIS_URL]
FLASK_ENV: production
SECRET_KEY: [Your secret key]
DATABASE_URL: [Your database connection string]
```

### 4. Verification

After deployment:

1. Check the logs in the Render dashboard
2. Verify that the application connects to Redis successfully
3. Confirm that the Celery worker is running properly

## Troubleshooting

### Common Issues

1. **Redis Connection Errors**:
   - Verify that the Redis service is running in your Render dashboard
   - Check that the `REDIS_URL` environment variable is correctly set
   - Ensure the Redis service is properly linked to your web and worker services

2. **Celery Worker Not Starting**:
   - Check the worker logs for any errors
   - Verify that `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` are correctly set
   - Ensure the worker service has access to the Redis service

3. **Application Startup Failures**:
   - Check the application logs for detailed error messages
   - Verify all required environment variables are set
   - Ensure the database is properly configured and accessible

## Additional Resources

- [Render Redis Documentation](https://render.com/docs/redis)
- [Render Environment Variables](https://render.com/docs/environment-variables)
- [Render Troubleshooting Guide](https://render.com/docs/troubleshooting-deploys)