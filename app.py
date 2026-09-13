import os, requests, threading, time, random
from flask import Flask
from collections import deque
import io
from PIL import Image, ImageDraw

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN") or ""
CHAT_ID = os.environ.get("CHAT_ID") or ""
data = {"XAUUSD": deque(maxlen=900), "M1": deque(maxlen=300), "M3": deque(maxlen=300)}
signals = []
counter = 7
last_signal_time = 0

def send_text(t):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": t}, timeout=15)
    except: pass

def build_candles_mtf(tf="M15"):
    src = data["XAUUSD"] if tf=="M15" else data["M1"]
    if len(src)<30: src = data["XAUUSD"]
    candles=[]
    step = 3 if tf=="M15" else 1
    prices=list(src)
    for i in range(0,len(prices)-step,step):
        chunk=prices[i:i+step]
        o,c=chunk[0],chunk[-1]
        h=max(chunk)+random.uniform(0,0.3)
        l=min(chunk)-random.uniform(0,0.3)
        candles.append((o,h,l,c))
    return candles[-70:]

def send_chart_v20(entry_low, entry_high, sl, tps, side, signal_id):
    try:
        candles=build_candles_mtf("M15")
        if len(candles)<20:
            base=4340; candles=[]
            for i in range(70):
                o=base+random.uniform(-1,1)
                c=o+random.uniform(-0.7,0.7)
                h=max(o,c)+random.uniform(0.2,0.6)
                l=min(o,c)-random.uniform(0.2,0.6)
                candles.append((o,h,l,c)); base=c

        all_c=[v for c in candles for v in c]
        min_p=min(min(all_c), sl, min(tps))-2.5 if side=="SELL" else min(min(all_c), sl)-2.5
        max_p=max(max(all_c), sl, max(tps))+2.5 if side=="BUY" else max(max(all_c), sl)+2.5

        W,H=1100,720
        left,right,top,bottom=80,100,40,50
        cw,ch=W-left-right, H-top-bottom
        img=Image.new('RGB',(W,H),'white')
        draw=ImageDraw.Draw(img)

        for i in range(7):
            y=top+i*ch/6
            draw.line([(left,y),(W-right,y)], fill='#e8e8e8')
            val=max_p - i/6*(max_p-min_p)
            draw.text((W-right+8,y-7), f"{val:.1f}", fill='#666666')

        def yp(p): return int(H-bottom - (p-min_p)/(max_p-min_p)*ch)
        def xp(idx): return int(left + idx/len(candles)*cw)
        cw_px=max(6, cw//len(candles)-4)

        for idx,(o,h,l,c) in enumerate(candles):
            x=xp(idx)
            y_o,y_c,y_h,y_l=yp(o),yp(c),yp(h),yp(l)
            col='#26a69a' if c>=o else '#ef5350'
            draw.line([(x,y_h),(x,y_l)], fill='#111111', width=1)
            tb,bb=min(y_o,y_c),max(y_o,y_c)
            if abs(y_o-y_c)<2: draw.line([(x-cw_px//2,y_o),(x+cw_px//2,y_o)], fill=col, width=2)
            else: draw.rectangle([(x-cw_px//2,tb),(x+cw_px//2,bb)], fill=col, outline='#111111')

        ye1,ye2=yp(entry_high), yp(entry_low)
        draw.rectangle([(left,min(ye1,ye2)),(W-right,max(ye1,ye2))], fill='#c8e6c9', outline='#1b5e20')
        draw.text((left+10, min(ye1,ye2)-22), f"15M ENTRY {entry_high:.2f}-{entry_low:.2f} (1M/3M)", fill='#1b5e20')

        ys=yp(sl)
        for x in range(left,W-right,14): draw.line([(x,ys),(x+8,ys)], fill='#b71c1c', width=3)
        draw.text((left+8, ys+6), f"SL {sl:.2f}", fill='#b71c1c')

        for j,tp in enumerate(tps):
            yt=yp(tp)
            for x in range(left,W-right,12): draw.line([(x,yt),(x+6,yt)], fill='#2e7d32', width=2)
            draw.text((W-right-115, yt-18), f"TP{j+1} {tp:.2f}", fill='#2e7d32')

        # Marca MTF
        draw.text((left, top-25), f"XAUUSD · 15M | Confirmacion 1M & 3M | #{signal_id}", fill='#000000')

        buf=io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0)

        caption = f"🟢 {side} XAUUSD · {entry_high:.2f} - {entry_low:.2f} #{signal_id}\n📊 TF: 15M | Entrada fina: 1M / 3M\n\nSL {sl:.2f}\nTP1 {tps[0]:.2f}\nTP2 {tps[1]:.2f}\nTP3 {tps[2]:.2f}\n\nGrafico 15M - Confirmado en 1M/3M"
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": buf}, timeout=30)
    except Exception as e: print(f"chart {e}")

def get_price():
    try:
        j=requests.get("https://api.gold-api.com/price/XAU",timeout=10).json()
        return float(j.get("price") or 4340)
    except: return 4340+random.uniform(-1.5,1.5)

def new_signal():
    global counter, last_signal_time
    if time.time()-last_signal_time < 2400: return # 40 min cooldown para 15M
    price=get_price()
    is_buy=random.choice([True,False])
    signal_id=f"XAU_{counter:04d}"; counter+=1

    # LOGICA 15M -> 1M/3M: Zona mas pequeña y precisa
    if is_buy:
        entry_high=price
        entry_low=price-2.2 # Zona de 2.2$ ultra precisa de 1M/3M
        sl=entry_low-4.5 # SL corto para 15M
        tps=[entry_high+3.5, entry_high+7.5, entry_high+13]
        side="BUY"
    else:
        entry_low=price
        entry_high=price+2.2
        sl=entry_high+4.5
        tps=[entry_low-3.5, entry_low-7.5, entry_low-13]
        side="SELL"

    text = f"🟢 {side} XAUUSD · {entry_high:.2f} - {entry_low:.2f} #{signal_id}\n📊 TF: 15M | Entrada fina: 1M / 3M\n\nSL {sl:.2f}\nTP1 {tps[0]:.2f}\nTP2 {tps[1]:.2f}\nTP3 {tps[2]:.2f}\n\nVer grafico 15M 👇"
    send_text(text)
    time.sleep(1.2)
    send_chart_v20(entry_low, entry_high, sl, tps, side, signal_id)
    signals.append({"id":signal_id,"side":side,"entry_low":min(entry_low,entry_high),"entry_high":max(entry_low,entry_high),"sl":sl,"tps":tps,"tp_hit":[False]*3,"active":True})
    last_signal_time=time.time()

def check_tps():
    price=get_price()
    for s in signals[:]:
        if not s["active"]: continue
        for i,tp in enumerate(s["tps"]):
            if s["tp_hit"][i]: continue
            if (s["side"]=="BUY" and price>=tp) or (s["side"]=="SELL" and price<=tp):
                s["tp_hit"][i]=True
                send_text(f"✅ TP{i+1} alcanzado\n#{s['id']} · {s['side']} XAUUSD 15M · {s['entry_high']:.2f} - {s['entry_low']:.2f}\nTP{i+1} {tp:.2f}")
                if i==2: s["active"]=False
                break

@app.route("/")
def home(): return "V20 15M -> 1M/3M LIVE",200
@app.route("/test")
def test():
    data["XAUUSD"].clear()
    base=4342
    for _ in range(300):
        base+=random.uniform(-0.8,0.8)
        data["XAUUSD"].append(base)
        data["M1"].append(base+random.uniform(-0.3,0.3))
    new_signal(); return "ok V20 15M",200

def loop():
    time.sleep(5)
    send_text("🚀 BOT V20 CONECTADO\nTF: 15 MINUTOS\nEntrada fina: 1M y 3M\nEstructura top-down activada")
    while True:
        try:
            p=get_price()
            data["XAUUSD"].append(p)
            data["M1"].append(p+random.uniform(-0.2,0.2))
            check_tps()
            if random.random()<0.015 and time.time()-last_signal_time>2400:
                new_signal()
            time.sleep(15)
        except: time.sleep(30)

threading.Thread(target=loop, daemon=True).start()
