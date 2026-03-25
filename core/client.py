import httpx
import asyncio
import time
from typing import Optional, Dict, List, Any

class BazosClient:
    BASE_URL = "https://www.bazos.cz/api/v1"
    
    def __init__(self, user_agent: str = "bazos/2.12.1 (cz.ackee.bazos; build:3582; android 14; model:Pixel) okhttp/4.8.1", device_id: str = "12345678", request_delay: float = 1.5):
        self.headers = {
            "User-Agent": user_agent,
            "X-DeviceID": device_id,
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=15.0)
        self.request_delay = request_delay
        self._last_request_time = 0.0
        self._lock = asyncio.Lock()
        
    async def _wait_rate_limit(self):
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self.request_delay:
                await asyncio.sleep(self.request_delay - elapsed)
            self._last_request_time = time.time()
    
    async def close(self):
        await self.client.aclose()
        
    async def search_ads(self, query: str = "", section: str = "", offset: int = 0, limit: int = 20, **kwargs) -> Dict[str, Any]:
        """
        Search for ads.
        kwargs can include: price_from, price_to, sort (date, price_asc, price_desc, distance), latitude, longitude
        """
        url = f"{self.BASE_URL}/ads.php"
        params = {
            "query": query,
            "section": section,
            "offset": offset,
            "limit": limit
        }
        params.update(kwargs)
        
        # Remove empty params
        params = {k: v for k, v in params.items() if v != ""}
        
        await self._wait_rate_limit()
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
        
    async def get_ad_detail(self, ad_id: str) -> Dict[str, Any]:
        """
        Get full details of a specific ad by ID.
        """
        url = f"{self.BASE_URL}/ad-detail-2.php"
        params = {
            "ad_id": ad_id,
            "edit": "false"
        }
        
        await self._wait_rate_limit()
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        return response.json()

# Simple testing block if run directly
if __name__ == "__main__":
    async def test():
        client = BazosClient()
        try:
            print("Fetching ads for 'macbook m1'...")
            res = await client.search_ads(query="macbook m1", section="PC", limit=5)
            # Find the actual structured data or just print top-level keys
            print("Response keys:", res.keys())
            
            # Print first result if available
            ads = res if isinstance(res, list) else res.get("ads", [])
            if ads:
                print("First ad title:", ads[0].get("title"))
                print("First ad ID:", ads[0].get("id"))
                if ads[0].get("id"):
                    # Fetch detail of first ad
                    print(f"Fetching detail for ad {ads[0].get('id')}...")
                    detail = await client.get_ad_detail(ads[0].get("id"))
                    print("Detail keys:", detail.keys())
            else:
                print(f"Full response: {res}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await client.close()
            
    asyncio.run(test())
