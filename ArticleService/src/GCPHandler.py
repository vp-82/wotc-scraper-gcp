from datetime import datetime
from typing import List, Optional

from google.cloud import firestore_v1

# Local imports
from src.ArticleHandler import ArticleLink, ArticleLinkAdapter


class FirestoreArticleLinkAdapter(ArticleLinkAdapter):
    def __init__(self, firestore_collection: firestore_v1.CollectionReference) -> None:
        super().__init__()
        self.collection = firestore_collection


    def save_link(self, article_link: ArticleLink) -> None:
        doc_ref = self.collection.document(article_link.url_hash)
        doc_ref.set({
            "url": article_link.url,
            "link_added_at": article_link.link_added_at
        })
        self.logger.info(f'Successfully saved link: {article_link.url}')


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
        for doc in self.collection.stream():
            data = doc.to_dict()
            if data is not None and "url" in data and "link_added_at" in data:
                link = ArticleLink(
                    link_url=data["url"],
                    link_added_at=data["link_added_at"]
                )
                links.append(link)
        return links




    def _get_link_by_hash(self, url_hash: str) -> List[ArticleLink]:
        doc_ref = self.collection.document(url_hash)
        doc = doc_ref.get()  # Get the DocumentSnapshot

        if doc.exists:  # Now you can use .exists
            data = doc.to_dict()
            if data is not None:
                return [ArticleLink(
                    link_url=data["url"],
                    link_added_at=data["link_added_at"]
                )]
        return []


    def _get_links_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ArticleLink]:
        self.logger.info(f'Retrieving links between dates: {start_date} - {end_date}')
        links = []
        query = self.collection.where("link_added_at", ">=", start_date).where("link_added_at", "<=", end_date)
        docs = query.stream()

        for doc in docs:
            if doc.exists:  # Check if the document exists
                data = doc.to_dict()
                if data is not None and "url" in data and "link_added_at" in data:
                    link = ArticleLink(
                        link_url=data["url"],
                        link_added_at=data["link_added_at"]
                    )
                    links.append(link)

        return links
