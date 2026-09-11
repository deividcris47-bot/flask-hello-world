import os, io, requests
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def crear_imagen_vip_modelo(df, entry, sl, tp1, tp2, tp3):
    # CONFIGURACIÓN DE COLORES QUE PEDISTE
    # Verde = Entrada, Roja = SL, Azul = TPs
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#121212')
    ax.set_facecolor('#121212')

    # --- VELAS REALES ---
    # df debe tener: open, high, low, close
    for i in range(len(df)):
        c = df['close'].iloc[i]
        o = df['open'].iloc[i]
        h = df['high'].iloc[i]
        l = df['low'].iloc[i]
        color = '#00e676' if c >= o else '#ff1744' # Verde y rojo trading
        ax.plot([i, i], [l, h], color=color, lw=1)
        ax.plot([i, i], [o, c], color=color, lw=4, solid_capstyle='round')

    # --- LINEAS ---
    ax.axhline(entry, color='#00e676', ls='--', lw=1.5) # VERDE ENTRADA
    ax.axhline(sl, color='#ff1744', ls='--', lw=1.2) # ROJA SL
    ax.axhline(tp1, color='#29b6f6', ls=':', lw=1.2) # AZUL TP1
    ax.axhline(tp2, color='#29b6f6', ls=':', lw=1.2) # AZUL TP2
    ax.axhline(tp3, color='#29b6f6', ls=':', lw=1.2) # AZUL TP3

    # Etiquetas tipo TradingView
    ax.text(len(df)*1.01, entry, f' Entry : {entry} ', backgroundcolor='#00e676', color='black', fontsize=9, fontweight='bold', va='center')
    ax.text(len(df)*1.01, sl, f' Stop loss : {sl} ', backgroundcolor='#424242', color='white', fontsize=9, va='center')
    ax.text(len(df)*1.01, tp1, f' TP 1 : {tp1} ', backgroundcolor='#0288d1', color='white', fontsize=9, va='center')
    ax.text(len(df)*1.01, tp2, f' TP 2 : {tp2} ', backgroundcolor='#0288d1', color='white', fontsize=9, va='center')
    ax.text(len(df)*1.01, tp3, f' TP 3 : {tp3} ', backgroundcolor='#0288d1', color='white', fontsize=9, va='center')

    plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=250, bbox_inches='tight', facecolor='#121212')
    plt.close()
    buf.seek(0)
    return buf

def enviar_telegram(imagen_buf, entry, sl, tp1, tp2, tp3):
    # Texto tipo que te gustó
    caption = f"""🔴 SELL XAUUSD · {entry} - {entry+5}
#XAU_{entry}

SL {sl}
TP1 {tp1}
TP2 {tp2}
TP3 {tp3}

Ver gráfico"""

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('signal.png', imagen_buf, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'HTML'}
    requests.post(url, files=files, data=data)

# EJEMPLO DE USO - aquí tu bot pone su lógica verde/roja
# df = tu dataframe de XAUUSD 1m
# entry = tu línea verde 4515.0
# sl = tu línea roja 4527.0
# tp1, tp2, tp3 = tus takes calculados
# img = crear_imagen_vip_modelo(df, entry, sl, tp1, tp2, tp3)
# enviar_telegram(img, entry, sl, tp1, tp2, tp3)
