from flask import Flask
import os, requests, io
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import pytz

app = Flask(__name__)

@app.route('/')
def home():
    return "ORO BOT VIP PRO V2 ✅"

@app.route('/enviar_grafico')
def enviar_grafico():
    try:
        BOT_TOKEN = (os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
        CHAT_ID = (os.getenv("TELEGRAM_CHAT_ID") or "").strip()

        data = yf.Ticker("GC=F").history(period="2d", interval="30m")
        if len(data) < 20:
            data = yf.Ticker("XAUUSD=X").history(period="2d", interval="30m")

        data = data.tail(50)
        precio = data['Close'].iloc[-1]
        max_p = data['High'].max()
        min_p = data['Low'].min()
        apertura = data['Open'].iloc[0]
        tendencia = "🟢 ALCISTA - BUSCAR COMPRAS" if precio > apertura else "🔴 BAJISTA - BUSCAR VENTAS"

        # GRAFICO TRADINGVIEW STYLE
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('#131722')
        ax.set_facecolor('#131722')

        ax.plot(data['Close'], color='#2962FF', linewidth=2.5)
        ax.fill_between(data.index, data['Close'], data['Close'].min(), alpha=0.1, color='#2962FF')

        # Lineas soporte/resistencia
        ax.axhline(max_p, color='#F23645', linestyle='--', linewidth=1, alpha=0.7)
        ax.axhline(min_p, color='#089981', linestyle='--', linewidth=1, alpha=0.7)
        ax.text(data.index[-1], max_p, f' R {max_p:.1f} ', backgroundcolor='#F23645', color='white', fontsize=9, va='center')
        ax.text(data.index[-1], min_p, f' S {min_p:.1f} ', backgroundcolor='#089981', color='white', fontsize=9, va='center')

        tz_ec = pytz.timezone('America/Guayaquil')
        hora_ec = datetime.now(tz_ec).strftime('%d/%m %H:%M')

        ax.set_title(f"XAUUSD • ORO • {precio:.2f} • {hora_ec} EC", fontsize=14, color='white', loc='left', fontweight='bold')
        ax.tick_params(colors='#787B86')
        ax.grid(True, color='#2A2E39', linestyle='-', linewidth=0.5, alpha=0.5)
        for spine in ax.spines.values():
            spine.set_color('#2A2E39')

        plt.xticks(rotation=0, color='#787B86')
        plt.yticks(color='#787B86')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200, facecolor='#131722')
        buf.seek(0)
        plt.close()

        caption = f"""📊 XAUUSD ORO - ANÁLISIS VIP PRO
💰 Precio: {precio:.2f}
{tendencia}
🔝 Resistencia: {max_p:.2f}
🔻 Soporte: {min_p:.2f}
⏰ Hora EC: {hora_ec}

Señales Deivid VIP 🚀
Canal Oficial"""

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files = {'photo': ('oro_tradingview.png', buf, 'image/png')}
        r = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption}, files=files, timeout=30)
        return f"Enviado V2! {r.text}"
    except Exception as e:
        return f"Error: {e}"
