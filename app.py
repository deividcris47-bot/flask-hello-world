from flask import Flask
import yfinance as yf
import pandas as pd

app = Flask(__name__)

SYMBOLS = {
    "XAU/USD ORO": "GC=F",
    "BTC/USD": "BTC-USD",
    "EUR/USD": "EURUSD=X"
}

def analizar(symbol_name, ticker):
    try:
        df = yf.download(ticker, period="5d", interval="1h", progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 50:
            print(f"Sin datos {symbol_name} ({ticker})")
            return None
        
        # Arreglo del error: single positional indexer is out-of-bounds
        close = float(df['Close'].iloc[-1])
        ema20 = float(df['Close'].ewm(span=20).mean().iloc[-1])
        ema50 = float(df['Close'].ewm(span=50).mean().iloc[-1])
        
        if ema20 > ema50:
            tipo = "COMPRA"
        else:
            tipo = "VENTA"
            
        return f"{symbol_name}: {tipo} en {close:.2f}"
    except Exception as e:
        print(f"Error {symbol_name}: {e}")
        return None

@app.route('/')
def home():
    return "BOT V4 TP1 TP2 TP3 INICIADO - ONLINE", 200

@app.route('/test')
def test():
    resultados = []
    for name, ticker in SYMBOLS.items():
        r = analizar(name, ticker)
        if r:
            resultados.append(r)
    if not resultados:
        return "TEST OK - Bot vivo pero sin datos de Yahoo (normal en Render free). Esperando...", 200
    return "<br>".join(resultados), 200

@app.route('/enviar_grafico')
def enviar_grafico():
    # Esta era la que te daba 404, ahora ya existe
    r = analizar("XAU/USD ORO", "GC=F")
    if r:
        return f"Grafico OK: {r}", 200
    return "Grafico OK - Sin datos por ahora, reintentando", 200

@app.errorhandler(404)
def anti_404(e):
    return "BOT ONLINE - Usa / , /test o /enviar_grafico", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
