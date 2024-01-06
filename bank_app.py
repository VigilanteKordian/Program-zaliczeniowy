import bcrypt
import kivy
import random
import json
import requests
from kivy.uix.dropdown import DropDown
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.network.urlrequest import UrlRequest
from kivy.app import App
from datetime import datetime
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window

kivy.require('1.11.1')

Window.clearcolor = (0.1, 0.1, 0.1, 1)
Window.size = (400, 600)

def basic_style(widget):
    widget.size_hint = (1, None) 
    widget.height = 40  
    widget.color = (1, 1, 1, 1)

    if isinstance(widget, Button):
        widget.background_color = (0.2, 0.6, 0.8, 1)
        widget.bold = True
        widget.font_size = '15sp'

    if isinstance(widget, TextInput):
        widget.background_color = (1, 1, 1, 0.3)
        widget.foreground_color = (0, 0, 0, 1)
        widget.multiline = False
        widget.padding = [10, (widget.height - widget.font_size) / 2]



class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        self.username = TextInput(hint_text='Login')
        self.password = TextInput(password=True, hint_text='Hasło')
        self.registration_status = Label(text='', color=(0, 1, 0, 1))
        self.captcha_question, self.captcha_answer = self.generate_captcha()
        self.captcha_label = Label(text=f'{self.captcha_question}\n(Wprowadź wynik poniżej)')
        self.captcha_input = TextInput(hint_text='Wprowadź wynik')
        self.add_widgets()
        
    def add_widgets(self):
        layout = BoxLayout(orientation='vertical', size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        layout.add_widget(Label(text='Zaloguj się do swojego konta bankowego', font_size=20))
        basic_style(self.username)
        basic_style(self.password)
        basic_style(self.captcha_input)
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(Button(text='Zaloguj', on_press=self.validate_user))
        layout.add_widget(Button(text='Zarejestruj nowe konto', on_press=lambda x: setattr(self.manager, 'current', 'register')))
        layout.add_widget(Button(text='Zmień hasło', on_press=lambda x: setattr(self.manager, 'current', 'change_password')))
        layout.add_widget(self.registration_status)
        layout.add_widget(self.captcha_label)
        layout.add_widget(self.captcha_input)
        self.add_widget(layout)

    def validate_user(self, instance):
        captcha_response = self.captcha_input.text
        if not self.validate_captcha(captcha_response):
            self.registration_status.text = 'Wynik nieprawidłowy'
            self.captcha_question, self.captcha_answer = self.generate_captcha()
            self.captcha_label.text = self.captcha_question
            self.captcha_input.text = ''

            app = App.get_running_app()
            app.log_login_attempt(self.username.text, success=False)
            return

        app = App.get_running_app()
        username = self.username.text
        password = self.password.text
        if app.check_password(username, password):
            app.current_username = username
            self.manager.current = 'main'

            app.log_login_attempt(username, success=True)
        else:
            self.registration_status.text = 'Próba zalogowania nieudana. Sprawdź dane lub zarejestruj się.'

            app.log_login_attempt(username, success=False)

    def generate_captcha(self):
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        question = f"{num1} + {num2}"
        answer = str(num1 + num2)
        return question, answer

    def validate_captcha(self, response):
        return response == self.captcha_answer

class RegistrationScreen(Screen):
    def __init__(self, **kwargs):
        super(RegistrationScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})


        layout.add_widget(Label(text='Zarejestruj nowe konto', font_size=20))

        layout.add_widget(Label(text='Login (min. 5 znaków):'))
        self.username = TextInput(hint_text='Login')
        layout.add_widget(self.username)

        layout.add_widget(Label(text='Hasło (min. 8 znaków, w tym cyfry i znaki specjalne):'))
        self.password = TextInput(password=True, hint_text='Hasło')
        layout.add_widget(self.password)

        register_button = Button(text='Zarejestruj', background_color=(0.2, 0.6, 0.8, 1))
        register_button.bind(on_press=self.register_user)
        layout.add_widget(register_button)

        self.registration_status = Label(text='')
        layout.add_widget(self.registration_status)

        back_button = Button(text='Powrót', background_color=(0.2, 0.6, 0.8, 1))
        back_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'login'))
        layout.add_widget(back_button)

        self.add_widget(layout)

    def register_user(self, instance):
        username = self.username.text
        password = self.password.text

        if not self.is_valid_username(username):
            self.registration_status.text = 'Nieprawidłowy login.'
            return

        if not self.is_valid_password(password):
            self.registration_status.text = 'Nieprawidłowe hasło.'
            return
            
        if len(username) < 5:
            self.registration_status.text = 'Login jest za krótki.'
            return

        if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password):
            self.registration_status.text = 'Hasło jest za słabe.'
            return

        if username in App.get_running_app().registered_users:
            self.registration_status.text = 'Ten login jest już zajęty.'
            return

        if username not in App.get_running_app().registered_users:
            App.get_running_app().register_user(username, password)
            self.manager.get_screen('login').registration_status.text = 'Rejestracja udana'
            self.manager.current = 'login'
        
    def is_valid_username(self, username):
        return len(username) >= 5 and username.isalnum()

    def is_valid_password(self, password):
        return (len(password) >= 8 and 
                any(char.isdigit() for char in password) and 
                any(char.isalpha() for char in password) and 
                any(not char.isalnum() for char in password))

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        layout.add_widget(Label(text='Witamy na twoim koncie w AHE-banku', font_size=20))

        balance_button = Button(text='Balans na koncie', background_color=(0.2, 0.6, 0.8, 1))
        balance_button.bind(on_press=lambda x: self.switch_to_screen('balance'))
        layout.add_widget(balance_button)

        history_button = Button(text='Historia transakcji', background_color=(0.2, 0.6, 0.8, 1))
        history_button.bind(on_press=lambda x: self.switch_to_screen('history'))
        layout.add_widget(history_button)

        transfer_button = Button(text='Wykonaj przelew', background_color=(0.2, 0.6, 0.8, 1))
        transfer_button.bind(on_press=lambda x: self.switch_to_screen('transfer'))
        layout.add_widget(transfer_button)

        loan_calculator_button = Button(text='Kalkulator kredytu', background_color=(0.2, 0.6, 0.8, 1))
        loan_calculator_button.bind(on_press=lambda x: self.switch_to_screen('loan_calculator'))
        layout.add_widget(loan_calculator_button)
        
        currency_rates_button = Button(text='Sprawdź kursy walut',  background_color=(0.2, 0.6, 0.8, 1))
        currency_rates_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'currency_rates'))
        layout.add_widget(currency_rates_button)

        change_password_button = Button(text='Zmień hasło', background_color=(0.2, 0.6, 0.8, 1))
        change_password_button.bind(on_press=lambda x: setattr(self.manager, 'current', 'change_password'))
        layout.add_widget(change_password_button)

        logout_button = Button(text='Wyloguj', background_color=(0.2, 0.6, 0.8, 1))
        logout_button.bind(on_press=self.logout)
        layout.add_widget(logout_button)

        self.add_widget(layout)

    def logout(self, instance):
        self.manager.current = 'login'

    def switch_to_screen(self, screen_name):
        self.manager.current = screen_name

    def on_enter(self, *args):
        super(MainScreen, self).on_enter(*args)
        app = App.get_running_app()
        self.username = self.manager.get_screen('login').username.text  # Aktualizacja nazwy użytkownika
        balance = app.user_balances.get(self.username, 0)
        balance_screen = self.manager.get_screen('balance')
        balance_screen.balance_label.text = f'Saldo: {balance} coinsów'

class BalanceScreen(Screen):
    def __init__(self, **kwargs):
        super(BalanceScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        layout.add_widget(Label(text='Balans na koncie', font_size=20))

        self.balance_label = Label(text='0 coinsów')  # Instance attribute instead of id
        layout.add_widget(self.balance_label)

        back_button = Button(text='Powrót', on_release=lambda x: setattr(self.manager, 'current', 'main'))
        basic_style(back_button)
        layout.add_widget(back_button)

        self.add_widget(layout)

class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super(HistoryScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        layout.add_widget(Label(text='Historia transakcji', font_size=20))

        self.history_label = Label(text='')
        layout.add_widget(self.history_label)

        back_button = Button(text='Powrót', on_release=lambda x: setattr(self.manager, 'current', 'main'))
        basic_style(back_button)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def on_enter(self, *args):
        app = App.get_running_app()
        username = self.manager.get_screen('main').username
        transactions = app.user_transactions.get(username, [])
        if transactions:
            formatted_transactions = '\n'.join(transactions)
            self.history_label.text = f'Historia transakcji:\n{formatted_transactions}'
        else:
            self.history_label.text = 'Brak transakcji.'

class FundTransferScreen(Screen):
    def __init__(self, **kwargs):
        super(FundTransferScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        

        self.balance_label = Label(text='Aktualny stan konta: ładowanie...')
        layout.add_widget(self.balance_label)

        layout.add_widget(Label(text='Wykonaj przelew', font_size=20))

        self.account_input = TextInput(hint_text='Konto odbiorcy')
        layout.add_widget(self.account_input)

        self.amount_input = TextInput(hint_text='Kwota')
        layout.add_widget(self.amount_input)

        self.status_label = Label(text='', color=(1, 0, 0, 1))
        layout.add_widget(self.status_label)

        transfer_button = Button(text='Wykonaj przelew')
        basic_style(transfer_button)
        transfer_button.bind(on_press=self.validate_transfer)
        layout.add_widget(transfer_button)

        back_button = Button(text='Powrót', on_release=lambda x: setattr(self.manager, 'current', 'main'))
        basic_style(back_button)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def on_pre_enter(self, *args):
        super(FundTransferScreen, self).on_pre_enter(*args)
        app = App.get_running_app()
        username = self.manager.get_screen('main').username
        balance = app.user_balances.get(username, 0)
        self.balance_label.text = f'Aktualny stan konta: {balance} coinsów'

    def validate_transfer(self, instance):
        account_number = self.account_input.text
        amount = self.amount_input.text

        if not self.is_valid_account_number(account_number):
            self.status_label.text = 'Nieprawidłowy numer konta.'
            return

        if not self.is_valid_amount(amount):
            self.status_label.text = 'Nieprawidłowa kwota.'
            return

        app = App.get_running_app()
        username = self.manager.get_screen('main').username
        current_balance = app.user_balances.get(username, 0)
        if current_balance >= int(amount):
            self.confirm_transfer(username, int(amount))
        else:
            self.status_label.text = 'Niewystarczające środki na koncie.'

    def confirm_transfer(self, username, amount):

        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text='Czy na pewno chcesz wykonać przelew?'))
        yes_button = Button(text='Tak', on_release=lambda x: self.execute_transfer(username, amount))
        no_button = Button(text='Nie', on_release=lambda x: self.dismiss_popup())
        content.add_widget(yes_button)
        content.add_widget(no_button)

        self.popup = Popup(title='Potwierdzenie przelewu', content=content, size_hint=(None, None), size=(300, 200))
        self.popup.open()

    def execute_transfer(self, username, amount):
 
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        transaction_record = f'{timestamp} - Przelew: {amount} coinsów'
        
        app = App.get_running_app()
        app.add_transaction(username, amount, timestamp)  # Dodajemy datę do transakcji
        self.dismiss_popup()
        self.manager.current = 'main'

    def dismiss_popup(self, *args):
        self.popup.dismiss()
        
    def is_valid_account_number(self, account_number):
        return len(account_number) == 24 and account_number.isdigit()

    def is_valid_amount(self, amount):
        try:
            amount = float(amount)
            return amount > 0
        except ValueError:
            return False

class LoanCalculatorScreen(Screen):
    def __init__(self, **kwargs):
        super(LoanCalculatorScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})


        layout.add_widget(Label(text='Kalkulator kredytu', font_size=20))

        layout.add_widget(Label(text='Kwota kredytu:'))
        self.loan_amount = TextInput(hint_text='Kwota', input_filter='float')
        layout.add_widget(self.loan_amount)

        layout.add_widget(Label(text='Roczna stopa procentowa:'))
        self.interest_rate = TextInput(hint_text='Procent', input_filter='float')
        layout.add_widget(self.interest_rate)

        layout.add_widget(Label(text='Okres spłaty (lata):'))
        self.loan_term = TextInput(hint_text='Lata', input_filter='int')
        layout.add_widget(self.loan_term)

        calculate_button = Button(text='Oblicz')
        basic_style(calculate_button)
        calculate_button.bind(on_press=self.calculate_loan)
        layout.add_widget(calculate_button)

        self.result_label = Label(text='')
        layout.add_widget(self.result_label)

        back_button = Button(text='Powrót', on_release=lambda x: setattr(self.manager, 'current', 'main'))
        basic_style(back_button)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def calculate_loan(self, instance):
        P = float(self.loan_amount.text)
        r = float(self.interest_rate.text) / 100 / 12
        n = float(self.loan_term.text) * 12

        M = P * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)
        total_payment = M * n
        total_interest = total_payment - P

        self.result_label.text = f"Miesięczna rata: {M:.2f}\nCałkowite odsetki: {total_interest:.2f}\nCałkowita kwota do zapłaty: {total_payment:.2f}"

class ChangePasswordScreen(Screen):
    def __init__(self, **kwargs):
        super(ChangePasswordScreen, self).__init__(**kwargs)
        self.username_input = TextInput(hint_text='Nazwa użytkownika')
        self.old_password = TextInput(password=True, hint_text='Stare hasło')
        self.new_password = TextInput(password=True, hint_text='Nowe hasło')
        self.status_label = Label(text='')
        self.add_widgets()
        
    def add_widgets(self):
        layout = BoxLayout(orientation='vertical', size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        layout.add_widget(Label(text='Zmień swoje hasło', font_size=20))
        basic_style(self.username_input)
        basic_style(self.old_password)
        basic_style(self.new_password)
        layout.add_widget(self.username_input)
        layout.add_widget(self.old_password)
        layout.add_widget(self.new_password)
        layout.add_widget(Button(text='Zmień hasło', on_press=self.change_password))
        layout.add_widget(self.status_label)
        layout.add_widget(Button(text='Powrót', on_release=self.go_to_login)) 
        self.add_widget(layout)

    def change_password(self, instance):
        app = App.get_running_app()
        username = self.username_input.text
        old_password = self.old_password.text
        new_password = self.new_password.text

        hashed_password = app.registered_users[username].encode('utf-8')
        if bcrypt.checkpw(old_password.encode('utf-8'), hashed_password):
            if len(new_password) >= 8:
                hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                app.registered_users[username] = hashed_new_password
                app.save_user_data()
                app.current_username = None  
                self.status_label.text = 'Hasło zmienione pomyślnie. Zaloguj się ponownie.'
            else:
                self.status_label.text = 'Nowe hasło jest za krótkie'
        else:
            self.status_label.text = 'Nieprawidłowa nazwa użytkownika lub stare hasło'


    def go_to_login(self, instance):
        self.manager.current = 'login'  

class CurrencyRatesScreen(Screen):
    def __init__(self, **kwargs):
        super(CurrencyRatesScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        self.from_currency_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        self.from_currency_input = TextInput(hint_text='Z waluty', size_hint=(0.7, 1))
        self.amount_input = TextInput(hint_text='Ilość', input_filter='float', size_hint=(0.3, 1))

        self.from_currency_layout.add_widget(self.from_currency_input)
        self.from_currency_layout.add_widget(self.amount_input)
        self.layout.add_widget(self.from_currency_layout)

        self.to_currency_input = TextInput(hint_text='Na walutę', size_hint=(1, None), height=40)
        self.layout.add_widget(self.to_currency_input)

        self.from_currency_dropdown = DropDown()
        self.to_currency_dropdown = DropDown()

        self.from_currency_input.bind(on_text=self.update_currency_suggestions)
        self.to_currency_input.bind(on_text=self.update_currency_suggestions)
        self.from_currency_input.bind(focus=self.on_currency_input_focus)
        self.to_currency_input.bind(focus=self.on_currency_input_focus)

        self.rates_label = Label(text='Wprowadź waluty do porównania')
        self.layout.add_widget(self.rates_label)


        back_button = Button(text='Powrót', on_press=lambda x: setattr(self.manager, 'current', 'main'))
        basic_style(back_button)
        self.layout.add_widget(back_button)

        self.add_widget(self.layout)

        self.fetch_currency_list()


    def on_currency_input_focus(self, instance, value):
        if value: 
            if instance is self.from_currency_input:
                self.from_currency_dropdown.open(instance)
            elif instance is self.to_currency_input:
                self.to_currency_dropdown.open(instance)
                
                
    def update_currency_suggestions(self, instance, text):
        dropdown = self.from_currency_dropdown if instance is self.from_currency_input else self.to_currency_dropdown
        dropdown.clear_widgets()
        filtered_currencies = [currency for currency in self.available_currencies if text.lower() in currency.lower()]
        for currency in filtered_currencies:
            btn = Button(text=f"{currency} ({self.full_currency_names.get(currency, '')})", size_hint_y=None, height=30)
            btn.bind(on_release=lambda btn: self.select_currency(btn.text.split(' ')[0], dropdown == self.to_currency_dropdown))
            dropdown.add_widget(btn)
        if text:
            dropdown.open(instance)

    def fetch_currency_list(self):
        url = 'https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies.min.json'
        UrlRequest(url, on_success=self.on_currency_list_success, on_failure=self.on_request_error, on_error=self.on_request_error)

    def on_currency_list_success(self, request, result):

        selected_currencies = [
            'usd', 'eur', 'gbp', 'jpy', 'chf', 'aud', 'cad', 
            'cny', 'hkd', 'inr', 'krw', 'sgd', 'nok', 'mxn', 
            'rub', 'zar', 'try', 'brl', 'sar', 'thb', 'idr', 
            'dkk', 'pln', 'twd', 'aed', 'myr', 'php', 'czk', 
            'sek', 'nzd'
        ]

        self.full_currency_names = {k: v for k, v in result.items() if k in selected_currencies}
        self.available_currencies = list(self.full_currency_names.keys())

        for currency in self.available_currencies:
            btn = Button(text=f"{currency.upper()} ({self.full_currency_names.get(currency, '')})", size_hint_y=None, height=30)
            btn.bind(on_release=lambda btn: self.select_currency(btn.text.split(' ')[0]))
            self.from_currency_dropdown.add_widget(btn)

            btn_to = Button(text=f"{currency.upper()} ({self.full_currency_names.get(currency, '')})", size_hint_y=None, height=30)
            btn_to.bind(on_release=lambda btn_to: self.select_currency(btn_to.text.split(' ')[0], to_currency=True))
            self.to_currency_dropdown.add_widget(btn_to)

    def on_request_error(self, request, error):
        self.rates_label.text = 'Nie udało się pobrać stawek'
            
    def select_currency(self, currency, to_currency=False):
        if to_currency:
            self.to_currency_input.text = currency
            self.to_currency_dropdown.dismiss()
        else:
            self.from_currency_input.text = currency
            self.from_currency_dropdown.dismiss()


        if self.from_currency_input.text and self.to_currency_input.text:
            from_currency = self.from_currency_input.text.split(' ')[0]
            to_currency = self.to_currency_input.text.split(' ')[0]
            self.fetch_exchange_rate(from_currency, to_currency)

    def fetch_exchange_rate(self, from_currency, to_currency):
        from_currency_code = from_currency.lower()
        to_currency_code = to_currency.lower()

        if from_currency_code != to_currency_code:
            url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/{from_currency_code}/{to_currency_code}.json"
            UrlRequest(url, on_success=self.on_exchange_rate_success, on_error=self.on_request_error, on_failure=self.on_request_error)
        else:
            self.rates_label.text = "Proszę wybrać dwie różne waluty."



    def on_exchange_rate_success(self, request, result):
        from_currency = self.from_currency_input.text.split(' ')[0].upper()
        to_currency = self.to_currency_input.text.split(' ')[0].upper()
        amount = float(self.amount_input.text) if self.amount_input.text else 1
        exchange_rate = result.get(to_currency.lower())

        if exchange_rate:
            converted_amount = exchange_rate * amount
            self.rates_label.text = f"{amount} {from_currency} = {converted_amount:.2f} {to_currency}"
        else:
            self.rates_label.text = "Nie znaleziono kursu wymiany."





class BankApp(App):
    current_username = None
    registered_users = {}
    user_balances = {}
    user_transactions = {}
    data_changed = False  

    def __init__(self, **kwargs):
        super(BankApp, self).__init__(**kwargs)
        self.load_user_data() 
        
    def register_user(self, username, password):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.registered_users[username] = hashed_password.decode('utf-8') 
        self.user_balances[username] = random.randint(500, 5000)  # Losowanie salda
        self.user_transactions[username] = []
        self.data_changed = True
        self.save_user_data()
        
    def check_password(self, username, password):
        if username in self.registered_users:
            hashed_password = self.registered_users[username]
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password)
        return False

    def add_transaction(self, username, amount, timestamp):

        transaction_record = f'{timestamp} - Przelew: {amount} coinsów'
        self.user_transactions.setdefault(username, []).append(transaction_record)
        self.user_balances[username] -= int(amount)  # Odejmujemy kwotę od salda
        self.data_changed = True
        self.save_user_data()

    def save_user_data(self):

        with open('user_data.json', 'w') as file:
            json.dump({
                'registered_users': self.registered_users,
                'user_balances': self.user_balances,
                'user_transactions': self.user_transactions
            }, file)
        self.data_changed = False

    def on_stop(self):
        self.save_user_data()

    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegistrationScreen(name='register'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(BalanceScreen(name='balance'))
        sm.add_widget(HistoryScreen(name='history'))
        sm.add_widget(FundTransferScreen(name='transfer'))
        sm.add_widget(LoanCalculatorScreen(name='loan_calculator'))
        sm.add_widget(ChangePasswordScreen(name='change_password'))
        sm.add_widget(CurrencyRatesScreen(name='currency_rates'))
        sm.current = 'login'
        return sm
        
    def check_password(self, username, password):
        if username in self.registered_users:
            # Konwersja zahashowanego hasła na bytes przed użyciem w bcrypt
            hashed_password = self.registered_users[username].encode('utf-8')
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password)
        return False
        
    def save_user_data(self):
        try:
            with open('user_data.json', 'w') as file:
                json.dump({
                    'registered_users': self.registered_users,
                    'user_balances': self.user_balances,
                    'user_transactions': self.user_transactions
                }, file)
            self.data_changed = False
        except IOError as e:
            Logger.error(f"Error saving user data to file: {e}")

    def load_user_data(self):
        try:
            with open('user_data.json', 'r') as file:
                data = json.load(file)
                self.registered_users = data.get('registered_users', {})
                self.user_balances = data.get('user_balances', {})
                self.user_transactions = data.get('user_transactions', {})
        except FileNotFoundError:
            Logger.info("user_data.json not found, creating a new file.")
            self.registered_users = {}
            self.user_balances = {}
            self.user_transactions = {}
        except json.JSONDecodeError as e:
            Logger.error(f"Error decoding JSON from user_data.json: {e}")
            # Inicjalizacja danych do domyślnych wartości w przypadku błędów
            self.registered_users = {}
            self.user_balances = {}
            self.user_transactions = {}
            
    def log_login_attempt(self, username, success):
        # Tworzenie rekordu próby logowania
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = 'successful' if success else 'failed'
        log_message = f"Login attempt by '{username}' on {timestamp} was {status}."
        
        with open('login_history.json', 'a') as log_file:
            json.dump({'timestamp': timestamp, 'username': username, 'status': status}, log_file)
            log_file.write('\n')  # Nowa linia po każdym wpisie

        Logger.info(log_message)


if __name__ == '__main__':
    try:
        BankApp().run()
    except Exception as e:
        print("Exception occurred:", e)
