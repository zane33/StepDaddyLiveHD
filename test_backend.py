#!/usr/bin/env python3
"""
Simple test script to verify backend functionality
"""
import asyncio
import httpx
import sys

async def test_backend():
    """Test the backend endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing backend endpoints...")
    
    async with httpx.AsyncClient() as client:
        # Test ping endpoint
        try:
            response = await client.get(f"{base_url}/ping")
            print(f"✅ Ping endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Channels count: {data.get('channels_count', 'N/A')}")
        except Exception as e:
            print(f"❌ Ping endpoint failed: {e}")
            return False
        
        # Test playlist endpoint
        try:
            response = await client.get(f"{base_url}/playlist.m3u8")
            print(f"✅ Playlist endpoint: {response.status_code}")
        except Exception as e:
            print(f"❌ Playlist endpoint failed: {e}")
            return False
    
    print("✅ Backend tests passed!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_backend())
    sys.exit(0 if success else 1) 