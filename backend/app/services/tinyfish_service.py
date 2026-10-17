import logging
import httpx
from typing import Optional, Dict, Any
from app.config import TINYFISH_API_KEY

logger = logging.getLogger(__name__)

class TinyFishService:
    def __init__(self):
        self.api_key = TINYFISH_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def search_product(self, query: str) -> Optional[str]:
        """Search for a product on quick-commerce via TinySearch"""
        if not self.api_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://api.search.tinyfish.ai/search",
                    headers=self.headers,
                    json={"query": f"{query} Blinkit Zepto ingredients nutritional information", "limit": 3}
                )
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results", [])
                    if results:
                        return results[0].get("url")
        except Exception as e:
            logger.warning(f"TinySearch query failed: {e}")
        return None

    async def fetch_product_details(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch full product page data via TinyFetch"""
        if not self.api_key or not url:
            return None
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    "https://api.fetch.tinyfish.ai/fetch",
                    headers=self.headers,
                    json={"url": url}
                )
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.warning(f"TinyFetch content extraction failed: {e}")
        return None

    async def search_and_fetch_bop(self, product_name: str) -> Optional[str]:
        """Convenience method to search and extract back-of-pack data"""
        url = await self.search_product(product_name)
        if url:
            data = await self.fetch_product_details(url)
            if data:
                return data.get("content", "") or data.get("text", "")
        return None

tinyfish_service = TinyFishService()
