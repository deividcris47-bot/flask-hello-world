from flask import Flask
import os, requests, io
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import pytz

app = Flask(__name__)

@app.route('/')
def home():
    return "ORO BOT VIP PRO ACTIVO ✅"

@app.route('/enviar_grafico')
def enviar_grafico():
    try:
        BOT_TOKEN = (os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
        CHAT_ID = (os.getenv("TELEGRAM_CHAT_ID") or "").strip()

        # Datos oro real
        data = yf.Ticker("GC=F").history(period="1d", interval="15m")
        if len(data) < 20:
            data = yf.Ticker("XAUUSD=X").history(period="1d", interval="15m")

        precio = data['Close'].iloc[-1]
        max_p = data['High'].max()
        min_p = data['Low'].min()
        apertura = data['Open'].iloc[0]
        tendencia = "🟢 ALCISTA - COMPRAS" if precio > apertura else "🔴 BAJISTA - VENTAS"

        # GRAFICO PRO NEGRO
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(data['Close'], color='#00ff88', linewidth=2.8)
        ax.fill_between(data.index, data['Close'], alpha=0.15, color='#00ff88')
        ax.axhline(max_p, color='red', linestyle='--', alpha=0.5, label=f'Resistencia {max_p:.2f}')
        ax.axhline(min_p, color='green', linestyle='--', alpha=0.5, label=f'Soporte {min_p:.2f}')

        tz_ec = pytz.timezone('America/Guayaquil')
        hora_ec = datetime.now(tz_ec).strftime('%d/%m %H:%M')

        ax.set_title(f"XAUUSD ORO | {precio:.2f} | {hora_ec}", fontsize=16, fontweight='bold', color='white')
        ax.set_ylabel("USD", color='white', fontsize=12)
        ax.grid(True, alpha=0.15)
        ax.legend()
        plt.xticks(rotation=30)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=220, facecolor='#0e0e0e', bbox_inches='tight')
        buf.seek(0)
        plt.close()

        caption = f"""📊 XAUUSD ORO - ANÁLISIS VIP PRO
💰 Precio: {precio:.2f}
{tendencia}
🔝 Máximo: {max_p:.2f}
🔻 Mínimo: {min_p:.2f}
⏰ Hora EC: {hora_ec}

Señales Deivid VIP 🚀
Canal Oficial"""

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files = {'photo': ('oro_vip_pro.png', buf, 'image/png')}
        r = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files=files, timeout=30)
        return f"Enviado PRO! {r.text}"
    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    app.run()
