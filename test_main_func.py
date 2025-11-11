import pytest

from main import CurrencyConverterApp


@pytest.fixture
def app():
    app_instance = CurrencyConverterApp()
    yield app_instance


def test_calculate_loan_success(app):
    app.loan_var.set(10000)
    app.loan_time_var.set(12)
    app.annual_interest_var.set(12)

    app.calculate_loan()

    assert 'Ежемесячный платёж: ' in app.monthly_label['text']
    assert 'Сумма всех платежей: ' in app.loan_sum_label['text']
    assert 'Начисленные проценты: ' in app.interest_label['text']

    logged_text = app.log_text.get('1.0', 'end')
    assert 'Вычислен ежемесячный платёж' in logged_text


def test_calculate_loan_invalid_loan_amount(app):
    app.loan_var.set(0)
    app.loan_time_var.set(12)
    app.annual_interest_var.set(12)

    app.calculate_loan()

    logged_text = app.log_text.get('1.0', 'end')
    assert 'Сумма кредита должно быть больше 0' in logged_text

    assert app.monthly_label['text'] == 'Ежемесячный платёж: 0 RUB'


def test_convert_success(monkeypatch, app):
    def mock_get_saved_rate(currency):
        return 75.0

    monkeypatch.setattr('main.get_saved_rate', mock_get_saved_rate)

    app.loan_var.set(100)
    app.target_var.set('USD')

    app.convert()

    assert 'Результат конвертации: 7500.00 USD' == app.result_label['text']
    logged_text = app.log_text.get('1.0', 'end')
    assert 'Конвертировано 100.0 RUB в USD по курсу 75.0000' in logged_text


def test_convert_none_rate(monkeypatch, app):
    def mock_get_saved_rate(currency):
        return None

    monkeypatch.setattr('main.get_saved_rate', mock_get_saved_rate)

    app.loan_var.set(100)
    app.target_var.set('EUR')

    app.convert()

    logged_text = app.log_text.get('1.0', 'end')
    assert 'Курс валюты EUR не найден в базе данных' in logged_text


def test_convert_exception(app):
    app.loan_var.set(100)
    app.target_var.set('')

    app.convert()

    logged_text = app.log_text.get('1.0', 'end')
    assert 'Не выбрана валюта для конвертации' in logged_text


def test_update_db_success(monkeypatch, app):
    def mock_fetch_rates():
        return {
            'USD': {'Value': 75.0},
            'EUR': {'Value': 85.0},
        }

    calls = []

    def mock_save_rate(id, code, value):
        calls.append((id, code, value))

    monkeypatch.setattr('main.fetch_rates', mock_fetch_rates)
    monkeypatch.setattr('main.save_rate', mock_save_rate)

    app.update_db()

    assert (1, 'USD', 75.0) in calls
    assert (2, 'EUR', 85.0) in calls
    assert app.target_entry['values'] == ('USD', 'EUR')

    logged_text = app.log_text.get('1.0', 'end')
    assert 'Курсы валют обновлены' in logged_text


def test_update_db_empty_rates(monkeypatch, app):
    def mock_fetch_rates():
        return {}

    def mock_save_rate(id, code, value):
        pytest.fail("save_rate should not be called")

    monkeypatch.setattr('main.fetch_rates', mock_fetch_rates)
    monkeypatch.setattr('main.save_rate', mock_save_rate)

    app.update_db()

    assert app.target_entry['values'] == ('')

    logged_text = app.log_text.get('1.0', 'end')
    assert 'Курсы валют обновлены' in logged_text
