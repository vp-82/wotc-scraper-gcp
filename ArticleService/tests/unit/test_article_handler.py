# test_article_handler.py
"""
Test module for the ArticleLink class
"""

import hashlib
import logging
from datetime import datetime

import pytest

from src.article_handler import ArticleLink

# Setup logger right below imports
logger = logging.getLogger(__name__)


@pytest.fixture(name="test_link_url")
def fixture_test_link_url():
    """
    Fixture for providing a sample link URL
    """
    return "/en/news/mtg-arena/the-most-played-cards-of-phyrexia-all-will-be-one-in-early-access"


def test_article_link_init(test_link_url):
    """
    Test the initialization of the ArticleLink class with provided link_added_at
    """
    link_added_at = datetime.now()
    article_link = ArticleLink(test_link_url, link_added_at)

    assert article_link.url == test_link_url
    assert article_link.url_hash == hashlib.md5(test_link_url.encode()).hexdigest()
    assert article_link.link_added_at == link_added_at


def test_article_link_init_default_link_added_at(test_link_url):
    """
    Test the initialization of the ArticleLink class with default link_added_at
    """
    article_link = ArticleLink(test_link_url)

    assert article_link.url == test_link_url
    assert article_link.url_hash == hashlib.md5(test_link_url.encode()).hexdigest()
    assert article_link.link_added_at is None
