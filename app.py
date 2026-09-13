import os, requests, threading, time
from flask import Flask
from collections import deque
import io
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
TOKEN = os.environ.get("BOT_TOKEN") or ""
CHAT_ID = os.environ.get("CHAT_ID") or ""
data = {"XAUUSD": deque(maxlen=100)}

def send_text(t):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": t}, timeout=15)
    except: pass

def send_chart_pil(entry, sl, tp1, tp2, tp3):
    try:
        prices = list(data["XAUUSD"])
        if len(prices) < 5:
            prices = [entry-2, entry-1, entry, entry+1, entry+2]*10
        prices = prices[-40:]
        min_p = min(prices + [sl, tp1])
        max_p = max(prices + [tp3, entry])
        if max_p == min_p: max_p += 1

        W, H = 800, 400
        img = Image.new('RGB', (W, H), 'white')
        draw = ImageDraw.Draw(img)
        
        # grilla
        for i in range(0, W, 80):
            draw.line([(i,0),(i,H)], fill='#eeeeee')
        for i in range(0, H, 50):
            draw.line([(0,i),(W,i)], fill='#eeeeee')

        # curva precio negra
        points = []
        for idx, p in enumerate(prices):
            x = int(idx / len(prices) * W)
            y = int(H - (p - min_p)/(max_p-min_p) * (H-60) - 20)
            points.append((x,y))
        if len(points) > 1:
            draw.line(points, fill='black', width=2)

        def y_pos(price):
            return int(H - (price - min_p)/(max_p-min_p) * (H-60) - 20)

        # lineas PRO como tu foto original
        draw.line([(0, y_pos(entry)), (W, y_pos(entry))], fill='green', width=4)
        draw.line([(0, y_pos(sl)), (W, y_pos(sl))], fill='red', width=3)
        # TPs punteadas
        for tp in [tp1, tp2, tp3]:
            yp = y_pos(tp)
            for x in range(0, W, 15):
                draw.line([(x, yp), (x+8, yp)], fill='#2e7d32', width=2)

        # textos
        draw.text((5, y_pos(entry)-15), f"ENTRADA {entry:.2f}", fill='green')
        draw.text((5, y_pos(sl)-15), f"SL {sl:.2f}", fill='red')
        draw.text((5, 5), f"XAUUSD - COMPRAR EN LINEA VERDE - 15M->1M/3M", fill='black')

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
        data={"chat_id": CHAT_ID, "caption": f"📊 GRAFICO PRO\nEnt: {entry:.2f} SL: {sl:.2f} TP3: {tp3:.2f}"},
        files={"photo": buf}, timeout=20)
        print("Grafico PIL enviado OK")
    except Exception as e:
        send_text(f"Error grafico PIL: {e}")
        print(f"Error PIL: {e}")

def get_price():
    try:
        return float(requests.get("https://api.gold-api.com/price/XAU", timeout=10).json().get("price", 4300))
    except:
        return 4349.70

@app.route("/")
def home(): return "V14.4 PIL LIVE", 200

@app.route("/test")
def test():
    p = get_price()
    data["XAUUSD"].clear()
    for i in range(40):
        data["XAUUSD"].append(p -2 + i*0.1 + (i%3)*0.2)
    entry = p
    send_text(f"✅ TEST V14.4 PIL\nXAU: {entry:.2f}\nEnviando grafico sin matplotlib...")
    time.sleep(1)
    send_chart_pil(entry, entry-6, entry+5, entry+10, entry+18)
    return "ok grafico PIL enviado", 200

def loop():
    time.sleep(5)
    send_text("🚀 BOT V14.4 PIL CONECTADO\nGrafico PRO sin recursion")
    while True:
        try:
            data["XAUUSD"].append(get_price())
            time.sleep(120)
        except: time.sleep(60)

threading.Thread(target=loop, daemon=True).start()
