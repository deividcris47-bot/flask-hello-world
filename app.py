from flask import Flask
import requests, os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL = "@xau_deivid_vip"
CHART_URL = "https://es.tradingview.com/chart/VGC6IMYR/"

@app.route("/")
def home():
    return "BOT XAU PRO NEGRO - A GRATIS LIVE"

@app.route("/enviar_grafico")
def enviar_grafico():
    try:
        # 1. Tomamos captura GRATIS de tu TradingView con API free
        screenshot_api = f"https://api.microlink.io/?url={CHART_URL}&screenshot=true&meta=false&embed=screenshot.url"
        r = requests.get(screenshot_api, timeout=30).json()
        img_url = r['data']['screenshot']['url']
        
        # 2. Descargamos la imagen
        img_data = requests.get(img_url, timeout=30).content
        
        # 3. La enviamos a tu canal VIP
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        
        caption = """🔥 **XAUUSD | ORO AL CONTADO**
💰 Precio: 4.350.340
📊 Temporalidad: 1m
📈 Gráfico TradingView PRO Negro

@xau_deivid_vip"""
        
        files = {'photo': ('xau_pro.png', img_data)}
        data = {'chat_id': CHANNEL, 'caption': caption, 'parse_mode': 'Markdown'}
        
        resp = requests.post(telegram_url, data=data, files=files)
        return f"Enviado! {resp.text}"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
