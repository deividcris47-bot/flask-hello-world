from flask import Flask
import datetime
import pytz

app = Flask(__name__)
ECUADOR = pytz.timezone('America/Guayaquil')

@app.route('/')
def home():
    hora_ec = datetime.datetime.now(ECUADOR).strftime("%H:%M:%S")
    return f"""
    V20 ACTIVO ✅<br>
    Hora Ecuador: {hora_ec}<br>
    7 señales: 19:00, 22:00, 03:00, 06:00, 08:30, 10:30, 13:00<br>
    Filtros: CHoCH + BOS + STRONG + ROMPIMIENTO vela grande 1M
    """

@app.route('/senal')
def senal():
    # Aquí va tu lógica CHoCH/BOS/Rompimiento con API de Binance/OANDA
    # No MT5
    return """
    🟢 Compra XAUUSD 🔥<br>
    SL: 4329.50<br>
    Entrar en: 4332.00<br>
    TP1: 4334.00<br>
    TP2: 4336.50<br>
    TP3: 4340.00
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
