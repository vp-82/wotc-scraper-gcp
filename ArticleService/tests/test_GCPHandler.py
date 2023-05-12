# Required imports
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
import sys

# Local imports
sys.path.append(".")
from src.ArticleHandler import ArticleLink
from src.GCPHandler import FirestoreArticleLinkAdapter


def test_save_link():
    # Setup
    firestore_client = Mock()
    firestore_client.collection = MagicMock()
    adapter = FirestoreArticleLinkAdapter(firestore_client)
    article_link = ArticleLink("http://example.com")

    # Call the method under test
    adapter.save_link(article_link)

    # Assert that the Firestore client was called with the correct arguments
    firestore_client.collection.assert_called_once_with("article_links")
    doc_ref = firestore_client.collection().document()
    doc_ref.set.assert_called_once_with({
        "url": article_link.url,
        "link_added_at": article_link.link_added_at
    })


def test_get_links():
    # Setup
    firestore_client = Mock()
    firestore_client.collection = MagicMock()
    adapter = FirestoreArticleLinkAdapter(firestore_client)

    # Call the method under test
    adapter.get_links()

    # Assert that the Firestore client was called with the correct arguments
    firestore_client.collection.assert_called_once_with("article_links")
    firestore_client.collection().stream.assert_called_once()


def test_get_link_by_hash():
    # Setup
    firestore_client = Mock()
    doc_snapshot = MagicMock()
    doc_snapshot.to_dict.return_value = {
        "url": "http://example.com",
        "link_added_at": datetime.now()
    }
    firestore_client.collection().document().get.return_value = doc_snapshot
    adapter = FirestoreArticleLinkAdapter(firestore_client)
    url_hash = "hash"

    # Call the method under test
    adapter.get_links(url_hash=url_hash)

    # Assert that the Firestore client was called with the correct arguments
    firestore_client.collection().document.assert_any_call(url_hash)
    firestore_client.collection().document().get.assert_any_call()




def test_get_links_by_date_range():
    # Setup
    firestore_client = Mock()
    firestore_client.collection = MagicMock()
    adapter = FirestoreArticleLinkAdapter(firestore_client)
    start_date = datetime.now()
    end_date = datetime.now()

    # Call the method under test
    adapter.get_links(start_date=start_date, end_date=end_date)

    # Assert that the Firestore client was called with the correct arguments
    firestore_client.collection.assert_called_once_with("article_links")
    firestore_client.collection().where.assert_called_with("link_added_at", ">=", start_date)
    firestore_client.collection().where().where.assert_called_with("link_added_at", "<=", end_date)
    firestore_client.collection().where().where().stream.assert_called_once()
