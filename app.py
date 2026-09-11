from flask import Flask
import yfinance as yf
import mplfinance as mpf
import pandas as pd
import requests
from io import BytesIO
import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)

BOT_TOKEN = "8870473192:AAElumHWfjg2paoljk1IANUvRW3dISms5eg"
CHAT_ID = "@TU_CANAL_AQUI"

@app.route('/')
def home():
    return "Bot ORO Velas Live"

@app.route('/enviar_grafico')
def enviar_grafico():
    try:
        df = yf.download("GC=F", period="2d", interval="30m", auto_adjust=True, progress=False)
        
        # FIX DEFINITIVO PARA YAHOO NUEVO
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df = df.dropna()
        df = df.tail(60)

        buf = BytesIO()
        mpf.plot(df, type='candle', style='yahoo',
                 title='XAUUSD ORO - 30M VIP',
                 ylabel='Precio USD',
                 figsize=(10,6),
                 savefig=dict(fname=buf, dpi=150, bbox_inches='tight'))
        buf.seek(0)

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files = {'photo': ('oro_velas.png', buf, 'image/png')}
        data = {'chat_id': CHAT_ID, 'caption': '🔥 ORO VIP - VELAS JAPONESAS 30M\n\nAnalisis Pro Activado\nProxima en 30 min'}

        r = requests.post(url, files=files, data=data)
        return f"Enviado OK: {r.text}"
        
    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
