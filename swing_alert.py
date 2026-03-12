import yfinance as yf
import pandas as pd
import requests
import os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

TICKERS = ["ONDS", "HUMA", "IREN", "RCAT", "QUBT", "UMAC", "ENVX", "SLDP", "SIDU", "RXRX", "RGTI", "LWLG", "SKYT", "AEHR", "SOUN", "RKLB", "IONQ", "AMPX", "ASTS", "EVER", "MELI", "TMDX", "SMR", "OKLO", "PL", "SOFI", "HIMS", "SYM", "RDW", "NU", "CRSP", "QS", "ACHR", "PATH", "NBIS", "UPST", "MARA", "TEM", "PANW", "TTD", "DLO", "OSCR", "ALAB", "BLDP", "NIO", "CIFR", "MU", "RBRK", "AMD", "CROX", "CPRX", "VAL", "LC", "RIOT", "ABCL", "ABAT", "CLOV", "BABA", "SATL", "RANI"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

def check_signal(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df is None or len(df) < 210:
            return None
        close = df["Close"].squeeze()
        high = df["High"].squeeze()
        volume = df["Volume"].squeeze()
        sma50  = close.rolling(50).mean()
        sma150 = close.rolling(150).mean()
        sma200 = close.rolling(200).mean()
        maximo20d = high.shift(1).rolling(20).max()
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain / loss))
        vol_rel = volume / volume.rolling(50).mean()
        prev_close = close.shift(1)
        tr = pd.concat([high - df["Low"].squeeze(), (high - prev_close).abs(), (df["Low"].squeeze() - prev_close).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        c, s50, s150, s200 = float(close.iloc[-1]), float(sma50.iloc[-1]), float(sma150.iloc[-1]), float(sma200.iloc[-1])
        c1, s50_1 = float(close.iloc[-2]), float(sma50.iloc[-2])
        max20, rsi_v, vr, atr_v = float(maximo20d.iloc[-1]), float(rsi.iloc[-1]), float(vol_rel.iloc[-1]), float(atr.iloc[-1])
        tendencia = c > s150 and s150 > s200 and s50 > s150
        senal_compra = (c > s50 and c1 <= s50_1 or c > max20) and tendencia and vr > 1.2
        if senal_compra:
            stop = c - (atr_v * 1.5)
            return {"ticker": ticker, "precio": round(c, 2), "rsi": round(rsi_v, 1), "vol_rel": round(vr, 2), "stop": round(stop, 2), "tp": round(c + (c - stop) * 2, 2)}
        return None
    except Exception as e:
        print(f"Error en {ticker}: {e}")
        return None

señales = [r for r in [check_signal(t) for t in TICKERS] if r]

if señales:
    for s in señ
