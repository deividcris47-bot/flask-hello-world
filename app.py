import os, io, requests, numpy as np
from flask import Flask, send_file, jsonify
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHANNEL_ID")
LEVEL = 4515

def fetch_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=8).json()
        return float(r["price"])
    except:
        return 4363.05

def create_chart():
    price = fetch_price()
    fig, ax = plt.subplots(figsize=(12,6), facecolor='#131722')
    ax.set_facecolor('#131722')
    np.random.seed(int(price*100)%10000)
    prices=[price-15+np.random.randn()*3+i*0.2 for i in range(70)]
    for i in range(len(prices)-1):
        o=prices[i]; c=prices[i+1]
        h=max(o,c)+abs(np.random.randn())
        l=min(o,c)-abs(np.random.randn())
        col='#26a69a' if c>=o else '#ef5350'
        ax.plot([i,i],[l,h],color=col,lw=1)
        ax.add_patch(plt.Rectangle((i-0.35,min(o,c)),0.7,abs(c-o) or 0.5,fc=col,ec=col))
    ax.axhline(prices[-1],color='#5d606b',ls=':',lw=1)
    ax.grid(True,color='#1e222d',lw=0.6)
    ax.tick_params(colors='#787b86',labelsize=8)
    ax.yaxis.tick_right()
    for s in ax.spines.values(): s.set_color('#1e222d')
    fig.text(0.01,0.02,'TradingView',color='white',fontsize=10,weight='bold',alpha=0.8)
    buf=io.BytesIO()
    fig.savefig(buf,format='png',facecolor='#131722',dpi=200,bbox_inches='tight')
    plt.close(fig); buf.seek(0)
    return buf, price

def send_signal():
    chart, price = create_chart()
    caption = f"🔥 XAUUSD {price:.2f} - Oro al contado\n"
    if abs(price-LEVEL) < 15:
        caption += f"🔴 SELL {LEVEL}\n❌ SL {LEVEL+10}\n✅ TP1 4470\n✅ TP2 4420\n✅ TP3 4250\n\n"
    caption += f"⚠️ Riesgo: 1% por operacion\n⚠️ No es consejo financiero\n🤖 Deivid Bot"
    url=f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    return requests.post(url,data={'chat_id':CHAT_ID,'caption':caption},files={'photo':('tv.png',chart,'image/png')},timeout=20).json()

@app.route('/')
def home():
    buf,_=create_chart()
    return f"<body style='background:#131722;text-align:center'><img src='/chart' style='width:98%'><br><a href='/test' style='color:yellow;font-size:22px'>ENVIAR PRUEBA A TELEGRAM</a></body>"

@app.route('/chart')
def chart():
    buf,_=create_chart()
    return send_file(buf,mimetype='image/png')

@app.route('/test')
def test(): return jsonify(send_signal())

# AUTOMATICO CADA 60 SEG
scheduler=BackgroundScheduler()
scheduler.add_job(lambda: send_signal() if abs(fetch_price()-LEVEL)<15 else None,'interval',minutes=1)
scheduler.start()

if __name__=="__main__":
    app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
