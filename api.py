import requests

API_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'


def fetch_rates() -> dict:
    response = requests.get(API_URL)
    data = response.json()
    return data.get('Valute', {})
