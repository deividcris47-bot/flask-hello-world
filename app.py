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

# --- CONFIGURA AQUI ---
TOKEN = os.environ.get("TELEGRAM_TOKEN", "AQUI_TU_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID", "@xau_deivid_vip")
TARGET_PRICE = 4515

enviado_hoy = False

def get_gold_price():
    try:
        # Precio oro en tiempo real
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()
        return float(r.get("price", 0))
    except:
        return 3600  # fallback

def enviar_senal_automatica(precio):
    global enviado_hoy
    if enviado_hoy:
        return
    
    # Crear grafico PRO negro
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

    mensaje = f"""🚨 **SEÑAL VIP AUTOMATICA - ORO TOCO 4515** 🚨

📈 PRECIO ACTUAL: {precio}

✅ ENTRADA: COMPRA
🎯 TP1: {TARGET_PRICE + 10}
🎯 TP2: {TARGET_PRICE + 25}
🛑 SL: {TARGET_PRICE - 15}

⚠️ Riesgo: 1% por operación
⏰ Hora: {datetime.now().strftime('%H:%M:%S')}

#XAUUSD #ORO #VIP @xau_deivid_vip
"""
    try:
        with open('/tmp/grafico.png', 'rb') as foto:
            url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
            data = {"chat_id": CHAT_ID, "caption": mensaje, "parse_mode": "Markdown"}
            files = {"photo": foto}
            requests.post(url, data=data, files=files, timeout=15)
        enviado_hoy = True
        print(f"✅ Señal enviada - Precio: {precio}")
    except Exception as e:
        print(f"Error enviando: {e}")

def check_price():
    global enviado_hoy
    precio = get_gold_price()
    print(f"[{datetime.now()}] Chequeando precio: {precio}")
    
    # Reset diario
    if datetime.now().hour == 0:
        enviado_hoy = False

    if precio >= TARGET_PRICE and not enviado_hoy:
        enviar_senal_automatica(precio)

# Test manual
@app.route('/test')
def test():
    enviar_senal_automatica(get_gold_price())
    global enviado_hoy
    enviado_hoy = False
    return "Señal de prueba enviada a Telegram ✅"

@app.route('/')
def home():
    return f"Bot VIP Live - Vigilando {TARGET_PRICE} - Estado: {'ENVIADO HOY' if enviado_hoy else 'ESPERANDO'}"

# Iniciar el chequeo automatico cada 1 minuto
scheduler = BackgroundScheduler()
scheduler.add_job(check_price, 'interval', minutes=1)
scheduler.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
