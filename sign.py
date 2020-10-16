import logging
from hashlib import sha256


SECRET = 'SecretKey01'


# Creates Sign
def comb_sign(**kwargs):
    """
    Строка формируется следующим образом: все обязательные параметры
    запроса упорядочиваются в алфавитном порядке ключей, значения
    конкатенируются через знак двоеточие (“:”), в конце добавляется
    секретный ключ (без знака ":"), от полученной строки генерируется
    sha256 хеш и его HEX-представление передается в параметре запроса
    sign.
    Для каждого метода свой набор обязательных параметров, также могут
    передаваться дополнительные параметры, но в формировании подписи
    они не участвуют.

    E.g.
    keys_sorted = ['amount', 'currency', 'payway', 'shop_id', 'shop_order_id']
    12.34:643:payeer_rub:5:4126SecretKey01

    https://xorbin.com/tools/sha256-hash-calculator

    Строка для генерации sha256 хеша имеет вид: 10.00:643:5:101SecretKey01
    HEX-представление хеша:
    
    sign = e4580435a252d61ef91b71cb23ed7bee4d77de94ced36411526d2ce3b66ada8f
    """

    # Combines key parameters for creating Sign
    keys_sorted = sorted([key for key in kwargs.keys()])
    sign = ''
    for key in keys_sorted:
        sign += str(kwargs[key])
        sign += ':'
    sign = sign[:-1] + SECRET
    
    # Hashing Sign using sha256
    sha256_sign = sha256(sign.encode('utf-8')).hexdigest()
    # app.logger.debug(f'New sign for {sign} generated successfully! {sha256_sign}')
    return sha256_sign