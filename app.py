import os, requests, threading, time
from flask import Flask
from collections import deque
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from datetime import datetime

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN") or ""
CHAT_ID = os.environ.get("CHAT_ID") or ""

data = {"XAUUSD": deque(maxlen=100)}

def send_telegram(text):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
    except: pass

def send_chart_pro(symbol, prices_list, direction, entry, sl, tp1, tp2, tp3):
    try:
        prices = list(prices_list)
        if len(prices) < 20:
            prices = prices + [prices[-1]]*20
        prices = prices[-50:]

        fig, ax = plt.subplots(figsize=(10,4.5))
        ax.plot(prices, color='#1b5e20', linewidth=1.5)
        
        # Lineas como tu foto
        ax.axhline(entry, color='green', linewidth=3, label=f'ENTRADA {entry:.2f}')
        ax.axhline(sl, color='red', linestyle='--', linewidth=2, label=f'SL {sl:.2f}')
        ax.axhline(tp1, color='#4caf50', linestyle=':', linewidth=1.5, label=f'TP1 {tp1:.2f}')
        ax.axhline(tp2, color='#388e3c', linestyle='-.', linewidth=1.5, label=f'TP2 {tp2:.2f}')
        ax.axhline(tp3, color='#2e7d32', linestyle=(0,(2,2)), linewidth=1.5, label=f'TP3 {tp3:.2f}')

        accion = "COMPRAR EN LINEA VERDE" if direction=="BUY" else "VENDER EN LINEA ROJA"
        ax.set_title(f"{symbol} - 15M -> 1M/3M - {accion}", fontsize=11, fontweight='bold', loc='left')
        ax.legend(loc='upper left', fontsize=7)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()

        bio = io.BytesIO()
        plt.savefig(bio, format='png', dpi=130)
        bio.seek(0)
        plt.close()

        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        requests.post(url, data={"chat_id": CHAT_ID, "caption": f"📊 {symbol} {direction}\nEnt: {entry:.2f} | SL: {sl:.2f} | TP3: {tp3:.2f}"}, files={"photo": bio}, timeout=20)
        print("Grafico enviado OK")
    except Exception as e:
        print(f"Error grafico: {e}")
        send_telegram(f"Error grafico: {e}")

def get_price_xau():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r.get("price", 4349))
    except:
        return 4349.70

@app.route("/")
def home(): return "Bot V14.2 LIVE", 200

@app.route("/test")
def test():
    price = get_price_xau()
    data["XAUUSD"].append(price)
    # simular mas datos para que el grafico se vea con curva
    for i in range(40):
        data["XAUUSD"].append(price + (i*0.1) - 2 + (i%3)*0.3)

    entry = price
    sl = entry - 6
    tp1 = entry + 5
    tp2 = entry + 10
    tp3 = entry + 18

    send_telegram(f"✅ TEST V14.2 GRAFICO\nXAU: {entry:.2f}\nEnviando imagen PRO...")
    time.sleep(1)
    send_chart_pro("XAUUSD", data["XAUUSD"], "BUY", entry, sl, tp1, tp2, tp3)
    return "ok grafico enviado", 200

def bot_loop():
    time.sleep(5)
    send_telegram("🚀 BOT V14.2 CONECTADO\nGrafico PRO FIX listo\nPrueba /test")
    while True:
        try:
            price = get_price_xau()
            data["XAUUSD"].append(price)
            time.sleep(120)
        except: time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
