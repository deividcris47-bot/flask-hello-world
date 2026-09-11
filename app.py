import os, time, io, threading, requests
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask

# --- CONFIG ---
TELEGRAM_TOKEN = os.getenv("8870473192:AAESM9ggyFPwx5n1trc7IV0GZijUkJzgxvw")
CHAT_ID = os.getenv("-1004419307514")
ENTRY_ZONE = 4515.0 # tu línea verde
SL_ZONE = 4527.0 # tu línea roja

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot VIP gráfico negro corriendo OK"

def crear_grafico_negro(df, entry, sl, tp1, tp2, tp3):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 5), facecolor='#0a0a0a')
    ax.set_facecolor('#0a0a0a')

    # Velas tipo trading
    for i in range(len(df)):
        o,h,l,c = df.iloc[i][['Open','High','Low','Close']]
        color = '#00ff88' if c>=o else '#ff3333'
        ax.plot([i,i],[l,h], color=color, lw=1)
        ax.plot([i,i],[o,c], color=color, lw=4, solid_capstyle='round')

    ax.axhline(entry, color='#00ff88', lw=1.2, ls='--')
    ax.axhline(sl, color='#ff3333', lw=1.2)
    ax.axhline(tp1, color='#00bfff', lw=1, ls=':')
    ax.axhline(tp2, color='#00bfff', lw=1, ls=':')
    ax.axhline(tp3, color='#00bfff', lw=1, ls=':')

    # Etiquetas
    ax.text(len(df), entry, f' Entry {entry} ', backgroundcolor='#00ff88', color='black', fontsize=8, va='center')
    ax.text(len(df), sl, f' Stop loss {sl} ', backgroundcolor='#333', color='white', fontsize=8, va='center')
    ax.text(len(df), tp1, f' TP1 {tp1} ', backgroundcolor='#0277bd', color='white', fontsize=8, va='center')

    plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', facecolor='#0a0a0a')
    plt.close()
    buf.seek(0)
    return buf

def enviar_senal(img_buf, entry, sl, tp1, tp2, tp3):
    caption = f"🔴 SELL XAUUSD\nEntry: {entry}\nStop loss: {sl}\nTP1: {tp1}\nTP2: {tp2}\nTP3: {tp3}\nVer gráfico"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('chart.png', img_buf, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': caption}
    requests.post(url, files=files, data=data)

def loop_bot():
    print("Bot VIP iniciado...")
    while True:
        try:
            # Descarga XAUUSD
            data = yf.download("GC=F", period="1d", interval="5m")
            if len(data) < 20:
                time.sleep(60)
                continue

            precio_actual = data['Close'].iloc[-1]
            print(f"Precio: {precio_actual}")

            # Si toca tu zona verde
            if abs(precio_actual - ENTRY_ZONE) < 2: # cuando toca 4515
                tp1 = ENTRY_ZONE - 25
                tp2 = ENTRY_ZONE - 45
                tp3 = ENTRY_ZONE - 75
                img = crear_grafico_negro(data.tail(50), ENTRY_ZONE, SL_ZONE, tp1, tp2, tp3)
                enviar_senal(img, ENTRY_ZONE, SL_ZONE, tp1, tp2, tp3)
                time.sleep(3600) # para no spamear, espera 1h

            time.sleep(30)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(30)

# Inicia el bot en segundo plano aunque sea Web Service
threading.Thread(target=loop_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
