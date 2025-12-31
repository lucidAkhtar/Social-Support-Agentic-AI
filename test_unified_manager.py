"""
Quick test of UnifiedDatabaseManager - Production-grade caching and query routing
Run: poetry run python test_unified_manager.py
"""
import time
from src.databases.unified_database_manager import UnifiedDatabaseManager

def test_unified_manager():
    print("=" * 80)
    print("UNIFIED DATABASE MANAGER - PRODUCTION TEST")
    print("=" * 80)
    
    # Initialize manager
    print("\n📦 Initializing UnifiedDatabaseManager...")
    start = time.time()
    manager = UnifiedDatabaseManager()
    init_time = (time.time() - start) * 1000
    print(f"✅ Initialized in {init_time:.2f}ms")
    
    # Health check
    print("\n🏥 Health Check:")
    health = manager.health_check()
    for db, status in health.items():
        icon = "✅" if "operational" in status else "⚠️"
        print(f"  {icon} {db}: {status}")
    
    # Test 1: Query application (cold - no cache)
    print("\n🔍 Test 1: Query Application (COLD - First Query)")
    app_id = "APP-000001"
    start = time.time()
    result = manager.query_application(app_id, include_full_context=False)
    duration = (time.time() - start) * 1000
    if result:
        print(f"  Result: {result.get('app_id', 'Not found')}")
        print(f"  Source: {result.get('source', 'unknown')}")
    else:
        print(f"  Result: No data (SQLite methods mismatch)")
    print(f"  ⏱️  Duration: {duration:.2f}ms")
    
    # Test 2: Query same application (hot - L1 cache)
    print("\n🔍 Test 2: Query Same Application (HOT - L1 Cache Hit)")
    start = time.time()
    result = manager.query_application(app_id, include_full_context=False)
    duration = (time.time() - start) * 1000
    if result:
        print(f"  Result: {result.get('app_id', 'Cached')}")
        print(f"  Source: {result.get('source', 'unknown')}")
    else:
        print(f"  Result: Still None")
    print(f"  ⏱️  Duration: {duration:.2f}ms {'✅ <10ms (cached)' if duration < 10 else '⚠️ >10ms'}")
    
    # Test 3: Search similar applications
    print("\n🔍 Test 3: Search Similar Applications")
    start = time.time()
    similar = manager.search_similar_applications(app_id=app_id, limit=3)
    duration = (time.time() - start) * 1000
    print(f"  Found: {len(similar)} similar applications")
    print(f"  ⏱️  Duration: {duration:.2f}ms")
    
    # Test 4: Get decision history
    print("\n🔍 Test 4: Get Decision History")
    start = time.time()
    decisions = manager.get_decision_history(app_id)
    duration = (time.time() - start) * 1000
    print(f"  Found: {len(decisions)} decisions")
    print(f"  ⏱️  Duration: {duration:.2f}ms")
    
    # Test 5: Full-text search
    print("\n🔍 Test 5: Full-Text Search")
    start = time.time()
    results = manager.full_text_search("income", limit=5)
    duration = (time.time() - start) * 1000
    print(f"  Found: {len(results)} results")
    print(f"  ⏱️  Duration: {duration:.2f}ms")
    
    # Test 6: Semantic search (ChromaDB)
    print("\n🔍 Test 6: Semantic Search (ChromaDB)")
    start = time.time()
    semantic_results = manager.semantic_search("low income large family", limit=3)
    duration = (time.time() - start) * 1000
    print(f"  Found: {len(semantic_results)} results")
    print(f"  ⏱️  Duration: {duration:.2f}ms")
    
    # Test 7: Graph context (NetworkX)
    print("\n🔍 Test 7: Graph Context (NetworkX)")
    start = time.time()
    graph_context = manager.get_graph_context(app_id)
    duration = (time.time() - start) * 1000
    print(f"  Neighbors: {graph_context.get('neighbor_count', 0)}")
    print(f"  ⏱️  Duration: {duration:.2f}ms")
    
    # Performance stats
    print("\n📊 Performance Statistics:")
    stats = manager.get_performance_stats()
    
    print(f"\n  Cache Stats:")
    cache = stats['cache']
    print(f"    Hits: {cache['hits']}")
    print(f"    Misses: {cache['misses']}")
    print(f"    Hit Rate: {cache['hit_rate']}")
    print(f"    Cache Size: {cache['cache_size']}/{cache['max_size']}")
    
    print(f"\n  Database Query Stats:")
    for db_name, db_stats in stats['databases'].items():
        if db_stats['query_count'] > 0:
            print(f"    {db_name}:")
            print(f"      Queries: {db_stats['query_count']}")
            print(f"      Avg Time: {db_stats['avg_time_ms']}ms")
    
    # Test 8: Batch queries (measure cache effectiveness)
    print("\n🔍 Test 8: Batch Queries (Cache Effectiveness)")
    test_apps = ["APP-000001", "APP-000002", "APP-000003", "APP-000001", "APP-000002"]
    total_time = 0
    for i, test_app in enumerate(test_apps, 1):
        start = time.time()
        result = manager.query_application(test_app, include_full_context=False)
        duration = (time.time() - start) * 1000
        total_time += duration
        cache_status = "✅ CACHED" if duration < 10 and result and result.get('source') == 'l1_cache' else "⚠️ DB QUERY"
        print(f"  Query {i} ({test_app}): {duration:.2f}ms {cache_status}")
    
    avg_time = total_time / len(test_apps)
    print(f"  Average: {avg_time:.2f}ms")
    
    # Final stats
    print("\n📊 Final Performance Summary:")
    final_stats = manager.get_performance_stats()
    final_cache = final_stats['cache']
    hit_rate = float(final_cache['hit_rate'].rstrip('%'))
    
    print(f"  Total Requests: {final_cache['hits'] + final_cache['misses']}")
    print(f"  Cache Hit Rate: {final_cache['hit_rate']}")
    print(f"  Status: {'✅ EXCELLENT' if hit_rate > 50 else '🔄 WARMING UP'}")
    
    print("\n" + "=" * 80)
    print("✅ UNIFIED DATABASE MANAGER TEST COMPLETE")
    print("=" * 80)
    
    # Recommendations
    print("\n💡 Recommendations:")
    if hit_rate < 50:
        print("  - Cache is still warming up. Run more queries to improve hit rate.")
    else:
        print("  - Cache performing well! Hit rate >50%")
    
    if avg_time < 50:
        print("  - ✅ Average response time <50ms (EXCELLENT)")
    else:
        print("  - ⚠️  Average response time >50ms (Consider optimization)")
    
    print("\n🚀 Next Steps:")
    print("  1. Integrate with RAGChatbotAgent")
    print("  2. Load test with 100+ concurrent queries")
    print("  3. Monitor cache hit rate in production (target >70%)")

if __name__ == "__main__":
    test_unified_manager()
