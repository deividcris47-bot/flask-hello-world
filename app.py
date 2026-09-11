import os, time, requests, yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from flask import Flask
from threading import Thread

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
TP1, TP2, TP3 = 4480, 4366, 4250

@app.route('/')
def home(): return "BOT 5 SNIPER GRAFICO FIX"
@app.route('/healthz')
def healthz(): return "OK", 200

def enviar_foto(texto, path):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(path, 'rb') as f:
            data = {"chat_id": CHANNEL_ID, "caption": texto, "parse_mode": "Markdown"}
            r = requests.post(url, data=data, files={"photo": f}, timeout=30)
            print(f"Telegram: {r.text}", flush=True)
    except Exception as e:
        print(f"Error envio foto: {e}", flush=True)
        # Si falla foto, envia solo texto
        try:
            url2 = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(url2, data={"chat_id": CHANNEL_ID, "text": texto, "parse_mode": "Markdown"}, timeout=20)
        except: pass

def generar_grafico(entry):
    try:
        df = yf.download("GC=F", period="2d", interval="30m", progress=False, auto_adjust=True)
        if df.empty: raise Exception("df vacio")
        df = df.tail(60)
        closes = df['Close'].values
        sl = entry + 12
        fig, ax = plt.subplots(figsize=(10,5))
        ax.plot(closes, color='white', linewidth=1.5)
        ax.axhline(entry, color='#00ff88', linestyle='--', label=f'ENTRY {entry:.1f}')
        ax.axhline(sl, color='#ff3b3b', linestyle='--', label=f'SL {sl:.1f}')
        ax.axhline(TP1, color='#00bfff', linestyle='-', label=f'TP1 {TP1}')
        ax.axhline(TP2, color='#00bfff', linestyle='-', label=f'TP2 {TP2}')
        ax.axhline(TP3, color='#ffcc00', linewidth=2, label=f'TP3 {TP3}')
        ax.set_facecolor('#121212'); fig.patch.set_facecolor('#121212')
        ax.tick_params(colors='white'); ax.set_title(f'XAUUSD SELL {entry:.1f} -> TP3 {TP3}', color='white')
        ax.legend()
        path = "/tmp/sniper.png"
        plt.tight_layout(); plt.savefig(path, dpi=150); plt.close()
        return path
    except Exception as e:
        print(f"Error grafico: {e}", flush=True)
        # Crea imagen simple si falla yfinance
        fig, ax = plt.subplots(figsize=(10,5))
        ax.text(0.5,0.5, f'ENTRY {entry}\nSL {entry+12}\nTP1 {TP1}\nTP2 {TP2}\nTP3 {TP3}', ha='center', va='center', color='white', fontsize=16)
        ax.set_facecolor('#121212'); fig.patch.set_facecolor('#121212'); ax.axis('off')
        path = "/tmp/sniper.png"
        plt.savefig(path, dpi=150); plt.close()
        return path

def bot_oro():
    print(">>> BOT 5 SNIPER CON GRAFICO FIX INICIADO <<<", flush=True)
    time.sleep(3)
    try:
        texto = "✅ *Bot 5 con Gráfico FIX conectado*\nEntry/SL/TP3 marcados - Próxima señal con foto"
        path = generar_grafico(4515)
        enviar_foto(texto, path)
    except Exception as e:
        print(f"Error inicio: {e}", flush=True)
    while True:
        try:
            df = yf.download("GC=F", period="1d", interval="1m", progress=False, auto_adjust=True)
            if df.empty: time.sleep(60); continue
            precio = float(df['Close'].iloc[-1])
            print(f"Precio: {precio}", flush=True)
            if 4508 <= precio <= 4525:
                entry = precio; sl = entry+12
                texto = f"🎯 *SNIPER SELL XAUUSD*\n\n*ENTRY:* `{entry:.2f}`\n*SL:* `{sl:.2f}`\n*TP1:* `{TP1}`\n*TP2:* `{TP2}`\n*TP3:* `{TP3}` *FINAL*\n\n📉 Hasta donde va a llegar marcado en gráfico."
                path = generar_grafico(entry)
                enviar_foto(texto, path)
                time.sleep(3600)
        except Exception as e:
            print(f"Error loop: {e}", flush=True)
        time.sleep(60)

Thread(target=bot_oro, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
