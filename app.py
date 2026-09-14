import MetaTrader5 as mt5
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import pytz

# CONFIG
SYMBOL = "XAUUSD"
ECUADOR = pytz.timezone('America/Guayaquil')

def formato_senal_precisa(tipo, entrada, sl, tp1, tp2, tp3):
    return f"""
🟢 {tipo} XAUUSD 🔥

SL: {sl:.2f}
Entrar en: {entrada:.2f}
TP1: {tp1:.2f}
TP2: {tp2:.2f}
TP3: {tp3:.2f}
"""

def detectar_smc(df):
    # CHoCH - Cambio de Caracter
    choch_bull = df['low'].iloc[-2] < df['low'].iloc[-3] and df['high'].iloc[-1] > df['high'].iloc[-2]
    # BOS - Break of Structure
    bos_bull = df['high'].iloc[-1] > df['last_swing_high']
    # STRONG LOW
    strong_low = df['low'].min()
    # ROMPIMIENTO CON VELA GRANDE 1M
    cuerpo = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
    vela_grande = cuerpo > df['atr'].iloc[-1] * 1.2
    volumen_fuerte = df['tick_volume'].iloc[-1] > df['tick_volume'].rolling(20).mean().iloc[-1] * 1.5
    rompimiento = df['close'].iloc[-1] > df['last_resistencia'] and vela_grande and volumen_fuerte
    
    return choch_bull, bos_bull, strong_low, rompimiento, vela_grande

def bot_v20():
    mt5.initialize()
    df15 = pd.DataFrame(mt5.copy_rates(SYMBOL, mt5.TIMEFRAME_M15, 0, 100))
    df1 = pd.DataFrame(mt5.copy_rates(SYMBOL, mt5.TIMEFRAME_M1, 0, 100))
    
    choch, bos, strong_low, romp, vela_grande = detectar_smc(df1)
    
    if choch and bos and romp:
        entrada = df1['close'].iloc[-1]
        sl = strong_low - 0.50
        tp1 = entrada + 2.0
        tp2 = entrada + 4.5
        tp3 = entrada + 8.0
        
        mensaje = formato_senal_precisa("Compra", entrada, sl, tp1, tp2, tp3)
        print(mensaje)
        
        # GRAFICO 15M
        plt.figure()
        plt.plot(df15['close'])
        plt.title(f"XAUUSD 15M - CHoCH+BOS+ROMP {datetime.now(ECUADOR)}")
        plt.savefig("grafico_15m.png")
        # Aquí mandas a WhatsApp/Telegram

# HORARIOS 7 SEÑALES HORA ECUADOR
horarios = ["19:00", "22:00", "03:00", "06:00", "08:30", "10:30", "13:00"]
print(f"V20 ACTIVO - {len(horarios)} señales - Hora Ecuador: {horarios}")
