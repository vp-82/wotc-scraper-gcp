import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
import datetime
import requests_mock
import re
from google.cloud import firestore
import os

import sys
sys.path.append('src')

from LinkScraper import Scraper, FirestoreArticleLinkAdapter
from GCPHandler import FirestoreArticleLinkAdapter
from ArticleHandler import ArticleLink

@pytest.fixture
def html_content_1():
    return """
    <article data-ctf-id="6un7L8lTRL696HYxwyVICi" class="css-415ug css-o3Y69">
        <a href="/en/news/announcements/the-lord-of-the-rings-tales-of-middle-earth-battle-of-the-pelennor-fields">
            <h3 class="css-9f4rq">The Lord of the Rings: Tales of Middle-earth™ Battle of the Pelennor Fields Statement</h3>
        </a>
    </article>
    """

@pytest.fixture
def html_content_2():
    return """
    <article data-ctf-id="3J34TTSUAm8MO8o9fjk5Ek" class="css-415ug css-o3Y69">
        <a href="/en/news/making-magic/crafting-the-ring-part-1">
            <h3 class="css-9f4rq">Crafting the Ring, Part 1</h3>
        </a>
    </article>
    """

@pytest.fixture
def scraper():
    adapter = MagicMock(spec=FirestoreArticleLinkAdapter)
    return Scraper(adapter), adapter

@patch('LinkScraper.requests.get')
def test_fetch_and_parse_page(mock_get, scraper):
    mock_response = MagicMock()
    mock_get.return_value = mock_response
    page_number = 1
    mock_response.text = 'some html content'

    scraper_obj, _ = scraper
    result = scraper_obj._fetch_and_parse_page_content(page_number)


def test_extract_links_from_soup(scraper, html_content_1, html_content_2):
    soup1 = BeautifulSoup(html_content_1, 'html.parser')
    soup2 = BeautifulSoup(html_content_2, 'html.parser')

    scraper_obj, _ = scraper

    result1 = scraper_obj._extract_links_from_soup(soup1)
    assert result1 == ['https://magic.wizards.com/en/news/announcements/the-lord-of-the-rings-tales-of-middle-earth-battle-of-the-pelennor-fields']

    result2 = scraper_obj._extract_links_from_soup(soup2)
    assert result2 == ['https://magic.wizards.com/en/news/making-magic/crafting-the-ring-part-1']


def test_load_known_link_ids(scraper):
    link1 = ArticleLink('https://magic.wizards.com/en/news/announcements/the-lord-of-the-rings-tales-of-middle-earth-battle-of-the-pelennor-fields', 
                        datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S"))
    link2 = ArticleLink('https://magic.wizards.com/en/news/making-magic/crafting-the-ring-part-1', 
                        datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S"))

    scraper_obj, adapter = scraper
    adapter.get_links.return_value = [link1, link2]

    result = scraper_obj._load_known_link_ids()

    adapter.get_links.assert_called_once()
    assert result == [link1.url_hash, link2.url_hash]

def test_create_link_info(scraper):
    scraper_obj, _ = scraper
    link = 'https://magic.wizards.com/en/news/announcements/the-lord-of-the-rings-tales-of-middle-earth-battle-of-the-pelennor-fields'
    result = scraper_obj._create_link_info(link)

    assert isinstance(result, ArticleLink)
    assert result.url == link
    assert isinstance(result.link_added_at, str)  # as you convert the datetime object to a string

def test_save_new_links(scraper):
    scraper_obj, adapter = scraper
    known_link_ids = [ArticleLink(url, datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")).url_hash 
                      for url in ['https://magic.wizards.com/en/news/announcements/the-lord-of-the-rings-tales-of-middle-earth-battle-of-the-pelennor-fields', 
                                  'https://magic.wizards.com/en/news/making-magic/crafting-the-ring-part-1']]
    new_links = ['https://magic.wizards.com/new_link']

    scraper_obj._save_new_links(new_links, known_link_ids)

    assert len(known_link_ids) == 3

@patch('LinkScraper.requests.get')
def test_scrape_links(mock_get, scraper, html_content_1, html_content_2):
    scraper_obj, adapter = scraper
    mock_get.side_effect = [MagicMock(text=html_content_1), MagicMock(text=html_content_2)]
    adapter.get_links.return_value = [ArticleLink('https://magic.wizards.com/en/news/announcements/the-lord-of-the-rings-tales-of-middle-earth-battle-of-the-pelennor-fields', datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S"))] 

    scraper_obj.scrape_links(1, 2)

    assert mock_get.call_count == 2
    adapter.save_link.assert_called()
    assert adapter.save_link.call_count == 1  # 'https://magic.wizards.com/en/news/making-magic/crafting-the-ring-part-1' is a new link

# Check if link format is valid
def is_valid_link(link):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, link) is not None

@pytest.fixture
def test_db():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="./tests/mtg-scraper-385015-aad053a61746.json"
    # Assuming you have set the GOOGLE_APPLICATION_CREDENTIALS environment variable
    db = firestore.Client()
    return db.collection('mtg_scraper_test_collection')

@pytest.mark.integration
def test_with_real_webpage(test_db):
    adapter = FirestoreArticleLinkAdapter(test_db)
    scraper = Scraper(adapter)
    scraper.scrape_links(1, 2)
    # Clean up after the test by deleting all documents in the test collection
    docs = test_db.stream()
    
    links = []
    for doc in docs:
        data = doc.to_dict()
        if "url" in data and "link_added_at" in data:
            link = ArticleLink(
                link_url=data["url"],
                link_added_at=data["link_added_at"]
            )
            links.append(link)

    assert len(links) > 0
    
    # Clean up
    docs = test_db.stream()
    for doc in docs:
        doc.reference.delete()



