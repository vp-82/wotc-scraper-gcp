import logging
import os
from unittest.mock import MagicMock, patch

import pytest
from google.cloud import firestore

from src.article_handler import ArticleLink
from src.link_scraper import FirestoreArticleLinkAdapter, Scraper

logger = logging.getLogger(__name__)


@pytest.fixture
def test_db():
    if os.getenv("CI_PIPELINE") == "true":
        # We're in the CI environment, the GOOGLE_APPLICATION_CREDENTIALS
        # environment variable is already set in the workflow file.
        pass
    else:
        # We're in the local development environment
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./tests/mtg-scraper-385015-aad053a61746.json"


    db = firestore.Client()
    return db.collection('mtg_scraper_test_collection')

@pytest.mark.integration
def test_with_real_webpage(test_db):
    logger.info("Starting integration test with real webpage...")
    adapter = FirestoreArticleLinkAdapter(test_db)
    scraper = Scraper(adapter)

    logger.info("Scraping links...")
    scraper.scrape_links(1, 2)

    logger.info("Storing links in the database...")
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

    logger.info("Cleaning up the database after test...")
    docs = test_db.stream()
    i = 0
    for doc in docs:
        doc.reference.delete()
        i += 1

    # Final test: check if the number of links matches with the number of cleaned up documents
    assert len(links) == i
    logger.info("Integration test completed successfully.")




