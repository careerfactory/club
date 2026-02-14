import ipaddress
import logging
import socket
from collections import namedtuple
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from django.utils.html import strip_tags
from newspaper import ArticleException, Config, Article
from requests import RequestException

DEFAULT_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 "
                  "Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
}
DEFAULT_REQUEST_TIMEOUT = 10
MAX_PARSABLE_CONTENT_LENGTH = 15 * 1024 * 1024  # 15Mb

log = logging.getLogger(__name__)


ParsedURL = namedtuple("ParsedURL", ["url", "domain", "title", "favicon", "summary", "image", "description"])


def parse_url_preview(url: str) -> Optional[ParsedURL]:
    real_url, content_type, content_length = resolve_url(url)

    # do not parse non-text content
    if not content_type or not content_type.startswith("text/"):
        return None

    try:
        article = load_and_parse_full_article_text_and_image(real_url)
    except ArticleException:
        return None

    canonical_url = article.canonical_link or real_url
    return ParsedURL(
        url=canonical_url,
        domain=urlparse(canonical_url).netloc,
        title=strip_tags(article.title),
        favicon=strip_tags(urljoin(article.url, article.meta_favicon)),
        summary="",
        image=article.top_image,
        description=article.meta_description,
    )


def resolve_url(entry_link):
    url = str(entry_link)
    content_type = None
    content_length = MAX_PARSABLE_CONTENT_LENGTH + 1  # don't parse null content-types
    depth = 10
    while depth > 0:
        depth -= 1
        if not is_safe_external_url(url):
            log.warning(f"Blocked unsafe URL: {url}")
            return None, content_type, content_length

        try:
            response = requests.head(
                url,
                timeout=DEFAULT_REQUEST_TIMEOUT,
                stream=True,
                headers=DEFAULT_REQUEST_HEADERS,
                allow_redirects=False,
            )
        except RequestException:
            log.warning(f"Failed to resolve URL: {url}")
            return None, content_type, content_length

        if 300 < response.status_code < 400:
            location = response.headers.get("location")
            if not location:
                return None, content_type, content_length
            url = urljoin(url, location)  # follow redirect safely
        else:
            content_type = response.headers.get("content-type")
            content_length = int(response.headers.get("content-length") or 0)
            break

    return url, content_type, content_length


def load_page_safe(url: str) -> str:
    if not is_safe_external_url(url):
        log.warning(f"Blocked unsafe URL fetch: {url}")
        return ""

    try:
        response = requests.get(
            url=url,
            timeout=DEFAULT_REQUEST_TIMEOUT,
            headers=DEFAULT_REQUEST_HEADERS,
            stream=True,  # the most important part — stream response to prevent loading everything into memory
            allow_redirects=False,
        )
    except RequestException as ex:
        log.warning(f"Error parsing the page: {url} {ex}")
        return ""
    # https://stackoverflow.com/a/23514616
    return response.raw.read(MAX_PARSABLE_CONTENT_LENGTH, decode_content=True)


def load_and_parse_full_article_text_and_image(url: str) -> Article:
    config = Config()
    config.MAX_SUMMARY_SENT = 8

    article = Article(url, config=config)
    article.set_html(load_page_safe(url))  # safer than article.download()
    article.parse()

    return article


def is_safe_external_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if not parsed.hostname:
        return False
    if parsed.hostname.lower() == "localhost":
        return False
    return is_public_hostname(parsed.hostname)


def is_public_hostname(hostname: str) -> bool:
    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False

    for _, _, _, _, sockaddr in addr_info:
        ip_address = ipaddress.ip_address(sockaddr[0])
        if (
            ip_address.is_private
            or ip_address.is_loopback
            or ip_address.is_link_local
            or ip_address.is_reserved
            or ip_address.is_multicast
            or ip_address.is_unspecified
        ):
            return False

    return True
