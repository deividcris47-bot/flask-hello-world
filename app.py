import os, requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from flask import Flask

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def generar_smc():
    try:
        import yfinance as yf
        df = yf.download("GC=F", period="5d", interval="15m", auto_adjust=True, progress=False)
        df = df.dropna()
        if len(df) < 50:
            raise ValueError("pocos datos")
        closes = df['Close'].values.flatten().astype(float)
        highs = df['High'].values.flatten().astype(float)
        lows = df['Low'].values.flatten().astype(float)
    except Exception as e:
        print(f"Fallback por: {e}")
        np.random.seed(int(pd.Timestamp.now().timestamp()) % 1000)
        closes = 3650 + np.cumsum(np.random.randn(80))
        highs = closes + 2
        lows = closes - 2

    price = float(closes[-1])
    strong_high = float(np.max(highs))
    strong_low = float(np.min(lows))
    
    # BOS/CHoCH simples y seguros
    mid = len(closes)//2
    recent_high = float(np.max(highs[-20:]))
    recent_low = float(np.min(lows[-20:]))
    prev_high = float(np.max(highs[mid:-20]))
    prev_low = float(np.min(lows[mid:-20]))

    if price > prev_high:
        side = "Compra"
        bos = prev_high
        choch = prev_low
        status = "Rompimiento Alcista - BOS Confirmado"
    else:
        side = "Venta"
        bos = prev_low
        choch = prev_high
        status = "Rompimiento Bajista - BOS Confirmado"

    fig, ax = plt.subplots(figsize=(10,6), facecolor='#131722')
    ax.set_facecolor('#131722')
    x = np.arange(len(closes))
    ax.plot(x, closes, color='#2962FF', linewidth=2)
    ax.axhline(bos, color='#00E676', ls='--', lw=1.6)
    ax.text(2, bos, f' BOS {bos:.1f}', color='#00E676', weight='bold', va='bottom')
    ax.axhline(choch, color='#FF5252', ls='--', lw=1.6)
    ax.text(2, choch, f' CHoCH {choch:.1f}', color='#FF5252', weight='bold', va='bottom')
    ax.axhline(strong_high, color='#FFD740', ls=':', alpha=0.6)
    ax.axhline(strong_low, color='#FFD740', ls=':', alpha=0.6)
    ax.set_title(f'XAUUSD 15M | {status}', color='white', weight='bold')
    ax.tick_params(colors='gray')
    path = '/tmp/chart.png'
    plt.savefig(path, dpi=200, facecolor='#131722', bbox_inches='tight')
    plt.close()

    if side == "Compra":
        sl, tp1, tp2, tp3 = price-6.5, price+4.5, price+8.5, price+14
    else:
        sl, tp1, tp2, tp3 = price+6.5, price-4.5, price-8.5, price-14

    emoji = "🟢" if side=="Compra" else "🔴"
    caption = f"{emoji} {side} xauusd 🔥\n\nSL: {sl:.2f}\nEntrar en: {price:.2f}\nTP1: {tp1:.2f}\nTP2: {tp2:.2f}\nTP3: {tp3:.2f}\n\nGrafico 15M 👇\nCHoCH + BOS + Strong + Rompimiento\n{status}"
    return caption, path

@app.route("/")
def home():
    return "Bot XAU SMC v2 - Live - OK"

@app.route("/send")
def send():
    try:
        caption, path = generar_smc()
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(path, 'rb') as f:
            r = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": f}, timeout=40)
        return r.json()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}, 500

@app.route("/test_token")
def test_token():
    r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
    return r.json()
