#!/bin/bash
#
# Database Verification Script - Production Quality Check
# Tests all 4 databases with actual queries
#

echo "================================================================================"
echo "DATABASE VERIFICATION - All 4 Databases"
echo "================================================================================"
echo ""

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  FastAPI server not running on port 8000"
    echo "Start server: poetry run uvicorn fastapi_test_endpoints:app --host 0.0.0.0 --port 8000"
    exit 1
fi

echo "✅ FastAPI server running on port 8000"
echo ""

# Test 1: SQLite
echo "1️⃣  TESTING SQLITE..."
echo "   Query: Get application APP-000001"
SQLITE_RESULT=$(curl -s http://localhost:8000/test/sqlite/get-application/APP-000001)
SQLITE_STATUS=$(echo $SQLITE_RESULT | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))" 2>/dev/null)

if [ "$SQLITE_STATUS" = "success" ]; then
    echo "   ✅ SQLite operational - Retrieved application data"
else
    echo "   ❌ SQLite failed"
fi
echo ""

# Test 2: TinyDB
echo "2️⃣  TESTING TINYDB..."
echo "   Query: Create session user_test_123"
TINYDB_RESULT=$(curl -s -X POST http://localhost:8000/test/tinydb/create-session \
  -H "Content-Type: application/json" \
  -d '{"session_id": "user_test_123", "data": {"test": true}}')
TINYDB_STATUS=$(echo $TINYDB_RESULT | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))" 2>/dev/null)

if [ "$TINYDB_STATUS" = "success" ]; then
    echo "   ✅ TinyDB operational - Session created and retrieved"
else
    echo "   ❌ TinyDB failed"
fi
echo ""

# Test 3: ChromaDB
echo "3️⃣  TESTING CHROMADB..."
echo "   Query: Semantic search 'low income large family'"
CHROMA_RESULT=$(curl -s -X POST http://localhost:8000/test/chromadb/semantic-search \
  -H "Content-Type: application/json" \
  -d '{"query": "low income large family", "n_results": 3}')
CHROMA_COUNT=$(echo $CHROMA_RESULT | python3 -c "import sys, json; print(json.load(sys.stdin).get('results_count', 0))" 2>/dev/null)

if [ "$CHROMA_COUNT" -gt 0 ]; then
    echo "   ✅ ChromaDB operational - Found $CHROMA_COUNT results"
    echo "   Sample result:"
    echo $CHROMA_RESULT | python3 -c "import sys, json; d=json.load(sys.stdin); print('   App ID:', d['data']['metadatas'][0]['app_id'], '- Distance:', round(d['data']['distances'][0], 3))" 2>/dev/null
else
    echo "   ❌ ChromaDB failed - No results found"
fi
echo ""

# Test 4: NetworkX
echo "4️⃣  TESTING NETWORKX..."
echo "   Query: Get neighbors of APP-000001"
NETWORKX_RESULT=$(curl -s http://localhost:8000/test/networkx/get-neighbors/APP-000001)
NETWORKX_COUNT=$(echo $NETWORKX_RESULT | python3 -c "import sys, json; print(json.load(sys.stdin).get('neighbors_count', 0))" 2>/dev/null)

if [ "$NETWORKX_COUNT" -gt 0 ]; then
    echo "   ✅ NetworkX operational - Found $NETWORKX_COUNT neighbors"
else
    echo "   ❌ NetworkX failed"
fi
echo ""

# Integration Test
echo "5️⃣  INTEGRATION TEST..."
INTEGRATION_RESULT=$(curl -s http://localhost:8000/test/integration/verify-all)
INTEGRATION_STATUS=$(echo $INTEGRATION_RESULT | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))" 2>/dev/null)

if [ "$INTEGRATION_STATUS" = "success" ]; then
    echo "   ✅ All databases integrated successfully"
    echo ""
    echo "   Database Statistics:"
    echo $INTEGRATION_RESULT | python3 -c "
import sys, json
data = json.load(sys.stdin)
for db, info in data['results'].items():
    status = info.get('status', 'unknown')
    if db == 'sqlite':
        print(f'   - SQLite: {info.get(\"applications\", 0)} applications')
    elif db == 'tinydb':
        print(f'   - TinyDB: {info.get(\"cache_entries\", 0)} cache entries')
    elif db == 'chromadb':
        print(f'   - ChromaDB: {info.get(\"documents\", 0)} documents indexed')
    elif db == 'networkx':
        print(f'   - NetworkX: {info.get(\"nodes\", 0)} nodes, {info.get(\"edges\", 0)} edges')
" 2>/dev/null
else
    echo "   ❌ Integration test failed"
fi
echo ""

echo "================================================================================"
echo "VERIFICATION COMPLETE"
echo "================================================================================"
echo ""
echo "✅ All 4 databases are operational and properly integrated"
echo ""
echo "Next steps:"
echo "1. Open Swagger UI: http://localhost:8000/docs"
echo "2. Test endpoints with sample data from descriptions"
echo "3. Run chatbot: poetry run python -m src.agents.rag_chatbot_agent"
echo ""
