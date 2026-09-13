import os, time, threading, requests, pandas as pd, traceback
from flask import Flask
from datetime import datetime, timedelta
import pytz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "88704419307514:AA...pon-tu-token-aqui")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "-1004419307514")
LAST_ERROR = "Ninguno"

PARES = {"BTCUSDT":"BTC/USD","PAXGUSDT":"XAU/USD ORO","EURUSDT":"EUR/USD"}

def get_data(s,i="15m",l=100):
    r=requests.get(f"https://api.binance.com/api/v3/klines?symbol={s}&interval={i}&limit={l}",timeout=10)
    df=pd.DataFrame(r.json(),columns=["t","o","h","l","c","v","ct","qv","n","tb","tq","i"])
    df["c"]=df["c"].astype(float); df["h"]=df["h"].astype(float); df["l"]=df["l"].astype(float)
    return df

def rsi_calc(s,p=14):
    d=s.diff(); g=d.where(d>0,0).rolling(p).mean(); l=-d.where(d<0,0).rolling(p).mean()
    return 100-(100/(1+g/l))

def analizar_par(symbol,nombre):
    df15=get_data(symbol,"15m",100); df1h=get_data(symbol,"1h",100)
    df15["ema9"]=df15["c"].ewm(span=9).mean(); df15["ema21"]=df15["c"].ewm(span=21).mean()
    df15["rsi"]=rsi_calc(df15["c"]); df1h["ema9"]=df1h["c"].ewm(span=9).mean(); df1h["ema21"]=df1h["c"].ewm(span=21).mean()
    precio=df15["c"].iloc[-1]; rsi=df15["rsi"].iloc[-1]
    ema9_15,ema21_15=df15["ema9"].iloc[-1],df15["ema21"].iloc[-1]
    ema9_1h,ema21_1h=df1h["ema9"].iloc[-1],df1h["ema21"].iloc[-1]
    res=df15["h"].tail(20).max(); sop=df15["l"].tail(20).min()
    tendencia="ALCISTA 🟢" if ema9_1h>ema21_1h else "BAJISTA 🔴"
    señal="🟡 ESPERAR"; tp1=tp2=tp3=sl=0
    if ema9_1h>ema21_1h:
        if precio>res*0.999 and ema9_15>ema21_15 and 50<rsi<75:
            señal="🟢 COMPRA FUERTE"; tp1, tp2, tp3 = precio*1.004, precio*1.008, precio*1.015; sl=precio*0.994
    else:
        if precio<sop*1.001 and ema9_15<ema21_15 and 25<rsi<50:
            señal="🔴 VENTA FUERTE"; tp1, tp2, tp3 = precio*0.996, precio*0.992, precio*0.985; sl=precio*1.006
    plt.figure(figsize=(10,6)); plt.plot(df15["c"].tail(60).values,linewidth=2.5,label="Precio")
    plt.plot(df15["ema9"].tail(60).values,linestyle="--",alpha=0.7,label="EMA9")
    plt.plot(df15["ema21"].tail(60).values,linestyle="--",alpha=0.7,label="EMA21")
    if tp1!=0:
        plt.axhline(tp1,color='green',linestyle='-',alpha=0.6,label=f'TP1 {tp1:.2f}'); plt.axhline(tp2,color='green',linestyle='-',alpha=0.8,label=f'TP2 {tp2:.2f}')
        plt.axhline(tp3,color='green',linestyle='-',linewidth=2,label=f'TP3 {tp3:.2f}'); plt.axhline(sl,color='red',linestyle='-',linewidth=2,label=f'SL {sl:.2f}')
    plt.legend(fontsize=8); plt.grid(True,alpha=0.3); plt.title(f"{nombre} - {señal} | RSI {rsi:.1f}",fontsize=12,fontweight='bold')
    buf=BytesIO(); plt.savefig(buf,format='png',dpi=150,bbox_inches='tight'); buf.seek(0); plt.close()
    if tp1!=0:
        cap=f"""{señal} | {nombre}\n📊 1H: {tendencia}\n💰 Entrada: ${precio:,.4f}\n📈 RSI 15M: {rsi:.1f}\n\n🎯 TP1: ${tp1:,.4f} (+0.4%)\n🎯 TP2: ${tp2:,.4f} (+0.8%)\n🎯 TP3: ${tp3:,.4f} (+1.5%)\n🛑 SL: ${sl:,.4f}\n\n⏰ {datetime.now(pytz.timezone('America/Guayaquil')).strftime('%d/%m %H:%M EC')}\n"""
    else:
        cap=f"""🟡 ESPERAR | {nombre}\n💰 ${precio:,.4f} | 1H: {tendencia} | RSI: {rsi:.1f}\n📉 Sop: ${sop:,.4f} | 📈 Res: ${res:,.4f}\n⏳ Sin entrada clara\n⏰ {datetime.now(pytz.timezone('America/Guayaquil')).strftime('%H:%M EC')}\n"""
    return buf,cap

def enviar_todos():
    global LAST_ERROR
    for symbol,nombre in PARES.items():
        try:
            img,cap=analizar_par(symbol,nombre)
            url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            files={'photo':(f'{symbol}.png',img,'image/png')}; data={'chat_id':CHANNEL_ID,'caption':cap}
            resp=requests.post(url,files=files,data=data,timeout=20)
            print(f"{nombre}: {resp.text}")
            if resp.status_code!=200: LAST_ERROR=resp.text
            time.sleep(5)
        except Exception as e: LAST_ERROR=traceback.format_exc(); print(LAST_ERROR)

@app.route('/')
def home(): return f"BOT V4.1 ACTIVO - Error: {LAST_ERROR[:200]} - EC: {datetime.now(pytz.timezone('America/Guayaquil')).strftime('%H:%M:%S')}",200

@app.route('/test')
def test():
    threading.Thread(target=enviar_todos,daemon=True).start()
    return "FORZANDO 3 SENALES! Revisa Telegram en 15s. Refresca / para ver error si no llega.",200

def bot_loop():
    tz=pytz.timezone('America/Guayaquil'); print(">>> BOT LOOP INICIADO")
    while True:
        try:
            now=datetime.now(tz); mp=((now.minute//15)+1)*15
            proximo=now.replace(minute=0,second=0,microsecond=0)+timedelta(hours=1) if mp==60 else now.replace(minute=mp,second=0,microsecond=0)
            espera=(proximo-now).total_seconds(); print(f"Proximo {proximo} espera {espera}s"); time.sleep(max(espera,10)); enviar_todos()
        except Exception as e: print(e); time.sleep(30)

threading.Thread(target=bot_loop,daemon=True).start()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
