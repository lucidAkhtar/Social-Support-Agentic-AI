"""
Load Testing Script for Social Support System
Tests 100+ concurrent users with performance metrics
Uses Python asyncio + aiohttp for high concurrency

Performance Targets:
- 95th percentile: <50ms (cached queries)
- 99th percentile: <200ms (uncached queries)
- Throughput: 1000+ requests/second
- Success rate: >99%
"""
import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict, Any
from datetime import datetime
import random


class LoadTester:
    """
    High-concurrency load tester for database endpoints
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            'total_requests': 0,
            'successful': 0,
            'failed': 0,
            'response_times': [],
            'errors': []
        }
        
        # Test data
        self.app_ids = [f"APP-{str(i).zfill(6)}" for i in range(1, 41)]
        self.test_queries = [
            "low income large family",
            "government employee",
            "unemployed",
            "high debt",
            "approved applications"
        ]
    
    async def make_request(
        self, 
        session: aiohttp.ClientSession, 
        method: str, 
        endpoint: str, 
        data: Dict = None
    ) -> Dict[str, Any]:
        """Make async HTTP request with timing"""
        url = f"{self.base_url}{endpoint}"
        start = time.time()
        
        try:
            if method.upper() == "GET":
                async with session.get(url) as response:
                    result = await response.json()
                    duration = (time.time() - start) * 1000  # ms
                    
                    self.results['total_requests'] += 1
                    self.results['response_times'].append(duration)
                    
                    if response.status == 200:
                        self.results['successful'] += 1
                    else:
                        self.results['failed'] += 1
                        self.results['errors'].append({
                            'endpoint': endpoint,
                            'status': response.status,
                            'error': result
                        })
                    
                    return {
                        'status': response.status,
                        'duration_ms': duration,
                        'data': result
                    }
            
            elif method.upper() == "POST":
                async with session.post(url, json=data) as response:
                    result = await response.json()
                    duration = (time.time() - start) * 1000  # ms
                    
                    self.results['total_requests'] += 1
                    self.results['response_times'].append(duration)
                    
                    if response.status == 200:
                        self.results['successful'] += 1
                    else:
                        self.results['failed'] += 1
                        self.results['errors'].append({
                            'endpoint': endpoint,
                            'status': response.status,
                            'error': result
                        })
                    
                    return {
                        'status': response.status,
                        'duration_ms': duration,
                        'data': result
                    }
        
        except Exception as e:
            duration = (time.time() - start) * 1000
            self.results['total_requests'] += 1
            self.results['failed'] += 1
            self.results['errors'].append({
                'endpoint': endpoint,
                'error': str(e)
            })
            return {
                'status': 'error',
                'duration_ms': duration,
                'error': str(e)
            }
    
    async def test_sqlite_get_application(self, session: aiohttp.ClientSession, app_id: str):
        """Test SQLite application retrieval"""
        return await self.make_request(
            session, 
            "GET", 
            f"/test/sqlite/get-application/{app_id}"
        )
    
    async def test_sqlite_search_similar(self, session: aiohttp.ClientSession):
        """Test SQLite similarity search"""
        income = random.choice([2500.0, 5000.0, 8000.0, 12000.0])
        family_size = random.choice([1, 2, 4, 6])
        return await self.make_request(
            session,
            "GET",
            f"/test/sqlite/search-similar?income={income}&family_size={family_size}&limit=5"
        )
    
    async def test_chromadb_semantic_search(self, session: aiohttp.ClientSession):
        """Test ChromaDB semantic search"""
        query = random.choice(self.test_queries)
        return await self.make_request(
            session,
            "POST",
            "/test/chromadb/semantic-search",
            data={"query": query, "n_results": 5}
        )
    
    async def test_networkx_get_neighbors(self, session: aiohttp.ClientSession, app_id: str):
        """Test NetworkX neighbor retrieval"""
        return await self.make_request(
            session,
            "GET",
            f"/test/networkx/get-neighbors/{app_id}"
        )
    
    async def test_integration(self, session: aiohttp.ClientSession):
        """Test integration endpoint"""
        return await self.make_request(
            session,
            "GET",
            "/test/integration/verify-all"
        )
    
    async def run_user_scenario(self, session: aiohttp.ClientSession, user_id: int):
        """
        Simulate realistic user behavior:
        1. Query specific application (50% probability)
        2. Search similar cases (30% probability)
        3. Semantic search (20% probability)
        """
        scenario = random.random()
        
        if scenario < 0.5:
            # Query application
            app_id = random.choice(self.app_ids)
            result = await self.test_sqlite_get_application(session, app_id)
            
            # Follow up with neighbors (30% probability)
            if random.random() < 0.3:
                await self.test_networkx_get_neighbors(session, app_id)
        
        elif scenario < 0.8:
            # Similarity search
            await self.test_sqlite_search_similar(session)
        
        else:
            # Semantic search
            await self.test_chromadb_semantic_search(session)
    
    async def run_load_test(self, num_users: int = 100, requests_per_user: int = 10):
        """
        Run load test with multiple concurrent users
        
        Args:
            num_users: Number of concurrent users
            requests_per_user: Requests each user makes
        """
        print(f"\n{'='*80}")
        print(f"LOAD TEST: {num_users} concurrent users × {requests_per_user} requests")
        print(f"{'='*80}\n")
        
        start_time = time.time()
        
        # Create session with connection pooling
        connector = aiohttp.TCPConnector(limit=200, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Create tasks for all users
            tasks = []
            for user_id in range(num_users):
                for _ in range(requests_per_user):
                    tasks.append(self.run_user_scenario(session, user_id))
            
            # Run all tasks concurrently
            print(f"🚀 Starting {len(tasks)} concurrent requests...")
            await asyncio.gather(*tasks, return_exceptions=True)
        
        total_duration = time.time() - start_time
        
        # Calculate statistics
        self.print_results(total_duration)
    
    def print_results(self, total_duration: float):
        """Print comprehensive test results"""
        print(f"\n{'='*80}")
        print(f"LOAD TEST RESULTS")
        print(f"{'='*80}\n")
        
        # Basic stats
        success_rate = (self.results['successful'] / self.results['total_requests']) * 100
        throughput = self.results['total_requests'] / total_duration
        
        print(f"📊 SUMMARY:")
        print(f"  Total Requests:  {self.results['total_requests']}")
        print(f"  Successful:      {self.results['successful']} ({success_rate:.1f}%)")
        print(f"  Failed:          {self.results['failed']}")
        print(f"  Total Duration:  {total_duration:.2f}s")
        print(f"  Throughput:      {throughput:.1f} req/s")
        
        # Response time statistics
        if self.results['response_times']:
            response_times = sorted(self.results['response_times'])
            avg = statistics.mean(response_times)
            median = statistics.median(response_times)
            p50 = response_times[int(len(response_times) * 0.50)]
            p90 = response_times[int(len(response_times) * 0.90)]
            p95 = response_times[int(len(response_times) * 0.95)]
            p99 = response_times[int(len(response_times) * 0.99)]
            p999 = response_times[int(len(response_times) * 0.999)]
            min_time = min(response_times)
            max_time = max(response_times)
            
            print(f"\n⏱️  RESPONSE TIMES:")
            print(f"  Average:     {avg:.2f}ms")
            print(f"  Median (p50): {median:.2f}ms")
            print(f"  p90:         {p90:.2f}ms")
            print(f"  p95:         {p95:.2f}ms {'✅' if p95 < 50 else '⚠️ TARGET: <50ms'}")
            print(f"  p99:         {p99:.2f}ms {'✅' if p99 < 200 else '⚠️ TARGET: <200ms'}")
            print(f"  p99.9:       {p999:.2f}ms")
            print(f"  Min:         {min_time:.2f}ms")
            print(f"  Max:         {max_time:.2f}ms")
            
            # Performance assessment
            print(f"\n✨ PERFORMANCE ASSESSMENT:")
            if p95 < 50 and p99 < 200 and success_rate > 99:
                print(f"  ✅ EXCELLENT: Production ready!")
                print(f"     - p95 < 50ms: Instant user experience")
                print(f"     - p99 < 200ms: Rare slow queries acceptable")
                print(f"     - Success rate > 99%: Highly reliable")
            elif p95 < 100 and p99 < 500:
                print(f"  ✅ GOOD: Acceptable performance")
                print(f"     - Room for optimization")
            else:
                print(f"  ⚠️  NEEDS IMPROVEMENT:")
                if p95 >= 100:
                    print(f"     - p95 too high: Add more caching")
                if p99 >= 500:
                    print(f"     - p99 too high: Optimize slow queries")
                if success_rate < 99:
                    print(f"     - Too many failures: Check error handling")
        
        # Error details
        if self.results['errors']:
            print(f"\n❌ ERRORS ({len(self.results['errors'])} total):")
            error_types = {}
            for error in self.results['errors'][:10]:  # Show first 10
                error_key = error.get('status', 'unknown')
                error_types[error_key] = error_types.get(error_key, 0) + 1
            
            for error_type, count in error_types.items():
                print(f"  {error_type}: {count} occurrences")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if self.results['response_times']:
            avg = statistics.mean(self.results['response_times'])
            if avg > 100:
                print(f"  - Enable L1/L2 caching to reduce average latency")
                print(f"  - Current average ({avg:.1f}ms) suggests cache misses")
            if p99 > 500:
                print(f"  - Add database indexes for slow queries")
                print(f"  - Consider query result pagination")
            if success_rate < 95:
                print(f"  - Add retry logic with exponential backoff")
                print(f"  - Implement circuit breaker pattern")
            if throughput < 100:
                print(f"  - Increase connection pool size")
                print(f"  - Add horizontal scaling (multiple workers)")
        
        print(f"\n{'='*80}\n")
    
    async def run_cache_warmup_test(self):
        """
        Test cache effectiveness by:
        1. Cold queries (first access)
        2. Warm queries (cached access)
        3. Compare performance
        """
        print(f"\n{'='*80}")
        print(f"CACHE WARMUP TEST")
        print(f"{'='*80}\n")
        
        connector = aiohttp.TCPConnector(limit=50)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Phase 1: Cold queries (fill cache)
            print("❄️  Phase 1: Cold queries (filling cache)...")
            cold_times = []
            for app_id in self.app_ids[:10]:  # Test first 10
                result = await self.test_sqlite_get_application(session, app_id)
                cold_times.append(result['duration_ms'])
                await asyncio.sleep(0.1)  # Small delay
            
            cold_avg = statistics.mean(cold_times)
            print(f"   Average cold query time: {cold_avg:.2f}ms")
            
            # Phase 2: Warm queries (from cache)
            print("\n🔥 Phase 2: Warm queries (from cache)...")
            warm_times = []
            for app_id in self.app_ids[:10]:  # Same apps
                result = await self.test_sqlite_get_application(session, app_id)
                warm_times.append(result['duration_ms'])
                await asyncio.sleep(0.1)
            
            warm_avg = statistics.mean(warm_times)
            print(f"   Average warm query time: {warm_avg:.2f}ms")
            
            # Analysis
            speedup = cold_avg / warm_avg if warm_avg > 0 else 1
            print(f"\n✨ CACHE EFFECTIVENESS:")
            print(f"   Cold average: {cold_avg:.2f}ms")
            print(f"   Warm average: {warm_avg:.2f}ms")
            print(f"   Speedup:      {speedup:.1f}x {'✅' if speedup > 2 else '⚠️'}")
            
            if speedup > 5:
                print(f"   🎉 EXCELLENT: Cache provides significant speedup!")
            elif speedup > 2:
                print(f"   ✅ GOOD: Cache is working effectively")
            else:
                print(f"   ⚠️  Cache may not be properly configured")


async def main():
    """Run comprehensive load tests"""
    tester = LoadTester()
    
    # Test 1: Cache warmup
    await tester.run_cache_warmup_test()
    
    # Reset results
    tester.results = {
        'total_requests': 0,
        'successful': 0,
        'failed': 0,
        'response_times': [],
        'errors': []
    }
    
    # Test 2: Moderate load (100 users × 10 requests = 1000 total)
    await tester.run_load_test(num_users=100, requests_per_user=10)
    
    # Test 3: High load (200 users × 20 requests = 4000 total)
    print("\n\n🔥 EXTREME LOAD TEST...")
    tester.results = {
        'total_requests': 0,
        'successful': 0,
        'failed': 0,
        'response_times': [],
        'errors': []
    }
    await tester.run_load_test(num_users=200, requests_per_user=20)


if __name__ == "__main__":
    print(f"""
{'='*80}
SOCIAL SUPPORT SYSTEM - LOAD TESTING SUITE
{'='*80}

This script will test system performance under heavy load:
- 100+ concurrent users
- 1000+ requests total
- Multi-database operations (SQLite, ChromaDB, NetworkX)
- Cache effectiveness measurement

Performance targets:
- p95 latency: <50ms (cached)
- p99 latency: <200ms (uncached)
- Success rate: >99%
- Throughput: >100 req/s

Starting tests...
    """)
    
    asyncio.run(main())
