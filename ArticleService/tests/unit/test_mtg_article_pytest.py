# test_mtg_article_pytest.py
import hashlib
import logging
from datetime import datetime

import pytest

from src.article_handler import ArticleLink, ArticleLinkAdapter

# Setup logger right below imports
logger = logging.getLogger(__name__)

# Define a fixture for the link URL.
@pytest.fixture
def link_url():
    return "/en/news/mtg-arena/the-most-played-cards-of-phyrexia-all-will-be-one-in-early-access"

def test_article_link_init(link_url):
    link_added_at = datetime.now()
    article_link = ArticleLink(link_url, link_added_at)

    assert article_link.url == link_url
    assert article_link.url_hash == hashlib.md5(link_url.encode()).hexdigest()
    assert article_link.link_added_at == link_added_at

def test_article_link_init_default_link_added_at(link_url):
    article_link = ArticleLink(link_url)

    assert article_link.url == link_url
    assert article_link.url_hash == hashlib.md5(link_url.encode()).hexdigest()
    assert article_link.link_added_at is None

