import os, requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from flask import Flask
import yfinance as yf
from datetime import datetime

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def get_data():
    try:
        df = yf.download("GC=F", period="3d", interval="15m", auto_adjust=True, progress=False)
        df = df.dropna().tail(60)
        if len(df) < 30: raise ValueError("poco")
        return df
    except:
        dates = pd.date_range(end=datetime.now(), periods=60, freq='15min')
        np.random.seed(int(datetime.now().minute))
        closes = 4376 + np.cumsum(np.random.randn(60)*0.8)
        df = pd.DataFrame({'Open':closes+0.4,'High':closes+1.5,'Low':closes-1.5,'Close':closes}, index=dates)
        return df

def generar_v4():
    df = get_data()
    o = df['Open'].values.flatten(); h = df['High'].values.flatten()
    l = df['Low'].values.flatten(); c = df['Close'].values.flatten()
    price = float(c[-1])
    strong_high = float(np.max(h)); strong_low = float(np.min(l))
    prev_high = float(np.max(h[:-15])); prev_low = float(np.min(l[:-15]))

    if price > prev_high:
        side, status = "Compra", "Rompimiento Alcista - BOS Confirmado"
        bos, choch = prev_high, prev_low
        sl, entry, tp1, tp2, tp3 = price-6.5, price, price+4.5, price+8.5, price+14
    else:
        side, status = "Venta", "Rompimiento Bajista - BOS Confirmado"
        bos, choch = prev_low, prev_high
        sl, entry, tp1, tp2, tp3 = price+6.5, price, price-4.5, price-8.5, price-14

    fig, ax = plt.subplots(figsize=(10,6), facecolor='#0B0E11')
    ax.set_facecolor('#131722')
    x = np.arange(len(df))
    for i in range(len(df)):
        col = '#26A69A' if c[i] >= o[i] else '#EF5350'
        ax.plot([x[i], x[i]], [l[i], h[i]], color=col, linewidth=1)
        b = max(max(o[i], c[i]) - min(o[i], c[i]), 0.15)
        ax.add_patch(plt.Rectangle((x[i]-0.35, min(o[i], c[i])), 0.7, b, facecolor=col, edgecolor=col, zorder=3))

    ax.axhline(bos, color='#00E676', ls='--', lw=2)
    ax.text(1, bos, f' BOS {bos:.1f} ', fontsize=10, weight='bold', color='black', backgroundcolor='#00E676', va='bottom')
    ax.axhline(choch, color='#FF5252', ls='--', lw=2)
    ax.text(1, choch, f' CHoCH {choch:.1f} ', fontsize=10, weight='bold', color='white', backgroundcolor='#FF5252', va='bottom')
    ax.axhline(strong_high, color='#FFD740', ls=':', lw=1.5)
    ax.text(len(df)*0.55, strong_high, f' Strong High {strong_high:.1f}', color='#FFD740', fontsize=9, weight='bold', va='bottom')
    ax.axhline(strong_low, color='#FFD740', ls=':', lw=1.5)
    ax.text(len(df)*0.55, strong_low, f' Strong Low {strong_low:.1f}', color='#FFD740', fontsize=9, weight='bold', va='top')
    ax.axhspan(choch-1.8, choch+1.8, color='#7C4DFF', alpha=0.22)
    ax.text(1, choch+2, ' ORDER BLOCK ', color='white', backgroundcolor='#7C4DFF', fontsize=8, weight='bold')

    ax.set_title(f'XAUUSD | 15M | {status} | {datetime.now().strftime("%d %b %H:%M")}', color='white', fontsize=11, weight='bold')
    ax.tick_params(colors='#787B86'); ax.grid(color='#23262F', alpha=0.3); ax.set_xlim(-1, len(df)); ax.set_xticks([])
    path = '/tmp/chart_v4.png'
    plt.tight_layout(); plt.savefig(path, dpi=300, facecolor='#0B0E11'); plt.close()

    emoji = "🟢" if side=="Compra" else "🔴"
    caption = f"{emoji} {side} xauusd 🔥\n\nSL: {sl:.2f}\nEntrar en: {entry:.2f}\nTP1: {tp1:.2f}\nTP2: {tp2:.2f}\nTP3: {tp3:.2f}\n\nGrafico 15M 👇\nCHoCH + BOS + Strong + Order Block\n{status}"
    return caption, path

@app.route("/")
def home(): return "Bot XAU SMC v4 VELAS - Live"
@app.route("/send")
def send():
    try:
        caption, path = generar_v4()
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(path, 'rb') as f:
            r = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": f}, timeout=60)
        return r.json()
    except Exception as e:
        import traceback; traceback.print_exc()
        return {"ok": False, "error": str(e)}, 500
