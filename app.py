import os, time, requests, yfinance as yf
import matplotlib
matplotlib.use('Agg')
import mplfinance as mpf
import matplotlib.pyplot as plt
from flask import Flask
from threading import Thread

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
TP1, TP2, TP3 = 4480, 4366, 4250

@app.route('/')
def home(): return "BOT VELAS PRO"
@app.route('/healthz')
def healthz(): return "OK", 200

def get_precio():
    df = yf.download("GC=F", period="1d", interval="1m", progress=False, auto_adjust=True)
    return float(df['Close'].values.flatten()[-1])

def enviar_foto(texto, path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(path, 'rb') as f:
        data = {"chat_id": CHANNEL_ID, "caption": texto, "parse_mode": "Markdown"}
        r = requests.post(url, data=data, files={"photo": f}, timeout=30)
        print(f"Telegram: {r.text}", flush=True)

def generar_grafico_velas(entry):
    df = yf.download("GC=F", period="2d", interval="30m", progress=False, auto_adjust=True)
    df = df.tail(60)
    df.index.name = 'Date'
    # Estilo tradingview
    mc = mpf.make_marketcolors(up='#00ff88', down='#ff3b3b', wick={'up':'#00ff88','down':'#ff3b3b'}, edge='inherit', volume='in')
    s = mpf.make_mpf_style(marketcolors=mc, base_mpf_style='nightclouds', facecolor='#121212', figcolor='#121212', gridcolor='#2a2a2a', gridstyle='--')
    
    sl = entry + 12
    hlines = dict(hlines=[entry, sl, TP1, TP2, TP3], colors=['#00ff88','#ff3b3b','#00bfff','#00bfff','#ffcc00'], linestyle=['--','--','-','-','-'], linewidths=[1.5,1.5,1,1,2.5])
    
    path = "/tmp/sniper_velas.png"
    mpf.plot(df, type='candle', style=s, title=f'XAUUSD SELL {entry:.1f} -> TP3 {TP3}', hlines=hlines, figsize=(10,5), savefig=dict(fname=path, dpi=150, bbox_inches='tight'))
    return path

def bot_oro():
    print(">>> BOT VELAS ROJAS VERDES INICIADO <<<", flush=True)
    time.sleep(5)
    path = generar_grafico_velas(4515)
    enviar_foto("✅ *Bot 5 VELAS PRO conectado*\nVelas rojas y verdes + Entry/SL/TP3 marcados", path)
    while True:
        try:
            precio = get_precio()
            print(f"Precio XAU: {precio}", flush=True)
            if 4508 <= precio <= 4525:
                entry = precio
                texto = f"🎯 *SNIPER SELL XAUUSD*\n\n*ENTRY:* `{entry:.2f}`\n*SL:* `{entry+12:.2f}`\n*TP1:* `{TP1}`\n*TP2:* `{TP2}`\n*TP3:* `{TP3}` *FINAL*\n\n📉 Gráfico velas hasta donde va a llegar."
                path = generar_grafico_velas(entry)
                enviar_foto(texto, path)
                time.sleep(3600)
        except Exception as e:
            print(f"Error: {e}", flush=True)
        time.sleep(60)

Thread(target=bot_oro, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
