from flask import Flask
import os, requests, io
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return "ORO BOT DEIVID VIP - ACTIVO ✅ Usa /enviar_grafico"

@app.route('/enviar_grafico')
def enviar_grafico():
    try:
        BOT_TOKEN = os.getenv("BOT_TOKEN","").strip() or os.getenv("TELEGRAM_BOT_TOKEN","").strip()
        CHAT_ID = os.getenv("TELEGRAM_CHAT_ID","").strip()

        # 1. Bajar precio de ORO
        ticker = yf.Ticker("GC=F") # Oro Futuros
        data = ticker.history(period="1d", interval="5m")
        if data.empty:
            ticker = yf.Ticker("XAUUSD=X")
            data = ticker.history(period="1d", interval="5m")

        # 2. Crear gráfico
        plt.figure(figsize=(10,5))
        plt.plot(data['Close'], linewidth=2)
        plt.title(f"XAUUSD - ORO - {datetime.now().strftime('%d/%m %H:%M')}")
        plt.xlabel("Hora")
        plt.ylabel("Precio USD")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150)
        buf.seek(0)
        plt.close()

        # 3. Enviar foto a Telegram
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files = {'photo': ('oro.png', buf, 'image/png')}
        caption = f"📊 XAUUSD ORO\nPrecio: {data['Close'].iloc[-1]:.2f}\nHora: {datetime.now().strftime('%H:%M')}\n\nSeñales Deivid VIP 🚀"
        payload = {"chat_id": CHAT_ID, "caption": caption}
        
        r = requests.post(url, data=payload, files=files)
        return f"Enviado! {r.text}"

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run()
