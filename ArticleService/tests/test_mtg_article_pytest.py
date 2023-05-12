# test_mtg_article_pytest.py

# Standard library imports
from datetime import datetime
import hashlib
import sys
from typing import Optional

# Third-party imports
# import pytest

# Local imports
sys.path.append(".")
from src.ArticleHandler import ArticleLink

def test_article_link_init():
    link_url = "/en/news/mtg-arena/the-most-played-cards-of-phyrexia-all-will-be-one-in-early-access"
    link_added_at = datetime.now()
    article_link = ArticleLink(link_url, link_added_at)

    assert article_link.url == link_url
    assert article_link.url_hash == hashlib.md5(link_url.encode()).hexdigest()
    assert article_link.link_added_at == link_added_at

def test_article_link_init_default_link_added_at():
    link_url = "/en/news/mtg-arena/the-most-played-cards-of-phyrexia-all-will-be-one-in-early-access"
    article_link = ArticleLink(link_url)

    assert article_link.url == link_url
    assert article_link.url_hash == hashlib.md5(link_url.encode()).hexdigest()
    assert article_link.link_added_at is None