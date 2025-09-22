"""
Performance testing script for CustomerCareGPT scaling validation
"""

import asyncio
import aiohttp
import time
import json
import random
from typing import List, Dict, Any
from datetime import datetime
import statistics
import argparse

class PerformanceTester:
    """Performance testing for CustomerCareGPT"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            'rag_queries': [],
            'document_uploads': [],
            'health_checks': [],
            'concurrent_users': []
        }
    
    async def test_rag_performance(
        self, 
        num_queries: int = 1000,
        concurrent_users: int = 50,
        workspace_id: str = "test_workspace"
    ):
        """Test RAG query performance"""
        print(f"Testing RAG performance: {num_queries} queries with {concurrent_users} concurrent users")
        
        queries = [
            "What is your return policy?",
            "How do I contact customer support?",
            "What are your business hours?",
            "How can I track my order?",
            "What payment methods do you accept?",
            "How do I cancel my subscription?",
            "What is your privacy policy?",
            "How do I update my account information?",
            "What are your shipping options?",
            "How do I reset my password?"
        ]
        
        async def execute_rag_query(session, query_id):
            query = random.choice(queries)
            start_time = time.time()
            
            try:
                async with session.post(
                    f"{self.base_url}/api/v1/rag/query",
                    json={
                        "workspace_id": workspace_id,
                        "query": query
                    },
                    headers={"Authorization": "Bearer test_token"}
                ) as response:
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'query_id': query_id,
                            'query': query,
                            'response_time': response_time,
                            'status': 'success',
                            'answer_length': len(data.get('answer', '')),
                            'sources_count': len(data.get('sources', []))
                        }
                    else:
                        return {
                            'query_id': query_id,
                            'query': query,
                            'response_time': response_time,
                            'status': 'error',
                            'error_code': response.status
                        }
            except Exception as e:
                end_time = time.time()
                return {
                    'query_id': query_id,
                    'query': query,
                    'response_time': end_time - start_time,
                    'status': 'error',
                    'error': str(e)
                }
        
        # Execute queries in batches
        batch_size = concurrent_users
        all_results = []
        
        for batch_start in range(0, num_queries, batch_size):
            batch_end = min(batch_start + batch_size, num_queries)
            batch_queries = range(batch_start, batch_end)
            
            async with aiohttp.ClientSession() as session:
                tasks = [execute_rag_query(session, i) for i in batch_queries]
                batch_results = await asyncio.gather(*tasks)
                all_results.extend(batch_results)
            
            print(f"Completed batch {batch_start//batch_size + 1}/{(num_queries + batch_size - 1)//batch_size}")
        
        self.results['rag_queries'] = all_results
        return self._analyze_rag_results(all_results)
    
    def _analyze_rag_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze RAG query results"""
        successful_results = [r for r in results if r['status'] == 'success']
        failed_results = [r for r in results if r['status'] == 'error']
        
        if not successful_results:
            return {
                'total_queries': len(results),
                'successful_queries': 0,
                'failed_queries': len(failed_results),
                'success_rate': 0.0,
                'avg_response_time': 0.0,
                'p95_response_time': 0.0,
                'p99_response_time': 0.0
            }
        
        response_times = [r['response_time'] for r in successful_results]
        
        return {
            'total_queries': len(results),
            'successful_queries': len(successful_results),
            'failed_queries': len(failed_results),
            'success_rate': len(successful_results) / len(results),
            'avg_response_time': statistics.mean(response_times),
            'median_response_time': statistics.median(response_times),
            'p95_response_time': self._percentile(response_times, 95),
            'p99_response_time': self._percentile(response_times, 99),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'avg_answer_length': statistics.mean([r['answer_length'] for r in successful_results]),
            'avg_sources_count': statistics.mean([r['sources_count'] for r in successful_results])
        }
    
    async def test_document_upload_performance(
        self, 
        num_uploads: int = 100,
        concurrent_uploads: int = 10
    ):
        """Test document upload performance"""
        print(f"Testing document upload performance: {num_uploads} uploads with {concurrent_uploads} concurrent uploads")
        
        # Create test document content
        test_content = "This is a test document for performance testing. " * 100
        
        async def upload_document(session, upload_id):
            start_time = time.time()
            
            try:
                data = aiohttp.FormData()
                data.add_field('file', test_content, filename=f'test_doc_{upload_id}.txt', content_type='text/plain')
                
                async with session.post(
                    f"{self.base_url}/api/v1/documents/upload",
                    data=data,
                    headers={"Authorization": "Bearer test_token"}
                ) as response:
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'upload_id': upload_id,
                            'response_time': response_time,
                            'status': 'success',
                            'document_id': data.get('document_id'),
                            'job_id': data.get('job_id')
                        }
                    else:
                        return {
                            'upload_id': upload_id,
                            'response_time': response_time,
                            'status': 'error',
                            'error_code': response.status
                        }
            except Exception as e:
                end_time = time.time()
                return {
                    'upload_id': upload_id,
                    'response_time': end_time - start_time,
                    'status': 'error',
                    'error': str(e)
                }
        
        # Execute uploads in batches
        batch_size = concurrent_uploads
        all_results = []
        
        for batch_start in range(0, num_uploads, batch_size):
            batch_end = min(batch_start + batch_size, num_uploads)
            batch_uploads = range(batch_start, batch_end)
            
            async with aiohttp.ClientSession() as session:
                tasks = [upload_document(session, i) for i in batch_uploads]
                batch_results = await asyncio.gather(*tasks)
                all_results.extend(batch_results)
            
            print(f"Completed upload batch {batch_start//batch_size + 1}/{(num_uploads + batch_size - 1)//batch_size}")
        
        self.results['document_uploads'] = all_results
        return self._analyze_upload_results(all_results)
    
    def _analyze_upload_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze document upload results"""
        successful_results = [r for r in results if r['status'] == 'success']
        failed_results = [r for r in results if r['status'] == 'error']
        
        if not successful_results:
            return {
                'total_uploads': len(results),
                'successful_uploads': 0,
                'failed_uploads': len(failed_results),
                'success_rate': 0.0,
                'avg_response_time': 0.0
            }
        
        response_times = [r['response_time'] for r in successful_results]
        
        return {
            'total_uploads': len(results),
            'successful_uploads': len(successful_results),
            'failed_uploads': len(failed_results),
            'success_rate': len(successful_results) / len(results),
            'avg_response_time': statistics.mean(response_times),
            'median_response_time': statistics.median(response_times),
            'p95_response_time': self._percentile(response_times, 95),
            'p99_response_time': self._percentile(response_times, 99),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times)
        }
    
    async def test_health_check_performance(self, num_checks: int = 100):
        """Test health check performance"""
        print(f"Testing health check performance: {num_checks} checks")
        
        async def check_health(session, check_id):
            start_time = time.time()
            
            try:
                async with session.get(f"{self.base_url}/health") as response:
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    return {
                        'check_id': check_id,
                        'response_time': response_time,
                        'status': 'success' if response.status == 200 else 'error',
                        'status_code': response.status
                    }
            except Exception as e:
                end_time = time.time()
                return {
                    'check_id': check_id,
                    'response_time': end_time - start_time,
                    'status': 'error',
                    'error': str(e)
                }
        
        async with aiohttp.ClientSession() as session:
            tasks = [check_health(session, i) for i in range(num_checks)]
            results = await asyncio.gather(*tasks)
        
        self.results['health_checks'] = results
        return self._analyze_health_results(results)
    
    def _analyze_health_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze health check results"""
        successful_results = [r for r in results if r['status'] == 'success']
        response_times = [r['response_time'] for r in successful_results]
        
        return {
            'total_checks': len(results),
            'successful_checks': len(successful_results),
            'success_rate': len(successful_results) / len(results),
            'avg_response_time': statistics.mean(response_times) if response_times else 0.0,
            'median_response_time': statistics.median(response_times) if response_times else 0.0,
            'p95_response_time': self._percentile(response_times, 95) if response_times else 0.0,
            'p99_response_time': self._percentile(response_times, 99) if response_times else 0.0
        }
    
    async def test_concurrent_users(
        self, 
        num_users: int = 300,
        queries_per_user: int = 10
    ):
        """Test concurrent user simulation"""
        print(f"Testing concurrent users: {num_users} users with {queries_per_user} queries each")
        
        async def simulate_user(user_id):
            user_results = []
            
            async with aiohttp.ClientSession() as session:
                for query_id in range(queries_per_user):
                    start_time = time.time()
                    
                    try:
                        async with session.post(
                            f"{self.base_url}/api/v1/rag/query",
                            json={
                                "workspace_id": f"user_{user_id}_workspace",
                                "query": f"User {user_id} query {query_id}"
                            },
                            headers={"Authorization": "Bearer test_token"}
                        ) as response:
                            end_time = time.time()
                            response_time = end_time - start_time
                            
                            user_results.append({
                                'user_id': user_id,
                                'query_id': query_id,
                                'response_time': response_time,
                                'status': 'success' if response.status == 200 else 'error',
                                'status_code': response.status
                            })
                    except Exception as e:
                        end_time = time.time()
                        user_results.append({
                            'user_id': user_id,
                            'query_id': query_id,
                            'response_time': end_time - start_time,
                            'status': 'error',
                            'error': str(e)
                        })
            
            return user_results
        
        # Simulate users in batches to avoid overwhelming the system
        batch_size = 50
        all_results = []
        
        for batch_start in range(0, num_users, batch_size):
            batch_end = min(batch_start + batch_size, num_users)
            batch_users = range(batch_start, batch_end)
            
            tasks = [simulate_user(user_id) for user_id in batch_users]
            batch_results = await asyncio.gather(*tasks)
            
            # Flatten results
            for user_results in batch_results:
                all_results.extend(user_results)
            
            print(f"Completed user batch {batch_start//batch_size + 1}/{(num_users + batch_size - 1)//batch_size}")
        
        self.results['concurrent_users'] = all_results
        return self._analyze_concurrent_results(all_results)
    
    def _analyze_concurrent_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze concurrent user results"""
        successful_results = [r for r in results if r['status'] == 'success']
        response_times = [r['response_time'] for r in successful_results]
        
        # Group by user
        user_stats = {}
        for result in results:
            user_id = result['user_id']
            if user_id not in user_stats:
                user_stats[user_id] = {'total': 0, 'successful': 0, 'response_times': []}
            
            user_stats[user_id]['total'] += 1
            if result['status'] == 'success':
                user_stats[user_id]['successful'] += 1
                user_stats[user_id]['response_times'].append(result['response_time'])
        
        user_success_rates = [stats['successful'] / stats['total'] for stats in user_stats.values()]
        user_avg_response_times = [statistics.mean(stats['response_times']) for stats in user_stats.values() if stats['response_times']]
        
        return {
            'total_queries': len(results),
            'successful_queries': len(successful_results),
            'success_rate': len(successful_results) / len(results),
            'unique_users': len(user_stats),
            'avg_user_success_rate': statistics.mean(user_success_rates) if user_success_rates else 0.0,
            'avg_response_time': statistics.mean(response_times) if response_times else 0.0,
            'median_response_time': statistics.median(response_times) if response_times else 0.0,
            'p95_response_time': self._percentile(response_times, 95) if response_times else 0.0,
            'p99_response_time': self._percentile(response_times, 99) if response_times else 0.0,
            'avg_user_response_time': statistics.mean(user_avg_response_times) if user_avg_response_times else 0.0
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def run_full_test_suite(self):
        """Run complete performance test suite"""
        print("Starting CustomerCareGPT Performance Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test 1: Health checks
        print("\n1. Health Check Performance Test")
        health_results = await self.test_health_check_performance(100)
        self._print_results("Health Checks", health_results)
        
        # Test 2: RAG queries
        print("\n2. RAG Query Performance Test")
        rag_results = await self.test_rag_performance(1000, 50)
        self._print_results("RAG Queries", rag_results)
        
        # Test 3: Document uploads
        print("\n3. Document Upload Performance Test")
        upload_results = await self.test_document_upload_performance(100, 10)
        self._print_results("Document Uploads", upload_results)
        
        # Test 4: Concurrent users
        print("\n4. Concurrent User Performance Test")
        concurrent_results = await self.test_concurrent_users(300, 10)
        self._print_results("Concurrent Users", concurrent_results)
        
        total_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("PERFORMANCE TEST SUMMARY")
        print("=" * 60)
        print(f"Total test time: {total_time:.2f} seconds")
        print(f"RAG success rate: {rag_results['success_rate']:.2%}")
        print(f"RAG avg response time: {rag_results['avg_response_time']:.3f}s")
        print(f"Upload success rate: {upload_results['success_rate']:.2%}")
        print(f"Concurrent user success rate: {concurrent_results['success_rate']:.2%}")
        print(f"Concurrent user avg response time: {concurrent_results['avg_response_time']:.3f}s")
        
        # Performance assessment
        print("\nPERFORMANCE ASSESSMENT:")
        if (rag_results['success_rate'] >= 0.95 and 
            rag_results['avg_response_time'] <= 3.0 and
            concurrent_results['success_rate'] >= 0.90):
            print("✅ EXCELLENT: System can handle 300+ business owners with 5k customers")
        elif (rag_results['success_rate'] >= 0.90 and 
              rag_results['avg_response_time'] <= 5.0 and
              concurrent_results['success_rate'] >= 0.85):
            print("✅ GOOD: System can handle 200+ business owners with 3k customers")
        else:
            print("❌ NEEDS IMPROVEMENT: System needs optimization for target load")
        
        return {
            'health_checks': health_results,
            'rag_queries': rag_results,
            'document_uploads': upload_results,
            'concurrent_users': concurrent_results,
            'total_test_time': total_time
        }
    
    def _print_results(self, test_name: str, results: Dict[str, Any]):
        """Print test results"""
        print(f"\n{test_name} Results:")
        for key, value in results.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value}")


async def main():
    parser = argparse.ArgumentParser(description='CustomerCareGPT Performance Test')
    parser.add_argument('--base-url', default='http://localhost:8000', help='Base URL for the API')
    parser.add_argument('--rag-queries', type=int, default=1000, help='Number of RAG queries to test')
    parser.add_argument('--concurrent-users', type=int, default=50, help='Number of concurrent users for RAG test')
    parser.add_argument('--document-uploads', type=int, default=100, help='Number of document uploads to test')
    parser.add_argument('--concurrent-uploads', type=int, default=10, help='Number of concurrent uploads')
    parser.add_argument('--simulate-users', type=int, default=300, help='Number of users to simulate')
    parser.add_argument('--queries-per-user', type=int, default=10, help='Queries per simulated user')
    
    args = parser.parse_args()
    
    tester = PerformanceTester(args.base_url)
    
    # Run individual tests or full suite
    if args.rag_queries > 0:
        rag_results = await tester.test_rag_performance(args.rag_queries, args.concurrent_users)
        tester._print_results("RAG Queries", rag_results)
    
    if args.document_uploads > 0:
        upload_results = await tester.test_document_upload_performance(args.document_uploads, args.concurrent_uploads)
        tester._print_results("Document Uploads", upload_results)
    
    if args.simulate_users > 0:
        concurrent_results = await tester.test_concurrent_users(args.simulate_users, args.queries_per_user)
        tester._print_results("Concurrent Users", concurrent_results)
    
    # Run full test suite if no specific tests requested
    if args.rag_queries == 0 and args.document_uploads == 0 and args.simulate_users == 0:
        await tester.run_full_test_suite()


if __name__ == "__main__":
    asyncio.run(main())
