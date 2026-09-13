from flask import Flask
import threading, time
from datetime import datetime
import pytz
import yfinance as yf

app = Flask(__name__)
LAST_ERROR = "Ninguno"

def hora_ec():
    return datetime.now(pytz.timezone('America/Guayaquil')).strftime('%H:%M:%S')

def obtener_precio(ticker):
    try:
        df = yf.download(ticker, period="2d", interval="1h", progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 2:
            return None
        return float(df['Close'].iloc[-1])
    except Exception as e:
        global LAST_ERROR
        LAST_ERROR = str(e)[:100]
        return None

def bot_loop():
    print(">>> BOT LOOP INICIADO V7 FIX")
    while True:
        try:
            p_xau = obtener_precio("GC=F")
            p_btc = obtener_precio("BTC-USD")
            p_eur = obtener_precio("EURUSD=X")
            print(f"{hora_ec()} XAU={p_xau} BTC={p_btc} EUR={p_eur} | {LAST_ERROR}")
            # Aquí va tu lógica de TP1 TP2 TP3 y envío a Telegram
        except Exception as e:
            print(f"Error loop: {e}")
        time.sleep(60)

# Iniciar bot en segundo plano para no bloquear Flask
threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home():
    return f"BOT V7 FIX ACTIVO - {hora_ec()} EC - Error: {LAST_ERROR}", 200

@app.route('/test')
def test():
    p = obtener_precio("GC=F")
    return f"TEST OK V7 - XAU: {p} - {hora_ec()} EC", 200

@app.route('/enviar_grafico')
def grafico():
    return "GRAFICO OK V7", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
