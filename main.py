from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, ListProperty
from kivy.uix.dropdown import DropDown
from kivy.uix.popup import Popup
import requests
import threading
import time
from datetime import datetime

# Classe para gerenciar taxas de conversão
class CurrencyConverter:
    def __init__(self):
        self.rates = {}
        self.currencies = ['BRL', 'USD', 'EUR']  # Moedas iniciais
        self.last_updated = None
        self.lock = threading.Lock()
        self.fetch_currencies()  # Carrega lista de moedas

    def fetch_currencies(self):
        try:
            response = requests.get('https://api.coingecko.com/api/v3/coins/list', timeout=5)
            response.raise_for_status()
            coins = response.json()
            self.currencies = ['BRL', 'USD', 'EUR']  # Moedas fiduciárias básicas
            for coin in coins[:50]:  # Limita a 50 moedas/criptos para desempenho
                self.currencies.append(coin['symbol'].upper())
        except (requests.RequestException, ValueError):
            pass  # Mantém as moedas básicas em caso de falha

    def update_rates(self):
        try:
            # Usa vs_currencies dinâmico com base nas moedas carregadas
            vs_currencies = ','.join(set(self.currencies) - {'BTC', 'ETH'})  # Exclui BTC e ETH do vs_currencies
            ids = ','.join([c.lower() for c in self.currencies if c not in ['BRL', 'USD', 'EUR']])
            if ids:
                url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies={vs_currencies}'
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                data = response.json()
                self.rates = {'BRL': 1.0, 'USD': 5.5, 'EUR': 6.0}  # Taxas base
                for coin_id, rates in data.items():
                    for curr, rate in rates.items():
                        self.rates[coin_id.upper()] = rate if curr == 'brl' else rate * self.rates[curr.upper()]
            self.last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except (requests.RequestException, ValueError, KeyError):
            self.rates = {'BRL': 1.0, 'USD': 5.5, 'EUR': 6.0, 'BTC': 300000, 'ETH': 15000}  # Fallback rates
            self.last_updated = None

    def convert(self, amount, from_currency, to_currency):
        with self.lock:
            if from_currency in self.rates and to_currency in self.rates:
                return amount * (self.rates[to_currency] / self.rates[from_currency])
            return 0

    def start_update_thread(self):
        def update_loop():
            while True:
                with self.lock:
                    self.update_rates()
                time.sleep(300)  # Atualiza a cada 5 minutos
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()

converter = CurrencyConverter()

class FIICalculatorApp(App):
    def build(self):
        self.sm = ScreenManager()
        self.sm.add_widget(MenuScreen(name='menu'))
        self.sm.add_widget(JurosCompostosScreen(name='juros'))
        self.sm.add_widget(RendaFixaScreen(name='rendafixa'))
        self.sm.add_widget(RendaMensalScreen(name='fii_renda'))
        self.sm.add_widget(DividendYieldScreen(name='fii_dividend'))
        self.sm.add_widget(PrecoCotaScreen(name='fii_preco'))
        self.sm.add_widget(ResultadoScreen(name='fii_resultado'))
        self.sm.add_widget(ConversorScreen(name='conversor'))
        converter.start_update_thread()  # Inicia a thread de atualização
        return self.sm

# Menu Principal
class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='Escolha uma Calculadora', font_size=20, bold=True))
        
        btn_juros = Button(text='Juros Compostos', size_hint=(1, 0.2))
        btn_rendafixa = Button(text='Renda Fixa', size_hint=(1, 0.2))
        btn_fii = Button(text='Fundos Imobiliários', size_hint=(1, 0.2))
        btn_conversor = Button(text='Conversor de Moedas', size_hint=(1, 0.2))
        
        btn_juros.bind(on_press=lambda x: self.manager.current = 'juros')
        btn_rendafixa.bind(on_press=lambda x: self.manager.current = 'rendafixa')
        btn_fii.bind(on_press=lambda x: self.manager.current = 'fii_renda')
        btn_conversor.bind(on_press=lambda x: self.manager.current = 'conversor')
        
        layout.add_widget(btn_juros)
        layout.add_widget(btn_rendafixa)
        layout.add_widget(btn_fii)
        layout.add_widget(btn_conversor)
        self.add_widget(layout)

# Juros Compostos
class JurosCompostosScreen(Screen):
    result_text = StringProperty('Saldo final:\\nR$ 0,00\\n\\nTotal investido:\\nR$ 0,00\\nJuros totais:\\nR$ 0,00')
    
    def __init__(self, **kwargs):
        super(JurosCompostosScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='Calculadora de Juros', font_size=20, bold=True))
        
        self.valor_inicial = TextInput(text='100000.00', hint_text='Valor inicial (R$)', input_filter='float')
        self.taxa_juros = TextInput(text='6', hint_text='Taxa de juros (%)', input_filter='float')
        self.duracao = TextInput(text='2', hint_text='Duração (anos)', input_filter='int')
        self.deposito_mensal = TextInput(text='0.00', hint_text='Depósito mensal (R$)', input_filter='float')
        
        layout.add_widget(self.valor_inicial)
        layout.add_widget(self.taxa_juros)
        layout.add_widget(self.duracao)
        layout.add_widget(self.deposito_mensal)
        
        btn_calcular = Button(text='Calcular', background_color=(0, 0.5, 1, 1))
        btn_calcular.bind(on_press=self.calcular)
        layout.add_widget(btn_calcular)
        
        self.result_label = Label(text=self.result_text, halign='left')
        layout.add_widget(self.result_label)
        
        self.add_widget(layout)
    
    def calcular(self, instance):
        try:
            valor_inicial = float(self.valor_inicial.text)
            taxa_juros = float(self.taxa_juros.text) / 100 / 12
            duracao = int(self.duracao.text) * 12
            deposito_mensal = float(self.deposito_mensal.text)
            
            saldo = valor_inicial
            total_investido = valor_inicial
            
            for _ in range(duracao):
                saldo *= (1 + taxa_juros)
                saldo += deposito_mensal
                total_investido += deposito_mensal
            
            juros_totais = saldo - valor_inicial - (deposito_mensal * duracao)
            self.result_text = f'Saldo final:\\nR$ {saldo:,.2f}\\n\\nTotal investido:\\nR$ {total_investido:,.2f}\\nJuros totais:\\nR$ {juros_totais:,.2f}'
            self.result_label.text = self.result_text
        except ValueError:
            self.result_text = 'Erro: Insira valores válidos!'
            self.result_label.text = self.result_text

# Renda Fixa
class TaxasRendaFixa:
    def __init__(self):
        self.taxa_selic = None
        self._fetch_taxas()
    
    def _fetch_taxas(self):
        try:
            response = requests.get('https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json', timeout=5)
            response.raise_for_status()
            data = response.json()
            if data and 'valor' in data[-1]:
                self.taxa_selic = float(data[-1]['valor'])
            else:
                self.taxa_selic = None
        except (requests.RequestException, ValueError):
            self.taxa_selic = None

    def update_taxas(self):
        self._fetch_taxas()

class RendaFixaScreen(Screen):
    result_text = StringProperty('Resultado:\\nSaldo final: R$ 0,00\\nJuros ganhos: R$ 0,00')
    
    def __init__(self, **kwargs):
        super(RendaFixaScreen, self).__init__(**kwargs)
        self.taxas = TaxasRendaFixa()
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='Simulador Renda Fixa', font_size=20, bold=True))
        
        self.investimento_inicial = TextInput(text='0.00', hint_text='Investimento Inicial (R$)', input_filter='float')
        self.investimento_mensal = TextInput(text='0.00', hint_text='Investimento Mensal (R$)', input_filter='float')
        self.periodo = TextInput(text='12', hint_text='Período (meses)', input_filter='int')
        
        layout.add_widget(self.investimento_inicial)
        layout.add_widget(self.investimento_mensal)
        layout.add_widget(self.periodo)
        
        btn_calcular = Button(text='Calcular', background_color=(0, 0.5, 1, 1))
        btn_calcular.bind(on_press=self.calcular)
        layout.add_widget(btn_calcular)
        
        self.result_label = Label(text=self.result_text, halign='left')
        layout.add_widget(self.result_label)
        
        self.add_widget(layout)
    
    def calcular(self, instance):
        if self.taxas.taxa_selic is None:
            self.result_text = 'Sem conexão com a internet'
            self.result_label.text = self.result_text
            return
        
        try:
            investimento_inicial = float(self.investimento_inicial.text)
            investimento_mensal = float(self.investimento_mensal.text)
            periodo = int(self.periodo.text)
            meses = periodo
            
            taxa_anual = self.taxas.taxa_selic / 100
            taxa_mensal = taxa_anual / 12
            
            saldo = investimento_inicial
            total_investido = investimento_inicial
            
            for _ in range(meses):
                saldo *= (1 + taxa_mensal)
                saldo += investimento_mensal
                total_investido += investimento_mensal
            
            juros_ganhos = saldo - total_investido
            self.result_text = f'Resultado:\\nSaldo final: R$ {saldo:,.2f}\\nJuros ganhos: R$ {juros_ganhos:,.2f}'
            self.result_label.text = self.result_text
        except ValueError:
            self.result_text = 'Erro: Insira valores válidos!'
            self.result_label.text = self.result_text

# Fundos Imobiliários
class RendaMensalScreen(Screen):
    def __init__(self, **kwargs):
        super(RendaMensalScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='Cálculo Renda Fundos Imobiliários', font_size=20, bold=True))
        layout.add_widget(Label(text='Renda mensal desejada', halign='center'))
        layout.add_widget(Label(text='Informe quanto pretende ganhar todos os meses.', halign='center', color=(0, 0, 0, 1)))
        
        self.renda_input = TextInput(text='0.00', hint_text='R$', input_filter='float', multiline=False)
        layout.add_widget(self.renda_input)
        
        btn_avancar = Button(text='Avançar', size_hint=(1, 0.5), background_color=(0, 0.5, 1, 1))
        btn_avancar.bind(on_press=self.avancar)
        layout.add_widget(btn_avancar)
        
        self.add_widget(layout)
    
    def avancar(self, instance):
        if float(self.renda_input.text) > 0:
            self.manager.get_screen('fii_dividend').renda_desejada = float(self.renda_input.text)
            self.manager.current = 'fii_dividend'
        else:
            self.show_error('Erro: Insira um valor válido para a renda desejada!')

    def show_error(self, message):
        popup = Popup(title='Erro', content=Label(text=message), size_hint=(0.8, 0.5))
        popup.open()

class DividendYieldScreen(Screen):
    renda_desejada = 0.0
    
    def __init__(self, **kwargs):
        super(DividendYieldScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='Cálculo Renda Fundos Imobiliários', font_size=20, bold=True))
        layout.add_widget(Label(text='Dividendo mensal', halign='center'))
        layout.add_widget(Label(text='Informe quanto de dividendo o fundo paga por mês.', halign='center', color=(0, 0, 0, 1)))
        
        self.dividendo_input = TextInput(text='0.00', hint_text='R$', input_filter='float', multiline=False)
        layout.add_widget(self.dividendo_input)
        
        btn_voltar = Button(text='Voltar', size_hint=(0.5, 0.5))
        btn_avancar = Button(text='Avançar', size_hint=(0.5, 0.5), background_color=(0, 0.5, 1, 1))
        btn_voltar.bind(on_press=lambda x: self.manager.current = 'fii_renda')
        btn_avancar.bind(on_press=self.avancar)
        btn_layout = BoxLayout()
        btn_layout.add_widget(btn_voltar)
        btn_layout.add_widget(btn_avancar)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def avancar(self, instance):
        if float(self.dividendo_input.text) > 0:
            self.manager.get_screen('fii_preco').renda_desejada = self.renda_desejada
            self.manager.get_screen('fii_preco').dividendo_mensal = float(self.dividendo_input.text)
            self.manager.current = 'fii_preco'
        else:
            self.show_error('Erro: Insira um valor válido para o dividendo mensal!')

    def show_error(self, message):
        popup = Popup(title='Erro', content=Label(text=message), size_hint=(0.8, 0.5))
        popup.open()

class PrecoCotaScreen(Screen):
    renda_desejada = 0.0
    dividendo_mensal = 0.0
    
    def __init__(self, **kwargs):
        super(PrecoCotaScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='Cálculo Renda Fundos Imobiliários', font_size=20, bold=True))
        layout.add_widget(Label(text='Preço cota', halign='center'))
        layout.add_widget(Label(text='Informe o valor de cada cota do fundo.', halign='center', color=(0, 0, 0, 1)))
        
        self.preco_input = TextInput(text='0.00', hint_text='R$', input_filter='float', multiline=False)
        layout.add_widget(self.preco_input)
        
        btn_voltar = Button(text='Voltar', size_hint=(0.5, 0.5))
        btn_calcular = Button(text='Calcular', size_hint=(0.5, 0.5), background_color=(0, 0.5, 1, 1))
        btn_voltar.bind(on_press=lambda x: self.manager.current = 'fii_dividend')
        btn_calcular.bind(on_press=self.calcular)
        btn_layout = BoxLayout()
        btn_layout.add_widget(btn_voltar)
        btn_layout.add_widget(btn_calcular)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def calcular(self, instance):
        if float(self.preco_input.text) > 0:
            self.manager.get_screen('fii_resultado').renda_desejada = self.renda_desejada
            self.manager.get_screen('fii_resultado').dividendo_mensal = self.dividendo_mensal
            self.manager.get_screen('fii_resultado').preco_cota = float(self.preco_input.text)
            self.manager.current = 'fii_resultado'
        else:
            self.show_error('Erro: Insira um valor válido para o preço da cota!')

    def show_error(self, message):
        popup = Popup(title='Erro', content=Label(text=message), size_hint=(0.8, 0.5))
        popup.open()

class ResultadoScreen(Screen):
    renda_desejada = 0.0
    dividendo_mensal = 0.0
    preco_cota = 0.0
    result_text = StringProperty('')

    def __init__(self, **kwargs):
        super(ResultadoScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='Cálculo Renda Fundos Imobiliários', font_size=20, bold=True))
        layout.add_widget(Label(text='Resultado', halign='center'))
        
        self.result_label = Label(text=self.result_text, halign='center')
        layout.add_widget(self.result_label)
        
        btn_ok = Button(text='OK', size_hint=(1, 0.5), background_color=(0, 0.5, 1, 1))
        btn_ok.bind(on_press=lambda x: self.manager.current = 'fii_renda')
        layout.add_widget(btn_ok)
        
        self.add_widget(layout)
    
    def on_enter(self):
        if self.preco_cota > 0:
            valor_investido = (self.renda_desejada / self.dividendo_mensal) * self.preco_cota
            self.result_text = f'Você precisa ter R$ {valor_investido:,.2f} investido\\npara ter uma renda mensal de R$ {self.renda_desejada:,.2f}'
            self.result_label.text = self.result_text
        else:
            self.result_text = 'Erro no cálculo. Verifique os valores inseridos.'
            self.result_label.text = self.result_text

# Conversor de Moedas e Criptomoedas
class ConversorScreen(Screen):
    result_text = StringProperty('Resultado: R$ 0.00\\nÚltima atualização: N/A')
    available_currencies = ListProperty([])

    def __init__(self, **kwargs):
        super(ConversorScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        layout.add_widget(Label(text='Conversor de Moedas', font_size=20, bold=True))

        # Campo de valor
        self.amount_input = TextInput(text='100', hint_text='Valor', input_filter='float', multiline=False)
        layout.add_widget(self.amount_input)

        # Dropdown para moeda de origem
        self.from_dropdown = DropDown()
        self.from_btn = Button(text='BRL', size_hint=(1, None), height=44)
        self.from_btn.bind(on_release=self.from_dropdown.open)
        layout.add_widget(self.from_btn)

        # Dropdown para moeda de destino
        self.to_dropdown = DropDown()
        self.to_btn = Button(text='USD', size_hint=(1, None), height=44)
        self.to_btn.bind(on_release=self.to_dropdown.open)
        layout.add_widget(self.to_btn)

        # Botão Converter
        btn_convert = Button(text='Converter', background_color=(0, 0.5, 1, 1))
        btn_convert.bind(on_press=self.convert)
        layout.add_widget(btn_convert)

        # Resultado
        self.result_label = Label(text=self.result_text, halign='center')
        layout.add_widget(self.result_label)

        self.add_widget(layout)
        self.update_currency_dropdowns()

    def update_currency_dropdowns(self):
        self.available_currencies = converter.currencies
        self.from_dropdown.clear_widgets()
        self.to_dropdown.clear_widgets()
        for currency in self.available_currencies:
            btn_from = Button(text=currency, size_hint_y=None, height=44)
            btn_from.bind(on_release=lambda btn, x=currency: self.select_from_currency(x))
            self.from_dropdown.add_widget(btn_from)

            btn_to = Button(text=currency, size_hint_y=None, height=44)
            btn_to.bind(on_release=lambda btn, x=currency: self.select_to_currency(x))
            self.to_dropdown.add_widget(btn_to)

    def select_from_currency(self, currency):
        self.from_btn.text = currency
        self.from_dropdown.select(currency)

    def select_to_currency(self, currency):
        self.to_btn.text = currency
        self.to_dropdown.select(currency)

    def convert(self, instance):
        try:
            amount = float(self.amount_input.text)
            from_currency = self.from_btn.text
            to_currency = self.to_btn.text
            result = converter.convert(amount, from_currency, to_currency)
            update_time = converter.last_updated or 'N/A'
            self.result_text = f'Resultado: {to_currency} {result:,.2f}\\nÚltima atualização: {update_time}'
            self.result_label.text = self.result_text
        except ValueError:
            self.result_text = 'Erro: Insira um valor válido!'
            self.result_label.text = self.result_text

if __name__ == '__main__':
    FIICalculatorApp().run()
