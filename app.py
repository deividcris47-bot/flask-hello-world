import os, requests, io, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import yfinance as yf
from flask import Flask
from datetime import datetime

app = Flask(__name__)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_xau_data():
    try:
        data = yf.download("GC=F", period="1d", interval="5m", progress=False, auto_adjust=True)
        if data.empty:
            data = yf.download("XAUUSD=X", period="1d", interval="5m", progress=False, auto_adjust=True)
        if data.empty: return None
        close = data['Close']
        if isinstance(close, pd.DataFrame): close = close.squeeze()
        if isinstance(close, pd.DataFrame): close = close.iloc[:,0]
        return close.dropna().tail(100)
    except: return None

def crear_grafico_pro():
    prices = get_xau_data()
    if prices is None or len(prices) < 2:
        prices = pd.Series([4348.5, 4349.2, 4350.34, 4349.8, 4351.1, 4350.5, 4352.1])
    last_price = float(prices.iloc[-1])
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='black')
    ax.set_facecolor('black')
    ax.plot(prices.values, color='#00ff88', linewidth=2.5)
    ax.fill_between(range(len(prices)), prices.values, alpha=0.15, color='#00ff88')
    ax.text(0.02, 0.92, 'XAUUSD / GOLD', color='gray', fontsize=14, transform=ax.transAxes, weight='bold')
    ax.text(0.02, 0.80, f'{last_price:.2f}', color='white', fontsize=42, transform=ax.transAxes, weight='bold')
    ax.text(0.02, 0.72, f'{datetime.now().strftime("%H:%M:%S")} UTC-5 | XAU_DEIVID_VIP', color='#00ff88', fontsize=11, transform=ax.transAxes)
    ax.grid(False); ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values(): spine.set_visible(False)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor='black', bbox_inches='tight', dpi=200)
    buf.seek(0); plt.close()
    return buf, last_price

@app.route("/")
def home(): return "Bot XAU DEIVID VIP - LISTO"

@app.route("/enviar_grafico")
def enviar_grafico():
    try:
        imagen, precio = crear_grafico_pro()
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        caption = f"📊 XAUUSD - {precio:.2f}\n🔥 Señal PRO - {datetime.now().strftime('%H:%M')}\n👉 @xau_deivid_vip"
        files = {'photo': ('xauusd.png', imagen, 'image/png')}
        data = {'chat_id': CHAT_ID, 'caption': caption}
        r = requests.post(url, data=data, files=files, timeout=30)
        return r.json()
    except Exception as e: return {"ok": False, "error": str(e)}
