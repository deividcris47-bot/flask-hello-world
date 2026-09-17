import os, time, threading, requests
import yfinance as yf
import pandas as pd
import mplfinance as mpf
from flask import Flask

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

ultima_senal = ""
contador = 194
senales_activas = []
zonas_alertadas = {}
bot_iniciado = False

def send_telegram(text, chart_path=None):
    try:
        if not BOT_TOKEN or not CHAT_ID:
            print("FALTA BOT_TOKEN O CHAT_ID")
            return
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}, timeout=15)
        if chart_path and os.path.exists(chart_path):
            url_photo = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(chart_path, 'rb') as f:
                requests.post(url_photo, data={"chat_id": CHAT_ID}, files={"photo": f}, timeout=20)
        print(f"Telegram enviado: {text[:50]}")
    except Exception as e:
        print("Error TG:", e)

def get_live_price():
    try:
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/GC=F", timeout=5).json()
        return float(r['chart']['result'][0]['meta']['regularMarketPrice'])
    except:
        return None

def get_data():
    try:
        df15 = yf.download("GC=F", period="10d", interval="15m", progress=False, auto_adjust=True)
        df5 = yf.download("GC=F", period="3d", interval="5m", progress=False, auto_adjust=True)
        if isinstance(df15.columns, pd.MultiIndex): df15.columns = df15.columns.get_level_values(0)
        if isinstance(df5.columns, pd.MultiIndex): df5.columns = df5.columns.get_level_values(0)
        return df15.dropna(), df5.dropna()
    except Exception as e:
        print("Error data:", e)
        return None, None

def detectar_zona_retesteo(df15):
    high_20 = float(df15['High'].rolling(20).max().iloc[-2])
    low_20 = float(df15['Low'].rolling(20).min().iloc[-2])
    toques_high = ((df15['High'].tail(20) >= high_20 - 3) & (df15['High'].tail(20) <= high_20 + 3)).sum()
    toques_low = ((df15['Low'].tail(20) >= low_20 - 3) & (df15['Low'].tail(20) <= low_20 + 3)).sum()
    return high_20, low_20, toques_high >= 2, toques_low >= 2

def detectar_intencion(df5):
    if len(df5) < 5: return None
    last = df5.iloc[-2]
    body = abs(float(last['Open']) - float(last['Close']))
    rango = float(last['High']) - float(last['Low'])
    if rango == 0 or rango < 2.5: return None
    cuerpo_grande = body > (rango * 0.6)
    close = float(last['Close'])
    open_ = float(last['Open'])
    low = float(last['Low'])
    high = float(last['High'])
    intencion_sell = cuerpo_grande and close < open_ and (close - low) < (rango * 0.3)
    intencion_buy = cuerpo_grande and close > open_ and (high - close) < (rango * 0.3)
    if intencion_sell: return "SELL"
    if intencion_buy: return "BUY"
    return None

def analizar():
    global ultima_senal, contador, senales_activas, zonas_alertadas
    df15, df5 = get_data()
    if df15 is None or df5 is None or len(df15) < 30: return
    precio = get_live_price()
    if not precio: precio = float(df5['Close'].iloc[-1])

    # 1. TPs
    for s in senales_activas[:]:
        try:
            if s['direccion'] == "SELL":
                if precio <= s['tp1'] and not s['tp1_hit']:
                    send_telegram(f"✅ *TP1 alcanzado* #XAU_{s['id']:04d}\nSELL {s['zona_low']:.0f}-{s['zona_high']:.0f} -> TP1 {s['tp1']:.0f}"); s['tp1_hit']=True
                elif precio <= s['tp2'] and not s['tp2_hit']:
                    send_telegram(f"✅✅ *TP2 alcanzado* #XAU_{s['id']:04d}\nTP2 {s['tp2']:.0f}"); s['tp2_hit']=True
                elif precio <= s['tp3'] and not s['tp3_hit']:
                    send_telegram(f"✅✅✅ *TP3 alcanzado* #XAU_{s['id']:04d}\nTP3 {s['tp3']:.0f}"); s['tp3_hit']=True
                if precio >= s['sl']:
                    send_telegram(f"🛑 *SL alcanzado* #XAU_{s['id']:04d}"); senales_activas.remove(s)
            else:
                if precio >= s['tp1'] and not s['tp1_hit']:
                    send_telegram(f"✅ *TP1 alcanzado* #XAU_{s['id']:04d}\nBUY {s['zona_low']:.0f}-{s['zona_high']:.0f} -> TP1 {s['tp1']:.0f}"); s['tp1_hit']=True
                elif precio >= s['tp2'] and not s['tp2_hit']:
                    send_telegram(f"✅✅ *TP2 alcanzado* #XAU_{s['id']:04d}\nTP2 {s['tp2']:.0f}"); s['tp2_hit']=True
                elif precio >= s['tp3'] and not s['tp3_hit']:
                    send_telegram(f"✅✅✅ *TP3 alcanzado* #XAU_{s['id']:04d}\nTP3 {s['tp3']:.0f}"); s['tp3_hit']=True
                if precio <= s['sl']:
                    send_telegram(f"🛑 *SL alcanzado* #XAU_{s['id']:04d}"); senales_activas.remove(s)
        except: pass

    # 2. ZONAS
    high_15, low_15, zona_high, zona_low = detectar_zona_retesteo(df15)
    intencion_5m = detectar_intencion(df5)

    # FASE 1: PRE-AVISO
    if intencion_5m:
        if intencion_5m == "SELL" and zona_high and abs(precio - high_15) < 12:
            key = f"pre_sell_{round(high_15)}"
            if time.time() - zonas_alertadas.get(key, 0) > 3600:
                zonas_alertadas[key] = time.time()
                send_telegram(
                    f"⚠️ *INTENCIÓN PARA VENTA DETECTADA*\n\n"
                    f"📍 Zona Retesteo 15M: {high_15-7:.0f} - {high_15:.0f}\n"
                    f"🎯 Toques en zona + Vela intención 5M bajista\n"
                    f"💰 Precio: {precio:.2f}\n"
                    f"📉 Esperando CHOCH + BOS + OB + FVG\n"
                    f"⏳ Posible SELL en minutos"
                )
        if intencion_5m == "BUY" and zona_low and abs(precio - low_15) < 12:
            key = f"pre_buy_{round(low_15)}"
            if time.time() - zonas_alertadas.get(key, 0) > 3600:
                zonas_alertadas[key] = time.time()
                send_telegram(
                    f"⚠️ *INTENCIÓN PARA COMPRA DETECTADA*\n\n"
                    f"📍 Zona Retesteo 15M: {low_15:.0f} - {low_15+7:.0f}\n"
                    f"🎯 Toques en zona + Vela intención 5M alcista\n"
                    f"💰 Precio: {precio:.2f}\n"
                    f"📈 Esperando CHOCH + BOS + OB + FVG\n"
                    f"⏳ Posible BUY en minutos"
                )

    # FASE 2: CONFIRMACION BOS REAL CON LIVE PRICE
    bos_sell = precio < (low_15 - 1)
    bos_buy = precio > (high_15 + 1)

    if bos_sell or bos_buy:
        direccion = "SELL" if bos_sell else "BUY"
        nivel = low_15 if bos_sell else high_15
        senal_id = f"{direccion}_{round(nivel)}"
        if senal_id == ultima_senal: return
        ultima_senal = senal_id
        contador += 1

        if direccion == "SELL":
            zl, zh = nivel - 7, nivel
            sl = nivel + 8
            tp1, tp2, tp3, tp4 = zl - 5, zl - 12, zl - 18, zl - 25
        else:
            zl, zh = nivel, nivel + 7
            sl = nivel - 8
            tp1, tp2, tp3, tp4 = zh + 5, zh + 12, zh + 18, zh + 25

        senales_activas.append({'id': contador, 'direccion': direccion, 'zona_low': zl, 'zona_high': zh, 'sl': sl, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3, 'tp1_hit': False, 'tp2_hit': False, 'tp3_hit': False})

        chart_path = "/tmp/chart.png"
        try:
            colors = mpf.make_marketcolors(up='#00ff88', down='#ff4444', wick='white', edge='white')
            style = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=colors, facecolor='#0d1117', figcolor='#0d1117', gridstyle='--', gridcolor='#222')
            mpf.plot(df5.tail(80), type='candle', style=style, savefig=dict(fname=chart_path, dpi=150), tight_layout=True)
        except: chart_path = None

        icono = "🔴" if direccion=="SELL" else "🟢"
        msg = (
            f"{icono} *{direccion} XAUUSD · {zl:.0f} – {zh:.0f}*\n"
            f"#XAU_{contador:04d}\n\n"
            f"📊 Retesteo 15M + Intención 5M + BOS CONFIRMADO\n"
            f"🎯 OB: {zl:.0f}-{zh:.0f} | FVG + CHoCH\n\n"
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
        except Exception as e: print("Error loop:", e)
        time.sleep(60)

threading.Thread(target=loop, daemon=True).start()

@app.route('/')
def home():
    global bot_iniciado
    if not bot_iniciado:
        bot_iniciado = True
        send_telegram("✅ *BOT V6.5 CONECTADO* ✅\n\n📍 Zonas de Retesteo 15M\n⚠️ Pre-aviso Intención 5M\n🔴 Confirmación BOS + OB + FVG + CHoCH\n✅ Aviso TP1/TP2/TP3 automático\n\nEsperando mercado...")
    return "V6.5 OK - Tena Live"

@app.route('/test')
def test():
    send_telegram("✅ *TEST OK* - Tu bot está conectado. Si ves esto, te llegarán las señales.")
    return "Test enviado a Telegram"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
