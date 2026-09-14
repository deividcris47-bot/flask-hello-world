import os, requests, io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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
        df = yf.download("GC=F", period="5d", interval="15m", auto_adjust=True, progress=False)
        df = df.dropna()
        if len(df) < 60:
            raise ValueError("pocos datos")
        return df.tail(80)
    except Exception as e:
        print(f"Usando datos sintéticos por: {e}")
        dates = pd.date_range(end=datetime.now(), periods=80, freq='15min')
        np.random.seed(5)
        closes = 4375 + np.cumsum(np.random.randn(80)*1.5)
        df = pd.DataFrame({
            'Open': closes + np.random.randn(80)*0.5,
            'High': closes + 2.5,
            'Low': closes - 2.5,
            'Close': closes
        }, index=dates)
        return df

def generar_smc_v3():
    df = get_data()
    closes = df['Close'].values.flatten().astype(float)
    highs = df['High'].values.flatten().astype(float)
    lows = df['Low'].values.flatten().astype(float)
    price = float(closes[-1])
    
    strong_high = float(np.max(highs))
    strong_low = float(np.min(lows))
    idx_high = int(np.argmax(highs))
    idx_low = int(np.argmin(lows))
    
    prev_high = float(np.max(highs[:-20]))
    prev_low = float(np.min(lows[:-20]))
    recent_high = float(np.max(highs[-20:]))
    recent_low = float(np.min(lows[-20:]))

    if price > prev_high:
        side = "Compra"
        bos_level = prev_high
        choch_level = prev_low
        status = "Rompimiento Alcista - BOS Confirmado"
        color_side = "#00E676"
    else:
        side = "Venta"
        bos_level = prev_low
        choch_level = prev_high
        status = f"Rompimiento Bajista - BOS Confirmado"
        color_side = "#FF5252"

    # SL / TP
    if side == "Compra":
        sl = price - 6.5
        tp1, tp2, tp3 = price+4.5, price+8.5, price+14
        entry = price
    else:
        sl = price + 6.5
        tp1, tp2, tp3 = price-4.5, price-8.5, price-14
        entry = price

    # --- GRAFICO PRO ---
    fig, ax = plt.subplots(figsize=(12, 7), facecolor='#0E0E10')
    ax.set_facecolor('#131722')
    
    x = np.arange(len(df))
    # Linea de precio azul pro
    ax.plot(x, closes, color='#2962FF', linewidth=2.2, zorder=3)
    # Sombra bajo precio
    ax.fill_between(x, closes, np.min(lows)-2, color='#2962FF', alpha=0.07)

    # BOS
    ax.axhline(bos_level, color='#00E676', linestyle='--', linewidth=1.8, alpha=0.9)
    ax.text(1, bos_level, f' BOS {bos_level:.1f} ', color='black', backgroundcolor='#00E676', weight='bold', fontsize=8, va='center')

    # CHoCH
    ax.axhline(choch_level, color='#FF5252', linestyle='--', linewidth=1.8, alpha=0.9)
    ax.text(1, choch_level, f' CHoCH {choch_level:.1f} ', color='white', backgroundcolor='#FF5252', weight='bold', fontsize=8, va='center')

    # Strong High / Low
    ax.axhline(strong_high, color='#FFD740', linestyle=':', linewidth=1.2, alpha=0.8)
    ax.text(len(df)-25, strong_high, f' Strong High {strong_high:.1f}', color='#FFD740', fontsize=7, va='bottom')
    ax.axhline(strong_low, color='#FFD740', linestyle=':', linewidth=1.2, alpha=0.8)
    ax.text(len(df)-25, strong_low, f' Strong Low {strong_low:.1f}', color='#FFD740', fontsize=7, va='top')

    # Order Block (zona)
    ob_top = choch_level
    ob_bottom = choch_level - (6 if side=="Venta" else -6)
    ax.axhspan(min(ob_top, ob_bottom), max(ob_top, ob_bottom), color='#7C4DFF', alpha=0.18)
    ax.text(1, (ob_top+ob_bottom)/2, ' ORDER BLOCK ', color='white', backgroundcolor='#7C4DFF', fontsize=7, weight='bold')

    # Entrada
    ax.axhline(entry, color='white', linestyle='-', linewidth=1, alpha=0.7)

    # Ejes
    ax.set_title(f'XAUUSD 15M | {status} | {datetime.now().strftime("%d %b %H:%M")}', color='white', fontsize=11, weight='bold', pad=15)
    
    # Fechas abajo reales
    step = len(df)//6
    ax.set_xticks(x[::step])
    labels = [pd.to_datetime(t).strftime('%d %H:%M') for t in df.index[::step]]
    ax.set_xticklabels(labels, color='#8E8E93', fontsize=8)
    ax.tick_params(axis='y', colors='#8E8E93', labelsize=8)
    ax.grid(color='#23262F', alpha=0.4, linewidth=0.5)
    
    for spine in ax.spines.values():
        spine.set_color('#23262F')

    path = '/tmp/chart_v3.png'
    plt.tight_layout()
    plt.savefig(path, dpi=250, facecolor='#0E0E10', bbox_inches='tight')
    plt.close()

    emoji = "🟢" if side=="Compra" else "🔴"
    caption = f"{emoji} {side} xauusd 🔥\n\nSL: {sl:.2f}\nEntrar en: {entry:.2f}\nTP1: {tp1:.2f}\nTP2: {tp2:.2f}\nTP3: {tp3:.2f}\n\nGrafico 15M 👇\nCHoCH + BOS + Strong + Rompimiento\n{status}"
    return caption, path

@app.route("/")
def home():
    return "Bot XAU SMC v3 PRO - Live"

@app.route("/send")
def send():
    try:
        caption, path = generar_smc_v3()
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(path, 'rb') as f:
            r = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": f}, timeout=50)
        return r.json()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}, 500

@app.route("/test_token")
def test_token():
    r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
    return r.json()
