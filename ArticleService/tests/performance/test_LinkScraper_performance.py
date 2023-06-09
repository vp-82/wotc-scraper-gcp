import logging
import os
import time

import pytest
from google.cloud import firestore

from src.article_handler import ArticleLink
from src.link_scraper import FirestoreArticleLinkAdapter, Scraper

logger = logging.getLogger(__name__)

@pytest.fixture
def test_db():
    if os.getenv("CI") == "true":
        # We're in the CI environment, the GOOGLE_APPLICATION_CREDENTIALS
        # environment variable is already set in the workflow file.
        pass
    else:
        # We're in the local development environment
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./tests/mtg-scraper-385015-aad053a61746.json"


    db = firestore.Client()
    return db.collection('mtg_scraper_test_collection')

@pytest.mark.performance
def test_with_real_webpage(test_db):
    logger.info("Starting performance test with real webpage...")

    adapter = FirestoreArticleLinkAdapter(test_db)
    scraper = Scraper(adapter)

    logger.info("Scraping links...")
    start_time = time.time()  # Save the current time
    scraper.scrape_links(1, 10)
    elapsed_time = time.time() - start_time  # Calculate the elapsed time
    logger.info(f"Finished scraping links, it took {elapsed_time} seconds.")

    logger.info("Storing links in the database...")
    start_time = time.time()
    docs = test_db.stream()
    elapsed_time = time.time() - start_time
    logger.info(f"Stored links in the database, it took {elapsed_time} seconds.")
    
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
    start_time = time.time()
    docs = test_db.stream()
    i = 0
    for doc in docs:
        doc.reference.delete()
        i += 1
    elapsed_time = time.time() - start_time
    logger.info(f"Cleaned up the database after test, it took {elapsed_time} seconds.")

    # Final test: check if the number of links matches with the number of cleaned up documents
    assert len(links) == i
    logger.info("Integration test completed successfully.")