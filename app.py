import os, requests, yfinance as yf
import mplfinance as mpf
import pandas as pd
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)

BOT_TOKEN = "8870473192:AAElumHWfjg2paoljk1IANUvRW3dISms5eg" 
CHAT_ID = "-1004419307514"

def get_y_enviar():
    try:
        data = yf.download("GC=F", period="3d", interval="30m", auto_adjust=True)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        df = data.tail(60).copy()
        if len(df) < 20: return
        last_price = float(df['Close'].iloc[-1])
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        es_compra = last_price > sma20
        if es_compra:
            tipo = "🟢 COMPRAR EN LINEA VERDE"
            entrada = last_price
            sl = entrada - 6.0
            tp1, tp2, tp3 = entrada + 4.0, entrada + 8.0, entrada + 13.0
            colors = ['green', 'red', 'green', 'green', 'green']
        else:
            tipo = "🔴 VENDER EN LINEA ROJA"
            entrada = last_price
            sl = entrada + 6.0
            tp1, tp2, tp3 = entrada - 4.0, entrada - 8.0, entrada - 13.0
            colors = ['red', 'red', 'green', 'green', 'green']
        hlines = dict(hlines=[entrada, sl, tp1, tp2, tp3], colors=colors, linestyle=['-', '--', '--', '-.', ':'], linewidths=[2, 1.8, 1, 1, 1])
        plot_path = "/tmp/xau_vip_pro.png"
        mpf.plot(df, type='candle', style='yahoo', title=f'XAUUSD - 30M VIP - {tipo}', ylabel='Precio USD', hlines=hlines, savefig=dict(fname=plot_path, dpi=200, bbox_inches='tight'))
        texto = f"🔥 ORO VIP - 30M 🔥\n{tipo}\n📍 ENTRADA: ${entrada:.2f}\n🛑 SL: ${sl:.2f}\n\n🟢 VERDE=COMPRAR\n🔴 ROJA=VENDER\n\n🎯 T1: ${tp1:.2f}\n🎯 T2: ${tp2:.2f}\n🎯 T3: ${tp3:.2f}"
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(plot_path, 'rb') as foto:
            requests.post(url, data={"chat_id": CHAT_ID, "caption": texto}, files={"photo": foto}, timeout=20)
        print(f"Enviado: {tipo}")
    except Exception as e:
        print(f"Error: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=get_y_enviar, trigger="interval", minutes=30)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def home(): return "Bot VIP AUTOMATICO ACTIVO - Cada 30 min"
@app.route('/enviar_grafico')
def manual(): get_y_enviar(); return "Enviado OK"

if __name__ == "__main__":
    get_y_enviar()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
