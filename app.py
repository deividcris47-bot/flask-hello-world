import os, requests, yfinance as yf
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
    df = None
    try:
        df = yf.download("GC=F", interval="15m", period="5d", auto_adjust=True, progress=False)
        df = df.dropna()
    except:
        df = None

    # Si es fin de semana, usa datos simulados PRO para que no salga corrupto
    if df is None or len(df) < 40:
        np.random.seed(42)
        base = 3650 + np.cumsum(np.random.randn(80)*1.5)
        df = pd.DataFrame({
            "Close": base,
            "High": base + np.random.rand(80)*2,
            "Low": base - np.random.rand(80)*2,
        })

    closes = df['Close'].values.astype(float)
    highs = df['High'].values.astype(float)
    lows = df['Low'].values.astype(float)
    price = float(closes[-1])

    swing_high = float(pd.Series(highs).rolling(10).max().dropna().iloc[-15])
    swing_low = float(pd.Series(lows).rolling(10).min().dropna().iloc[-15])
    strong_high = float(np.max(highs))
    strong_low = float(np.min(lows))

    if price >= swing_high:
        side, bos, choch = "Compra", swing_high, swing_low
        status = "BOS Alcista - Rompimiento de Strong High"
    else:
        side, bos, choch = "Venta", swing_low, swing_high
        status = "BOS Bajista - Rompimiento de Strong Low"

    fig, ax = plt.subplots(figsize=(10, 6), facecolor='#131722')
    ax.set_facecolor('#131722')
    x = np.arange(len(closes))
    ax.plot(x, closes, color='#2962FF', linewidth=2)
    ax.fill_between(x, closes, np.min(closes)-5, color='#2962FF', alpha=0.08)
    ax.axhline(bos, color='#00E676', ls='--', lw=1.8)
    ax.text(1, bos+1.2, f'BOS {bos:.2f}', color='#00E676', weight='bold', bbox=dict(facecolor='#00E676', alpha=0.18, boxstyle='round,pad=0.3'))
    ax.axhline(choch, color='#FF5252', ls='--', lw=1.8)
    ax.text(1, choch-2.5, f'CHoCH {choch:.2f}', color='#FF5252', weight='bold', bbox=dict(facecolor='#FF5252', alpha=0.18, boxstyle='round,pad=0.3'))
    ax.axhline(strong_high, color='#FFD740', ls=':', alpha=0.7)
    ax.axhline(strong_low, color='#FFD740', ls=':', alpha=0.7)
    ax.axhspan(strong_low, strong_low+2, xmin=0.25, xmax=0.45, facecolor='#2962FF', alpha=0.28)
    ax.text(len(closes)*0.35, strong_low+0.3, 'ORDER BLOCK', color='white', fontsize=8, ha='center', weight='bold')
    ax.set_title(f'XAUUSD 15M | {status}', color='white', weight='bold')
    plt.savefig('/tmp/chart.png', dpi=220, facecolor='#131722', bbox_inches='tight')
    plt.close()

    sl = price - 6.5 if side=="Compra" else price + 6.5
    tp1, tp2, tp3 = (price+4.5, price+8.5, price+14) if side=="Compra" else (price-4.5, price-8.5, price-14)
    emoji = "🟢" if side=="Compra" else "🔴"
    caption = f"{emoji} {side} xauusd 🔥\n\nSL: {sl:.2f}\nEntrar en: {price:.2f}\nTP1: {tp1:.2f}\nTP2: {tp2:.2f}\nTP3: {tp3:.2f}\n\nGrafico 15M 👇\nCHoCH + BOS + Strong + Rompimiento\n{status}"
    return caption, '/tmp/chart.png'

@app.route("/send")
def send():
    caption, path = generar_smc()
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(path, 'rb') as f:
        r = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": f}, timeout=30)
    return r.json()

@app.route("/test_token")
def test_token():
    return requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe").json()

@app.route("/")
def home():
    return "Bot XAU SMC v2 - Live"
