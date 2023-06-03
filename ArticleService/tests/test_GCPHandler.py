# test_GCPHandler_pytest.py
import sys
sys.path.append('src')

import pytest
from datetime import datetime
from unittest.mock import MagicMock
from ArticleHandler import ArticleLink
from GCPHandler import FirestoreArticleLinkAdapter

# This is a pytest fixture. It's a way of setting up some code that
# you want to share between multiple tests.
@pytest.fixture
def firestore_adapter():
    timestamp = datetime.now()
    firestore_client = MagicMock()
    mock_collection = MagicMock()
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = {
        "url": "https://magic.wizards.com/en/news/mtg-arena/mtg-arena-announcements-may-1-2023",
        "link_added_at": timestamp
    }
    mock_collection.stream.return_value = [mock_doc]

    def collection_side_effect(*args, **kwargs):
        return mock_collection

    firestore_client.collection.side_effect = collection_side_effect
    adapter = FirestoreArticleLinkAdapter(firestore_client)
    
    return adapter, firestore_client, mock_collection, mock_doc, timestamp

def test_save_link(firestore_adapter):
    adapter, firestore_client, mock_collection, mock_doc, timestamp = firestore_adapter
    article_link = ArticleLink("https://magic.wizards.com/en/news/mtg-arena/mtg-arena-announcements-may-1-2023")
    
    adapter.save_link(article_link)
    
    firestore_client.collection.assert_called_once_with("article_links")
    doc_ref = firestore_client.collection().document()
    doc_ref.set.assert_called_once_with({
        "url": article_link.url,
        "link_added_at": article_link.link_added_at
    })

def test_get_links(firestore_adapter):
    adapter, firestore_client, mock_collection, mock_doc, timestamp = firestore_adapter

    links = adapter.get_links()
    
    firestore_client.collection.assert_called_once_with("article_links")

def test_get_link_by_hash(firestore_adapter):
    adapter, firestore_client, mock_collection, mock_doc, timestamp = firestore_adapter
    url_hash = 'somehash'  # replace with a valid url hash
    article_link = ArticleLink(
        "https://magic.wizards.com/en/news/mtg-arena/mtg-arena-announcements-may-1-2023",
        link_added_at=timestamp  # use the same timestamp
    )

    # configure mock to return a document with the specified hash
    doc_ref = MagicMock()
    doc_ref.get.return_value = mock_doc
    mock_collection.document.return_value = doc_ref

    links = adapter.get_links(url_hash=url_hash)

    mock_collection.document.assert_called_once_with(url_hash)
    doc_ref.get.assert_called_once()

    assert len(links) == 1
    assert links[0].url == article_link.url
    assert links[0].link_added_at == article_link.link_added_at

def test_get_links_by_date_range(firestore_adapter):
    adapter, firestore_client, mock_collection, mock_doc, timestamp = firestore_adapter
    start_date = datetime.now()
    end_date = start_date  # replace with valid start and end dates
    article_link = ArticleLink("https://magic.wizards.com/en/news/mtg-arena/mtg-arena-announcements-may-1-2023", link_added_at=timestamp)

    # configure mock to return a stream of documents within the date range
    mock_query = MagicMock()
    mock_query.stream.return_value = [mock_doc]
    mock_query.where.return_value = mock_query  # return mock_query on second where call
    mock_collection.where.return_value = mock_query

    links = adapter.get_links(start_date=start_date, end_date=end_date)

    mock_collection.where.assert_called_once_with("link_added_at", ">=", start_date)
    mock_query.where.assert_called_once_with("link_added_at", "<=", end_date)
    mock_query.stream.assert_called_once()

    assert len(links) == 1
    assert links[0].url == article_link.url
    assert links[0].link_added_at == article_link.link_added_at

def test_get_link_by_non_existent_hash(firestore_adapter):
    adapter, firestore_client, mock_collection, mock_doc, timestamp = firestore_adapter
    url_hash = 'nonexistenthash'

    # configure mock to return no document with the specified hash
    doc_ref = MagicMock()
    mock_doc.exists = False  # make the document non-existent
    doc_ref.get.return_value = mock_doc
    mock_collection.document.return_value = doc_ref

    links = adapter.get_links(url_hash=url_hash)

    mock_collection.document.assert_called_once_with(url_hash)
    doc_ref.get.assert_called_once()

    assert len(links) == 0  # The list should be empty since no document was found



