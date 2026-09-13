import os, requests, threading, time
from flask import Flask
from collections import deque
import io

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN") or ""
CHAT_ID = os.environ.get("CHAT_ID") or ""
data = {"XAUUSD": deque(maxlen=100)}

def send_text(t):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": t}, timeout=15)
    except: pass

def send_chart(entry, sl, tp1, tp2, tp3):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        prices = list(data["XAUUSD"])
        if len(prices) < 10:
            prices = [entry-2, entry-1, entry, entry+1, entry+2]*10

        plt.figure(figsize=(8,4))
        plt.plot(prices[-40:], color='black')
        plt.axhline(entry, color='green', linewidth=2)
        plt.axhline(sl, color='red', linewidth=2, linestyle='--')
        plt.axhline(tp1, color='green', linewidth=1, linestyle=':')
        plt.axhline(tp2, color='green', linewidth=1, linestyle='-.')
        plt.axhline(tp3, color='green', linewidth=1, linestyle=':')
        plt.title(f"XAUUSD BUY Ent {entry:.2f} SL {sl:.2f}")
        plt.grid(True, alpha=0.3)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        plt.close('all')
        
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
        data={"chat_id": CHAT_ID, "caption": f"GRAFICO PRO Ent {entry:.2f}"},
        files={"photo": buf}, timeout=20)
    except Exception as e:
        send_text(f"Error grafico: {e}")

def get_price():
    try:
        return float(requests.get("https://api.gold-api.com/price/XAU", timeout=10).json().get("price", 4300))
    except:
        return 4349.0

@app.route("/")
def home(): return "V14.3 LIVE", 200

@app.route("/test")
def test():
    p = get_price()
    data["XAUUSD"].append(p)
    for i in range(30):
        data["XAUUSD"].append(p + i*0.05)
    entry = p
    send_text(f"✅ TEST V14.3 XAU {entry:.2f} enviando grafico...")
    time.sleep(1)
    send_chart(entry, entry-6, entry+5, entry+10, entry+18)
    return "ok grafico enviado", 200

def loop():
    time.sleep(5)
    send_text("🚀 BOT V14.3 FIX RECURSION CONECTADO")
    while True:
        try:
            data["XAUUSD"].append(get_price())
            time.sleep(120)
        except: time.sleep(60)

threading.Thread(target=loop, daemon=True).start()
