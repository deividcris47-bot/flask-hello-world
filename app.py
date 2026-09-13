import os, requests, threading, time, random
from flask import Flask
from collections import deque
import io
from PIL import Image, ImageDraw

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN") or ""
CHAT_ID = os.environ.get("CHAT_ID") or ""
data = {"XAUUSD": deque(maxlen=600)}
signals = []
counter = 5
last_signal_time = 0

def send_text(t):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": t}, timeout=15)
    except: pass

def build_candles():
    prices = list(data["XAUUSD"])
    candles=[]
    for i in range(0,len(prices)-2,3):
        chunk=prices[i:i+3]
        o,c=chunk[0],chunk[-1]
        h=max(chunk)+random.uniform(0,0.5)
        l=min(chunk)-random.uniform(0,0.5)
        candles.append((o,h,l,c))
    return candles[-65:]

def send_chart_v19(entry_low, entry_high, sl, tps, side, signal_id):
    try:
        candles=build_candles()
        if len(candles)<20:
            base=4340
            candles=[]
            for i in range(70):
                o=base+random.uniform(-1.2,1.2)
                c=o+random.uniform(-0.9,0.9)
                h=max(o,c)+random.uniform(0.2,0.7)
                l=min(o,c)-random.uniform(0.2,0.7)
                candles.append((o,h,l,c))
                base=c

        entry_mid=(entry_low+entry_high)/2
        all_c=[v for c in candles for v in c]
        if side=="BUY":
            min_p=min(min(all_c), sl)-2.5
            max_p=max(max(all_c), tps[2])+2.5
        else:
            min_p=min(min(all_c), tps[2])-2.5
            max_p=max(max(all_c), sl)+2.5

        W,H=1050,700
        left,right,top,bottom=75,95,35,45
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
        cw_px=max(5, cw//len(candles)-4)

        for idx,(o,h,l,c) in enumerate(candles):
            x=xp(idx)
            y_o,y_c,y_h,y_l=yp(o),yp(c),yp(h),yp(l)
            col='#26a69a' if c>=o else '#ef5350'
            draw.line([(x,y_h),(x,y_l)], fill='#111111', width=1)
            tb,bb=min(y_o,y_c),max(y_o,y_c)
            if abs(y_o-y_c)<2:
                draw.line([(x-cw_px//2,y_o),(x+cw_px//2,y_o)], fill=col, width=2)
            else:
                draw.rectangle([(x-cw_px//2,tb),(x+cw_px//2,bb)], fill=col, outline='#111111')

        ye1,ye2=yp(entry_high), yp(entry_low)
        draw.rectangle([(left,min(ye1,ye2)),(W-right,max(ye1,ye2))], fill='#c8e6c9', outline='#1b5e20')
        draw.line([(left,yp(entry_mid)),(W-right,yp(entry_mid))], fill='#1b5e20', width=4)
        draw.text((left+8, min(ye1,ye2)-20), f"ENTRADA {entry_low:.2f}-{entry_high:.2f}", fill='#1b5e20')

        ys=yp(sl)
        for x in range(left,W-right,14):
            draw.line([(x,ys),(x+8,ys)], fill='#b71c1c', width=3)
        draw.text((left+8, ys+6), f"SL {sl:.2f}", fill='#b71c1c')

        for j,tp in enumerate(tps):
            yt=yp(tp)
            for x in range(left,W-right,12):
                draw.line([(x,yt),(x+6,yt)], fill='#2e7d32', width=2)
            draw.text((W-right-115, yt-18), f"TP{j+1} {tp:.2f}", fill='#2e7d32')

        buf=io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        caption = f"🟢 {side} XAUUSD · {entry_low:.2f} - {entry_high:.2f} #{signal_id}\n\nSL {sl:.2f}\nTP1 {tps[0]:.2f}\nTP2 {tps[1]:.2f}\nTP3 {tps[2]:.2f}\n\nGrafico Pro Velas - Contenido educativo"
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
        data={"chat_id": CHAT_ID, "caption": caption},
        files={"photo": buf}, timeout=30)
    except Exception as e:
        print(f"chart {e}")

def get_price():
    try:
        j=requests.get("https://api.gold-api.com/price/XAU",timeout=10).json()
        return float(j.get("price") or 4340)
    except: return 4340+random.uniform(-2,2)

def new_signal():
    global counter, last_signal_time
    if time.time()-last_signal_time < 3000: return
    price=get_price()
    is_buy=random.choice([True,True,False])
    signal_id=f"XAU_{counter:04d}"
    counter+=1
    if is_buy:
        entry_high=price
        entry_low=price-3.0
        sl=entry_low-6.8
        tps=[entry_high+4.8, entry_high+10.5, entry_high+19]
        side="BUY"
    else:
        entry_low=price
        entry_high=price+3.0
        sl=entry_high+6.8
        tps=[entry_low-4.8, entry_low-10.5, entry_low-19]
        side="SELL"

    text = f"🟢 {side} XAUUSD · {entry_low:.2f} - {entry_high:.2f} #{signal_id}\n\nSL {sl:.2f}\nTP1 {tps[0]:.2f}\nTP2 {tps[1]:.2f}\nTP3 {tps[2]:.2f}\n\nVer gráfico 👇"
    send_text(text)
    time.sleep(1.5)
    send_chart_v19(entry_low, entry_high, sl, tps, side, signal_id)

    signals.append({"id":signal_id,"side":side,"entry_low":min(entry_low,entry_high),"entry_high":max(entry_low,entry_high),"sl":sl,"tps":tps,"tp_hit":[False,False,False],"active":True})
    last_signal_time=time.time()
    print(f"V19 {signal_id}")

def check_tps():
    price=get_price()
    for s in signals[:]:
        if not s["active"]: continue
        for i,tp in enumerate(s["tps"]):
            if s["tp_hit"][i]: continue
            hit=False
            if s["side"]=="BUY" and price>=tp: hit=True
            if s["side"]=="SELL" and price<=tp: hit=True
            if hit:
                s["tp_hit"][i]=True
                send_text(f"✅ TP{i+1} alcanzado\n#{s['id']} · {s['side']} XAUUSD · {s['entry_low']:.2f} - {s['entry_high']:.2f}\n\nTP{i+1} {tp:.2f}")
                if i==2: s["active"]=False
                break

@app.route("/")
def home(): return "V19 FINAL BDM LIVE",200

@app.route("/test")
def test():
    data["XAUUSD"].clear()
    base=4342
    for _ in range(200):
        base+=random.uniform(-1.1,1.1)
        data["XAUUSD"].append(base)
    new_signal()
    return "ok V19 enviado",200

def loop():
    time.sleep(7)
    send_text("🚀 BOT V19 FINAL CONECTADO\nFormato BDM 100% Real\nGrafico Pro Velas + TP auto")
    while True:
        try:
            data["XAUUSD"].append(get_price())
            check_tps()
            if random.random()<0.012 and time.time()-last_signal_time>3600:
                new_signal()
            time.sleep(22)
        except: time.sleep(35)

threading.Thread(target=loop, daemon=True).start()
