#!/usr/bin/env python3
"""
Performance monitoring script for StepDaddyLiveHD
"""
import asyncio
import aiohttp
import time
import statistics
import sys
from typing import List, Dict

async def test_endpoint(session: aiohttp.ClientSession, url: str, name: str) -> Dict:
    """Test a single endpoint and return performance metrics"""
    start_time = time.time()
    try:
        async with session.get(url) as response:
            response_time = time.time() - start_time
            return {
                "name": name,
                "url": url,
                "status": response.status,
                "response_time": response_time,
                "success": response.status == 200
            }
    except Exception as e:
        response_time = time.time() - start_time
        return {
            "name": name,
            "url": url,
            "status": "ERROR",
            "response_time": response_time,
            "success": False,
            "error": str(e)
        }

async def load_test(base_url: str, endpoint: str, concurrent_requests: int = 10, duration: int = 30):
    """Perform a load test on a specific endpoint"""
    print(f"\n🔍 Load testing {endpoint} with {concurrent_requests} concurrent requests for {duration} seconds...")
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        tasks = []
        results = []
        
        # Create tasks for the duration
        while time.time() - start_time < duration:
            # Create concurrent requests
            batch_tasks = []
            for i in range(concurrent_requests):
                task = test_endpoint(session, f"{base_url}{endpoint}", f"request_{i}")
                batch_tasks.append(task)
            
            # Wait for batch to complete
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend([r for r in batch_results if not isinstance(r, Exception)])
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        # Analyze results
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            print(f"✅ Successful requests: {len(successful_requests)}")
            print(f"❌ Failed requests: {len(failed_requests)}")
            print(f"📊 Response times:")
            print(f"   Average: {statistics.mean(response_times):.3f}s")
            print(f"   Median: {statistics.median(response_times):.3f}s")
            print(f"   Min: {min(response_times):.3f}s")
            print(f"   Max: {max(response_times):.3f}s")
            print(f"   Requests per second: {len(successful_requests) / duration:.1f}")
        else:
            print("❌ No successful requests")
        
        if failed_requests:
            print(f"🔍 Failed request errors:")
            for error in set([r.get("error", "Unknown error") for r in failed_requests]):
                count = len([r for r in failed_requests if r.get("error") == error])
                print(f"   {error}: {count} times")

async def main():
    """Main monitoring function"""
    if len(sys.argv) < 2:
        print("Usage: python monitor_performance.py <base_url>")
        print("Example: python monitor_performance.py http://localhost:3000")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    
    print("🚀 StepDaddyLiveHD Performance Monitor")
    print("=" * 50)
    
    # Test basic endpoints
    endpoints = [
        ("/ping", "Health Check"),
        ("/health", "Health Status"),
        ("/playlist.m3u8", "Playlist"),
    ]
    
    async with aiohttp.ClientSession() as session:
        print("\n📋 Basic Endpoint Tests:")
        for endpoint, name in endpoints:
            result = await test_endpoint(session, f"{base_url}{endpoint}", name)
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {name}: {result['response_time']:.3f}s (Status: {result['status']})")
            if not result["success"] and "error" in result:
                print(f"   Error: {result['error']}")
    
    # Load tests
    await load_test(base_url, "/ping", concurrent_requests=20, duration=10)
    await load_test(base_url, "/playlist.m3u8", concurrent_requests=10, duration=15)
    
    print("\n🎯 Performance Recommendations:")
    print("1. If response times are high (>2s), consider:")
    print("   - Increasing WORKERS environment variable")
    print("   - Checking network connectivity to daddylive servers")
    print("   - Monitoring system resources (CPU, memory)")
    print("2. If many requests fail, check:")
    print("   - Backend service status")
    print("   - Rate limiting configuration")
    print("   - External API availability")
    print("3. For optimal performance:")
    print("   - Use WORKERS=4-8 for most deployments")
    print("   - Monitor cache hit rates")
    print("   - Consider using a CDN for static content")

if __name__ == "__main__":
    asyncio.run(main()) 