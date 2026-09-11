import os, time, requests, yfinance as yf
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from flask import Flask
from threading import Thread

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

TP1, TP2, TP3 = 4480, 4366, 4250

@app.route('/')
def home(): return "BOT 5 SNIPER + GRAFICO ACTIVO"
@app.route('/healthz')
def healthz(): return "OK", 200

def enviar_foto(texto, imagen_path):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(imagen_path, 'rb') as f:
            data = {"chat_id": CHANNEL_ID, "caption": texto, "parse_mode": "Markdown"}
            r = requests.post(url, data=data, files={"photo": f}, timeout=30)
            print(f"Foto enviada: {r.text}")
    except Exception as e:
        print(f"Error foto: {e}")

def generar_grafico(entry):
    df = yf.download("GC=F", period="2d", interval="15m", progress=False)
    df = df.tail(100)
    # niveles
    sl = entry + 12
    
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10,6))
    
    mpf.plot(df, type='candle', ax=ax, style='yahoo', volume=False)
    
    ax.axhline(entry, color='#00ff88', linestyle='--', linewidth=1.5, label=f'ENTRY {entry:.2f}')
    ax.axhline(sl, color='#ff3b3b', linestyle='--', linewidth=1.5, label=f'SL {sl:.2f}')
    ax.axhline(TP1, color='#00bfff', linestyle='-', linewidth=1.2, label=f'TP1 {TP1}')
    ax.axhline(TP2, color='#00bfff', linestyle='-', linewidth=1.2, label=f'TP2 {TP2}')
    ax.axhline(TP3, color='#ffcc00', linestyle='-', linewidth=2, label=f'TP3 {TP3} FINAL')
    
    ax.set_title(f'XAUUSD SNIPER - SELL {entry:.2f} -> TP3 {TP3}', color='white')
    ax.legend(loc='upper left')
    plt.tight_layout()
    path = "/tmp/sniper.png"
    plt.savefig(path, dpi=200)
    plt.close()
    return path

def bot_oro():
    print(">>> BOT 5 SNIPER CON GRAFICO INICIADO <<<", flush=True)
    time.sleep(5)
    enviar_foto("✅ *Bot 5 SNIPER + Gráficos TradingView Activado*\nPróxima señal vendrá con gráfico marcado ENTRY/SL/TP3", generar_grafico(4515))
    
    while True:
        try:
            df = yf.download("GC=F", period="1d", interval="1m", progress=False)
            if df.empty: time.sleep(60); continue
            precio = float(df['Close'].iloc[-1])
            print(f"Precio: {precio}", flush=True)
            
            if 4508 <= precio <= 4525:
                entry = precio
                sl = entry + 12
                texto = f"🎯 *SNIPER SELL XAUUSD*\n\n*ENTRY:* `{entry:.2f}`\n*SL:* `{sl:.2f}`\n*TP1:* `{TP1}`\n*TP2:* `{TP2}`\n*TP3:* `{TP3}` *FINAL TARGET*\n\n📉 Gráfico marcado hasta donde va a llegar."
                path = generar_grafico(entry)
                enviar_foto(texto, path)
                time.sleep(3600)
        except Exception as e:
            print(f"Error: {e}", flush=True)
        time.sleep(60)

Thread(target=bot_oro, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
