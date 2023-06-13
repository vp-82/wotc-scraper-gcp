# test_link_scraper.py
"""
This module contains unit tests and helper functions for the link scraping functionality of a web scraper.
The web scraper is designed to extract article links from a website and store the information about the
links such as the link itself and the date it was added. The tests cover functionalities such as fetching
and parsing page content, extracting links from the parsed content, loading known link IDs, creating link
information, saving new links, and the main link scraping process. The helper functions provide sample HTML
content for the tests and validate link formats.
"""

import datetime
import logging
import re
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from src.article_handler import ArticleLink
from src.link_scraper import FirestoreArticleLinkAdapter, Scraper

# Setup logger right below imports
logger = logging.getLogger(__name__)


@pytest.fixture(name='html_cont_1')
def html_content_1():
    """
    Pytest fixture that returns a string of HTML content containing a single article link.
    This can be used in tests to simulate a webpage.
    """
    return """
    <article data-ctf-id="6un7L8lTRL696HYxwyVICi" class="css-415ug css-o3Y69">
        <a href="/en/news/announcements/the-lord-of-the-rings-tales-of-middle-earth-battle-of-the-pelennor-fields">
            <h3 class="css-9f4rq">The Lord of the Rings: Tales of Middle-earth™ Battle of the Pelennor Fields Statement</h3>
        </a>
    </article>
    """


@pytest.fixture(name='html_cont_2')
def html_content_2():
    """
    Pytest fixture that returns a string of HTML content containing a single article link.
    This can be used in tests to simulate a webpage.
    """
    return """
    <article data-ctf-id="3J34TTSUAm8MO8o9fjk5Ek" class="css-415ug css-o3Y69">
        <a href="/en/news/making-magic/crafting-the-ring-part-1">
            <h3 class="css-9f4rq">Crafting the Ring, Part 1</h3>
        </a>
    </article>
    """


@pytest.fixture(name="html_content_2_links")
def html_content_two_articles():
    """
    Pytest fixture that returns a string of HTML content containing two article links.
    This can be used in tests to simulate a webpage with multiple articles.
    """
    return """
    <article data-ctf-id="6un7L8lTRL696HYxwyVICi" class="css-415ug css-o3Y69">
        <a href="/en/news/announcements/the-lord-of-the-rings-tales-of-middle-earth-battle-of-the-pelennor-fields">
            <h3 class="css-9f4rq">The Lord of the Rings: Tales of Middle-earth™ Battle of the Pelennor Fields Statement</h3>
        </a>
    </article>
        <article data-ctf-id="3J34TTSUAm8MO8o9fjk5Ek" class="css-415ug css-o3Y69">
        <a href="/en/news/making-magic/crafting-the-ring-part-1">
            <h3 class="css-9f4rq">Crafting the Ring, Part 1</h3>
        </a>
    </article>
    """


@pytest.fixture(name="scraper")
def fixture_scraper():
    """
    Pytest fixture that creates and returns a Scraper object and a MagicMock FirestoreArticleLinkAdapter.
    The MagicMock FirestoreArticleLinkAdapter can be used to simulate database operations without making
    actual calls to the database.
    """
    adapter = MagicMock(spec=FirestoreArticleLinkAdapter)
    return Scraper(adapter), adapter


@patch('src.link_scraper.requests.get')
def test_fetch_and_parse_page(mock_get, scraper):
    """
    Test for the `_fetch_and_parse_page_content` method of the Scraper class.
    This method is supposed to fetch a webpage and parse its content.
    """
    test_fetch_and_parse_page_logger = logging.getLogger('test_fetch_and_parse_page')
    test_fetch_and_parse_page_logger.info('Running test_fetch_and_parse_page...')

    mock_response = MagicMock()
    mock_get.return_value = mock_response
    page_number = 1
    mock_response.text = 'some html content'

    scraper_obj, _ = scraper
    # pylint: disable=protected-access
    _ = scraper_obj._fetch_and_parse_page_content(page_number)


def test_extract_links_from_soup(scraper, html_cont_1, html_cont_2):
    """
    Test for the `_extract_links_from_soup` method of the Scraper class.
    This method is supposed to extract all article links from a BeautifulSoup object of parsed HTML content.
    """
    test_extract_links_from_soup_logger = logging.getLogger('test_extract_links_from_soup')
    test_extract_links_from_soup_logger.info('Running test_extract_links_from_soup...')

    soup1 = BeautifulSoup(html_cont_1, 'html.parser')
    soup2 = BeautifulSoup(html_cont_2, 'html.parser')

    scraper_obj, _ = scraper

    # pylint: disable=protected-access
    result1 = scraper_obj._extract_links_from_soup(soup1)
    expected_result = [
        'https://magic.wizards.com/en/news/announcements/'
        'the-lord-of-the-rings-tales-of-middle-earth-battle-of-the-pelennor-fields'
    ]
    assert result1 == expected_result

    result2 = scraper_obj._extract_links_from_soup(soup2)
    assert result2 == ['https://magic.wizards.com/en/news/making-magic/crafting-the-ring-part-1']


def test_load_known_link_ids(scraper):
    """
    Test for the `_load_known_link_ids` method of the Scraper class.
    This method is supposed to load all known link IDs from the FirestoreArticleLinkAdapter.
    """
    link1 = ArticleLink(
        'https://magic.wizards.com/en/news/announcements/'
        'the-lord-of-the-rings-tales-of-middle-earth-battle-of-the-pelennor-fields',
        datetime.datetime.now()
    )

    link2 = ArticleLink(
        'https://magic.wizards.com/en/news/making-magic/crafting-the-ring-part-1',
        datetime.datetime.now()
    )

    scraper_obj, adapter = scraper
    adapter.get_links.return_value = [link1, link2]

    # pylint: disable=protected-access
    result = scraper_obj._load_known_link_ids()

    adapter.get_links.assert_called_once()
    assert result == [link1.url_hash, link2.url_hash]


def test_create_link_info(scraper):
    """
    Test for the `_create_link_info` method of the Scraper class.
    This method is supposed to create an ArticleLink object from a link string.
    """
    test_create_link_info_logger = logging.getLogger('test_create_link_info')
    test_create_link_info_logger.info('Running test_create_link_info...')

    test_create_link_info_logger = logging.getLogger('test_load_known_link_ids')
    test_create_link_info_logger.info('Running test_load_known_link_ids...')

    scraper_obj, _ = scraper
    link = (
        'https://magic.wizards.com/en/news/announcements/'
        'the-lord-of-the-rings-tales-of-middle-earth-battle-of-the-pelennor-fields'
    )

    # pylint: disable=protected-access
    result = scraper_obj._create_link_info(link)

    assert isinstance(result, ArticleLink)
    assert result.url == link
    assert isinstance(result.link_added_at, datetime.datetime)  # as you convert the datetime object to a string


def test_save_new_links(scraper):
    """
    Test for the `_save_new_links` method of the Scraper class.
    This method is supposed to save new links to the FirestoreArticleLinkAdapter.
    """
    test_save_new_links_logger = logging.getLogger('test_save_new_links')
    test_save_new_links_logger.info('Running test_save_new_links...')

    scraper_obj, _ = scraper
    known_link_ids = [
        ArticleLink(url, datetime.datetime.now()).url_hash
        for url in [
            'https://magic.wizards.com/en/news/announcements/'
            'the-lord-of-the-rings-tales-of-middle-earth-battle-of-the-pelennor-fields',
            'https://magic.wizards.com/en/news/making-magic/crafting-the-ring-part-1'
        ]
    ]

    new_links = ['https://magic.wizards.com/new_link']

    # pylint: disable=protected-access
    scraper_obj._save_new_links(new_links, known_link_ids)

    assert len(known_link_ids) == 3


@patch('src.link_scraper.requests.get')
def test_scrape_links(mock_get, scraper, html_content_2_links):
    """
    Test for the `scrape_links` method of the Scraper class.
    This method is the main link scraping process which orchestrates the fetching, parsing, extracting, and
    saving of links.
    """
    scraper_obj, adapter = scraper
    mock_get.side_effect = [MagicMock(text=html_content_2_links)]
    adapter.get_links.return_value = [
        ArticleLink(
            'https://magic.wizards.com/en/news/announcements/'
            'the-lord-of-the-rings-tales-of-middle-earth-battle-of-the-pelennor-fields',
            datetime.datetime.now()
        )
    ]

    scraper_obj.scrape_links(1, 2)

    assert mock_get.call_count == 1
    adapter.save_link.assert_called()
    # 'https://magic.wizards.com/en/news/making-magic/crafting-the-ring-part-1' is a new link
    assert adapter.save_link.call_count == 1


# Check if link format is valid
def is_valid_link(link):
    """
    Helper function that checks if a given string is a valid link.
    It uses a regular expression to check the link format.
    """
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, link) is not None
