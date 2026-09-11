from flask import Flask
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import os
import requests
from io import BytesIO

app = Flask(__name__)

TOKEN = "AQUI_TU_TOKEN_DE_TELEGRAM"
CHAT_ID = "AQUI_TU_ID_DE_CANAL"

def generar_grafico_velas():
    # Descargar ORO
    data = yf.download("GC=F", period="1d", interval="15m")
    
    # Calcular RSI rápido
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # Estilo pro
    style = mpf.make_mpf_style(base_mpf_style='tradingview', rc={'font.size': 10})
    
    # Guardar imagen
    buf = BytesIO()
    mpf.plot(data, type='candle', style=style, title='ORO (XAUUSD) - VIP 30M\nRSI: {:.1f}'.format(data['RSI'].iloc[-1]),
             ylabel='Precio', volume=False, figsize=(10,6), savefig=dict(fname=buf, dpi=150))
    buf.seek(0)
    return buf

@app.route('/enviar_grafico')
def enviar_grafico():
    try:
        buf = generar_grafico_velas()
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        files = {'photo': ('oro_velas.png', buf)}
        data = {'chat_id': CHAT_ID, 'caption': '🔥 ORO VIP - Velas Japonesas 30M\n\nRSI + Tendencia\n\nPróxima señal en 30 min\n@TuCanalVIP'}
        r = requests.post(url, files=files, data=data)
        return f"Enviado: {r.text}"
    except Exception as e:
        return f"Error: {e}"

@app.route('/')
def home():
    return "Bot Oro Velas Japonesas ACTIVO"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
