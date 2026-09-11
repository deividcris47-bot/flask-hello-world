import os, requests, yfinance as yf, io, time, threading
import matplotlib
matplotlib.use('Agg')
import mplfinance as mpf
import pandas as pd
from flask import Flask, send_file

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PRECIO_ALERTA = 4515

app = Flask(__name__)

# Estilo TradingView Negro
s = mpf.make_mpf_style(
    base_mpf_style='nightclouds',
    facecolor='black',
    edgecolor='white',
    figcolor='black',
    gridcolor='#222222',
    gridstyle='--',
    rc={'axes.labelcolor':'white', 'xtick.color':'white', 'ytick.color':'white'}
)

def crear_grafico_tradingview(precio_actual=None):
    # Bajamos 2 dias en 15 min para que se vea bonito
    df = yf.download("GC=F", period="3d", interval="15m")
    df.index.name = 'Date'

    # Niveles VIP
    hlines = dict(hlines=[PRECIO_ALERTA, PRECIO_ALERTA+10, PRECIO_ALERTA-10, 4250],
                  colors=['#00FF00','#FF0000','#00AAFF','#FFD700'],
                  linewidths=[1.5,1,1,1],
                  linestyle='--')

    buf = io.BytesIO()
    fig, axlist = mpf.plot(df, type='candle', style=s,
                           title=f'XAUUSD - ORO {precio_actual:.2f} - VIP DEIVID' if precio_actual else 'XAUUSD - ORO VIP DEIVID',
                           ylabel='Precio',
                           hlines=hlines,
                           figratio=(16,9),
                           figscale=1.2,
                           returnfig=True)

    # Texto Entry / SL / TP3
    ax = axlist[0]
    ax.text(0.02, 0.95, f'ENTRY SELL: {PRECIO_ALERTA}\nSL: {PRECIO_ALERTA+10}\nTP3: 4250',
            transform=ax.transAxes, color='white', fontsize=9,
            bbox=dict(facecolor='black', edgecolor='#00FF00', boxstyle='round'))

    fig.savefig(buf, format='png', facecolor='black', bbox_inches='tight', dpi=150)
    buf.seek(0)
    return buf

def enviar_a_telegram(buf, precio):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files = {'photo': buf}
    data = {'chat_id': CHANNEL_ID, 'caption': f'🔥 XAUUSD SELL {PRECIO_ALERTA} -> TP3 4250\nPrecio actual: {precio:.2f}\n✅ Bot TradingView VIP ACTIVO'}
    requests.post(url, data=data, files=files)

@app.route('/')
def home():
    return """
    <body style='background:black;color:white;text-align:center;font-family:Arial'>
    <h2>✅ Bot VIP TradingView ACTIVO - Esperando 4515</h2>
    <p>Grafico en vivo (se actualiza cada vez que recargas):</p>
    <img src='/chart' style='width:95%;max-width:900px;border:2px solid #00FF00'>
    <br><br>
    <a href='/chart' style='color:#00FF00'>Ver solo grafico</a> |
    <a href='/test' style='color:yellow'>Probar envio a Telegram</a>
    <p>Precio oro ahora: se chequea cada 60 seg</p>
    </body>
    """

@app.route('/chart')
def chart():
    precio = float(yf.Ticker("GC=F").fast_info['last_price'])
    buf = crear_grafico_tradingview(precio)
    return send_file(buf, mimetype='image/png')

@app.route('/test')
def test():
    precio = float(yf.Ticker("GC=F").fast_info['last_price'])
    buf = crear_grafico_tradingview(precio)
    enviar_a_telegram(buf, precio)
    return f"✅ Enviado a Telegram! Precio: {precio} - Revisa tu canal"

def monitor():
    enviado=False
    while True:
        try:
            precio = float(yf.Ticker("GC=F").fast_info['last_price'])
            print(f"Precio: {precio}")
            if precio >= PRECIO_ALERTA and not enviado:
                buf = crear_grafico_tradingview(precio)
                enviar_a_telegram(buf, precio)
                enviado=True
            if precio < PRECIO_ALERTA-15:
                enviado=False
        except Exception as e:
            print(e)
        time.sleep(60)

threading.Thread(target=monitor, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
