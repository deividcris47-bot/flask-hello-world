import os, requests, io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from flask import Flask, send_file

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PRECIO = 4515

app = Flask(__name__)

def crear_grafico_tradingview():
    buf = io.BytesIO()
    fig, ax = plt.subplots(figsize=(12,6), facecolor='#131722')
    ax.set_facecolor('#131722')

    # Simulacion realista como tu screenshot de 4363
    np.random.seed(int(np.random.rand()*1000))
    prices=[]
    p=4363
    for _ in range(80):
        p += np.random.uniform(-3.5,3.5)
        prices.append(p)
    # Para que tenga picos como tu foto
    prices[10:18] = [x+12 for x in prices[10:18]]
    prices[40:50] = [x-15 for x in prices[40:50]]

    for i in range(len(prices)-1):
        o=prices[i]; c=prices[i+1]
        h=max(o,c)+np.random.uniform(0.5,3)
        l=min(o,c)-np.random.uniform(0.5,3)
        color='#26a69a' if c>=o else '#ef5350'
        ax.plot([i,i],[l,h], color=color, linewidth=1)
        ax.add_patch(plt.Rectangle((i-0.35, min(o,c)), 0.7, abs(c-o) or 0.4, facecolor=color, edgecolor=color))

    # Linea punteada precio actual como TradingView
    current=prices[-1]
    ax.axhline(current, color='#5d606b', linestyle=':', linewidth=1, alpha=0.9)

    # Estilo TradingView exacto
    ax.grid(True, color='#1e222d', linewidth=0.6)
    ax.tick_params(colors='#787b86', labelsize=8)
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    for spine in ax.spines.values():
        spine.set_color('#1e222d')

    times=['14:45','15:00','15:15','15:30','15:45','16:00','16:15','17:00','17:15','17:30','17:45']
    ax.set_xticks([8,15,22,29,36,43,50,58,65,72,78])
    ax.set_xticklabels(times)

    # Texto TradingView abajo izq
    fig.text(0.01, 0.02, 'TradingView', color='white', fontsize=10, weight='bold', alpha=0.9)

    plt.tight_layout()
    fig.savefig(buf, format='png', facecolor='#131722', dpi=200, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf

@app.route('/')
def home():
    return "<body style='background:#131722;text-align:center'><img src='/chart' style='width:98%'><br><a href='/test' style='color:yellow;font-size:20px'>Enviar a Telegram</a></body>"

@app.route('/chart')
def chart():
    return send_file(crear_grafico_tradingview(), mimetype='image/png')

@app.route('/test')
def test():
    buf=crear_grafico_tradingview()
    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files={'photo':('tv.png',buf,'image/png')}
    data={'chat_id':CHANNEL_ID, 'caption':'🔥 XAUUSD 4363.059 - Oro al contado\n✅ Estilo TradingView PRO NEGRO'}
    r=requests.post(url,data=data,files=files,timeout=20)
    return f"{r.text}"

if __name__=="__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
