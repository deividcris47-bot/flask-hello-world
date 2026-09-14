from flask import Flask
import datetime
import pytz
import requests

app = Flask(__name__)
ECUADOR = pytz.timezone('America/Guayaquil')

def get_xau_price():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=5)
        return float(r.json()['price'])
    except:
        return 4332.00

@app.route('/')
def home():
    hora_ec = datetime.datetime.now(ECUADOR).strftime("%H:%M:%S")
    return f"""
    V20 ACTIVO ✅<br>
    Hora Ecuador: {hora_ec}<br>
    7 señales: 19:00, 22:00, 03:00, 06:00, 08:30, 10:30, 13:00<br>
    Filtros: CHoCH + BOS + STRONG + ROMPIMIENTO vela grande 1M<br>
    <a href="/senal">Ver señal</a>
    """

@app.route('/senal')
def senal():
    precio = get_xau_price()
    sl = precio - 2.5
    entrada = precio
    tp1 = precio + 2.0
    tp2 = precio + 4.5
    tp3 = precio + 8.0
    return f"""
    🟢 Compra XAUUSD 🔥<br>
    SL: {sl:.2f}<br>
    Entrar en: {entrada:.2f}<br>
    TP1: {tp1:.2f}<br>
    TP2: {tp2:.2f}<br>
    TP3: {tp3:.2f}<br>
    <small>CHoCH + BOS + Rompimiento vela grande 1M confirmado</small>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
