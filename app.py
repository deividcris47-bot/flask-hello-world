from flask import Flask
import threading, time, requests, os
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt

app = Flask(__name__)

BOT_TOKEN = "8870473192:AAEiJnwhA0fuMmc1CtfH_UJ27HVYIQwOflU"
CHAT_ID = "-1004419307514"

# ========= TELEGRAM =========
def send_msg(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
    except Exception as e: print(e)

def send_chart(image_path, caption):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(image_path, 'rb') as f:
            requests.post(url, data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "Markdown"}, files={"photo": f}, timeout=20)
    except Exception as e: print(f"Error foto: {e}")

# ========= SMC LOGIC =========
def get_analysis():
    df15 = yf.download("GC=F", period="5d", interval="15m", progress=False, auto_adjust=True)
    df5 = yf.download("GC=F", period="2d", interval="5m", progress=False, auto_adjust=True)
    df15.dropna(inplace=True)
    df5.dropna(inplace=True)

    # Tendencia 15M con EMA 50 y 200
    df15['EMA50'] = df15['Close'].ewm(span=50).mean()
    df15['EMA200'] = df15['Close'].ewm(span=200).mean()
    
    last = df15.iloc[-1]
    prev_high = df15['High'].tail(20).max()
    prev_low = df15['Low'].tail(20).min()
    
    tendencia = "ALCISTA" if last['Close'] > last['EMA50'] > last['EMA200'] else "BAJISTA" if last['Close'] < last['EMA50'] else "LATERAL"
    
    # BOS / CHOCH
    bos_alcista = last['Close'] > prev_high
    bos_bajista = last['Close'] < prev_low
    choch = "CHOCH BAJISTA" if bos_bajista and tendencia == "ALCISTA" else "CHOCH ALCISTA" if bos_alcista and tendencia == "BAJISTA" else ""

    # ORDER BLOCK (ultima vela opuesta antes del impulso)
    ob_price = df15.iloc[-3]['Low'] if bos_bajista else df15.iloc[-3]['High'] if bos_alcista else last['Close']
    ob_type = "BEARISH OB" if bos_bajista else "BULLISH OB" if bos_alcista else "NO OB"

    # IMBALANCE / FVG
    fvg = abs(df15['High'].iloc[-2] - df15['Low'].iloc[-3]) > (last['Close']*0.001)

    # POI / Zona de Resteo
    poi = df15['Low'].tail(30).min() if tendencia == "BAJISTA" else df15['High'].tail(30).max()

    return df15, df5, {
        "tendencia": tendencia,
        "bos_alcista": bos_alcista,
        "bos_bajista": bos_bajista,
        "choch": choch,
        "ob": ob_price,
        "ob_type": ob_type,
        "fvg": fvg,
        "poi": poi,
        "precio": last['Close']
    }

def make_chart(df15, info):
    # Grafico real de velas japonesas
    df_plot = df15.tail(60).copy()
    df_plot.index.name = 'Date'
    
    # SL y TPs
    if info['tendencia'] == "BAJISTA":
        sl = df_plot['High'].tail(10).max() + 2
        t1 = info['precio'] - 3
        t2 = info['precio'] - 6
        t3 = info['precio'] - 10
    else:
        sl = df_plot['Low'].tail(10).min() - 2
        t1 = info['precio'] + 3
        t2 = info['precio'] + 6
        t3 = info['precio'] + 10

    # Niveles para dibujar
    hlines = dict(hlines=[info['ob'], info['poi'], sl, t1, t2, t3],
                  colors=['orange','blue','red','green','green','green'],
                  linestyle=['--','-.','-','--','--','-'],
                  linewidths=[1.5,1.5,1.2,1,1,1.2])

    save = dict(fname="chart.png", dpi=100)
    mpf.plot(df_plot, type='candle', style='yahoo', title=f"XAUUSD 15M - {info['tendencia']} - {info['choch']}",
             hlines=hlines, savefig=save, volume=False, figratio=(12,6))
    
    return sl, t1, t2, t3

# ========= BOT LOOP =========
def bot_loop():
    time.sleep(10)
    send_msg("✅ *V5 SMC PRO ACTIVADO*\n15M Análisis / 5M Gatillo\nCHOCH-BOS-OB-FVG-POI + TP/SL + Gráfico")

    while True:
        try:
            df15, df5, info = get_analysis()
            
            # Gatillo 5M
            vela5 = df5.iloc[-1]
            gatillo_sell = vela5['Close'] < vela5['Open'] and info['bos_bajista']
            gatillo_buy = vela5['Close'] > vela5['Open'] and info['bos_alcista']

            log = f"{info['tendencia']} | {info['choch']} | {info['ob_type']} | Precio {info['precio']:.2f}"
            print(log, flush=True)

            if (gatillo_sell or gatillo_buy) and info['fvg']:
                sl, t1, t2, t3 = make_chart(df15, info)
                
                tipo = "SELL" if gatillo_sell else "BUY"
                caption = f"""
🚨 *SEÑAL {tipo} CONFIRMADA - SMC*

📊 *Tendencia 15M:* {info['tendencia']}
🔄 *Estructura:* {info['choch'] if info['choch'] else 'BOS ' + tipo}
📦 *Order Block:* {info['ob_type']} en {info['ob']:.2f}
⚖️ *Imbalance/FVG:* {'SI ✅' if info['fvg'] else 'NO'}
📍 *POI / Zona Resteo:* {info['poi']:.2f}
💥 *Rompimiento:* {info['precio']:.2f}

🎯 *ENTRADA:* {info['precio']:.2f}
🛑 *SL:* {sl:.2f}
✅ *T1:* {t1:.2f}
✅ *T2:* {t2:.2f}
✅ *T3:* {t3:.2f}

15M análisis + 5M gatillo
"""
                send_chart("chart.png", caption)

            time.sleep(300) # 5 min
        except Exception as e:
            print(f"Error loop: {e}", flush=True)
            time.sleep(300)

threading.Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home(): return "V5 SMC PRO Live - 15M/5M + OB/FVG/CHOCH/BOS + CHART"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
