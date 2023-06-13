# test_firestore_article_link_adapter.py
"""
This module contains a set of tests for FirestoreArticleLinkAdapter, part of the article handler in an application.
The tests cover functionalities like saving a link, getting all links, getting a link by its hash, getting links within
a date range, and handling non-existent hashes.

Tests are designed to be run with pytest and use fixtures for setup. The Python logging module is used for logging test
events for easier debugging and test validation.
"""


import logging
from datetime import datetime
from unittest.mock import MagicMock, PropertyMock

import pytest

from src.article_handler import ArticleLink
from src.firestore_article_link_adapter import FirestoreArticleLinkAdapter

# Setup logger right below imports
logger = logging.getLogger(__name__)


@pytest.fixture(name="firestore_adapter")
def fixture_firestore_adapter():
    """
    Pytest fixture to set up a FirestoreArticleLinkAdapter instance
    with a mocked Firestore client, collection, and document.

    Returns:
        Tuple containing the FirestoreArticleLinkAdapter instance,
        Firestore client, collection, document, and timestamp.
    """
    timestamp = datetime.now()
    firestore_client = MagicMock()
    mock_collection = MagicMock()
    mock_doc = MagicMock()
    mock_doc_ref = MagicMock()
    mock_doc_ref.to_dict.return_value = {
        "url": "https://magic.wizards.com/en/news/mtg-arena/mtg-arena-announcements-may-1-2023",
        "url_hash": "66ddaa70da65a525b5dc64efc8fe17b8",
        "link_added_at": timestamp
    }
    mock_doc.get.return_value = mock_doc_ref

    mock_doc.to_dict.return_value = {
        "url": "https://magic.wizards.com/en/news/mtg-arena/mtg-arena-announcements-may-1-2023",
        "url_hash": "66ddaa70da65a525b5dc64efc8fe17b8",
        "link_added_at": timestamp
    }
    mock_collection.stream.return_value = [mock_doc]

    def collection_side_effect(*_args, **_kwargs):
        return mock_collection

    def document_side_effect(*_args, **_kwargs):
        return mock_doc

    mock_collection.side_effect = collection_side_effect
    mock_collection.document.side_effect = document_side_effect
    adapter = FirestoreArticleLinkAdapter(mock_collection)
    return adapter, firestore_client, mock_collection, mock_doc, timestamp


def test_save_link(firestore_adapter):
    """
    Test the save_link method of FirestoreArticleLinkAdapter.
    """
    test_save_link_logger = logging.getLogger('test_save_link')

    adapter, _, mock_collection, mock_doc, _ = firestore_adapter
    article_link = ArticleLink("https://magic.wizards.com/en/news/mtg-arena/mtg-arena-announcements-may-1-2023")

    test_save_link_logger.info("Saving link: %s", article_link.url)
    adapter.save_link(article_link)

    mock_collection.document.assert_called_once_with(article_link.url_hash)
    mock_doc.set.assert_called_with({
        "url": article_link.url,
        "link_added_at": article_link.link_added_at
    })


def test_get_links(firestore_adapter):
    """
    Test the get_links method of FirestoreArticleLinkAdapter.
    """
    test_get_links_logger = logging.getLogger('test_get_links')

    adapter, _, mock_collection, _, _ = firestore_adapter

    test_get_links_logger.info("Get Links...")
    adapter.get_links()

    # Assert that the stream method is called on the mock collection
    mock_collection.stream.assert_called_once()


def test_get_link_by_hash(firestore_adapter):
    """
    Test the get_link_by_hash method of FirestoreArticleLinkAdapter.
    """
    test_get_link_by_hash_logger = logging.getLogger('test_get_link_by_hash')

    adapter, _, mock_collection, mock_doc, timestamp = firestore_adapter
    article_link = ArticleLink(
        "https://magic.wizards.com/en/news/mtg-arena/mtg-arena-announcements-may-1-2023",
        link_added_at=timestamp  # use the same timestamp
    )

    # configure mock to return a document with the specified hash
    doc_ref = MagicMock()
    doc_ref.get.return_value = mock_doc
    mock_collection.document.return_value = doc_ref

    test_get_link_by_hash_logger.info("Get link by hash: %s", article_link.url_hash)
    links = adapter.get_links(url_hash=article_link.url_hash)

    mock_collection.document.assert_called_once_with(article_link.url_hash)
    mock_doc.get.return_value.to_dict.assert_called_once()

    assert len(links) == 1
    assert links[0].url == article_link.url
    assert links[0].link_added_at == article_link.link_added_at


def test_get_links_by_date_range(firestore_adapter):
    """
    Test the get_links_by_date_range method of FirestoreArticleLinkAdapter.
    """
    test_get_links_by_date_range_logger = logging.getLogger('test_get_links_by_date_range')
    adapter, _, mock_collection, mock_doc, timestamp = firestore_adapter
    start_date = datetime.now()
    end_date = start_date  # replace with valid start and end dates
    article_link = ArticleLink(
        "https://magic.wizards.com/en/news/mtg-arena/mtg-arena-announcements-may-1-2023",
        link_added_at=timestamp
    )

    # configure mock to return a stream of documents within the date range
    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_doc]
    mock_query.where.return_value = mock_query  # return mock_query on second where call
    mock_collection.where.return_value = mock_query

    test_get_links_by_date_range_logger.info(
        "Get link by startdate and enddate: start: %s, end: %s",
        start_date,
        end_date
    )

    links = adapter.get_links(start_date=start_date, end_date=end_date)

    mock_collection.where.assert_called_once_with("link_added_at", ">=", start_date)
    mock_query.where.assert_called_once_with("link_added_at", "<=", end_date)
    mock_query.stream.assert_called_once()

    assert len(links) == 1
    assert links[0].url == article_link.url
    assert links[0].link_added_at == article_link.link_added_at


def test_get_link_by_non_existent_hash(firestore_adapter):
    """
    Test the get_link_by_non_existent_hash method of FirestoreArticleLinkAdapter.
    """
    test_get_link_by_non_existent_hash_logger = logging.getLogger('test_get_link_by_non_existent_hash')
    adapter, _, mock_collection, mock_doc, _ = firestore_adapter
    url_hash = 'nonexistenthash'

    # configure mock to return no document with the specified hash
    mock_non_existing = MagicMock()
    type(mock_non_existing).exists = PropertyMock(return_value=False)

    mock_doc.get.return_value = mock_non_existing
    test_get_link_by_non_existent_hash_logger.info("Get link by non existing hash: %s", url_hash)
    links = adapter.get_links(url_hash=url_hash)

    mock_collection.document.assert_called_once_with(url_hash)
    mock_doc.get.assert_called_once()

    assert len(links) == 0  # The list should be empty since no document was found
