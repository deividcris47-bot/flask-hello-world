import os, requests, threading, time, random
from flask import Flask
from collections import deque
import io
from PIL import Image, ImageDraw

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN") or ""
CHAT_ID = os.environ.get("CHAT_ID") or ""
data = {"XAUUSD": deque(maxlen=500)}
signals = []
counter = 4
last_signal_time = 0

def send_text(t):
    try:
        return requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": t, "parse_mode": "Markdown"}, timeout=15).json()
    except: return {}

def build_candles():
    prices = list(data["XAUUSD"])
    candles = []
    for i in range(0, len(prices)-2, 3):
        chunk = prices[i:i+3]
        o,c = chunk[0], chunk[-1]
        h = max(chunk)+random.uniform(0,0.4)
        l = min(chunk)-random.uniform(0,0.4)
        candles.append((o,h,l,c))
    return candles[-60:]

def send_chart_bdm(entry_low, entry_high, sl, tps, side, signal_id):
    try:
        candles = build_candles()
        if len(candles)<15:
            base=4339
            candles=[]
            for i in range(60):
                o=base+random.uniform(-1.5,1.5)
                c=o+random.uniform(-1,1)
                if i==50: c=o+6
                h=max(o,c)+random.uniform(0.2,0.8)
                l=min(o,c)-random.uniform(0.2,0.8)
                candles.append((o,h,l,c))
                base=c

        entry_mid=(entry_low+entry_high)/2
        # ZOOM CORREGIDO - para que las velas se vean grandes como tu ultima captura
        all_candle = [v for c in candles for v in c]
        min_c, max_c = min(all_candle), max(all_candle)
        min_p = min(min_c, sl, entry_low)-2
        max_p = max(max_c, entry_high, tps[2] if side=="BUY" else entry_high)+4
        if side=="SELL":
            min_p = min(min_c, tps[2])-4
            max_p = max(max_c, sl, entry_high)+2

        W,H=1000,650
        left,right,top,bottom=70,90,30,40
        cw,ch=W-left-right, H-top-bottom
        img=Image.new('RGB',(W,H),'white')
        draw=ImageDraw.Draw(img)

        for i in range(7):
            y=top+i*ch/6
            draw.line([(left,y),(W-right,y)], fill='#e0e0e0')
            val=max_p - i/6*(max_p-min_p)
            draw.text((W-right+5,y-6), f"{val:.1f}", fill='#555555')

        def yp(p): return int(H-bottom - (p-min_p)/(max_p-min_p)*ch)
        def xp(idx): return int(left + idx/len(candles)*cw)
        cw_px=max(4, cw//len(candles)-3)

        for idx,(o,h,l,c) in enumerate(candles):
            x=xp(idx)
            y_o,y_c,y_h,y_l=yp(o),yp(c),yp(h),yp(l)
            col='#26a69a' if c>=o else '#ef5350'
            draw.line([(x,y_h),(x,y_l)], fill='black', width=1)
            tb,bb=min(y_o,y_c),max(y_o,y_c)
            if abs(y_o-y_c)<2:
                draw.line([(x-cw_px//2,y_o),(x+cw_px//2,y_o)], fill=col, width=2)
            else:
                draw.rectangle([(x-cw_px//2,tb),(x+cw_px//2,bb)], fill=col, outline='black')

        ye1,ye2=yp(entry_high), yp(entry_low)
        draw.rectangle([(left,min(ye1,ye2)),(W-right,max(ye1,ye2))], fill='#e8f5e9', outline='#1b5e20')
        draw.line([(left,yp(entry_mid)),(W-right,yp(entry_mid))], fill='#1b5e20', width=4)
        draw.text((left+5, yp(entry_mid)-18), f"ENTRADA {entry_mid:.2f}", fill='#1b5e20')

        ys=yp(sl)
        for x in range(left,W-right,12):
            draw.line([(x,ys),(x+7,ys)], fill='#c62828', width=3)
        draw.text((left+5, ys-18), f"SL {sl:.2f}", fill='#c62828')

        for j,tp in enumerate(tps):
            yt=yp(tp)
            for x in range(left,W-right,10):
                draw.line([(x,yt),(x+5,yt)], fill='#2e7d32', width=1)
            draw.text((W-right-110, yt-16), f"TP{j+1} {tp:.2f}", fill='#2e7d32')

        buf=io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
        data={"chat_id": CHAT_ID, "caption": f"📊 {side} XAUUSD #{signal_id} - Grafico Pro Velas"},
        files={"photo": buf}, timeout=30)
    except Exception as e:
        print(f"chart error {e}")

def get_price():
    try:
        j=requests.get("https://api.gold-api.com/price/XAU",timeout=10).json()
        return float(j.get("price") or 4339)
    except: return 4339+random.uniform(-2,2)

def new_signal():
    global counter, last_signal_time
    if time.time()-last_signal_time < 2400: return
    price=get_price()
    is_buy=random.choice([True,True,False])
    signal_id=f"XAU_{counter:04d}"
    counter+=1
    if is_buy:
        entry_high=price
        entry_low=price-2.8
        sl=entry_low-6.5
        tps=[entry_high+4.5, entry_high+10, entry_high+18]
        side="BUY"
    else:
        entry_low=price
        entry_high=price+2.8
        sl=entry_high+6.5
        tps=[entry_low-4.5, entry_low-10, entry_low-18]
        side="SELL"

    # FORMATO EXACTO COMO TU FOTO BDM
    text = f"🟢 {side} XAUUSD · {entry_low:.2f} - {entry_high:.2f} #{signal_id}\n\nSL {sl:.2f}\nTP1 {tps[0]:.2f}\nTP2 {tps[1]:.2f}\nTP3 {tps[2]:.2f}\n\nVer gráfico"
    send_text(text)
    time.sleep(1.2)
    send_chart_bdm(entry_low, entry_high, sl, tps, side, signal_id)

    signals.append({"id":signal_id,"side":side,"entry_low":min(entry_low,entry_high),"entry_high":max(entry_low,entry_high),"sl":sl,"tps":tps,"tp_hit":[False,False,False],"active":True})
    last_signal_time=time.time()

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
def home(): return "V18 BDM LIVE",200

@app.route("/test")
def test():
    data["XAUUSD"].clear()
    base=4339
    for _ in range(150):
        base+=random.uniform(-1.2,1.2)
        data["XAUUSD"].append(base)
    new_signal()
    return "ok V18 BDM enviado",200

def loop():
    time.sleep(6)
    send_text("🚀 *BOT V18 BDM CONECTADO*\n✅ Formato igual a tu foto BTC\n✅ Seguimiento TP1/TP2/TP3 auto\n✅ Grafico velas PRO\n\nProbando /test para ver formato...")
    while True:
        try:
            data["XAUUSD"].append(get_price())
            check_tps()
            if random.random()<0.015 and time.time()-last_signal_time>3300:
                new_signal()
            time.sleep(20)
        except: time.sleep(30)

threading.Thread(target=loop, daemon=True).start()
