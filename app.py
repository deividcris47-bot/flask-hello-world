from flask import Flask
import threading
import time
import requests
import yfinance as yf

app = Flask(__name__)

# === PON AQUI TUS DATOS REALES - ES LO UNICO QUE TIENES QUE CAMBIAR ===
BOT_TOKEN = "8870473192:AAEiJnwhA0fuMmc1CtfH_UJ27HVYIQwOflU"
CHAT_ID = "-1004419307514"
# =====================================================================

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        print(f"Telegram enviado: {msg}", flush=True)
    except Exception as e:
        print(f"Error Telegram: {e}", flush=True)

def es_8_8():
    # Logica de 8 velas del ORO - tu logica original
    try:
        data = yf.download("GC=F", period="1d", interval="15m", progress=False)
        if len(data) < 9:
            return False, "No hay suficientes datos"

        # Ejemplo: 8 velas alcistas seguidas
        ultimas_8 = data.tail(8)
        alcistas = 0
        for i in range(len(ultimas_8)):
            if ultimas_8['Close'].iloc[i] > ultimas_8['Open'].iloc[i]:
                alcistas += 1

        if alcistas == 8:
            return True, f"SEÑAL 8/8 BUY - XAUUSD {data['Close'].iloc[-1]:.2f}"
        return False, f"Revisando... {alcistas}/8 alcistas - Precio: {data['Close'].iloc[-1]:.2f}"
    except Exception as e:
        return False, f"Error leyendo oro: {e}"

def bot_loop():
    time.sleep(10)
    send_telegram("✅ PRUEBA OK - Bot 8/8 conectado a Render! Ya estoy revisando el ORO cada 5 min.")

    while True:
        try:
            hay_senal, mensaje = es_8_8()
            print(mensaje, flush=True)
            if hay_senal:
                send_telegram(f"🚨 {mensaje}\n\nhttps://www.tradingview.com/symbols/GC1!")
            time.sleep(300) # revisa cada 5 minutos
        except Exception as e:
            print(f"Error en loop: {e}", flush=True)
            time.sleep(300)

# Esta linea prende el bot
threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home():
    return "Bot 8/8 Live - XAUUSD Activo"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
