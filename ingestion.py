import feedparser
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import quote
from bs4 import BeautifulSoup
from config import CATEGORY_KEYWORDS, GOOGLE_NEWS_RSS

def clean_html(html):
    if not html:
        return ""
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)

def ingest_raw_news():
    articles = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            after_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            query = quote(f"{keyword} after:{after_date}")
            rss_url = GOOGLE_NEWS_RSS.format(query)
            
            feed = feedparser.parse(rss_url)
            for item in feed.entries:
                articles.append({
                    "title": item.get("title", ""),
                    "description": clean_html(item.get("description", "")),
                    "url": item.get("link", ""),
                    "source": item.get("source", {}).get("title", ""),
                    "published_date": item.get("published", ""),
                    "category": category
                })

    df = pd.DataFrame(articles)
    if df.empty:
        return df

    # Drop duplicate exact URLs to protect specific categorizations
    df.drop_duplicates(subset="url", inplace=True)
    return df