import abc
from typing import List, Optional
from google.cloud import firestore
from datetime import datetime
import sys

# Local imports
sys.path.append(".")
from src.ArticleHandler import ArticleLinkAdapter, ArticleLink


class FirestoreArticleLinkAdapter(ArticleLinkAdapter):

    def __init__(self, firestore_client: firestore.Client, collection_name: str = "article_links") -> None:
        self.firestore_client = firestore_client
        self.collection = self.firestore_client.collection(collection_name)

    def save_link(self, article_link: ArticleLink) -> None:
        """Save an ArticleLink to Firestore."""
        doc_ref = self.collection.document(article_link.url_hash)
        doc_ref.set({
            "url": article_link.url,
            "link_added_at": article_link.link_added_at
        })

    def get_links(self, url_hash: Optional[str] = None, start_date: Optional[datetime] = None,
                end_date: Optional[datetime] = None) -> List[ArticleLink]:
        """Retrieve ArticleLinks from Firestore, with optional filters for hash and date range."""
        if url_hash:
            return self._get_link_by_hash(url_hash)
        elif start_date and end_date:
            return self._get_links_by_date_range(start_date, end_date)
        else:
            return self._get_all_links()

    def _get_all_links(self) -> List[ArticleLink]:
        links = []
        docs = self.collection.stream()

        for doc in docs:
            data = doc.to_dict()
            link = ArticleLink(
                link_url=data["url"],
                link_added_at=data["link_added_at"]
            )
            links.append(link)

        return links

    def _get_link_by_hash(self, url_hash: str) -> List[ArticleLink]:
        doc_ref = self.collection.document(url_hash)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            return [ArticleLink(
                link_url=data["url"],
                link_added_at=data["link_added_at"]
            )]
        else:
            return []

    def _get_links_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ArticleLink]:
        links = []
        query = self.collection.where("link_added_at", ">=", start_date).where("link_added_at", "<=", end_date)
        docs = query.stream()

        for doc in docs:
            data = doc.to_dict()
            link = ArticleLink(
                link_url=data["url"],
                link_added_at=data["link_added_at"]
            )
            links.append(link)

        return links