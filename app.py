import os, time, threading, requests, yfinance as yf, pandas as pd, random
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN", "8389616359:AAHzg1l8Pq4I2R4r9Jzq0x1y2z3a4b5c6d")
CHAT_ID = os.getenv("CHAT_ID", "-1001234567890")
SYMBOL = "GC=F"
app = Flask(__name__)

# Memoria para no repetir
ultima = {"t":0, "entrada":0, "tipo":None, "tps":[], "sl":0, "id":None}
tps_tocados = set()

def enviar_texto_tp(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e: print(f"Error texto: {e}")

def enviar_foto_bdm(ruta, tipo, entrada, sl, tps, id_op, es_tp4=False):
    color = "🔴" if tipo=="SELL" else "🟢"
    if not es_tp4:
        caption = f"""{color} {tipo} XAUUSD · {entrada:.0f}
#{id_op}

SL {sl:.0f}
TP1 {tps[0]:.0f}
TP2 {tps[1]:.0f}
TP3 {tps[2]:.0f}

Ver gráfico

Contenido educativo, no es asesoramiento financiero."""
    else:
        caption = f"""✅ TP4 alcanzado - Cerramos todo
#{id_op} · {tipo} XAUUSD · {entrada:.0f}
Entrada {entrada:.0f} -> TP4 {tps[3]:.0f} (+{abs(tps[3]-entrada):.0f}$)"""

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        with open(ruta,'rb') as f:
            requests.post(url, data={"chat_id":CHAT_ID,"caption":caption}, files={"photo":f}, timeout=15)
    except Exception as e: print(f"Error foto: {e}")

def generar_grafico_bdm(df15, tipo, entrada, sl, tps):
    try:
        df = df15.tail(90)
        fig, ax = plt.subplots(figsize=(8,4.5), dpi=150)
        fig.patch.set_facecolor('#131722'); ax.set_facecolor('#131722')
        for i in range(len(df)):
            o,h,l,c = float(df['Open'].iloc[i]), float(df['High'].iloc[i]), float(df['Low'].iloc[i]), float(df['Close'].iloc[i])
            col = '#26a69a' if c>=o else '#ef5350'
            ax.plot([i,i],[l,h],color=col,linewidth=0.8); ax.plot([i,i],[o,c],color=col,linewidth=2.5)
        ax.axhline(entrada, color='#2962ff', linestyle=':', linewidth=1.2)
        ax.axhline(sl, color='#ff3d00', linestyle=':', linewidth=1)
        for tp in tps[:3]: ax.axhline(tp, color='#00c853', linestyle=':', linewidth=0.7)
        if len(tps)>3: ax.axhline(tps[3], color='#ffd600', linestyle='--', linewidth=1.2)
        ax.text(len(df)-1, entrada, f' {entrada:.0f}', color='white', fontsize=8, weight='bold')
        ax.set_xticks([]); ax.set_yticks([]); ax.spines[:].set_visible(False)
        ruta = '/tmp/bdm.png'; plt.tight_layout(pad=0.5); plt.savefig(ruta, facecolor='#131722'); plt.close(); return ruta
    except Exception as e:
        print(f"Error grafico: {e}"); return None

def get_data():
    try:
        df = yf.download(SYMBOL, period="2d", interval="15m", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df.dropna()
    except: return None

def check():
    while True:
        try:
            df15 = get_data()
            if df15 is None: time.sleep(30); continue
            precio = float(df15['Close'].iloc[-1])
            high_20 = float(df15['High'].rolling(30).max().iloc[-1])
            low_20 = float(df15['Low'].rolling(30).min().iloc[-1])

            # 1. VIGILAR OPERACION ABIERTA - SOLO 1 VEZ CADA TP
            if ultima["id"]:
                tipo = ultima["tipo"]; entrada = ultima["entrada"]; tps = ultima["tps"]; sl = ultima["sl"]; id_op = ultima["id"]
                key_tp1 = f"{id_op}_TP1"
                key_tp4 = f"{id_op}_TP4"

                if tipo=="BUY":
                    if precio >= tps[0] and key_tp1 not in tps_tocados:
                        enviar_texto_tp(f"✅ TP1 alcanzado\n#{id_op} · BUY XAUUSD · {entrada:.0f}")
                        tps_tocados.add(key_tp1)
                    if precio >= tps[3] and key_tp4 not in tps_tocados:
                        ruta=generar_grafico_bdm(df15,tipo,entrada,sl,tps)
                        if ruta: enviar_foto_bdm(ruta,tipo,entrada,sl,tps,id_op,es_tp4=True)
                        tps_tocados.add(key_tp4); ultima["id"]=None; tps_tocados.clear()
                        ultima["t"] = time.time()
                else: # SELL
                    if precio <= tps[0] and key_tp1 not in tps_tocados:
                        enviar_texto_tp(f"✅ TP1 alcanzado\n#{id_op} · SELL XAUUSD · {entrada:.0f}")
                        tps_tocados.add(key_tp1)
                    if precio <= tps[3] and key_tp4 not in tps_tocados:
                        ruta=generar_grafico_bdm(df15,tipo,entrada,sl,tps)
                        if ruta: enviar_foto_bdm(ruta,tipo,entrada,sl,tps,id_op,es_tp4=True)
                        tps_tocados.add(key_tp4); ultima["id"]=None; tps_tocados.clear()
                        ultima["t"] = time.time()
                time.sleep(15); continue

            # 2. NUEVA SEÑAL - SOLO CADA 40 MIN (anti-doble)
            if time.time() - ultima["t"] < 2400: time.sleep(15); continue

            tipo=None; zona=None
            if abs(precio-high_20)<=10: tipo="SELL"; zona=high_20
            elif abs(precio-low_20)<=10: tipo="BUY"; zona=low_20
            else: time.sleep(15); continue

            entrada = zona
            if tipo=="BUY":
                sl = entrada - 11
                tps = [entrada+5, entrada+10, entrada+18, entrada+28]
            else:
                sl = entrada + 11
                tps = [entrada-5, entrada-10, entrada-18, entrada-28]

            id_op = f"XAU_0{random.randint(200,299)}{random.randint(0,9)}"
            ruta = generar_grafico_bdm(df15, tipo, entrada, sl, tps)
            if ruta:
                enviar_foto_bdm(ruta, tipo, entrada, sl, tps, id_op, es_tp4=False)
                ultima.update({"t":time.time(), "entrada":entrada, "tipo":tipo, "tps":tps, "sl":sl, "id":id_op})

            time.sleep(15)
        except Exception as e: print(e); time.sleep(15)

@app.route('/')
def home(): return "V7.2 BDM 3TP FIX OK - Sin dobles"
@app.route('/test')
def test():
    df15=get_data(); p=float(df15['Close'].iloc[-1])
    tps=[p+5,p+10,p+18,p+28]; ruta=generar_grafico_bdm(df15,"SELL",p,p+11,tps)
    enviar_foto_bdm(ruta,"SELL",p,p+11,tps,f"XAU_0{random.randint(200,299)}")
    return "TEST 3TP ENVIADO - Revisa Telegram"

threading.Thread(target=check, daemon=True).start()
if __name__=='__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
