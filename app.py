import os, requests, yfinance as yf, io, time, threading
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PRECIO_ALERTA = 4515

app = Flask(__name__)

def enviar_grafico_vip(precio):
    df = yf.download("GC=F", period="1d", interval="5m")
    fig, ax = plt.subplots(figsize=(10,5))
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    
    ax.plot(df['Close'], color='white', linewidth=1.5)
    ax.axhline(PRECIO_ALERTA, color='#00FF00', linestyle='--', linewidth=2, label=f'ALERTA {PRECIO_ALERTA}')
    ax.axhline(PRECIO_ALERTA+10, color='red', linestyle='--', linewidth=1)
    ax.axhline(PRECIO_ALERTA-10, color='blue', linestyle='--', linewidth=1)
    
    ax.set_title(f'ORO (XAU/USD) - {precio:.2f} - TOCO 4515', color='white', fontsize=14, fontweight='bold')
    ax.tick_params(colors='white')
    ax.legend()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor='black', bbox_inches='tight')
    buf.seek(0)
    plt.close()

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files = {'photo': buf}
    data = {'chat_id': CHANNEL_ID, 'caption': f'🔥 ALERTA VIP NEGRO\nPrecio tocó {PRECIO_ALERTA}\nActual: {precio:.2f}\n#ORO #VIP'}
    requests.post(url, data=data, files=files)

def monitor():
    enviado = False
    while True:
        try:
            precio = yf.Ticker("GC=F").fast_info['last_price']
            print(f"Precio: {precio}")
            if precio >= PRECIO_ALERTA and not enviado:
                enviar_grafico_vip(precio)
                enviado = True
            if precio < PRECIO_ALERTA - 20:
                enviado = False
        except Exception as e:
            print(e)
        time.sleep(60)

@app.route('/')
def home():
    return "Bot VIP Negro ACTIVO - Esperando 4515..."

threading.Thread(target=monitor, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
