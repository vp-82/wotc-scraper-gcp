# Standard library imports
from datetime import datetime
import hashlib
import abc
from typing import List, Optional

class ArticleLink:
    def __init__(self, link_url: str, link_added_at: Optional[datetime] = None) -> None:
        self.url = link_url
        self.url_hash = hashlib.md5(link_url.encode()).hexdigest()
        self.link_added_at = link_added_at

class ArticleLink:
    def __init__(self, link_url: str, link_added_at: Optional[datetime] = None) -> None:
        self.url = link_url
        self.url_hash = hashlib.md5(link_url.encode()).hexdigest()
        self.link_added_at = link_added_at


class ArticleLinkAdapter(abc.ABC):
    @abc.abstractmethod
    def save_link(self, article_link: ArticleLink) -> None:
        """Save an ArticleLink to the storage."""
        pass

    @abc.abstractmethod
    def get_links(self, url_hash: Optional[str] = None, start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> List[ArticleLink]:
        """Retrieve ArticleLinks from the storage, with optional filters for hash and date range."""
        pass