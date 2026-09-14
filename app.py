import os, requests, yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def generar_grafico_smc():
    # 1. XAUUSD 15M real
    df = yf.download("GC=F", interval="15m", period="5d", auto_adjust=True)
    df = df.dropna().tail(80)
    closes = df['Close'].values
    
    price = float(closes[-1])
    # Detectar estructura SMC simple
    swing_high = float(df['High'].rolling(10).max().iloc[-20])
    swing_low = float(df['Low'].rolling(10).min().iloc[-20])
    strong_high = float(df['High'].max())
    strong_low = float(df['Low'].min())
    
    # BOS si rompe strong, CHoCH si rompe swing contrario
    if price > swing_high:
        side = "Compra"
        bos_level = swing_high
        choch_level = swing_low
        status = "Rompimiento alcista - BOS confirmado"
    else:
        side = "Venta"
        bos_level = swing_low
        choch_level = swing_high
        status = "Rompimiento bajista - BOS confirmado"
    
    # 2. Graficar estilo TradingView PRO
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='#131722')
    ax.set_facecolor('#131722')
    
    x = range(len(closes))
    ax.plot(x, closes, color='#2962FF', linewidth=1.8)
    ax.fill_between(x, closes, min(closes)-5, color='#2962FF', alpha=0.08)
    
    # BOS
    ax.axhline(bos_level, color='#00E676', linestyle='--', linewidth=1.5, alpha=0.8)
    ax.text(len(closes)*0.6, bos_level+1, f'BOS - {bos_level:.2f}', color='#00E676', fontsize=10, weight='bold',
            bbox=dict(facecolor='#00E676', alpha=0.15, boxstyle='round,pad=0.3'))
    
    # CHoCH
    ax.axhline(choch_level, color='#FF5252', linestyle='--', linewidth=1.5, alpha=0.8)
    ax.text(len(closes)*0.6, choch_level-2, f'CHoCH - {choch_level:.2f}', color='#FF5252', fontsize=10, weight='bold',
            bbox=dict(facecolor='#FF5252', alpha=0.15, boxstyle='round,pad=0.3'))
    
    # Strong
    ax.axhline(strong_high, color='#FFD740', linestyle=':', linewidth=1, alpha=0.6)
    ax.text(1, strong_high, 'Strong High', color='#FFD740', fontsize=8)
    ax.axhline(strong_low, color='#FFD740', linestyle=':', linewidth=1, alpha=0.6)
    ax.text(1, strong_low, 'Strong Low', color='#FFD740', fontsize=8)
    
    # Order Block
    ax.axhspan(strong_low, strong_low+2, xmin=0.2, xmax=0.4, facecolor='#2962FF', alpha=0.25)
    ax.text(len(closes)*0.2, strong_low+0.5, 'ORDER BLOCK', color='white', fontsize=8, ha='center')
    
    ax.set_title(f'XAUUSD 15M | {status} | {side}', color='white', fontsize=13, weight='bold', pad=15)
    ax.tick_params(colors='#787B86')
    for spine in ax.spines.values():
        spine.set_color('#363A45')
    
    plt.tight_layout()
    plt.savefig('/tmp/chart.png', dpi=250, facecolor='#131722', bbox_inches='tight')
    plt.close()
    
    # 3. SL TP
    if side == "Compra":
        sl = price - 6.5
        tp1, tp2, tp3 = price + 4.5, price + 8.5, price + 14
    else:
        sl = price + 6.5
        tp1, tp2, tp3 = price - 4.5, price - 8.5, price - 14
    
    caption = f"""{"🟢" if side=="Compra" else "🔴"} {side} xauusd 🔥

SL: {sl:.2f}
Entrar en: {price:.2f}
TP1: {tp1:.2f}
TP2: {tp2:.2f}
TP3: {tp3:.2f}

Grafico 15M 👇
CHoCH + BOS + Strong + Rompimiento
{status}"""
    
    return caption, '/tmp/chart.png'

@app.route("/send")
def send():
    caption, path = generar_grafico_smc()
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(path, 'rb') as f:
        r = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}, files={"photo": f})
    return r.json()

@app.route("/test_token")
def test_token():
    return requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe").json()

@app.route("/")
def home():
    return "Bot XAU VIP con SMC activo"
