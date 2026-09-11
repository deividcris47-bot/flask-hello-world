import os
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import yfinance as yf
from flask import Flask
from datetime import datetime
import io

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") # tu @xau_deivid_vip o ID -100xxx

def get_xau_data():
    try:
        # Precio real Oro
        data = yf.download("GC=F", period="1d", interval="5m", progress=False)
        if data.empty:
            data = yf.download("XAUUSD=X", period="1d", interval="5m", progress=False)
        return data['Close'].tail(100)
    except:
        return None

def crear_grafico_pro():
    prices = get_xau_data()
    if prices is None or len(prices) == 0:
        # precio ejemplo si falla internet
        import pandas as pd
        prices = pd.Series([4348.5, 4349.2, 4350.34, 4349.8, 4351.1, 4350.5])

    last_price = float(prices.iloc[-1])

    # ESTILO NEGRO PRO
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='black')
    ax.set_facecolor('black')
    
    ax.plot(prices.values, color='#00ff88', linewidth=2.5)
    ax.fill_between(range(len(prices)), prices.values, alpha=0.15, color='#00ff88')
    
    # Precio grande como tu foto
    ax.text(0.02, 0.92, f'XAUUSD', color='gray', fontsize=14, transform=ax.transAxes, weight='bold')
    ax.text(0.02, 0.80, f'{last_price:.2f}', color='white', fontsize=36, transform=ax.transAxes, weight='bold')
    ax.text(0.02, 0.73, f'{datetime.now().strftime("%H:%M:%S")} UTC-5 | XAU_DEIVID_VIP', color='#00ff88', fontsize=10, transform=ax.transAxes)

    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor='black', bbox_inches='tight', dpi=200)
    buf.seek(0)
    plt.close()
    return buf, last_price

@app.route("/")
def home():
    return "Bot XAU DEIVID VIP LIVE - /enviar_grafico"

@app.route("/enviar_grafico")
def enviar_grafico():
    try:
        imagen, precio = crear_grafico_pro()
        
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        caption = f"📊 XAUUSD - {precio:.2f}\n🔥 Señal PRO - {datetime.now().strftime('%H:%M')} \n👉 @xau_deivid_vip"

        files = {'photo': ('xauusd.png', imagen, 'image/png')}
        data = {'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}

        r = requests.post(url, data=data, files=files, timeout=30)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
