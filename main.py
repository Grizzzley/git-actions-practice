import tkinter as tk
from tkinter import ttk
from db import init_db, save_rate, get_saved_rate
from api import fetch_rates


class CurrencyConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Конвертер Валют')
        self.geometry('600x700')

        self.loan_var = tk.DoubleVar(value=0.0)
        self.loan_time_var = tk.DoubleVar(value=0.0)
        self.annual_interest_var = tk.DoubleVar(value=0.0)
        self.base_var = tk.StringVar(value='RUB')
        self.target_var = tk.StringVar()

        self.create_widgets()
        init_db()

    def create_widgets(self):
        ttk.Label(self, text='Сумма кредита').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(self, textvariable=self.loan_var).grid(row=0, column=1, sticky='we', padx=5, pady=5)
        ttk.Label(self, text='RUB').grid(row=0, column=2, sticky='w', padx=5, pady=5)

        ttk.Label(self, text='Срок кредита (в месяцах)').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(self, textvariable=self.loan_time_var).grid(row=1, column=1, sticky='we', padx=5, pady=5)
        ttk.Label(self, text='Мес.').grid(row=1, column=2, sticky='w', padx=5, pady=5)

        ttk.Label(self, text='Процентная ставка (%)').grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(self, textvariable=self.annual_interest_var).grid(row=2, column=1, sticky='we', padx=5, pady=5)
        ttk.Label(self, text='%').grid(row=2, column=2, sticky='w', padx=5, pady=5)
        
        ttk.Button(self, text='Рассчитать кредит', command=self.calculate_loan).grid(row=3, column=1, columnspan=1, pady=10, sticky='we')

        self.monthly_label = ttk.Label(self, text='Ежемесячный платёж: 0 RUB')
        self.monthly_label.grid(row=4, column=0, columnspan=3, sticky='n', padx=5)

        self.loan_sum_label = ttk.Label(self, text='Сумма всех платежей: 0 RUB')
        self.loan_sum_label.grid(row=5, column=0, columnspan=3, sticky='n', padx=5)

        self.interest_label = ttk.Label(self, text='Начисленные проценты: 0 RUB')
        self.interest_label.grid(row=6, column=0, columnspan=3, sticky='n', padx=5)

        ttk.Label(self, text='Исходная валюта:').grid(row=7, column=0, sticky='w', padx=5, pady=5)
        ttk.Label(self, textvariable=self.base_var).grid(row=7, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(self, text='Выберите валюту:').grid(row=8, column=0, sticky='w', padx=5, pady=5)
        self.target_entry = ttk.Combobox(self, textvariable=self.target_var, state='readonly')
        self.target_entry.grid(row=8, column=1, padx=5, pady=5, sticky='we')

        ttk.Button(self, text='Конвертировать', command=self.convert).grid(row=9, column=1, columnspan=1, pady=10, sticky='we')

        self.result_label = ttk.Label(self, text='Результат конвертации:')
        self.result_label.grid(row=10, column=0, columnspan=3, sticky='w', padx=5, pady=5)

        ttk.Button(self, text='Обновить курс валют', command=self.update_db).grid(row=11, column=1, columnspan=1, pady=10, sticky='we')

        self.log_text = tk.Text(self, height=6, width=70, wrap="word", state='disabled')
        self.log_text.grid(row=12, column=0, columnspan=3, padx=5, pady=5, sticky='nsew')

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(12, weight=1)

    def log(self, message: str):
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.configure(state='disabled')
        self.log_text.see(tk.END)

    def is_loan_invalid(self, value: float, message: str) -> bool:
        if value <= 0:
            self.log(f'{message} должно быть больше 0')
            return True
        return False

    def calculate_loan(self):
        loan = self.loan_var.get()
        months = self.loan_time_var.get()
        interest = self.annual_interest_var.get()

        if self.is_loan_invalid(loan, 'Сумма кредита') \
           or self.is_loan_invalid(months, 'Срок кредита') \
           or self.is_loan_invalid(interest, 'Процентная ставка'):
            return

        monthly_rate = interest / 100 / 12
        monthly_payment = loan * monthly_rate / (1 - (1 + monthly_rate) ** -months)
        total_payment = monthly_payment * months
        interest_amount = total_payment - loan

        self.monthly_label.config(text=f'Ежемесячный платёж: {monthly_payment:.2f} RUB')
        self.loan_sum_label.config(text=f'Сумма всех платежей: {total_payment:.2f} RUB')
        self.interest_label.config(text=f'Начисленные проценты: {interest_amount:.2f} RUB')

        self.log('Вычислен ежемесячный платёж')

    def convert(self):
        amount = self.loan_var.get()
        target = self.target_var.get()
        if target == '':
            self.log('Не выбрана валюта для конвертации')
            return
        rate = get_saved_rate(target)
        if rate is None:
            self.log(f'Курс валюты {target} не найден в базе данных')
            return

        result = amount * rate
        self.result_label.config(text=f'Результат конвертации: {result:.2f} {target}')
        self.log(f'Конвертировано {amount} RUB в {target} по курсу {rate:.4f}')

    def update_db(self):
        try:
            rates = fetch_rates()
            for index, (code, info) in enumerate(rates.items()):
                save_rate(index+1, code, info['Value'])
            if rates:
                self.target_entry['values'] = list(rates.keys())
            self.log('Курсы валют обновлены')
        except Exception as e:
            self.log(f'Ошибка при обновлении курсов: {e}')


if __name__ == '__main__':
    app = CurrencyConverterApp()
    app.mainloop()
