import yfinance as yf, requests, time, pytz
import matplotlib.pyplot as plt
from datetime import datetime

BOT_TOKEN = "8870473192:AAElumHWfjg2paoljk1IANUvRW3dISms5eg"
CHAT_ID = "-1004419307514"
URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
SIMBOLOS = {"XAUUSD":"GC=F","EURUSD":"EURUSD=X","BTCUSD":"BTC-USD"}

EC_TZ = pytz.timezone('America/Guayaquil')

def get_sesion():
    h = datetime.now(EC_TZ).hour
    if 19 <= h or h < 3: return "🌏 ASIA"
    if 3 <= h < 8: return "🇬🇧 LONDRES"
    if 8 <= h < 17: return "🇺🇸 NEW YORK"
    return "FUERA"

def enviar_grafico_1m(df_1m, zona_top, zona_bottom, sl, tp1, tp2, tp3, par, accion):
    fig, ax = plt.subplots(figsize=(6.5,3.8), dpi=250)
    fig.patch.set_facecolor('#0e0e0e')
    ax.set_facecolor('#0e0e0e')

    df = df_1m.tail(120).reset_index(drop=True)
    for i,row in df.iterrows():
        col = '#26a69a' if row['Close']>=row['Open'] else '#ef5350'
        ax.plot([i,i],[row['Low'],row['High']], color=col, lw=0.8)
        bh = abs(row['Close']-row['Open'])
        if bh < (1 if par!="BTCUSD" else 5): bh = 1 if par!="BTCUSD" else 5
        ax.add_patch(plt.Rectangle((i-0.35, min(row['Open'],row['Close'])), 0.7, bh, facecolor=col, edgecolor=col, lw=0.5))

    # ZONA COMO TU FOTO
    ax.axhline(zona_top, color='#4fc3f7', lw=0.9, ls=(0,(2,2)), alpha=0.9)
    ax.axhline(zona_bottom, color='#4fc3f7', lw=0.9, ls=(0,(2,2)), alpha=0.9)
    ax.axhspan(zona_bottom, zona_top, color='#4fc3f7', alpha=0.15)
    ax.set_xlim(-2, len(df)+2)
    ax.axis('off')
    plt.tight_layout(pad=0.2)
    plt.savefig('chart.png', facecolor='#0e0e0e', bbox_inches='tight', pad_inches=0.05)
    plt.close()

    color = "🟢" if accion=="BUY" else "🔴"
    prec = 2 if par=="XAUUSD" else 5 if par=="EURUSD" else 0
    
    texto = f"""{color} {accion} {par} - {round(zona_top,prec)} - {round(zona_bottom,prec)}
#{par}_0002

SL  {round(sl,prec)}
TP1 {round(tp1,prec)}
TP2 {round(tp2,prec)}
TP3 {round(tp3,prec)}

⏰ {datetime.now(EC_TZ).strftime('%H:%M')} EC - {get_sesion()}
Contenido educativo, no es asesoramiento financiero."""

    with open('chart.png','rb') as f:
        requests.post(URL+"sendPhoto", data={'chat_id':CHAT_ID,'caption':texto}, files={'photo':f})

def analizar():
    sesion = get_sesion()
    if sesion=="FUERA": 
        print(f"Fuera de sesion {datetime.now(EC_TZ).strftime('%H:%M')}"); return

    for par, yahoo in SIMBOLOS.items():
        # 15M para analisis PDA
        df15 = yf.download(yahoo, period="5d", interval="15m", auto_adjust=True).dropna()
        # 1M para visual
        df1 = yf.download(yahoo, period="1d", interval="1m", auto_adjust=True).dropna()
        if len(df15)<50 or len(df1)<50: continue

        lastH = df15['High'].tail(30).max()
        lastL = df15['Low'].tail(30).min()
        c = df15['Close'].iloc[-1]
        p = df15['Close'].iloc[-2]

        accion = None
        if c > lastH and p < lastH: accion="BUY"
        if c < lastL and p > lastL: accion="SELL"
        if not accion: continue

        # ZONA 15M pero se ve en 1M
        if par=="XAUUSD":
            zona_top = c + 1.5; zona_bottom = c - 1.5
            sl = df15['Low'].tail(20).min() if accion=="BUY" else df15['High'].tail(20).max()
            tp1,tp2,tp3 = (c+3,c+6,c+12) if accion=="BUY" else (c-3,c-6,c-12)
        elif par=="EURUSD":
            zona_top = c + 0.00015; zona_bottom = c - 0.00015
            sl = df15['Low'].tail(20).min() if accion=="BUY" else df15['High'].tail(20).max()
            tp1,tp2,tp3 = (c+0.0008,c+0.0015,c+0.0025) if accion=="BUY" else (c-0.0008,c-0.0015,c-0.0025)
        else: # BTC
            zona_top = c + 15; zona_bottom = c - 15
            sl = c - 50 if accion=="BUY" else c + 50
            tp1,tp2,tp3 = (c+30,c+60,c+120) if accion=="BUY" else (c-30,c-60,c-120)

        enviar_grafico_1m(df1, zona_top, zona_bottom, sl, tp1, tp2, tp3, par, accion)

def esperar_1501():
    ahora = datetime.now(EC_TZ)
    minuto = ahora.minute
    proximo = ((minuto // 15) + 1) * 15
    espera = 0
    if proximo == 60:
        espera = (60 - minuto)*60 - ahora.second + 60 # +60 = minuto 01
    else:
        espera = (proximo - minuto)*60 - ahora.second + 60
    print(f"⏳ Proxima vela 15M a las :01 - faltan {espera//60}m - {datetime.now(EC_TZ).strftime('%H:%M:%S')} EC")
    time.sleep(espera)

# LOOP CADA 15:01 EC
while True:
    try: analizar()
    except Exception as e: print(e)
    esperar_1501()
