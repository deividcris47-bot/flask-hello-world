from flask import Flask
import yfinance as yf

app = Flask(__name__)

@app.route('/')
def home():
    return "BOT XAU SENALES DEIVID VIP - ONLINE", 200

@app.route('/test')
def test():
    try:
        df = yf.download("GC=F", period="1d", interval="1h", progress=False)
        if df is None or df.empty:
            return "TEST OK - Bot vivo (Yahoo sin datos)", 200
        precio = float(df['Close'].iloc[-1])
        return f"TEST OK - Bot vivo - XAU {precio:.2f}", 200
    except Exception as e:
        return f"TEST OK - Bot vivo - {e}", 200

@app.route('/enviar_grafico')
def enviar_grafico():
    return "Grafico OK - Ruta activa", 200

@app.errorhandler(404)
def notfound(e):
    return "BOT ONLINE - Usa /test", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
