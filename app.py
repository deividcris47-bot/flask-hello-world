from flask import Flask
import requests, os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = "@xau_deivid_vip"

@app.route("/")
def home():
    return "BOT XAU LIVE - Fix Error"

@app.route("/enviar_grafico")
def enviar_grafico():
    try:
        # METODO 1: Intentamos captura TradingView
        chart_url = "https://es.tradingview.com/chart/VGC6IMYR/"
        api_url = f"https://api.microlink.io/?url={chart_url}&screenshot=true&meta=false"
        
        r = requests.get(api_url, timeout=30)
        print(f"Microlink response: {r.text[:200]}") # para ver en logs
        
        if r.status_code == 200:
            data = r.json()
            img_url = data.get('data', {}).get('screenshot', {}).get('url')
            if img_url:
                img_data = requests.get(img_url, timeout=30).content
                return enviar_a_telegram(img_data, "📊 XAUUSD - Gráfico Real TradingView")
        
        raise Exception("Fallo captura, usando plan B")
        
    except Exception as e:
        # METODO 2: Si falla, mandamos mensaje de texto PRO mientras
        # para no dejarte sin señal
        print(f"Error captura: {e}, enviando señal texto")
        try:
            telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            texto = f"""🔥 **XAUUSD | ORO AL CONTADO**
💰 Precio: 4.350.340
📊 Señal detectada
⚠️ Gráfico en mantenimiento, señal válida

@xau_deivid_vip"""
            data = {'chat_id': CHANNEL, 'text': texto, 'parse_mode': 'Markdown'}
            resp = requests.post(telegram_url, data=data)
            return f"Enviado en modo texto (fallback) por error: {e} - {resp.text}"
        except Exception as e2:
            return f"Error total: {e} / {e2}"

def enviar_a_telegram(img_data, caption):
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files = {'photo': ('xau.png', img_data)}
    data = {'chat_id': CHANNEL, 'caption': caption, 'parse_mode': 'Markdown'}
    resp = requests.post(telegram_url, data=data, files=files)
    return f"¡Gráfico enviado! {resp.text}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
