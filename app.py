import os, requests
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

app = Flask(__name__)

@app.route('/')
def home():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": "✅ PRUEBA - Bot VIP gráfico negro funcionando"}
    r = requests.post(url, data=payload)
    return f"<h1>Respuesta de Telegram:</h1><pre>{r.text}</pre><br>Token: {BOT_TOKEN[:8]}... Chat: {CHANNEL_ID}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
