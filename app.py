import requests, pandas as pd, matplotlib.pyplot as plt, pytz, time, os, threading
from datetime import datetime
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN", "8870473192:AAElumHWfjg2paoljk1IANUvRW3dISms5eg")
CHAT_ID = os.getenv("CHAT_ID", "@-1004419307514")
EC_TZ = pytz.timezone('America/Guayaquil')

app = Flask(__name__)
@app.route('/')
def home():
    return "✅ Bot BTC 1M TradingView Live - Deivid"

def get_1m():
    url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=55"
    r = requests.get(url, timeout=10).json()
    df = pd.DataFrame(r, columns=['t','O','H','L','C','v','ct','q','n','tb','tq','i'])
    return df[['O','H','L','C']].astype(float).rename(columns={'O':'Open','H':'High','L':'Low','C':'Close'})

def grafico_TV_1m(df, entrada, sl, tp1, tp2, tp3):
    fig, ax = plt.subplots(figsize=(10,6.2), dpi=300)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax.grid(True, color='#e0e0e0', lw=0.7)
    
    for i,row in df.iterrows():
        col = '#089981' if row['Close']>=row['Open'] else '#f23645'
        ax.plot([i,i],[row['Low'],row['High']], color='#2a2e39', lw=0.8)
        bh = abs(row['Close']-row['Open'])
        if bh < 1: bh = 1
        ax.add_patch(plt.Rectangle((i-0.36, min(row['Open'],row['Close'])), 0.72, bh,
                                   facecolor=col, edgecolor='#131722', lw=0.5))
    # NIVELES COMO TU FOTO
    ax.axhline(entrada, color='#0a7a2e', lw=2.2, ls='-')
    ax.axhline(sl, color='#d50000', lw=1.8, ls='--')
    ax.axhline(tp1, color='#2e7d32', lw=1, ls=':')
    ax.axhline(tp2, color='#2e7d32', lw=1, ls='-.')
    ax.axhline(tp3, color='#2e7d32', lw=0.9, ls=':')
    
    ax.set_xlim(-1, len(df))
    ax.set_ylim(df['Low'].min()-15, df['High'].max()+15)
    ax.yaxis.tick_right()
    plt.tight_layout()
    plt.savefig('chart.png', facecolor='white', bbox_inches='tight', dpi=300)
    plt.close()

def bot_loop():
    while True:
        try:
            df = get_1m()
            entrada = df['Close'].iloc[-1]
            sl = entrada - 6
            tp1, tp2, tp3 = entrada+4, entrada+8, entrada+14
            grafico_TV_1m(df, entrada, sl, tp1, tp2, tp3)
            with open('chart.png','rb') as f:
                requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                    data={'chat_id': CHAT_ID, 'caption': f"BTCUSDT 1M | POI {entrada:.1f} | SL {sl:.1f} | {datetime.now(EC_TZ).strftime('%H:%M')} EC"},
                    files={'photo': f}, timeout=15)
            print(f"✅ Enviado 1M {datetime.now(EC_TZ)}")
        except Exception as e:
            print(f"Error: {e}")
        ahora = datetime.now(EC_TZ)
        espera = (15 - ahora.minute % 15)*60 - ahora.second + 60
        time.sleep(espera)

# Hilo del bot
threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
