"""
test_link_scraper.py: This module contains the integration tests for the Scraper class
which is responsible for scraping article links from a webpage and storing them in a Firestore database.
"""

import logging
import os

import pytest
from google.cloud import firestore

from src.article_handler import ArticleLink
from src.link_scraper import FirestoreArticleLinkAdapter, Scraper

logger = logging.getLogger(__name__)


@pytest.fixture(name="test_db")
def fixture_test_db():
    """
    Pytest fixture for setting up the Firestore database client.

    Depending on the environment (CI or local), it sets the appropriate
    Google application credentials and returns a reference to the Firestore collection.

    Returns:
        google.cloud.firestore_v1.collection.CollectionReference:
        A reference to the Firestore collection used for testing.
    """
    if os.getenv("CI_PIPELINE") == "true":
        # We're in the CI environment, the GOOGLE_APPLICATION_CREDENTIALS
        # environment variable is already set in the workflow file.
        pass
    else:
        # We're in the local development environment
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./tests/mtg-scraper-385015-aad053a61746.json"

    # pylint: disable=invalid-name
    db = firestore.Client()
    return db.collection('mtg_scraper_test_collection')


@pytest.mark.integration
def test_with_real_webpage(test_db):
    """
    Integration test for the Scraper class with a real webpage.

    This test scrapes links from a real webpage, stores them in a Firestore database,
    and checks if the number of stored links is greater than zero. After the test,
    it cleans up the database and checks if the number of deleted documents matches
    with the number of stored links.

    Args:
        test_db (google.cloud.firestore_v1.collection.CollectionReference):
        A reference to the Firestore collection used for testing.
    """
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
