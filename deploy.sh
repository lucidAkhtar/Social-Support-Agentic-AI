#!/bin/bash
# Production Deployment Script for Social Support System

set -e  # Exit on error

echo "=========================================="
echo "Social Support System - Production Deploy"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "\n${YELLOW}1. Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites satisfied${NC}"

# Build Docker image
echo -e "\n${YELLOW}2. Building Docker image...${NC}"
docker build -t social-support-app:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Create necessary directories
echo -e "\n${YELLOW}3. Creating directories...${NC}"
mkdir -p data/databases data/processed data/raw logs monitoring/grafana-dashboards nginx/ssl

echo -e "${GREEN}✅ Directories created${NC}"

# Stop existing containers
echo -e "\n${YELLOW}4. Stopping existing containers...${NC}"
docker-compose down

# Start services
echo -e "\n${YELLOW}5. Starting services...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo -e "\n${YELLOW}6. Waiting for services to be ready...${NC}"
sleep 10

# Check health
echo -e "\n${YELLOW}7. Checking service health...${NC}"

# Check app
if curl -f http://localhost:8000/test/integration/verify-all &> /dev/null; then
    echo -e "${GREEN}✅ Application is healthy${NC}"
else
    echo -e "${RED}❌ Application health check failed${NC}"
    docker-compose logs app
    exit 1
fi

# Check Ollama
if curl -f http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${GREEN}✅ Ollama is running${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama may need model download${NC}"
fi

# Check Prometheus
if curl -f http://localhost:9090/-/healthy &> /dev/null; then
    echo -e "${GREEN}✅ Prometheus is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Prometheus may be starting${NC}"
fi

# Check Grafana
if curl -f http://localhost:3000/api/health &> /dev/null; then
    echo -e "${GREEN}✅ Grafana is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Grafana may be starting${NC}"
fi

# Summary
echo -e "\n=========================================="
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE${NC}"
echo "=========================================="
echo ""
echo "Services:"
echo "  📊 Application:  http://localhost:8000"
echo "  📚 API Docs:     http://localhost:8000/docs"
echo "  🤖 Ollama:       http://localhost:11434"
echo "  📈 Prometheus:   http://localhost:9090"
echo "  📊 Grafana:      http://localhost:3000"
echo "     Username: admin"
echo "     Password: social_support_2024"
echo ""
echo "Next steps:"
echo "  1. Download Ollama model: docker exec -it social-support-ollama ollama pull mistral"
echo "  2. Run load test: poetry run python load_test.py"
echo "  3. View logs: docker-compose logs -f app"
echo "  4. Stop services: docker-compose down"
echo ""
