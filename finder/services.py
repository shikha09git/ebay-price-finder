"""
eBay API integration service with demo data fallback.
"""
import base64
import os
import random
import statistics
from decimal import Decimal
from typing import Optional

import requests
from django.conf import settings

try:
    from google.cloud import vision
    from google.oauth2 import service_account
except ImportError:
    vision = None
    service_account = None


class EbayAPIService:
    
    
    OAUTH_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    BROWSE_API_URL = "https://api.ebay.com/buy/browse/v1"
    
    def __init__(self):
        self.app_id = getattr(settings, 'EBAY_APP_ID', '')
        self.cert_id = getattr(settings, 'EBAY_CERT_ID', '')
        self._access_token = None
    
    def _get_oauth_token(self) -> Optional[str]:
        """Get OAuth application token from eBay."""
        if not self.app_id or not self.cert_id:
            return None
            
        credentials = f"{self.app_id}:{self.cert_id}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }
        
        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        }
        
        try:
            response = requests.post(self.OAUTH_TOKEN_URL, headers=headers, data=data)
            response.raise_for_status()
            return response.json().get("access_token")
        except requests.RequestException:
            return None
    
    @property
    def access_token(self) -> Optional[str]:
        if not self._access_token:
            self._access_token = self._get_oauth_token()
        return self._access_token
    
    def search_products(self, keywords: str, limit: int = 50) -> list[dict]:
        """Search for products on eBay by keywords."""
        if not self.access_token:
            return self._get_demo_results(keywords)
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            "Content-Type": "application/json"
        }
        
        params = {
            "q": keywords,
            "limit": min(limit, 200),
            "filter": "buyingOptions:{FIXED_PRICE}"
        }
        
        try:
            response = requests.get(
                f"{self.BROWSE_API_URL}/item_summary/search",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            items = response.json().get("itemSummaries", [])
            return self._parse_items(items)
        except requests.RequestException:
            return self._get_demo_results(keywords)
    
    def _parse_items(self, items: list) -> list[dict]:
        results = []
        for item in items:
            price_info = item.get("price", {})
            results.append({
                "title": item.get("title", ""),
                "description": item.get("shortDescription", ""),
                "price": Decimal(price_info.get("value", "0")),
                "currency": price_info.get("currency", "USD"),
                "seller": item.get("seller", {}).get("username", ""),
                "item_url": item.get("itemWebUrl", ""),
                "image_url": item.get("image", {}).get("imageUrl", ""),
                "condition": item.get("condition", ""),
            })
        return results
    
    def _get_demo_results(self, keywords: str) -> list[dict]:
       
        base_prices = {
            "oil": 25.99, "bottle": 15.99, "motor": 35.99,
            "synthetic": 45.99, "mobil": 39.99, "castrol": 37.99
        }
        
        keywords_lower = keywords.lower()
        base_price = 29.99
        for key, price in base_prices.items():
            if key in keywords_lower:
                base_price = price
                break
        
        demo_sellers = [
            "auto_parts_direct", "motor_supplies_usa", "oilchange_pro",
            "carcare_warehouse", "best_auto_deals", "performance_fluids",
            "discount_auto_store", "prime_automotive", "value_auto_parts",
            "super_car_supplies", "mechanic_depot", "garage_essentials"
        ]
        
        results = []
        for i in range(12):
            price_variation = random.uniform(0.7, 1.4)
            price = round(base_price * price_variation, 2)
            
            results.append({
                "title": f"{keywords} - {random.choice(['Brand New', 'Premium', 'Best Seller', 'Top Rated'])} - Listing {i+1}",
                "description": f"{keywords} demo listing with standard features.",
                "price": Decimal(str(price)),
                "currency": "USD",
                "seller": random.choice(demo_sellers),
                "item_url": f"https://www.ebay.com/itm/demo{i+1}",
                "image_url": "",
                "condition": random.choice(["New", "New", "New", "Like New", "Used"]),
            })
        
        return sorted(results, key=lambda x: x["price"])


class ImageRecognitionService:
    
    
    def __init__(self) -> None:
        self._client = None
        self._enabled = False

        if vision is None or service_account is None:
            return

        credentials_path = (
            getattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS', '')
            or os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
        )
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            self._client = vision.ImageAnnotatorClient(credentials=credentials)
            self._enabled = True

    def recognize_product(self, image_path: str) -> tuple[str, list[str], str]:
        """Return primary label, labels list, and optional web label."""
        if not self._enabled:
            primary = self._fallback_keywords(image_path)
            return primary, [primary], ""

        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = self._client.annotate_image({
            "image": image,
            "features": [
                {"type": vision.Feature.Type.LABEL_DETECTION, "max_results": 7},
                {"type": vision.Feature.Type.WEB_DETECTION, "max_results": 3},
            ],
        })

        if response.error.message:
            primary = self._fallback_keywords(image_path)
            return primary, [primary], ""

        labels = [label.description for label in response.label_annotations]
        web_label = ""
        if response.web_detection and response.web_detection.best_guess_labels:
            web_label = response.web_detection.best_guess_labels[0].label

        primary = web_label or (labels[0] if labels else "product")
        if primary and primary not in labels:
            labels.insert(0, primary)

        return primary, labels, web_label

    def _fallback_keywords(self, image_path: str) -> str:
        filename = os.path.basename(image_path)
        name = os.path.splitext(filename)[0]
        keywords = name.replace("_", " ").replace("-", " ")
        return keywords if keywords else "product"


class PriceSuggestionService:
    
    
    @staticmethod
    def calculate_suggestion(prices: list[Decimal]) -> dict:
        if not prices:
            return {
                "min_price": Decimal("0"),
                "max_price": Decimal("0"),
                "average_price": Decimal("0"),
                "median_price": Decimal("0"),
                "suggested_price": Decimal("0"),
                "total_listings": 0,
            }
        
        float_prices = [float(p) for p in prices]
        
        min_price = min(float_prices)
        max_price = max(float_prices)
        average_price = statistics.mean(float_prices)
        median_price = statistics.median(float_prices)
        
        # Price 5% below median for competitive edge
        suggested = median_price * 0.95
        if suggested < min_price:
            suggested = min_price
        if suggested > max_price * 0.9:
            suggested = max_price * 0.9
        
        return {
            "min_price": Decimal(str(round(min_price, 2))),
            "max_price": Decimal(str(round(max_price, 2))),
            "average_price": Decimal(str(round(average_price, 2))),
            "median_price": Decimal(str(round(median_price, 2))),
            "suggested_price": Decimal(str(round(suggested, 2))),
            "total_listings": len(prices),
        }
