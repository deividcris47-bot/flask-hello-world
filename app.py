import os, requests, yfinance as yf
import matplotlib.pyplot as plt
from flask import Flask

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def generar_smc():
    df = yf.download("GC=F", interval="15m", period="5d", auto_adjust=True)
    df = df.dropna().tail(80)
    closes = df['Close'].values
    price = float(closes[-1])
    
    swing_high = float(df['High'].rolling(10).max().iloc[-20])
    swing_low = float(df['Low'].rolling(10).min().iloc[-20])
    strong_high = float(df['High'].max())
    strong_low = float(df['Low'].min())
    
    if price > swing_high:
        side, status = "Compra", "Rompimiento alcista - BOS"
        bos, choch = swing_high, swing_low
    else:
        side, status = "Venta", "Rompimiento bajista - BOS"
        bos, choch = swing_low, swing_high

    fig, ax = plt.subplots(figsize=(10,6), facecolor='#131722')
    ax.set_facecolor('#131722')
    ax.plot(range(len(closes)), closes, color='#2962FF', linewidth=2)
    
    ax.axhline(bos, color='#00E676', ls='--', lw=1.5)
    ax.text(len(closes)*0.65, bos, f'BOS {bos:.2f}', color='#00E676', weight='bold', bbox=dict(facecolor='#00E676', alpha=0.15, boxstyle='round'))
    
    ax.axhline(choch, color='#FF5252', ls='--', lw=1.5)
    ax.text(len(closes)*0.65, choch, f'CHoCH {choch:.2f}', color='#FF5252', weight='bold', bbox=dict(facecolor='#FF5252', alpha=0.15, boxstyle='round'))
    
    ax.axhline(strong_high, color='#FFD740', ls=':', alpha=0.6)
    ax.axhline(strong_low, color='#FFD740', ls=':', alpha=0.6)
    ax.text(2, strong_high, 'Strong High', color='#FFD740', fontsize=8)
    ax.text(2, strong_low, 'Strong Low', color='#FFD740', fontsize=8)
    
    ax.set_title(f'XAUUSD 15M | {status} | {side}', color='white', weight='bold')
    ax.tick_params(colors='#787B86')
    
    plt.savefig('/tmp/chart.png', dpi=250, facecolor='#131722', bbox_inches='tight')
    plt.close()

    sl = price - 6.5 if side=="Compra" else price + 6.5
    tp1, tp2, tp3 = price+4.5, price+8.5, price+14
    if side=="Venta":
        tp1, tp2, tp3 = price-4.5, price-8.5, price-14

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
    caption, path = generar_smc()
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(path, 'rb') as f:
        r = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": f})
    return r.json()

@app.route("/test_token")
def test_token():
    return requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe").json()

@app.route("/")
def home():
    return "Bot SMC Live"
