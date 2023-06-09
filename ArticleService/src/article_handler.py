"""
This module defines the ArticleLink class and ArticleLinkAdapter abstract base class.
"""

# Standard library imports
import abc
import hashlib
import logging
from datetime import datetime
from typing import List, Optional


class ArticleLink:
    """
    Represents a link to an article with its URL, URL hash, and the time when the link was added.
    """
    def __init__(self, link_url: str, link_added_at: Optional[datetime] = None) -> None:
        self.url = link_url
        self.url_hash = hashlib.md5(link_url.encode()).hexdigest()
        self.link_added_at = link_added_at

    def __str__(self) -> str:
        return self.url


class ArticleLinkAdapter(abc.ABC):
    """
    Abstract base class for adapters that can save an ArticleLink and retrieve ArticleLinks.
    """
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    @abc.abstractmethod
    def save_link(self, article_link: ArticleLink) -> None:  # pragma: no cover
        """Save an ArticleLink to the storage."""

    @abc.abstractmethod
    def get_links(self, url_hash: Optional[str] = None, start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> List[ArticleLink]:  # pragma: no cover
        """Retrieve ArticleLinks from the storage, with optional filters for hash and date range."""
