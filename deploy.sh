#!/bin/bash

# FulfillmentEA Deployment Script for Linux/macOS
# This script deploys the backend and dashboard using Docker

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
PRODUCTION=false
HELP=false

# Function to show help
show_help() {
    echo -e "${GREEN}FulfillmentEA Deployment Script${NC}"
    echo ""
    echo "Usage:"
    echo "    ./deploy.sh [options]"
    echo ""
    echo "Options:"
    echo "    -e, --environment <env>  Deployment environment (development, staging, production)"
    echo "    -p, --production         Shortcut for production deployment"
    echo "    -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "    ./deploy.sh                           # Deploy development"
    echo "    ./deploy.sh -e staging                # Deploy staging"
    echo "    ./deploy.sh -p                        # Deploy production"
    echo "    ./deploy.sh --production              # Deploy production"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--production)
            PRODUCTION=true
            shift
            ;;
        -h|--help)
            HELP=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Show help if requested
if [ "$HELP" = true ]; then
    show_help
    exit 0
fi

# Set environment to production if flag is set
if [ "$PRODUCTION" = true ]; then
    ENVIRONMENT="production"
fi

echo -e "🚀 ${GREEN}Starting FulfillmentEA deployment...${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"

# Check if Docker is running
if ! docker version >/dev/null 2>&1; then
    echo -e "❌ ${RED}Docker is not running. Please start Docker first.${NC}"
    exit 1
else
    echo -e "✅ ${GREEN}Docker is running${NC}"
fi

# Check if docker-compose is available
if ! docker-compose --version >/dev/null 2>&1; then
    echo -e "❌ ${RED}Docker Compose is not available. Please install Docker Compose.${NC}"
    exit 1
else
    echo -e "✅ ${GREEN}Docker Compose is available${NC}"
fi

# Stop existing containers
echo -e "🛑 ${YELLOW}Stopping existing containers...${NC}"
docker-compose down

# Remove old images (optional)
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "🧹 ${YELLOW}Removing old images...${NC}"
    docker-compose down --rmi all
fi

# Build and start services
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "🏗️  ${YELLOW}Building and starting production services...${NC}"
    
    # Create necessary directories
    if [ ! -d "nginx/ssl" ]; then
        mkdir -p nginx/ssl
        echo -e "📁 ${GREEN}Created nginx/ssl directory${NC}"
    fi
    
    if [ ! -d "nginx/logs" ]; then
        mkdir -p nginx/logs
        echo -e "📁 ${GREEN}Created nginx/logs directory${NC}"
    fi
    
    # Check if SSL certificates exist
    if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
        echo -e "⚠️  ${YELLOW}SSL certificates not found in nginx/ssl/${NC}"
        echo -e "   Please add your SSL certificates:${NC}"
        echo -e "   - nginx/ssl/cert.pem (SSL certificate)${NC}"
        echo -e "   - nginx/ssl/key.pem (SSL private key)${NC}"
        echo -e "   Then run this script again.${NC}"
        exit 1
    fi
    
    # Start with production profile
    docker-compose --profile production up -d --build
else
    echo -e "🏗️  ${YELLOW}Building and starting development services...${NC}"
    docker-compose up -d --build
fi

# Wait for services to be ready
echo -e "⏳ ${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Check service health
echo -e "🔍 ${YELLOW}Checking service health...${NC}"

# Check backend health
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo -e "✅ ${GREEN}Backend is healthy${NC}"
else
    echo -e "❌ ${RED}Backend health check failed${NC}"
fi

# Check dashboard health
if curl -f http://localhost:8501/_stcore/health >/dev/null 2>&1; then
    echo -e "✅ ${GREEN}Dashboard is healthy${NC}"
else
    echo -e "❌ ${RED}Dashboard health check failed${NC}"
fi

# Show service status
echo -e "📊 ${GREEN}Service Status:${NC}"
docker-compose ps

# Show access URLs
echo -e "🌐 ${GREEN}Access URLs:${NC}"
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "   Dashboard: ${CYAN}https://dashboard.fulfillmentea.com${NC}"
    echo -e "   API: ${CYAN}https://api.fulfillmentea.com${NC}"
    echo -e "   API Docs: ${CYAN}https://api.fulfillmentea.com/docs${NC}"
else
    echo -e "   Dashboard: ${CYAN}http://localhost:8501${NC}"
    echo -e "   API: ${CYAN}http://localhost:8000${NC}"
    echo -e "   API Docs: ${CYAN}http://localhost:8000/docs${NC}"
fi

echo -e "🎉 ${GREEN}Deployment completed successfully!${NC}"

if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "📝 ${YELLOW}Next steps:${NC}"
    echo -e "   1. Update your DNS records to point to this server:${WHITE}"
    echo -e "      - api.fulfillmentea.com → [YOUR_SERVER_IP]${WHITE}"
    echo -e "      - dashboard.fulfillmentea.com → [YOUR_SERVER_IP]${WHITE}"
    echo -e "   2. Update your mobile app configuration to use the new API domain${WHITE}"
    echo -e "   3. Test the services from external access${WHITE}"
fi
