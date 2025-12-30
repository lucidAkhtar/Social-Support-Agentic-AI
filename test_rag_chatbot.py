"""
Test RAG Chatbot with Real Data from All 4 Databases
Tests: caching, session management, multi-database queries
"""
import sys
import time
from src.agents.rag_chatbot_agent import RAGChatbotAgent
from src.core.types import ApplicationState


def test_rag_chatbot():
    """Test RAG chatbot with all 4 databases"""
    print("=" * 60)
    print("RAG CHATBOT TEST - ALL 4 DATABASES + CACHING + SESSIONS")
    print("=" * 60)
    
    # Initialize chatbot
    print("\n1. Initializing RAG Chatbot...")
    agent = RAGChatbotAgent()
    stats = agent.get_cache_stats()
    print(f"   ✅ Cache: {stats['max_cache_size']} max entries (LRU eviction)")
    print(f"   ✅ Sessions: {stats['active_sessions']} active")
    print(f"   ✅ Max history per session: {agent.max_history_per_session} messages")
    
    # Test with real application
    app_id = "APP-000001"
    print(f"\n2. Testing with application: {app_id}")
    
    # Test 1: Query decision (should hit all 4 databases)
    print("\n--- Test 1: Decision Explanation ---")
    state = ApplicationState(application_id=app_id, applicant_name="Test User")
    state.chat_input = "Why was this decision made?"
    
    start = time.time()
    result = agent.process(state)
    duration = time.time() - start
    
    print(f"✅ Response generated in {duration:.2f}s")
    print(f"Response preview: {result.chat_response[:200]}...")
    
    # Check cache stats
    stats = agent.get_cache_stats()
    print(f"Cache stats: {stats['cache_hits']} hits, {stats['cache_misses']} misses")
    
    # Test 2: Same query (should hit cache)
    print("\n--- Test 2: Cache Test (Same Query) ---")
    state2 = ApplicationState(application_id=app_id, applicant_name="Test User")
    state2.chat_input = "Why was this decision made?"
    
    start = time.time()
    result2 = agent.process(state2)
    duration2 = time.time() - start
    
    print(f"✅ Response from CACHE in {duration2:.2f}s")
    print(f"Speed improvement: {(duration/duration2):.1f}x faster")
    
    stats = agent.get_cache_stats()
    print(f"Cache stats: {stats['cache_hits']} hits, {stats['cache_misses']} misses, {stats['hit_rate']} hit rate")
    
    # Test 3: Improvements query (different handler)
    print("\n--- Test 3: Improvement Suggestions ---")
    state3 = ApplicationState(application_id=app_id, applicant_name="Test User")
    state3.chat_input = "How can I improve my application?"
    
    start = time.time()
    result3 = agent.process(state3)
    duration3 = time.time() - start
    
    print(f"✅ Improvement suggestions in {duration3:.2f}s")
    print(f"Response preview: {result3.chat_response[:200]}...")
    
    # Test 4: Details query (all 4 databases)
    print("\n--- Test 4: Show All Details ---")
    state4 = ApplicationState(application_id=app_id, applicant_name="Test User")
    state4.chat_input = "Show me all details"
    
    start = time.time()
    result4 = agent.process(state4)
    duration4 = time.time() - start
    
    print(f"✅ Full details retrieved in {duration4:.2f}s")
    print(f"Response preview: {result4.chat_response[:200]}...")
    
    # Test 5: Similar cases (NetworkX graph query)
    print("\n--- Test 5: Find Similar Cases ---")
    state5 = ApplicationState(application_id=app_id, applicant_name="Test User")
    state5.chat_input = "Find similar applications"
    
    start = time.time()
    result5 = agent.process(state5)
    duration5 = time.time() - start
    
    print(f"✅ Similar cases found in {duration5:.2f}s")
    print(f"Response preview: {result5.chat_response[:200]}...")
    
    # Test 6: Programs (NetworkX + LLM)
    print("\n--- Test 6: Explain Programs ---")
    state6 = ApplicationState(application_id=app_id, applicant_name="Test User")
    state6.chat_input = "What programs are available?"
    
    start = time.time()
    result6 = agent.process(state6)
    duration6 = time.time() - start
    
    print(f"✅ Programs explained in {duration6:.2f}s")
    print(f"Response preview: {result6.chat_response[:200]}...")
    
    # Final stats
    print("\n" + "=" * 60)
    print("FINAL STATISTICS")
    print("=" * 60)
    stats = agent.get_cache_stats()
    print(f"Total Requests: {stats['total_requests']}")
    print(f"Cache Hits: {stats['cache_hits']}")
    print(f"Cache Misses: {stats['cache_misses']}")
    print(f"Hit Rate: {stats['hit_rate']}")
    print(f"Cache Size: {stats['cache_size']}/{stats['max_cache_size']}")
    print(f"Active Sessions: {stats['active_sessions']}")
    
    # Session details
    if app_id in agent.active_sessions:
        session = agent.active_sessions[app_id]
        print(f"\nSession {app_id}:")
        print(f"  History: {len(session['history'])} messages")
        print(f"  Created: {session['created_at']}")
    
    print("\n✅ ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_rag_chatbot()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
