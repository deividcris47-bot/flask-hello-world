import os, time, threading, requests, pandas as pd
from flask import Flask
from datetime import datetime, timedelta
import pytz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO

app = Flask(__name__)
@app.route('/')
def home(): return "BOT V4 TP1 TP2 TP3 ACTIVO", 200

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8324174552:AAE3Cc3u5annbT7EOb4p1m2mP4OqG0g")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@XAUDeividVipSenales")

PARES = {
    "BTCUSDT": "BTC/USD",
    "PAXGUSDT": "XAU/USD ORO",
    "EURUSDT": "EUR/USD"
}

def get_data(symbol, interval="15m", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    r = requests.get(url, timeout=10).json()
    df = pd.DataFrame(r, columns=["t","o","h","l","c","v","ct","qv","n","tb","tq","i"])
    df["c"] = df["c"].astype(float)
    df["h"] = df["h"].astype(float)
    df["l"] = df["l"].astype(float)
    return df

def rsi_calc(s, p=14):
    d = s.diff()
    g = d.where(d>0,0).rolling(p).mean()
    l = -d.where(d<0,0).rolling(p).mean()
    return 100 - (100/(1+g/l))

def analizar_par(symbol, nombre):
    df15 = get_data(symbol, "15m", 100)
    df1h = get_data(symbol, "1h", 100)
    df15["ema9"] = df15["c"].ewm(span=9).mean()
    df15["ema21"] = df15["c"].ewm(span=21).mean()
    df15["rsi"] = rsi_calc(df15["c"])
    df1h["ema9"] = df1h["c"].ewm(span=9).mean()
    df1h["ema21"] = df1h["c"].ewm(span=21).mean()
    
    precio = df15["c"].iloc[-1]
    rsi = df15["rsi"].iloc[-1]
    ema9_15, ema21_15 = df15["ema9"].iloc[-1], df15["ema21"].iloc[-1]
    ema9_1h, ema21_1h = df1h["ema9"].iloc[-1], df1h["ema21"].iloc[-1]
    res = df15["h"].tail(20).max()
    sop = df15["l"].tail(20).min()
    
    tendencia = "ALCISTA 🟢" if ema9_1h > ema21_1h else "BAJISTA 🔴"
    
    # TPs y SL
    señal = "🟡 ESPERAR"
    tp1=tp2=tp3=sl=0
    es_compra = False

    if ema9_1h > ema21_1h: # BUSCA COMPRA
        if precio > res*0.999 and ema9_15 > ema21_15 and 50<rsi<75:
            señal = "🟢 COMPRA FUERTE"
            tp1, tp2, tp3 = precio*1.004, precio*1.008, precio*1.015
            sl = precio*0.994
            es_compra = True
    else: # BUSCA VENTA
        if precio < sop*1.001 and ema9_15 < ema21_15 and 25<rsi<50:
            señal = "🔴 VENTA FUERTE"
            tp1, tp2, tp3 = precio*0.996, precio*0.992, precio*0.985
            sl = precio*1.006
            es_compra = False

    # GRAFICO CON TPs
    plt.figure(figsize=(10,6))
    plt.plot(df15["c"].tail(60).values, linewidth=2.5, label="Precio")
    plt.plot(df15["ema9"].tail(60).values, linestyle="--", alpha=0.7, label="EMA9")
    plt.plot(df15["ema21"].tail(60).values, linestyle="--", alpha=0.7, label="EMA21")
    
    if tp1!=0:
        plt.axhline(tp1, color='green', linestyle='-', alpha=0.6, label=f'TP1 {tp1:.2f}')
        plt.axhline(tp2, color='green', linestyle='-', alpha=0.8, label=f'TP2 {tp2:.2f}')
        plt.axhline(tp3, color='green', linestyle='-', linewidth=2, label=f'TP3 {tp3:.2f}')
        plt.axhline(sl, color='red', linestyle='-', linewidth=2, label=f'SL {sl:.2f}')
    else:
        plt.axhline(res, color='red', linestyle=':', alpha=0.5, label=f'Res {res:.2f}')
        plt.axhline(sop, color='green', linestyle=':', alpha=0.5, label=f'Sop {sop:.2f}')

    plt.legend(fontsize=8, loc='upper left'); plt.grid(True, alpha=0.3)
    plt.title(f"{nombre} - {señal} | RSI {rsi:.1f}", fontsize=12, fontweight='bold')
    buf = BytesIO(); plt.savefig(buf, format='png', dpi=150, bbox_inches='tight'); buf.seek(0); plt.close()

    if tp1!=0:
        caption = f"""{señal} | {nombre}
📊 Tendencia 1H: {tendencia}
💰 Entrada: ${precio:,.4f}
📈 RSI 15M: {rsi:.1f}

🎯 TP1: ${tp1:,.4f} (+0.4%)
🎯 TP2: ${tp2:,.4f} (+0.8%)
🎯 TP3: ${tp3:,.4f} (+1.5%)
🛑 SL: ${sl:,.4f}

💡 Cierra 50% en TP1, 30% en TP2, deja 20% a TP3
⏰ {datetime.now(pytz.timezone('America/Guayaquil')).strftime('%d/%m %H:%M EC')}
"""
    else:
        caption = f"""🟡 ESPERAR | {nombre}
💰 Precio: ${precio:,.4f}
📊 1H: {tendencia} | RSI: {rsi:.1f}
📉 Soporte: ${sop:,.4f}
📈 Resistencia: ${res:,.4f}

⏳ Sin ruptura clara. No entrar.
⏰ {datetime.now(pytz.timezone('America/Guayaquil')).strftime('%d/%m %H:%M EC')}
"""

    return buf, caption

def enviar_todos():
    for symbol, nombre in PARES.items():
        try:
            img, cap = analizar_par(symbol, nombre)
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            requests.post(url, files={'photo': (f'{symbol}.png', img, 'image/png')}, data={'chat_id': CHANNEL_ID, 'caption': cap}, timeout=20)
            time.sleep(15)
        except Exception as e: print(f"Error {nombre}: {e}")

def bot_loop():
    tz = pytz.timezone('America/Guayaquil')
    print(">>> BOT V4 TP1 TP2 TP3 INICIADO")
    while True:
        now = datetime.now(tz)
        mp = ((now.minute//15)+1)*15
        proximo = now.replace(minute=0, second=0, microsecond=0)+timedelta(hours=1) if mp==60 else now.replace(minute=mp, second=0, microsecond=0)
        espera = (proximo-now).total_seconds()
        time.sleep(max(espera,10))
        enviar_todos()

threading.Thread(target=bot_loop, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
