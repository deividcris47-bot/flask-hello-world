from flask import Flask
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import requests
from io import BytesIO
import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)

# --- PEGA AQUI TUS DATOS ---
BOT_TOKEN = "AQUI_TU_TOKEN"
CHAT_ID = "AQUI_TU_CHAT_ID"
# ---------------------------

@app.route('/')
def home():
    return "Bot ORO Velas Live"

@app.route('/enviar_grafico')
def enviar_grafico():
    try:
        # Datos ORO 15m
        df = yf.download("GC=F", period="1d", interval="15m", auto_adjust=True)
        df = df.tail(50) # ultimas 50 velas

        # Crear grafico de velas
        buf = BytesIO()
        mpf.plot(df, type='candle', style='yahoo', 
                 title='XAUUSD ORO - 30M VIP',
                 ylabel='Precio',
                 figsize=(10,6),
                 savefig=dict(fname=buf, dpi=120, bbox_inches='tight'))
        buf.seek(0)

        # Enviar a Telegram
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files = {'photo': ('oro_velas.png', buf, 'image/png')}
        data = {'chat_id': CHAT_ID, 'caption': '🔥 ORO VIP - VELAS JAPONESAS 30M\n\nTendencia: Alcista/Bajista\nSoporte y Resistencia\n\nProxima en 30 min ⏰'}
        
        r = requests.post(url, files=files, data=data)
        return f"Enviado OK: {r.text}"
    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
