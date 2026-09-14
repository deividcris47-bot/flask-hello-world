import os
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
from flask import Flask
from datetime import datetime
import json

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
CONTADOR_FILE = "/tmp/contador.json"

def get_contador():
    try:
        with open(CONTADOR_FILE, "r") as f:
            data = json.load(f)
            fecha = data.get("fecha")
            hoy = datetime.now().strftime("%Y-%m-%d")
            if fecha != hoy:
                return 0, hoy
            return data.get("count", 0), hoy
    except:
        return 0, datetime.now().strftime("%Y-%m-%d")

def save_contador(count, fecha):
    with open(CONTADOR_FILE, "w") as f:
        json.dump({"count": count, "fecha": fecha}, f)

def enviar_telegram(texto, imagen_path=None):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto" if imagen_path else f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        if imagen_path:
            with open(imagen_path, 'rb') as photo:
                data = {"chat_id": CHAT_ID, "caption": texto, "parse_mode": "Markdown"}
                r = requests.post(url, data=data, files={"photo": photo}, timeout=20)
        else:
            data = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"}
            r = requests.post(url, data=data, timeout=20)
        print(f"Telegram response: {r.text}")
        return r.json()
    except Exception as e:
        print(f"Error telegram: {e}")
        return {"ok": False}

def analizar():
    # XAUUSD = GC=F en Yahoo
    try:
        df_1m = yf.download("GC=F", period="1d", interval="1m")
        df_5m = yf.download("GC=F", period="5d", interval="5m")
        df_15m = yf.download("GC=F", period="5d", interval="15m")
        
        if df_1m.empty or len(df_1m) < 50:
            return None, "Mercado cerrado fin de semana", 0, 0

        precio = float(df_1m['Close'].iloc[-1])
        
        # Logica Sniper simple (BOS + OB) - si no hay señal retorna esperando
        # Para prueba forzamos señal
        return df_1m, precio, df_5m, df_15m
    except Exception as e:
        return None, f"Error Yahoo: {e}", 0, 0

@app.route("/")
def home():
    return "Bot XAUUSD Sniper Activo - Usa /send"

@app.route("/send")
def send():
    from flask import request
    is_test = request.args.get("test") == "1"
    
    count, fecha_hoy = get_contador()
    if count >= 8 and not is_test:
        return f"Limite 8/8 alcanzado hoy {fecha_hoy}"

    df_1m, precio, df_5m, df_15m = analizar()
    
    if df_1m is None:
        if is_test:
            # MODO PRUEBA: fuerza señal aunque mercado cerrado
            precio = 4330.44
            texto = f"🟢 *Señal Comprar* `0/8` - *{precio}* (PRUEBA)\nTend: BAJISTA | BOS + CHOCH + OB | Zona limpia"
            # crea grafico dummy negro
            import matplotlib.pyplot as plt
            plt.figure(figsize=(8,4))
            plt.plot([4300, 4320, 4330, precio])
            plt.title(f"XAUUSD TEST - {precio}")
            plt.savefig("/tmp/chart.png")
            plt.close()
            enviar_telegram(texto, "/tmp/chart.png")
            return f"Señal Comprar 0/8 enviada - {precio} (PRUEBA)"
        else:
            return f"Mercado cerrado fin de semana | Velas 1M: 0 | El domingo 5pm abre"

    # Aqui iria tu logica real BOS+CHOCH+OB
    # Por ahora si no hay señal:
    if not is_test:
        return f"Esperando sniper | Tend:BAJISTA | Velas 1M:{len(df_1m)} | Precio:{precio:.2f} | {count}/8"

    # Si es test y mercado abierto
    texto = f"🟢 *Señal Comprar* `{count+1}/8` - *{precio:.2f}* (PRUEBA)\nTend: BAJISTA | BOS detectado | OB Limpio"
    import matplotlib.pyplot as plt
    plt.figure(figsize=(8,4))
    plt.plot(df_1m['Close'].tail(100))
    plt.title(f"XAUUSD - {precio:.2f}")
    plt.savefig("/tmp/chart.png")
    plt.close()
    enviar_telegram(texto, "/tmp/chart.png")
    return f"Señal Comprar {count+1}/8 enviada - {precio} (PRUEBA)"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
