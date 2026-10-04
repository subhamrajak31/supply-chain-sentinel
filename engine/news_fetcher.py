import feedparser
import urllib.parse
from typing import List, Dict, Any

def fetch_supply_chain_news(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Fetches real-time supply chain news articles from Google News RSS feed 
    based on a targeted query string (e.g., "Taiwan port delay").
    
    Returns a list of structured dictionaries with article title, link, and publish date.
    """
    # URL encode the search query to safely handle spaces and special characters
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    print(f"📡 Querying RSS Feed for: '{query}'...")
    
    # Parse the RSS feed URL
    parsed_feed = feedparser.parse(rss_url)
    
    articles = []
    
    # Extract entries up to the specified max_results limit
    for entry in parsed_feed.entries[:max_results]:
        article_data = {
            "title": entry.get("title", "No Title"),
            "link": entry.get("link", ""),
            "published": entry.get("published", "Unknown Date"),
            "source": entry.get("source", {}).get("title", "Google News")
        }
        articles.append(article_data)
        
    return articles


if __name__ == "__main__":
    # Test our ingestion engine with supply chain queries targeting our active suppliers (Taiwan & Suez)
    test_queries = ["Taiwan port delay shipping", "Suez Canal maritime news"]
    
    for q in test_queries:
        results = fetch_supply_chain_news(q, max_results=3)
        print(f"\n--- Found {len(results)} Articles for '{q}' ---")
        for i, article in enumerate(results, start=1):
            print(f"{i}. {article['title']}")
            print(f"   Source: {article['source']} | Date: {article['published']}")
            print(f"   Link: {article['link']}\n")