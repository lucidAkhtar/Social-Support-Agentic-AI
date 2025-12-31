#!/bin/bash
# Production Deployment Script for Social Support Agentic AI System
# Architecture: FastAPI + 6 Agents + 4 Databases

set -e  # Exit on error

echo "=========================================================="
echo "🚀 Social Support Agentic AI - Production Deployment"
echo "=========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Create necessary directories
echo -e "\n${YELLOW}2. Creating directories...${NC}"
mkdir -p data/databases data/processed data/raw data/observability logs

echo -e "${GREEN}✅ Directories created${NC}"

# Build Docker image
echo -e "\n${YELLOW}3. Building Docker image...${NC}"
docker-compose build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Stop existing containers
echo -e "\n${YELLOW}4. Stopping existing containers...${NC}"
docker-compose down

# Start services
echo -e "\n${YELLOW}5. Starting services...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo -e "\n${YELLOW}6. Waiting for services to initialize...${NC}"
sleep 10

# Check health
echo -e "\n${YELLOW}7. Checking service health...${NC}"

# Check FastAPI application
MAX_RETRIES=10
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo -e "${GREEN}✅ FastAPI application is healthy${NC}"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -e "${BLUE}⏳ Waiting for FastAPI... (attempt $RETRY_COUNT/$MAX_RETRIES)${NC}"
        sleep 3
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ FastAPI health check failed${NC}"
    docker-compose logs app
    exit 1
fi

# Check Ollama
if curl -f http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${GREEN}✅ Ollama service is running${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama may need model download (see instructions below)${NC}"
fi

# Summary
echo -e "\n=========================================================="
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE${NC}"
echo "=========================================================="
echo ""
echo "📦 Architecture:"
echo "  • 6 Agents: Extraction, Validation, Eligibility, Recommendation, Explanation, RAG Chatbot"
echo "  • 4 Databases: SQLite, TinyDB, ChromaDB, NetworkX Graph"
echo ""
echo "🌐 Services:"
echo "  • FastAPI Backend:  http://localhost:8000"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Health Check:      http://localhost:8000/health"
echo "  • Ollama LLM:        http://localhost:11434"
echo ""
echo "📋 Next Steps:"
echo "  1. Download Ollama model:"
echo "     ${BLUE}docker exec -it social-support-ollama ollama pull mistral${NC}"
echo ""
echo "  2. Test the API:"
echo "     ${BLUE}curl http://localhost:8000/health${NC}"
echo ""
echo "  3. View application logs:"
echo "     ${BLUE}docker-compose logs -f app${NC}"
echo ""
echo "  4. View all services:"
echo "     ${BLUE}docker-compose ps${NC}"
echo ""
echo "  5. Stop services:"
echo "     ${BLUE}docker-compose down${NC}"
echo ""
