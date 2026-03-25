import asyncio
import os
from ai.filter import AIFilter
from core.client import BazosClient
from dotenv import load_dotenv

async def main():
    load_dotenv()
    print("Testing Agentic Flow...")
    ai = AIFilter()
    client = BazosClient()
    prompt = "I want to buy a Lifepo4 battery for a PV system under 20000 CZK"
    
    print(f"Parsing intent for: {prompt}")
    intent = await ai.parse_search_intent(prompt)
    print("Intent:", intent)
    
    query = intent.get("query", "")
    category = intent.get("category", "")
    
    print(f"Searching Bazos: {query} in {category}")
    res = await client.search_ads(query=query, section=category, limit=5)
    ads = res if isinstance(res, list) else res.get("ads", [])
    
    if ads:
        print(f"Evaluating {len(ads)} ads...")
        analyzed = await ai.evaluate_listings(ads, prompt)
        print("First analyzed ad description:", analyzed[0].get("ai_eval", {}).get("description"))
        print("First analyzed ad score:", analyzed[0].get("ai_eval", {}).get("score"))
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
