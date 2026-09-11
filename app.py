import os
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURACION CORREGIDA ---
TOKEN = os.environ.get("BOT_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID", "-1004419307514") # EL ID NUMERICO QUE SI FUNCIONA
TARGET_PRICE = 4515

enviado_hoy = False

def get_gold_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r.get("price", 0))
    except Exception as e:
        print(f"Error precio: {e}")
        return 3600

def enviar_senal_automatica(precio):
    global enviado_hoy
    if enviado_hoy:
        print("Ya fue enviado hoy, no se reenvia")
        return
    
    fig, ax = plt.subplots(figsize=(10,6), facecolor='black')
    ax.set_facecolor('black')
    x = np.linspace(0, 10, 100)
    y = np.random.normal(0,1,100).cumsum() + precio
    ax.plot(x, y, color='#00FF00', linewidth=2)
    ax.axhline(TARGET_PRICE, color='red', linestyle='--', label=f'OBJETIVO {TARGET_PRICE}')
    ax.set_title(f'XAUUSD - TOCO {TARGET_PRICE} - SEÑAL VIP', color='white', fontsize=14, weight='bold')
    ax.tick_params(colors='white')
    plt.savefig('/tmp/grafico.png', facecolor='black')
    plt.close()

    mensaje = f"🚨 SEÑAL VIP AUTOMATICA - ORO TOCO 4515 🚨\n\n📈 PRECIO ACTUAL: {precio}\n\n✅ ENTRADA: COMPRA\n🎯 TP1: {TARGET_PRICE + 10}\n🎯 TP2: {TARGET_PRICE + 25}\n🛑 SL: {TARGET_PRICE - 15}\n\n⏰ Hora: {datetime.now().strftime('%H:%M:%S')}\n\n#XAUUSD #ORO #VIP"
    try:
        with open('/tmp/grafico.png', 'rb') as foto:
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            data = {"chat_id": CHAT_ID, "caption": mensaje}
            files = {"photo": foto}
            resp = requests.post(url, data=data, files=files, timeout=15)
            print(f"Telegram responde: {resp.text}") # AHORA SI VEREMOS EL ERROR
        enviado_hoy = True
    except Exception as e:
        print(f"Error enviando: {e}")

def check_price():
    global enviado_hoy
    precio = get_gold_price()
    print(f"[{datetime.now()}] Chequeando precio: {precio}")
    if datetime.now().hour == 0:
        enviado_hoy = False
    if precio >= TARGET_PRICE and not enviado_hoy:
        enviar_senal_automatica(precio)

@app.route('/test')
def test():
    global enviado_hoy
    enviado_hoy = False
    precio = get_gold_price()
    print(f"TEST con precio {precio} -> CHAT_ID {CHAT_ID} TOKEN existe: {bool(TOKEN)}")
    enviar_senal_automatica(precio)
    enviado_hoy = False
    return f"Prueba ejecutada - Mira los LOGS - Precio: {precio} - Chat: {CHAT_ID}"

@app.route('/')
def home():
    return f"Bot VIP Live - Vigilando {TARGET_PRICE} - Estado: {'ENVIADO HOY' if enviado_hoy else 'ESPERANDO'}"

scheduler = BackgroundScheduler()
scheduler.add_job(check_price, 'interval', minutes=1)
scheduler.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
