import os, requests, threading, time, random
from flask import Flask
from datetime import datetime, timedelta
from collections import deque
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN") or ""
CHAT_ID = os.environ.get("CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID") or ""

data = {"XAUUSD": deque(maxlen=100), "BTCUSD": deque(maxlen=100), "EURUSD": deque(maxlen=100)}
last_signal = {"XAUUSD": 0, "BTCUSD": 0, "EURUSD": 0}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
    except: pass

def send_chart_pro(symbol, prices_list, direction, entry, sl, tp1, tp2, tp3):
    try:
        prices = list(prices_list)[-50:]
        if len(prices) < 20: prices = prices + [prices[-1]]*20

        fig, ax = plt.subplots(figsize=(11,5))
        ax.plot(prices, color='#2e7d32', linewidth=1.2, alpha=0.7)

        # Lineas estilo tu foto
        ax.axhline(entry, color='#006400', linestyle='-', linewidth=2.5, label=f'ENTRADA {entry:.2f}')
        ax.axhline(sl, color='red', linestyle='--', linewidth=1.8, label=f'SL {sl:.2f}')
        ax.axhline(tp1, color='#2e7d32', linestyle=':', linewidth=1.3)
        ax.axhline(tp2, color='#388e3c', linestyle='-.', linewidth=1.3)
        ax.axhline(tp3, color='#43a047', linestyle=(0, (2,2)), linewidth=1.3)

        accion = "COMPRAR EN LINEA VERDE" if direction=="BUY" else "VENDER EN LINEA ROJA"
        ax.set_title(f"{symbol} - 15M -> 1M/3M - {accion}", fontsize=12, fontweight='bold', loc='left')
        ax.set_ylabel("Precio")
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper left', fontsize=8)
        plt.tight_layout()
        path = f"/tmp/{symbol}_PRO.png"
        plt.savefig(path, dpi=120)
        plt.close()
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        with open(path, 'rb') as f:
            requests.post(url, data={"chat_id": CHAT_ID, "caption": f"📊 {symbol} {direction} | {accion}\nEnt: {entry:.2f} | SL: {sl:.2f} | TP3: {tp3:.2f}"}, files={"photo": f}, timeout=20)
    except Exception as e:
        print("Graf error:", e)

def get_prices():
    prices = {}
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        prices["XAUUSD"] = float(r.get("price", 0))
    except: prices["XAUUSD"] = None
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10).json()
        prices["BTCUSD"] = float(r["bitcoin"]["usd"])
    except: prices["BTCUSD"] = None
    try:
        r = requests.get("https://api.frankfurter.app/latest?from=EUR&to=USD", timeout=10).json()
        prices["EURUSD"] = float(r["rates"]["USD"])
    except: prices["EURUSD"] = None
    return prices

def ema(arr, period):
    if len(arr) < period: return None
    k = 2 / (period + 1)
    ema_val = sum(list(arr)[:period]) / period
    for p in list(arr)[period:]: ema_val = p * k + ema_val * (1 - k)
    return ema_val

def rsi(arr, period=14):
    if len(arr) < period + 1: return 50
    deltas = [arr[i] - arr[i-1] for i in range(1, len(arr))]
    gains = [d if d>0 else 0 for d in deltas[-period:]]
    losses = [-d if d<0 else 0 for d in deltas[-period:]]
    ag = sum(gains)/period; al = sum(losses)/period
    if al == 0: return 100
    return 100 - (100/(1+ag/al))

@app.route("/")
def home(): return "Bot V14.1 FIX ONLINE", 200

@app.route("/test")
def test():
    p = get_prices()
    for s in p:
        if p[s]: data[s].append(p[s])
    price = p["XAUUSD"] or 4410
    send_chart_pro("XAUUSD", data["XAUUSD"], "BUY", price, price-6, price+5, price+10, price+18)
    send_telegram(f"✅ TEST V14.1 OK\nXAU: {price}")
    return "ok", 200

def bot_loop():
    time.sleep(10)
    send_telegram("🚀 BOT V14.1 FIX CONECTADO\n📊 SL TP1 TP2 TP3\nGrafico PRO activo")
    while True:
        try:
            prices = get_prices()
            for symbol, price in prices.items():
                if not price: continue
                data[symbol].append(price)
                arr = data[symbol]
                if len(arr) < 60: continue
                e20 = ema(arr, 20); e50 = ema(arr, 50); e200 = ema(arr, 60); rsi_v = rsi(list(arr), 14)
                if symbol == "XAUUSD": sl_d, tp1_d, tp2_d, tp3_d = 4.5, 6, 12, 20
                elif symbol == "BTCUSD": sl_d, tp1_d, tp2_d, tp3_d = 150, 250, 500, 800
                else: sl_d, tp1_d, tp2_d, tp3_d = 0.0006, 0.0009, 0.0018, 0.0028
                sig = None
                if price > e50 and e50 > e200 and e20 > e50 and 50 < rsi_v < 72 and price > e20:
                    if time.time() - last_signal[symbol] > 1800: sig = ("BUY", rsi_v, sl_d, tp1_d, tp2_d, tp3_d)
                elif price < e50 and e50 < e200 and e20 < e50 and 28 < rsi_v < 50 and price < e20:
                    if time.time() - last_signal[symbol] > 1800: sig = ("SELL", rsi_v, sl_d, tp1_d, tp2_d, tp3_d)
                if sig:
                    direction, rsi_v, sl_d, tp1_d, tp2_d, tp3_d = sig
                    last_signal[symbol] = time.time()
                    sl = price - sl_d if direction=="BUY" else price + sl_d
                    tp1 = price + tp1_d if direction=="BUY" else price - tp1_d
                    tp2 = price + tp2_d if direction=="BUY" else price - tp2_d
                    tp3 = price + tp3_d if direction=="BUY" else price - tp3_d
                    icon = "🟡" if "XAU" in symbol else "🟠" if "BTC" in symbol else "🔵"
                    accion = "COMPRAR EN LINEA VERDE" if direction=="BUY" else "VENDER EN LINEA ROJA"
                    msg = f"""{icon} *{symbol} - {accion}* {icon}\n\n*Entrada: {price:.2f}*\n*SL: {sl:.2f}*\n*TP1: {tp1:.2f}*\n*TP2: {tp2:.2f}*\n*TP3: {tp3:.2f}*\n\nRSI: {rsi_v:.1f} | 15M -> 1M/3M\n⏰ {datetime.now().strftime('%H:%M')} EC"""
                    send_telegram(msg)
                    time.sleep(1)
                    send_chart_pro(symbol, arr, direction, price, sl, tp1, tp2, tp3)
            time.sleep(120)
        except Exception as e:
            print(e); time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
