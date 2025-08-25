# Docker Deployment Guide

This guide provides comprehensive instructions for building and deploying the AI Customer Service System using Docker in production environments.

## Quick Start

### Local Development with Docker Compose

```bash
# Clone and navigate to the project
cd wind

# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Build and start all services
docker-compose up --build

# Access the application
# Web interface: http://localhost:5000
# Redis: localhost:6379
```

### Production Build

```bash
# Build production image
docker build -t ai-customer-service:latest .

# Run with external Redis and MongoDB Atlas
docker run -d \
  --name ai-customer-service \
  -p 5000:5000 \
  -e REDIS_URL=redis://your-redis-host:6379/0 \
  -e MONGODB_URI=mongodb+srv://username:password@cluster0.mongodb.net/hotel_service?retryWrites=true&w=majority \
  -e SECRET_KEY=your-production-secret \
  -e GOOGLE_API_KEY=your-api-key \
  ai-customer-service:latest
```

## Cloud Platform Deployments

### AWS ECS (Elastic Container Service)

#### 1. Build and Push to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name ai-customer-service

# Get login token
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com

# Build and tag image
docker build -t ai-customer-service .
docker tag ai-customer-service:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/ai-customer-service:latest

# Push image
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/ai-customer-service:latest
```

#### 2. ECS Task Definition

```json
{
  "family": "ai-customer-service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "ai-customer-service",
      "image": "123456789012.dkr.ecr.us-west-2.amazonaws.com/ai-customer-service:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "FLASK_ENV", "value": "production"},
        {"name": "REDIS_URL", "value": "redis://your-elasticache-endpoint:6379/0"},
        {"name": "MONGODB_URI", "value": "mongodb+srv://username:password@cluster0.mongodb.net/hotel_service?retryWrites=true&w=majority"}
      ],
      "secrets": [
        {"name": "SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789012:secret:app-secrets"},
        {"name": "GOOGLE_API_KEY", "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789012:secret:api-keys"}
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:5000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-customer-service",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/ai-customer-service

# Deploy to Cloud Run
gcloud run deploy ai-customer-service \
  --image gcr.io/PROJECT_ID/ai-customer-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FLASK_ENV=production \
  --set-env-vars REDIS_URL=redis://your-memorystore-ip:6379/0 \
  --memory 1Gi \
  --cpu 1 \
  --concurrency 80 \
  --max-instances 10
```

### Azure Container Instances

```bash
# Create resource group
az group create --name ai-customer-service-rg --location eastus

# Create container registry
az acr create --resource-group ai-customer-service-rg --name aiserviceregistry --sku Basic

# Build and push image
az acr build --registry aiserviceregistry --image ai-customer-service:latest .

# Deploy container instance
az container create \
  --resource-group ai-customer-service-rg \
  --name ai-customer-service \
  --image aiserviceregistry.azurecr.io/ai-customer-service:latest \
  --cpu 1 \
  --memory 1 \
  --registry-login-server aiserviceregistry.azurecr.io \
  --registry-username $(az acr credential show --name aiserviceregistry --query username -o tsv) \
  --registry-password $(az acr credential show --name aiserviceregistry --query passwords[0].value -o tsv) \
  --dns-name-label ai-customer-service \
  --ports 5000 \
  --environment-variables FLASK_ENV=production REDIS_URL=redis://your-redis-cache:6379/0
```

### Kubernetes Deployment

#### Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-customer-service
  labels:
    app: ai-customer-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-customer-service
  template:
    metadata:
      labels:
        app: ai-customer-service
    spec:
      containers:
      - name: ai-customer-service
        image: your-registry/ai-customer-service:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: google-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ai-customer-service
spec:
  selector:
    app: ai-customer-service
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
  type: LoadBalancer
```

## Environment Configuration

### Required Environment Variables

```bash
# Application
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-production-secret-key

# Database
DATABASE_URL=sqlite:///instance/hotel_service.db
# For production, consider PostgreSQL:
# DATABASE_URL=postgresql://user:password@host:port/database

# Redis
REDIS_URL=redis://redis-host:6379/0
CELERY_BROKER_URL=redis://redis-host:6379/0
CELERY_RESULT_BACKEND=redis://redis-host:6379/0

# API Keys
GOOGLE_API_KEY=your-google-api-key

# Hotel Configuration
HOTEL_NAME=Your Hotel Name
HOTEL_PHONE=+1234567890
HOTEL_EMAIL=info@yourhotel.com
HOTEL_ADDRESS=Your Hotel Address
```

### Security Best Practices

1. **Secrets Management**
   - Use cloud provider secret managers (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager)
   - Never hardcode secrets in images
   - Rotate secrets regularly

2. **Network Security**
   - Use private networks/VPCs
   - Implement proper firewall rules
   - Use TLS/SSL for all communications

3. **Container Security**
   - Run as non-root user (already implemented)
   - Use minimal base images (Alpine)
   - Regularly update base images
   - Scan images for vulnerabilities

## Monitoring and Logging

### Health Checks

The application includes a comprehensive health check endpoint at `/health` that verifies:
- Database connectivity
- Redis connectivity
- Application status

### Logging

Configure centralized logging:

```bash
# For Docker Compose
docker-compose logs -f app

# For production, use log aggregation services:
# - AWS CloudWatch
# - Google Cloud Logging
# - Azure Monitor
# - ELK Stack
# - Datadog
```

### Metrics

Consider implementing:
- Application metrics (Prometheus)
- Infrastructure metrics
- Custom business metrics
- Alerting (PagerDuty, Slack)

## Scaling Considerations

### Horizontal Scaling

1. **Stateless Design**: Application is stateless and can be scaled horizontally
2. **Load Balancing**: Use cloud load balancers or ingress controllers
3. **Session Management**: Redis handles session storage
4. **Database**: Consider read replicas for high traffic

### Performance Optimization

1. **Resource Limits**: Set appropriate CPU and memory limits
2. **Connection Pooling**: Configure database connection pooling
3. **Caching**: Leverage Redis for caching
4. **CDN**: Use CDN for static assets

## Troubleshooting

### Common Issues

1. **Health Check Failures**
   ```bash
   # Check logs
   docker logs container-name
   
   # Test health endpoint manually
   curl http://localhost:5000/health
   ```

2. **Redis Connection Issues**
   ```bash
   # Verify Redis connectivity
   redis-cli -h redis-host -p 6379 ping
   ```

3. **Database Issues**
   ```bash
   # Check database file permissions
   ls -la instance/
   
   # Initialize database if needed
   docker exec -it container-name python init_db.py
   ```

### Debug Mode

```bash
# Run with debug logging
docker run -e FLASK_DEBUG=True -e LOG_LEVEL=DEBUG your-image
```

## Backup and Recovery

### Database Backup

```bash
# SQLite backup
docker exec container-name cp /app/instance/hotel_service.db /backup/

# For PostgreSQL
docker exec container-name pg_dump -U user database > backup.sql
```

### Redis Backup

```bash
# Redis backup
docker exec redis-container redis-cli BGSAVE
```

## CI/CD Pipeline Example

```yaml
# GitHub Actions example
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker image
      run: |
        docker build -t ai-customer-service:${{ github.sha }} .
        
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push ai-customer-service:${{ github.sha }}
        
    - name: Deploy to production
      run: |
        # Deploy using your preferred method
        # kubectl, aws ecs, gcloud run, etc.
```

This deployment guide provides a comprehensive foundation for deploying the AI Customer Service System in production environments across major cloud platforms.