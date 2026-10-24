"""Safety tests for the local inference smoke script URL policy."""
import pytest

from scripts.smoke_local_model import loopback_base_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8000",
        "http://localhost:8000/",
        "https://[::1]:8000",
    ],
)
def test_loopback_base_url_accepts_local_hosts(url):
    assert loopback_base_url(url).rstrip("/") == url.rstrip("/")


@pytest.mark.parametrize(
    "url",
    [
        "https://api.example.com",
        "http://192.168.1.20:8000",
        "http://user:password@127.0.0.1:8000",
        "http://127.0.0.1:8000?target=remote",
        "file:///etc/passwd",
    ],
)
def test_loopback_base_url_rejects_non_loopback_or_ambiguous_urls(url):
    with pytest.raises(ValueError):
        loopback_base_url(url)
