"""
Quick test of RAG database queries without LLM calls
"""
from src.agents.rag_chatbot_agent import RAGChatbotAgent

agent = RAGChatbotAgent()
app_id = "APP-000001"

print("Testing database queries...")
print(f"\nApplication: {app_id}")

# Test each database
print("\n1. SQLite Application:")
app = agent._query_sqlite_application(app_id)
print(f"   {'✅' if app else '❌'} Result: {app}")

print("\n2. SQLite Profile:")
profile = agent._query_sqlite_profile(app_id)
print(f"   {'✅' if profile else '❌'} Result: {profile}")

print("\n3. SQLite Validation:")
validation = agent._query_sqlite_validation(app_id)
print(f"   {'✅' if validation else '❌'} Result: {validation}")

print("\n4. SQLite Decision:")
decision = agent._query_sqlite_decision(app_id)
print(f"   {'✅' if decision else '❌'} Result: {decision}")

print("\n5. TinyDB Cache:")
cache = agent._query_tinydb_cache(app_id)
print(f"   {'✅' if cache else '❌'} Result: {cache}")

print("\n6. TinyDB Documents:")
docs = agent._query_tinydb_documents(app_id)
print(f"   {'✅' if docs else '❌'} Count: {len(docs)}")

print("\n7. NetworkX Similar:")
similar = agent._query_networkx_similar(app_id)
print(f"   {'✅' if similar else '❌'} Count: {len(similar)}")

print("\n8. NetworkX Programs:")
programs = agent._query_networkx_programs(app_id)
print(f"   {'✅' if programs else '❌'} Count: {len(programs)}")

print("\n9. NetworkX Connections:")
connections = agent._query_networkx_connections(app_id)
print(f"   {'✅' if connections else '❌'} Result: {connections}")

print("\n10. ChromaDB Semantic:")
semantic = agent._query_chromadb_semantic(app_id)
print(f"   {'✅' if semantic else '❌'} Count: {len(semantic)}")

print("\n✅ Database query test complete")
