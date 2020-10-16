import requests
import logging
from decimal import Decimal
from logging.handlers import SysLogHandler

from flask import Flask, render_template, redirect, request, Response, jsonify

from sign import comb_sign
from models import Payment
from extensions import db
from currency import moneyfmt


SHOP_ID = 5
PAYWAY = 'payeer_rub'
SHOP_ORDER_ID = 101

CURRENCIES = {
    'RUB': 643,
    'EUR': 978,
    'USD': 840,
}


app = Flask(__name__)
app.debug = True
app.secret_key = 'development key'

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///database.db'
db.init_app(app)

# Logging
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)
    
syslog_handler = SysLogHandler()
syslog_handler.setLevel(logging.ERROR)
app.logger.addHandler(syslog_handler)


@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "POST":
        currency = request.form.get('currency')
        amount = Decimal(request.form.get('amount'))
        formated_amount = moneyfmt(amount)
        currency_code = CURRENCIES.get(currency)
        description = request.form.get('description')
        
        app.logger.debug('Trying to create a new payment')
        app.logger.debug(f'{amount}({formated_amount}), {currency}, {description}')

        # PAY method(for EUR)
        if currency_code == 978:
            app.logger.debug('PAY METHOD. Trying to create a new payment')
            sign = comb_sign(amount=formated_amount, currency=currency_code, shop_id=SHOP_ID, shop_order_id=SHOP_ORDER_ID)
            app.logger.debug(f'PAY METHOD. Sign created successfully: {sign}')
            payment_form = f'''
            <h2>Are you sure you wanna send {amount}{currency} ?</h2>
                <form name='Pay' method="POST" action="https://pay.piastrix.com/en/pay">
                    <input type="hidden" name="amount" value="{formated_amount}"/>
                    <input type="hidden" name="currency" value="{currency_code}"/>
                    <input type="hidden" name="shop_id" value="{SHOP_ID}"/>
                    <input type="hidden" name="sign" value="{sign}"/>
                    <input type="hidden" name="shop_order_id" value="{SHOP_ORDER_ID}"/>
                    <input type="hidden" name="description" value="{description}"/>
                    <button type='submit'>Submit</button>
                </form>
            '''
            # Creating Payment
            # Piastrix gotta have callbacks for those purposes,
            #   i did not stick to the documentation, so it just creates a payment object
            payment_object = Payment(amount=formated_amount, currency=currency, description=description)
            app.logger.debug(f'PAY METHOD. Payment {payment_object}')                
            db.session.add(payment_object)
            db.session.commit()

            return  payment_form

        # BILL method(for RUB)
        elif currency_code == 643:
            app.logger.debug('BILL METHOD. Trying to create a new payment')
            sign = comb_sign(payer_currency=currency_code, shop_amount=formated_amount,
                shop_currency=currency_code, shop_id=SHOP_ID, shop_order_id=SHOP_ORDER_ID)
            app.logger.debug(f'BILL METHOD. Sign created successfully: {sign}')
            data = {
                "payer_currency": currency_code,
                "shop_amount": formated_amount,
                "shop_currency": currency_code,
                "shop_id": SHOP_ID,
                "shop_order_id": SHOP_ORDER_ID,
                "sign": sign,
            }
            app.logger.debug(data)
            headers = {'Content-type': 'application/json'}
            try:
                response = requests.post('https://core.piastrix.com/bill/create', 
                    json=data, headers=headers)
            except requests.exceptions.RequestException as e:
                app.logger.warning(f'BILL METHOD. Exception during sending request: {e}')
                return f'Error: {e}'            

            response_json = response.json()
            
            app.logger.debug('BILL METHOD. Request handled successfully')
            app.logger.debug(response_json)

            if response_json.get('error_code') == 0 and response_json.get('result') == True:
                app.logger.debug('BILL METHOD. Result data exists')
                # Creating Payment
                payment_object = Payment(amount=formated_amount, currency=currency, description=description)
                app.logger.debug(f'BILL METHOD. Payment {payment_object}')                
                db.session.add(payment_object)
                db.session.commit()
                return '<h1>Successfully created</h1>'
            app.logger.warning('BILL METHOD. No result data')
        
        # Invoice method(for USD and other currencies) 
        else:
            sign = comb_sign(currency=currency_code, amount=formated_amount,
                payway=PAYWAY, shop_id=SHOP_ID, shop_order_id=SHOP_ORDER_ID)
            app.logger.debug(f'INVOICE METHOD. Sign created successfully: {sign}')

            data = {
                "amount": formated_amount,
                "currency": currency_code,
                "payway": PAYWAY,
                "shop_id": SHOP_ID,
                "shop_order_id": SHOP_ORDER_ID,
                "sign": sign,
            }
            app.logger.debug(data)

            headers = {'Content-type': 'application/json'}
            try:
                response = requests.post('https://core.piastrix.com/invoice/create', 
                    json=data, headers=headers)
            except requests.exceptions.RequestException as e:
                app.logger.warning(f'INVOICE METHOD. Exception during sending request: {e}')
                return f'Error: {e}'            

            response_json = response.json()
                
            app.logger.debug('INVOICE METHOD. Request handled successfully')
            app.logger.debug(response_json)

            if response_json.get('error_code') == 0 and response_json.get('result') == True:
                app.logger.debug('INVOICE METHOD. Result data exists')

                method = response_json['data'].get('method')
                url = response_json['data'].get('url')

                lang = response_json['data']['data'].get('lang')
                m_curorderid = response_json['data']['data'].get('m_curorderid')
                m_historyid = response_json['data']['data'].get('m_historyid')
                m_historytm = response_json['data']['data'].get('m_historytm')
                referer = response_json['data']['data'].get('referer')

                # Creating Payment
                payment_object = Payment(amount=formated_amount, currency=currency, description=description)
                app.logger.debug(f'INVOICE METHOD. Payment {payment_object}')                
                db.session.add(payment_object)
                db.session.commit()

                invoice_form = f"""
                    <form method="{method}" action="{url}">
                        <input name="lang" value="{lang}" />
                        <input name="m_curorderid" value="{m_curorderid}"/>
                        <input name="m_historyid" value="{m_historyid}"/>
                        <input name="m_historytm" value="{m_historytm}"/>
                        <input name="referer" value="{referer}"/>
                        <input type="submit"/>
                    </form>
                """
                return invoice_form
            app.logger.warning('INVOICE METHOD. No result data')
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
