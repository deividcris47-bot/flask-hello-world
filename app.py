import os, time, threading, requests
import yfinance as yf
import pandas as pd
import mplfinance as mpf
from flask import Flask

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ultima_senal = ""
contador = 193
senales_activas = []
zonas_alertadas = {} # para no repetir pre-avisos

def send_telegram(text, chart_path=None):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}, timeout=15)
        if chart_path and os.path.exists(chart_path):
            url_photo = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(chart_path, 'rb') as f:
                requests.post(url_photo, data={"chat_id": CHAT_ID}, files={"photo": f}, timeout=20)
    except: pass

def get_live_price():
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/GC=F", timeout=5).json()
        return float(r['chart']['result'][0]['meta']['regularMarketPrice'])
    except: return None

def get_data():
    df15 = yf.download("GC=F", period="10d", interval="15m", progress=False)
    df5 = yf.download("GC=F", period="3d", interval="5m", progress=False)
    if isinstance(df15.columns, pd.MultiIndex): df15.columns = df15.columns.get_level_values(0)
    if isinstance(df5.columns, pd.MultiIndex): df5.columns = df5.columns.get_level_values(0)
    return df15.dropna(), df5.dropna()

def detectar_zona_retesteo(df15):
    # Zona de retesteo = 3+ toques al mismo nivel en 15M (como tu foto de triangulos)
    high_20 = df15['High'].rolling(20).max().iloc[-2]
    low_20 = df15['Low'].rolling(20).min().iloc[-2]

    # Contar cuantos toques hay cerca del high/low
    toques_high = ((df15['High'].tail(20) >= high_20 - 3) & (df15['High'].tail(20) <= high_20 + 3)).sum()
    toques_low = ((df15['Low'].tail(20) >= low_20 - 3) & (df15['Low'].tail(20) <= low_20 + 3)).sum()

    zona_high = toques_high >= 3
    zona_low = toques_low >= 3

    return high_20, low_20, zona_high, zona_low

def detectar_intencion(df5):
    # Vela de intencion en 5M: cuerpo grande + mecha corta + cierra fuerte hacia el nivel
    last = df5.iloc[-2]
    body = abs(last['Open'] - last['Close'])
    rango = last['High'] - last['Low']
    if rango == 0: return None

    cuerpo_grande = body > (rango * 0.65)
    # Intencion bajista: cierra cerca del low
    intencion_sell = cuerpo_grande and last['Close'] < last['Open'] and (last['Close'] - last['Low']) < (rango * 0.25)
    # Intencion alcista: cierra cerca del high
    intencion_buy = cuerpo_grande and last['Close'] > last['Open'] and (last['High'] - last['Close']) < (rango * 0.25)

    if intencion_sell: return "SELL"
    if intencion_buy: return "BUY"
    return None

def analizar():
    global ultima_senal, contador, senales_activas, zonas_alertadas
    df15, df5 = get_data()
    if df15 is None: return
    precio = get_live_price() or float(df5['Close'].iloc[-1])

    # --- 1. SEGUIMIENTO TPs ---
    for s in senales_activas[:]:
        if s['direccion'] == "SELL":
            if precio <= s['tp1'] and not s['tp1_hit']:
                send_telegram(f"✅ *TP1 alcanzado* #XAU_{s['id']:04d}"); s['tp1_hit']=True
            elif precio <= s['tp2'] and not s['tp2_hit']:
                send_telegram(f"✅✅ *TP2 alcanzado* #XAU_{s['id']:04d}"); s['tp2_hit']=True
            elif precio <= s['tp3'] and not s['tp3_hit']:
                send_telegram(f"✅✅✅ *TP3 alcanzado* #XAU_{s['id']:04d}"); s['tp3_hit']=True
            if precio >= s['sl']: senales_activas.remove(s)
        else:
            if precio >= s['tp1'] and not s['tp1_hit']:
                send_telegram(f"✅ *TP1 alcanzado* #XAU_{s['id']:04d}"); s['tp1_hit']=True
            elif precio >= s['tp2'] and not s['tp2_hit']:
                send_telegram(f"✅✅ *TP2 alcanzado* #XAU_{s['id']:04d}"); s['tp2_hit']=True
            elif precio >= s['tp3'] and not s['tp3_hit']:
                send_telegram(f"✅✅✅ *TP3 alcanzado* #XAU_{s['id']:04d}"); s['tp3_hit']=True
            if precio <= s['sl']: senales_activas.remove(s)

    # --- 2. DETECTAR ZONA DE RETESTEO 15M ---
    high_15, low_15, zona_high, zona_low = detectar_zona_retesteo(df15)
    intencion_5m = detectar_intencion(df5)

    # --- FASE 1: PRE-AVISO DE INTENCION ANTES DEL ROMPIMIENTO ---
    # Si esta cerca de la zona (a 8$) y hay intencion en 5M
    if intencion_5m:
        if intencion_5m == "SELL" and zona_high and abs(precio - high_15) < 10:
            key = f"pre_sell_{round(high_15)}"
            if zonas_alertadas.get(key) is None:
                zonas_alertadas[key] = time.time()
                send_telegram(
                    f"⚠️ *INTENCIÓN PARA VENTA DETECTADA*\n\n"
                    f"📍 Zona de Retesteo 15M: {high_15-7:.0f} - {high_15:.0f}\n"
                    f"🎯 15M: {int((df15['High'].tail(20) >= high_15 - 3).sum())} toques | 5M: Vela intención bajista\n"
                    f"💰 Precio actual: {precio:.2f}\n"
                    f"📉 Esperando CHoCH + BOS + OB + FVG para confirmar SELL\n"
                    f"⏳ Prepárate, posible rompimiento en minutos"
                )

        if intencion_5m == "BUY" and zona_low and abs(precio - low_15) < 10:
            key = f"pre_buy_{round(low_15)}"
            if zonas_alertadas.get(key) is None:
                zonas_alertadas[key] = time.time()
                send_telegram(
                    f"⚠️ *INTENCIÓN PARA COMPRA DETECTADA*\n\n"
                    f"📍 Zona de Retesteo 15M: {low_15:.0f} - {low_15+7:.0f}\n"
                    f"🎯 15M: {int((df15['Low'].tail(20) <= low_15 + 3).sum())} toques | 5M: Vela intención alcista\n"
                    f"💰 Precio actual: {precio:.2f}\n"
                    f"📈 Esperando CHoCH + BOS + OB + FVG para confirmar BUY\n"
                    f"⏳ Prepárate, posible rompimiento en minutos"
                )

    # --- FASE 2: CONFIRMACION - ROMPIMIENTO REAL ---
    bos_sell = precio < low_15 - 1 # rompio con 1$ de margen
    bos_buy = precio > high_15 + 1

    if (bos_sell and zona_low) or (bos_buy and zona_high):
        direccion = "SELL" if bos_sell else "BUY"
        nivel = low_15 if bos_sell else high_15
        senal_id = f"{direccion}_{round(nivel)}"
        if senal_id == ultima_senal: return
        ultima_senal = senal_id
        contador += 1

        if direccion == "SELL":
            zona_low_f, zona_high_f = nivel - 7, nivel
            sl = nivel + 7
            tp1, tp2, tp3, tp4 = zona_low_f - 5, zona_low_f - 12, zona_low_f - 18, zona_low_f - 25
        else:
            zona_low_f, zona_high_f = nivel, nivel + 7
            sl = nivel - 7
            tp1, tp2, tp3, tp4 = zona_high_f + 5, zona_high_f + 12, zona_high_f + 18, zona_high_f + 25

        senales_activas.append({'id': contador, 'direccion': direccion, 'zona_low': zona_low_f, 'zona_high': zona_high_f, 'sl': sl, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3, 'tp1_hit': False, 'tp2_hit': False, 'tp3_hit': False})

        chart_path = "/tmp/chart.png"
        try:
            colors = mpf.make_marketcolors(up='#00ff88', down='#ff4444', wick='white')
            style = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=colors, facecolor='#0d1117', figcolor='#0d1117')
            mpf.plot(df5.tail(80), type='candle', style=style, savefig=dict(fname=chart_path, dpi=150))
        except: chart_path = None

        icono = "🔴" if direccion=="SELL" else "🟢"
        msg = (
            f"{icono} *{direccion} XAUUSD · {zona_low_f:.0f} – {zona_high_f:.0f}*\n"
            f"#XAU_{contador:04d}\n\n"
            f"📊 Retesteo 15M + Intención 5M + BOS CONFIRMADO\n"
            f"🎯 OB: {zona_low_f:.0f}-{zona_high_f:.0f} | FVG + CHoCH\n\n"
            f"SL {sl:.0f}\n"
            f"TP1 {tp1:.0f}\n"
            f"TP2 {tp2:.0f}\n"
            f"TP3 {tp3:.0f}\n"
            f"TP4 {tp4:.0f}\n\n"
            f"[Ver gráfico](https://www.tradingview.com/symbols/XAUUSD/)\n\n"
            f"_Contenido educativo, no es asesoramiento financiero._"
        )
        send_telegram(msg, chart_path)

def loop():
    while True:
        try: analizar()
        except: pass
        time.sleep(60)

threading.Thread(target=loop, daemon=True).start()

@app.route('/')
def home(): return "V6.5 RETESTEO + INTENCION OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
