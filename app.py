import os, requests, yfinance as yf
import mplfinance as mpf
import pandas as pd
from flask import Flask
app = Flask(__name__)

BOT_TOKEN = "8870473192:AAElumHWfjg2paoljk1IANUvRW3dISms5eg"
CHAT_ID = "-1004419307514"

def get_analisis_pro():
    data = yf.download("GC=F", period="3d", interval="30m", auto_adjust=True)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    df = data.tail(60).copy()
    close = df['Close']
    last_price = float(close.iloc[-1])
    sma20 = close.rolling(20).mean().iloc[-1]
    es_compra = last_price > sma20

    if es_compra:
        # SI TOCA COMPRAR
        tipo = "🟢 COMPRAR EN LINEA VERDE"
        entrada = last_price
        color_entrada = 'green'
        sl = entrada - 6.0
        tp1 = entrada + 4.0
        tp2 = entrada + 8.0
        tp3 = entrada + 13.0
        hlines = dict(hlines=[entrada, sl, tp1, tp2, tp3], colors=['green', 'red', 'green', 'green', 'green'], linestyle=['-', '--', '--', '-.', ':'], linewidths=[2, 1.8, 1, 1, 1])
    else:
        # SI TOCA VENDER
        tipo = "🔴 VENDER EN LINEA ROJA"
        entrada = last_price
        color_entrada = 'red'
        sl = entrada + 6.0
        tp1 = entrada - 4.0
        tp2 = entrada - 8.0
        tp3 = entrada - 13.0
        hlines = dict(hlines=[entrada, sl, tp1, tp2, tp3], colors=['red', 'red', 'green', 'green', 'green'], linestyle=['-', '--', '--', '-.', ':'], linewidths=[2, 1.8, 1, 1, 1])

    plot_path = "/tmp/xau_vip_pro.png"
    mpf.plot(df, type='candle', style='yahoo', title=f'XAUUSD - 30M VIP - {tipo}', ylabel='Precio USD', hlines=hlines, savefig=dict(fname=plot_path, dpi=200, bbox_inches='tight'))

    texto = f"""🔥 ORO VIP - 30M 🔥
{tipo}
📍 ENTRADA: ${entrada:.2f}
🟢 LINEA VERDE = COMPRAR
🔴 LINEA ROJA = VENDER

🎯 T1: ${tp1:.2f}
🎯 T2: ${tp2:.2f}
🎯 T3: ${tp3:.2f}
🛑 SL: ${sl:.2f}

👇 ABRIR GRAFICO 👇"""

    return plot_path, texto

@app.route('/')
def home(): return "Bot VIP"
@app.route('/enviar_grafico')
def enviar():
    try:
        grafico, texto = get_analisis_pro()
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(grafico, 'rb') as foto:
            r = requests.post(url, data={"chat_id": CHAT_ID, "caption": texto}, files={"photo": foto})
        return f"Enviado OK: {r.text[:400]}"
    except Exception as e:
        return f"Error: {e}"
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
