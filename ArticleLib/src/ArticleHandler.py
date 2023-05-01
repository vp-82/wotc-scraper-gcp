# Standard library imports
from datetime import datetime
import hashlib
from typing import Optional

class ArticleLink:
    def __init__(self, link_url: str, link_added_at: Optional[datetime] = None) -> None:
        self.url = link_url
        self.url_hash = hashlib.md5(link_url.encode()).hexdigest()
        self.link_added_at = link_added_at


class MTGArticle:
    def __init__(self, article_link: ArticleLink, title: str, article_text: Optional[str]) -> None:
        self.article_link = article_link
        self.title = title
        self.article_text = article_text