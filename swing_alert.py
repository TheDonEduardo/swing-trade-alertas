import yfinance as yf
import pandas as pd
import requests
import os

# ==========================================
# CONFIGURACIÓN
# ==========================================
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

TICKERS = ["RCAT", "ONDS", "QUBT", "UMAC", "HUMA", "IREN"]

# ==========================================
# FUNCIÓN: ENVIAR MENSAJE TELEGRAM
# ==========================================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

# ==========================================
# FUNCIÓN: CALCULAR SEÑAL SWING TRADE PRO V4
# ==========================================
def check_signal(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df is None or len(df) < 210:
            return None

        close = df["Close"].squeeze()
        high = df["High"].squeeze()
        volume = df["Volume"].squeeze()

        # Medias móviles
        sma50  = close.rolling(50).mean()
        sma150 = close.rolling(150).mean()
        sma200 = close.rolling(200).mean()

        # Techo 20 días (máximo de los 20 días anteriores)
        maximo20d = high.shift(1).rolling(20).max()

        # RSI 14
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Volumen relativo
        vol_media = volume.rolling(50).mean()
        vol_rel = volume / vol_media

        # ATR 14
        prev_close = close.shift(1)
        tr = pd.concat([
            high - df["Low"].squeeze(),
            (high - prev_close).abs(),
            (df["Low"].squeeze() - prev_close).abs()
        ], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()

        # Última vela
        i = -1
        c       = float(close.iloc[i])
        s50     = float(sma50.iloc[i])
        s150    = float(sma150.iloc[i])
        s200    = float(sma200.iloc[i])
        s50_1   = float(sma50.iloc[i-1])
        c1      = float(close.iloc[i-1])
        max20   = float(maximo20d.iloc[i])
        rsi_v   = float(rsi.iloc[i])
        vr      = float(vol_rel.iloc[i])
        atr_v   = float(atr.iloc[i])

        # Condiciones
        tendencia     = c > s150 and s150 > s200 and s50 > s150
        cruce_sma50   = c > s50 and c1 <= s50_1
        ruptura_20d   = c > max20
        compra_fuerza = cruce_sma50 or ruptura_20d
        senal_compra  = compra_fuerza and tendencia and vr > 1.2

        # Stop y TP
        stop = c - (atr_v * 1.5)
        tp   = c + ((c - stop) * 2)

        if senal_compra:
            return {
                "ticker": ticker,
                "precio": round(c, 2),
                "rsi": round(rsi_v, 1),
                "vol_rel": round(vr, 2),
                "stop": round(stop, 2),
                "tp": round(tp, 2),
                "tipo": "🟢 COMPRA — Rombo Verde"
            }

        return None

    except Exception as e:
        print(f"Error en {ticker}: {e}")
        return None

# ==========================================
# MAIN
# ==========================================
señales = []

for ticker in TICKERS:
    resultado = check_signal(ticker)
    if resultado:
        señales.append(resultado)

if señales:
    for s in señales:
        msg = (
            f"<b>{s['tipo']}</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📌 Ticker: <b>{s['ticker']}</b>\n"
            f"💰 Precio: ${s['precio']}\n"
            f"📊 RSI: {s['rsi']}\n"
            f"📦 Vol Relativo: {s['vol_rel']}x\n"
            f"🛑 Stop: ${s['stop']}\n"
            f"🎯 TP (2R): ${s['tp']}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚠️ Confirmar en chart antes de entrar"
        )
        send_telegram(msg)
else:
    send_telegram("✅ <b>Swing Trade Pro V4</b>\nScan completado — Sin señales activas hoy.")
