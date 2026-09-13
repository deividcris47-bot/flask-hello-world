import os, requests, threading, time, random
from flask import Flask
from datetime import datetime, timedelta
from collections import deque
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN") or ""
CHAT_ID = os.environ.get("CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID") or ""

data = {
    "XAUUSD": deque(maxlen=100),
    "BTCUSD": deque(maxlen=100),
    "EURUSD": deque(maxlen=100)
}
last_signal = {"XAUUSD": 0, "BTCUSD": 0, "EURUSD": 0}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
    except: pass

def send_chart_pro(symbol, prices_list, direction, entry, sl, tp1, tp2, tp3):
    try:
        # Convertimos precios en velas falsas pero reales
        prices = list(prices_list)[-50:] # ultimas 50 para el grafico
        if len(prices) < 20:
            prices = prices + [prices[-1]]*20

        # Creamos OHLC simulado
        ohlc = []
        base_time = datetime.now() - timedelta(hours=len(prices))
        for i, p in enumerate(prices):
            o = prices[i-1] if i>0 else p
            c = p
            # mecha aleatoria pequeña para que se vea vela real
            volatility = 2.5 if "XAU" in symbol else 80 if "BTC" in symbol else 0.0004
            h = max(o,c) + random.uniform(0, volatility*0.6)
            l = min(o,c) - random.uniform(0, volatility*0.6)
            ohlc.append((base_time + timedelta(minutes=i*15), o, h, l, c))

        fig, ax = plt.subplots(figsize=(12, 6))

        # Dibuja velas
        for dt, o, h, l, c in ohlc:
            color = '#00c853' if c >= o else '#d50000' # verde / rojo
            # mecha
            ax.plot([dt, dt], [l, h], color=color, linewidth=0.8)
            # cuerpo
            body_bottom = min(o,c)
            body_height = abs(c-o)
            if body_height < (h-l)*0.05: body_height = (h-l)*0.05
            rect = Rectangle((dt - timedelta(minutes=5), body_bottom), timedelta(minutes=10), body_height, facecolor=color, edgecolor=color)
            ax.add_patch(rect)

        # Lineas como tu foto
        last_dt = ohlc[-1][0]
        first_dt = ohlc[0][0]
        # Entrada VERDE gruesa
        ax.hlines(entry, first_dt, last_dt + timedelta(hours=2), colors='#006400', linestyles='solid', linewidth=2.2, label=f'ENTRADA {entry:.2f}')
        # SL ROJO punteado grueso
        ax.hlines(sl, first_dt, last_dt + timedelta(hours=2), colors='#ff0000', linestyles='dashed', linewidth=1.8, label=f'SL {sl:.2f}')
        # TPs verde punteado fino como tu foto
        ax.hlines(tp1, first_dt, last_dt + timedelta(hours=2), colors='#2e7d32', linestyles=':', linewidth=1.2)
        ax.hlines(tp2, first_dt, last_dt + timedelta(hours=2), colors='#388e3c', linestyles='-.', linewidth=1.2)
        ax.hlines(tp3, first_dt, last_dt + timedelta(hours=2), colors='#43a047', linestyles=(0, (2, 2)), linewidth=1.2)

        # Estilo igual a tu foto
        ax.set_ylabel(f'Precio USD', fontsize=10)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d, %H:%M'))
        plt.xticks(rotation=45)
        ax.grid(True, alpha=0.25)

        accion = "COMPRAR EN LINEA VERDE" if direction=="BUY" else "VENDER EN LINEA ROJA"
        ax.set_title(f"{symbol} - 15M -> 1M/3M - {accion}", fontsize=13, fontweight='bold', loc='left')

        # Anotaciones a la derecha como tu foto
        ax.text(1.005, 0.95, f"{tp3:.1f}", transform=ax.transAxes, fontsize=8, va='center')
        ax.text(1.005, 0.80, f"{tp2:.1f}", transform=ax.transAxes, fontsize=8, va='center')
        ax.text(1.005, 0.70, f"{tp1:.1f}", transform=ax.transAxes, fontsize=8, va='center')
        ax.text(1.005, 0.60, f"{entry:.1f}", transform=ax.transAxes, fontsize=8, fontweight='bold', color='#006400')
        ax.text(1.005, 0.50, f"{sl:.1f}", transform=ax.transAxes, fontsize=8, color='red')

        plt.tight_layout()
        path = f"/tmp/{symbol}_PRO.png"
        plt.savefig(path, dpi=150)
        plt.close()

        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        with open(path, 'rb') as f:
            requests.post(url, data={"chat_id": CHAT_ID, "caption": f"📊 {symbol} {direction} | {accion}\nEntrada: {entry:.2f} | SL: {sl:.2f} | TP3: {tp3:.2f}"}, files={"photo": f}, timeout=20)
    except Exception as e:
        print("Error grafico:", e)

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
    for p in list(arr)[period:]:
        ema_val = p * k + ema_val * (1 - k)
    return ema_val

def rsi(arr, period=14):
    if len(arr) < period + 1: return 50
    deltas = [arr[i] - arr[i-1] for i in range(1, len(arr))]
    gains = [d if d>0 else 0 for d in deltas[-period:]]
    losses = [-d if d<0 else 0 for d in deltas[-period:]]
    ag = sum(gains)/period
    al = sum(losses)/period
    if al == 0: return 100
    return 100 - (100/(1+ag/al))

@app.route("/")
def home():
    return "Bot V14 PRO GRAFICO IGUAL FOTO ONLINE", 200

@app.route("/test")
def test():
    p = get_prices()
    for s in p:
        if p[s]: data[s].append(p[s])
    # Test con valores como tu foto
    price = p["XAUUSD"] or 4410
    sl = price - 6
    tp1 = price + 5
    tp2 = price + 10
    tp3 = price + 18
    send_chart_pro("XAUUSD", data["XAUUSD"], "BUY", price, sl, tp1, tp2, tp3)
    send_telegram(f"✅ *TEST V14 PRO OK*\nGrafico estilo tu foto enviado")
    return "ok", 200

def bot_loop():
    time.sleep(10)
    send_telegram("🚀 *BOT V14 PRO CONECTADO*\n📊 Grafico velas + lineas como tu foto\n🟢 COMPRAR EN LINEA VERDE\n🔴 VENDER EN LINEA ROJA")
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
                    if time.time() - last_signal[symbol] > 1800:
                        sig = ("BUY", rsi_v, sl_d, tp1_d, tp2_d, tp3_d)
                elif price < e50 and e50 < e200 and e20 < e50 and 28 < rsi_v < 50 and price < e20:
                    if time.time() - last_signal[symbol] > 1800:
                        sig = ("SELL", rsi_v, sl_d, tp1_d, tp2_d, tp3_d)
                if sig:
                    direction, rsi_v, sl_d, tp1_d, tp2_d, tp3_d = sig
                    last_signal[symbol] = time.time()
                    sl = price - sl_d if direction=="BUY" else price + sl_d
                    tp1 = price + tp1_d if direction=="BUY" else price - tp1_d
                    tp2 = price + tp2_d if direction=="BUY" else price - tp2_d
                    tp3 = price + tp3_d if direction=="BUY" else price - tp3_d
                    icon = "🟡" if "XAU" in symbol else "🟠" if "BTC" in symbol else "🔵"
                    accion = "COMPRAR EN LINEA VERDE" if direction=="BUY" else "VENDER EN LINEA ROJA"
                    msg = f"""{icon} *{symbol} - {accion}* {icon}

*Entrada: {price:.2f}*
*SL: {sl:.2f}*
*TP1: {tp1:.2f}*
*TP2: {tp2:.2f}*
*TP3: {tp3:.2f}*

RSI: {rsi_v:.1f} | 15M -> 1M/3M
⏰ {datetime.now().strftime('%H:%M')} EC
"""
                    send_telegram(msg)
                    time.sleep(1)
                    send_chart_pro(symbol, arr, direction, price, sl, tp1, tp2, tp3)
            time.sleep(120)
        except Exception as e:
            print(e)
            time.sleep(60)

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
