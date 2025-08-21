# FulfillmentEA Deployment Guide

This guide will help you deploy your FulfillmentEA backend and dashboard to a production server with domain support.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed on your server
- Domain names configured (api.fulfillmentea.com and dashboard.fulfillmentea.com)
- SSL certificates for HTTPS
- Server with at least 2GB RAM and 20GB storage

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd fulfillmentea-native
```

### 2. Configure Environment
Copy and edit the production environment file:
```bash
cp env.production .env
# Edit .env with your actual values
```

### 3. Add SSL Certificates
Place your SSL certificates in the `nginx/ssl/` directory:
- `nginx/ssl/cert.pem` - Your SSL certificate
- `nginx/ssl/key.pem` - Your SSL private key

### 4. Deploy
```bash
# Windows PowerShell
.\deploy.ps1 -Production

# Linux/Mac
chmod +x deploy.sh
./deploy.sh --production

# Or manually
docker-compose --profile production up -d --build
```

## 🌐 Domain Configuration

### DNS Records
Configure these DNS records to point to your server IP:
```
Type: A
Name: api.fulfillmentea.com
Value: [YOUR_SERVER_IP]

Type: A  
Name: dashboard.fulfillmentea.com
Value: [YOUR_SERVER_IP]
```

### SSL Certificates
You can obtain free SSL certificates from Let's Encrypt:
```bash
# Install certbot
sudo apt install certbot

# Generate certificates
sudo certbot certonly --standalone -d api.fulfillmentea.com
sudo certbot certonly --standalone -d dashboard.fulfillmentea.com

# Copy certificates to nginx/ssl/
sudo cp /etc/letsencrypt/live/api.fulfillmentea.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/api.fulfillmentea.com/privkey.pem nginx/ssl/key.pem
```

## 🔧 Configuration

### Environment Variables
Key variables in `.env`:
```bash
# Security
SECRET_KEY=your-super-secure-secret-key-here

# BlkSMS Configuration
BLKSMS_CLIENT_ID=your_actual_client_id
BLKSMS_CLIENT_SECRET=your_actual_client_secret
BLKSMS_ENABLED=true

# CORS (for production)
CORS_ORIGINS=["https://api.fulfillmentea.com", "https://dashboard.fulfillmentea.com"]
```

### Mobile App Configuration
Update your mobile app to use the new API domain:
```typescript
// In mobile/src/api/client.ts
const baseURL = 'https://api.fulfillmentea.com';
```

## 📊 Service Architecture

```
Internet
    ↓
Nginx (Port 80/443)
    ↓
├── api.fulfillmentea.com → Backend (Port 8000)
└── dashboard.fulfillmentea.com → Dashboard (Port 8501)
```

## 🐳 Docker Services

### Development
```bash
docker-compose up -d
```
- Backend: http://localhost:8000
- Dashboard: http://localhost:8501

### Production
```bash
docker-compose --profile production up -d
```
- Backend: https://api.fulfillmentea.com
- Dashboard: https://dashboard.fulfillmentea.com

## 🔍 Monitoring and Health Checks

### Health Endpoints
- Backend: `https://api.fulfillmentea.com/health`
- Dashboard: `https://dashboard.fulfillmentea.com/_stcore/health`

### Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs dashboard
docker-compose logs nginx
```

### Container Status
```bash
docker-compose ps
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
netstat -tulpn | grep :8000
netstat -tulpn | grep :8501

# Stop conflicting services
sudo systemctl stop <service-name>
```

#### 2. SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Verify certificate matches domain
openssl x509 -in nginx/ssl/cert.pem -noout -subject
```

#### 3. Database Issues
```bash
# Access database
docker-compose exec backend sqlite3 backend/db.sqlite3

# Check tables
.tables
.schema
```

#### 4. Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod -R 755 nginx/ssl/
```

### Reset Everything
```bash
# Stop and remove everything
docker-compose down --volumes --remove-orphans

# Remove all images
docker system prune -a

# Start fresh
docker-compose up -d --build
```

## 🔄 Updates and Maintenance

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Backup Database
```bash
# Create backup
docker-compose exec backend sqlite3 backend/db.sqlite3 ".backup backup_$(date +%Y%m%d_%H%M%S).db"

# Restore from backup
docker-compose exec backend sqlite3 backend/db.sqlite3 ".restore backup_20231201_120000.db"
```

### SSL Certificate Renewal
```bash
# Renew certificates
sudo certbot renew

# Copy new certificates
sudo cp /etc/letsencrypt/live/api.fulfillmentea.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/api.fulfillmentea.com/privkey.pem nginx/ssl/key.pem

# Reload nginx
docker-compose restart nginx
```

## 📱 Mobile App Updates

After deployment, update your mobile app configuration:

1. **Update API base URL** in `mobile/src/api/client.ts`
2. **Test all endpoints** to ensure they work with the new domain
3. **Update any hardcoded URLs** in the mobile app
4. **Test OTP verification** and delivery processes

## 🔒 Security Considerations

- Change default `SECRET_KEY` in production
- Use strong passwords for admin accounts
- Regularly update dependencies
- Monitor access logs
- Enable firewall rules
- Use HTTPS everywhere
- Implement rate limiting (already configured in Nginx)

## 📞 Support

If you encounter issues:
1. Check the logs: `docker-compose logs`
2. Verify DNS configuration
3. Test SSL certificates
4. Check firewall settings
5. Verify environment variables

## 🎯 Next Steps

After successful deployment:
1. Test all functionality from external access
2. Set up monitoring and alerting
3. Configure automated backups
4. Set up SSL certificate auto-renewal
5. Monitor performance and optimize as needed
