from typing import List, Tuple  # noqa: F401
from urllib.parse import urlencode

import pytest
from multidict import MultiDict, MultiDictProxy

from yarl import URL


# ========================================
# Basic chars in query values
# ========================================

URLS_WITH_BASIC_QUERY_VALUES = [
    (
        URL('http://example.com'),
        MultiDict(),
    ),
    (
        URL('http://example.com?a'),
        MultiDict([('a', '')]),
    ),
    (
        URL('http://example.com?a='),
        MultiDict([('a', '')]),
    ),
]  # type: List[Tuple[URL, MultiDict]]

URLS_WITH_ASCII_QUERY_VALUES = [
    (
        # TODO: Double check if key is expected as `a b` or `a+b`.
        URL('http://example.com?a+b=c+d'),
        MultiDict({'a b': 'c d'}),
    ),
    (
        URL('http://example.com?a=1&b=2'),
        MultiDict([('a', '1'), ('b', '2')]),
    ),
    (
        URL('http://example.com?a=1&b=2&a=3'),
        MultiDict([('a', '1'), ('b', '2'), ('a', '3')]),
    ),
]  # type: List[Tuple[URL, MultiDict]]

URLS_WITH_NON_ASCII_QUERY_VALUES = [
    # BMP chars
    (
        URL('http://example.com?ключ=знач'),
        MultiDict({'ключ': 'знач'}),
    ),
    (
        URL('http://example.com?foo=ᴜɴɪᴄᴏᴅᴇ'),
        MultiDict({'foo': 'ᴜɴɪᴄᴏᴅᴇ'}),
    ),

    # Non-BMP chars
    (
        URL('http://example.com?bar=𝕦𝕟𝕚𝕔𝕠𝕕𝕖'),
        MultiDict({'bar': '𝕦𝕟𝕚𝕔𝕠𝕕𝕖'}),
    ),
]  # type: List[Tuple[URL, MultiDict]]


@pytest.mark.parametrize(
    'original_url, expected_query',
    URLS_WITH_BASIC_QUERY_VALUES
    + URLS_WITH_ASCII_QUERY_VALUES
    + URLS_WITH_NON_ASCII_QUERY_VALUES,
)
def test_query_basic_parsing(original_url, expected_query):
    assert isinstance(original_url.query, MultiDictProxy)
    assert original_url.query == expected_query


@pytest.mark.parametrize(
    'original_url, expected_query',
    URLS_WITH_ASCII_QUERY_VALUES + URLS_WITH_NON_ASCII_QUERY_VALUES,
)
def test_query_basic_update_query(original_url, expected_query):
    new_url = original_url.update_query({})
    assert new_url == original_url


def test_query_dont_unqoute_twice():
    sample_url = 'http://base.place?' + urlencode({'a': '/////'})
    query = urlencode({'url': sample_url})
    full_url = 'http://test_url.aha?' + query

    url = URL(full_url)
    assert url.query['url'] == sample_url


# ========================================
# Reserved chars in query values
# ========================================

URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES = [
    # Ampersand
    (URL('http://127.0.0.1/?a=10&b=20'),   2, '10'),
    (URL('http://127.0.0.1/?a=10%26b=20'), 1, '10&b=20'),
    (URL('http://127.0.0.1/?a=10%3Bb=20'), 1, '10;b=20'),
    # Semicolon
    (URL('http://127.0.0.1/?a=10;b=20'),   2, '10'),
    (URL('http://127.0.0.1/?a=10%26b=20'), 1, '10&b=20'),
    (URL('http://127.0.0.1/?a=10%3Bb=20'), 1, '10;b=20'),
]


@pytest.mark.parametrize(
    'original_url, expected_query_len, expected_value_a',
    URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES,
)
def test_query_separators_from_parsing(
    original_url,
    expected_query_len,
    expected_value_a,
):
    assert len(original_url.query) == expected_query_len
    assert original_url.query['a'] == expected_value_a


@pytest.mark.parametrize(
    'original_url, expected_query_len, expected_value_a',
    URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES,
)
def test_query_separators_from_update_query(
    original_url,
    expected_query_len,
    expected_value_a,
):
    new_url = original_url.update_query({
        'c': expected_value_a,
    })
    assert new_url.query['a'] == expected_value_a
    assert new_url.query['c'] == expected_value_a


@pytest.mark.parametrize(
    'original_url, expected_query_len, expected_value_a',
    URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES,
)
def test_query_separators_from_with_query(
    original_url,
    expected_query_len,
    expected_value_a,
):
    new_url = original_url.with_query({
        'c': expected_value_a,
    })
    assert new_url.query['c'] == expected_value_a


@pytest.mark.parametrize(
    'original_url, expected_query_len, expected_value_a',
    URLS_WITH_RESERVED_CHARS_IN_QUERY_VALUES,
)
def test_query_from_empty_update_query(
    original_url,
    expected_query_len,
    expected_value_a,
):
    new_url = original_url.update_query({})

    assert new_url.query['a'] == original_url.query['a']

    if 'b' in original_url.query:
        assert new_url.query['b'] == original_url.query['b']

    # FIXME: Broken because of asymmetric query encoding
    # assert new_url == original_url


# ========================================
# Setting and getting query values
# ========================================

def test_query_set_encoded_url_as_value():
    original_url = URL('http://example.com')

    new_url_1 = original_url.update_query({'foo': '𝕦𝕟𝕚'})
    assert '𝕦𝕟𝕚' == new_url_1.query['foo']

    new_url_1_str = str(new_url_1)
    assert (
        'http://example.com/?foo=%F0%9D%95%A6%F0%9D%95%9F%F0%9D%95%9A'
    ) == new_url_1_str

    new_url_2 = original_url.update_query({'bar': new_url_1_str})
    # FIXME: Double-decoding query value
    # assert new_url_1_str == new_url_2.query['bar']
    assert 'http://example.com/?foo=𝕦𝕟𝕚' == new_url_2.query['bar']

    new_url_2_str = str(new_url_2)
    # FIXME: Double-decoding query value
    # assert (
    #     'http://example.com/?bar=http%3A//example.com/%3Ffoo%3D'
    #     '%25F0%259D%2595%25A6%25F0%259D%2595%259F%25F0%259D%2595%259A'
    # ) == new_url_2_str
    assert (
        'http://example.com/?bar=http://example.com/?foo%3D'
        '%F0%9D%95%A6%F0%9D%95%9F%F0%9D%95%9A'
    ) == new_url_2_str

    new_url_3 = original_url.with_query({'bar': new_url_1_str})
    # FIXME: Double-decoding query value
    # assert new_url_1_str == new_url_3.query['bar']
    assert 'http://example.com/?foo=𝕦𝕟𝕚' == new_url_3.query['bar']

    new_url_3_str = str(new_url_3)
    # FIXME: Double-decoding query value
    # assert (
    #     'http://example.com/?bar=http%3A//example.com/%3Ffoo%3D'
    #     '%25F0%259D%2595%25A6%25F0%259D%2595%259F%25F0%259D%2595%259A'
    # ) == new_url_3_str
    assert (
        'http://example.com/?bar=http://example.com/?foo%3D'
        '%F0%9D%95%A6%F0%9D%95%9F%F0%9D%95%9A'
    ) == new_url_3_str
