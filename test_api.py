import pytest
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout, SSLError

from api import fetch_rates

API_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'


def test_fetch_rates_success(requests_mock):
    mock_data = {
        "Valute": {"USD": {"Value": 89.0}},
        "success": True
    }
    requests_mock.get(API_URL, json=mock_data, status_code=200)
    rates = fetch_rates()
    assert "USD" in rates
    assert rates["USD"]["Value"] == 89.0


def test_fetch_rates_success_without_success_field(requests_mock):
    mock_data = {
        "Valute": {"USD": {"Value": 88.0}}
        # no 'success' field here
    }
    requests_mock.get(API_URL, json=mock_data, status_code=200)
    rates = fetch_rates()
    assert "USD" in rates
    assert rates["USD"]["Value"] == 88.0


def test_fetch_rates_http_error(requests_mock):
    requests_mock.get(API_URL, status_code=500)
    with pytest.raises(HTTPError):
        fetch_rates()


def test_fetch_rates_connection_error(monkeypatch):
    def raise_connection_error(*args, **kwargs):
        raise ConnectionError("Connection failed")

    monkeypatch.setattr(requests, "get", raise_connection_error)
    with pytest.raises(ConnectionError):
        fetch_rates()


def test_fetch_rates_timeout_error(monkeypatch):
    def raise_timeout_error(*args, **kwargs):
        raise Timeout("Timeout occurred")

    monkeypatch.setattr(requests, "get", raise_timeout_error)
    with pytest.raises(Timeout):
        fetch_rates()


def test_fetch_rates_empty_valute(requests_mock):
    mock_data = {"Valute": {}}
    requests_mock.get(API_URL, json=mock_data, status_code=200)
    rates = fetch_rates()
    assert rates == {}


def test_fetch_rates_malformed_json(requests_mock):
    requests_mock.get(API_URL, text="Not a JSON string", status_code=200)
    with pytest.raises(requests.exceptions.JSONDecodeError):
        fetch_rates()


def test_fetch_rates_ssl_error(monkeypatch):
    def raise_ssl_error(*args, **kwargs):
        raise SSLError("SSL certificate error")

    monkeypatch.setattr(requests, "get", raise_ssl_error)
    with pytest.raises(SSLError):
        fetch_rates()
