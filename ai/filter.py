import os
import json
import re
import logging
from openai import AsyncOpenAI
from typing import Dict, List, Any

class AIFilter:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            # We don't want to crash immediately on import if key is missing, 
            # just print a warning or handle later.
            pass
            
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key or "dummy_key",
        )
        self.model = "google/gemini-2.5-flash" # Fast and good at JSON
        
    async def parse_search_intent(self, user_prompt: str, model: str = None) -> Dict[str, str]:
        """
        Parses a natural language prompt into a Bazos search query and category.
        """
        system_prompt = (
            "You are an AI assistant that extracts search intents for a classifieds website (Bazos.cz).\n"
            "Given a user's natural language request (in English or Czech), extract the optimal short search query (keywords only, in Czech, e.g. 'baterie 48v', 'lifepo4') and the best matching category code(s).\n"
            "Valid categories: AU (Auto), DE (Children), DU (Home/Garden), EL (Electronics), FO (Photography), HU (Music), KN (Books), MO (Mobile), MT (Motorcycles), NA (Furniture), OB (Clothing), PC (Computers), PR (Work), RE (Real Estate), SL (Services), SP (Sports), ST (Machinery), VS (Tickets), ZV (Animals), OS (Other).\n"
            "If the request is broad, include up to 3 relevant categories. If none fit perfectly, use an empty array.\n"
            "Respond ONLY with a raw JSON object. No markdown block. Keys: 'query' (string keywords), 'categories' (array of 2-letter codes or empty array)."
        )
        
        content = ""
        try:
            response = await self.client.chat.completions.create(
                model=model or self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            content = response.choices[0].message.content.strip()
            
            # Robust JSON extraction
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                content = match.group(0)
                
            return json.loads(content)
        except Exception as e:
            logging.error(f"Error parsing intent (Content: {content}): {e}")
            # Fallback naive keywords
            keywords = " ".join(user_prompt.split()[:3])
            return {"query": keywords, "categories": []} # fallback

    async def evaluate_listings(self, listings: List[Dict[str, Any]], criteria: str, model: str = None) -> List[Dict[str, Any]]:
        """
        Evaluate a list of Bazos listings against a natural language criteria.
        Returns the original listings enriched with AI evaluations.
        """
        if not listings:
            return []
            
        # Simplified listings to save tokens
        simplified = []
        for l in listings:
            simplified.append({
                "id": l.get("id"),
                "title": l.get("title"),
                "description": l.get("description", "")[:500], # truncated
                "price": l.get("price_formatted", l.get("price"))
            })
            
        system_prompt = (
            "You are an expert AI assistant that evaluates listings from a classifieds website. "
            "You will receive a user criteria and a JSON list of items. "
            "Respond ONLY with a valid JSON object containing a 'results' array. "
            "Each object inside 'results' must contain exactly these fields:\n"
            "- id: (string) the listing ID\n"
            "- meets_criteria: (boolean) whether it is a good match\n"
            "- description: (string) a clear description of what the listing is selling and why it matches or doesn't\n"
            "- score: (integer 1-10) how good the deal/match is\n"
        )
        
        user_prompt = f"Criteria: {criteria}\n\nListings to evaluate:\n{json.dumps(simplified)}"
        
        try:
            response = await self.client.chat.completions.create(
                model=model or self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            content = response.choices[0].message.content
            # Clean up markdown fencing if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
                
            ai_data = json.loads(content)
            results_list = ai_data.get("results", [])
            
            # Merge with original listings
            ai_map = {str(item.get("id")): item for item in results_list}
            
            enriched = []
            for l in listings:
                l_id = str(l.get("id"))
                l_copy = dict(l)
                if l_id in ai_map:
                    l_copy["ai_eval"] = ai_map[l_id]
                else:
                    l_copy["ai_eval"] = {"meets_criteria": False, "description": "AI parsing error", "score": 0}
                enriched.append(l_copy)
                
            return enriched
            
        except Exception as e:
            print(f"Error calling AI API or parsing response: {e}")
            return listings
