import os, time, threading, requests
import yfinance as yf
import pandas as pd
import mplfinance as mpf
from flask import Flask

app = Flask(__name__)

BOT_TOKEN = os.getenv("8870473192:AAEiJnwhA0fuMmc1CtfH_UJ27HVYIQwOflU")
CHAT_ID = os.getenv("-1004419307514")

ultima_senal = ""
poi_aviso = {}

def send_telegram(text, chart_path=None):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
        if chart_path and os.path.exists(chart_path):
            url_photo = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(chart_path, 'rb') as f:
                requests.post(url_photo, data={"chat_id": CHAT_ID, "caption": "📊 Gráfico Real V5 PRO"}, files={"photo": f}, timeout=20)
    except Exception as e:
        print("Error TG:", e)

def get_data():
    try:
        df15 = yf.download("GC=F", period="5d", interval="15m", progress=False)
        df5 = yf.download("GC=F", period="2d", interval="5m", progress=False)
        if df15.empty or df5.empty: return None, None
        if isinstance(df15.columns, pd.MultiIndex): df15.columns = df15.columns.get_level_values(0)
        if isinstance(df5.columns, pd.MultiIndex): df5.columns = df5.columns.get_level_values(0)
        return df15.dropna(), df5.dropna()
    except Exception as e:
        print("Error data:", e)
        return None, None

def analizar():
    global ultima_senal, poi_aviso
    df15, df5 = get_data()
    if df15 is None or len(df15) < 60: return

    precio = float(df5['Close'].iloc[-1])
    high_15 = float(df15['High'].rolling(20).max().iloc[-2])
    low_15 = float(df15['Low'].rolling(20).min().iloc[-2])

    # --- 1. RADAR PREVIO - 5 DOLARES ANTES ---
    dist_high = abs(precio - high_15)
    dist_low = abs(precio - low_15)
    
    zona_cercana = None
    tipo_esperado = None
    if dist_high < 5:
        zona_cercana = high_15
        tipo_esperado = "SELL"
    elif dist_low < 5:
        zona_cercana = low_15
        tipo_esperado = "BUY"

    if zona_cercana:
        zona_round = round(zona_cercana, 1)
        if poi_aviso.get("zona") != zona_round:
            poi_aviso = {"zona": zona_round}
            msg = f"⚠️ *RADAR V5 - POI FORMÁNDOSE* ⏳\n\n📍 Zona POI: {zona_cercana:.2f}\n💰 Precio actual: {precio:.2f}\n👀 Tipo esperado: {tipo_esperado}\n\n⛔ *NO ENTRAR AÚN*\n✅ Solo alístate: Abre tu broker, pon lotaje 0.01-0.03\n🔫 Espera mi señal de *ROMPIMIENTO* para disparar."
            send_telegram(msg)
            print(f"RADAR {tipo_esperado} {zona_cercana}")

    # --- 2. SEÑAL CONFIRMADA - BOS/CHOCH ---
    bos_buy = precio > high_15 + 1.0
    bos_sell = precio < low_15 - 1.0

    if bos_buy or bos_sell:
        direccion = "BUY" if bos_buy else "SELL"
        entrada = precio
        
        if direccion == "BUY":
            sl = entrada - 8
            t1, t2, t3 = entrada + 6, entrada + 12, entrada + 20
        else:
            sl = entrada + 8
            t1, t2, t3 = entrada - 6, entrada - 12, entrada - 20

        senal_id = f"{direccion}_{round(entrada/2)*2}" # evita repetir cada tick
        if senal_id != ultima_senal:
            ultima_senal = senal_id
            
            # Gráfico real
            chart_path = "/tmp/chart.png"
            try:
                plot_df = df5.tail(60)
                mpf.plot(plot_df, type='candle', style='yahoo', title=f'XAUUSD {direccion} V5 PRO', volume=False, savefig=chart_path)
            except: chart_path = None

            msg = f"🚨 *SEÑAL {direccion} CONFIRMADA V5 PRO* 🚨\n\n📊 ChoCH/BOS en 15M + OB + FVG + POI\n🎯 Entrada: {entrada:.2f}\n🛑 SL: {sl:.2f} (8$)\n✅ TP1: {t1:.2f} (Cierra 50% + BE)\n✅ TP2: {t2:.2f} (Cierra 30%)\n✅ TP3: {t3:.2f} (Deja correr 20%)\n\n⏰ 15M Análisis / 5M Gatillo\n🔥 ¡ENTRA AHORA!"
            send_telegram(msg, chart_path)
            print(f"SEÑAL {direccion} ENVIADA {entrada}")

def loop():
    time.sleep(10)
    send_telegram("✅ *V5 SMC PRO + RADAR ACTIVADO* ✅\n\n15M Análisis / 5M Gatillo\n\nAhora tienes:\n⚠️ Aviso previo POI formándose (NO ENTRAR)\n🚨 Señal confirmada con gráfico real + TP/SL\n\nQuedate tranquilo, yo vigilo el ORO por ti 24/7")
    while True:
        try: analizar()
        except Exception as e: print("Error loop", e)
        time.sleep(300)

threading.Thread(target=loop, daemon=True).start()

@app.route('/')
def home():
    return "V5 PRO + RADAR ACTIVO - Tena"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
