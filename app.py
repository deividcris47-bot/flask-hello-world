import os
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "BOT V4.1 ACTIVO - XAU SENALES DEIVID VIP - Listo para /test", 200

@app.route('/test')
def test():
    return "TEST OK - El bot esta vivo. Ahora ponemos las senales con TP1 TP2 TP3", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
