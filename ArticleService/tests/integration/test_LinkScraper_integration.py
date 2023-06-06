import pytest
from unittest.mock import patch, MagicMock
from google.cloud import firestore
import os

import sys
sys.path.append('src')

from LinkScraper import Scraper, FirestoreArticleLinkAdapter
from ArticleHandler import ArticleLink


@pytest.fixture
def test_db():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="./tests/mtg-scraper-385015-aad053a61746.json"
    # Assuming you have set the GOOGLE_APPLICATION_CREDENTIALS environment variable
    db = firestore.Client()
    return db.collection('mtg_scraper_test_collection')

@pytest.mark.integration
def test_with_real_webpage(test_db):
    adapter = FirestoreArticleLinkAdapter(test_db)
    scraper = Scraper(adapter)
    scraper.scrape_links(1, 2)
    # Clean up after the test by deleting all documents in the test collection
    docs = test_db.stream()
    
    links = []
    for doc in docs:
        data = doc.to_dict()
        if "url" in data and "link_added_at" in data:
            link = ArticleLink(
                link_url=data["url"],
                link_added_at=data["link_added_at"]
            )
            links.append(link)

    assert len(links) > 0
    
    # Clean up
    docs = test_db.stream()
    for doc in docs:
        doc.reference.delete()



