import yfinance as yf
import pandas as pd
import requests
import os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# Base original combinada con los nuevos tickers de la watchlist algorítmica transnacional
TICKERS = [
    # --- TICKERS ORIGINALES ---
    "ONDS", "HUMA", "IREN", "RCAT", "QUBT", "UMAC", "ENVX", "SLDP", "SIDU", "RXRX", 
    "RGTI", "LWLG", "SKYT", "AEHR", "SOUN", "RKLB", "IONQ", "AMPX", "ASTS", "EVER", 
    "MELI", "TMDX", "SMR", "OKLO", "PL", "SOFI", "HIMS", "SYM", "RDW", "NU", "CRSP", 
    "QS", "ACHR", "PATH", "NBIS", "UPST", "MARA", "TEM", "PANW", "TTD", "DLO", "OSCR", 
    "ALAB", "BLDP", "NIO", "CIFR", "MU", "RBRK", "AMD", "CROX", "CPRX", "VAL", "LC", 
    "RIOT", "ABCL", "ABAT", "CLOV", "BABA", "SATL", "RANI", "NVO", "MRNA", "XPEV", 
    "KRKNF", "PNG", "PLMR", "LMND", "CRDO", "AXTI", "HOOD", "ZETA", "META", "FLNC", 
    "EOSE", "BE", "TSM", "ASML", "QBTS", "MSFT", "AAPL", "NVDA", "GOOGL", "AMZN", 
    "AVGO", "TSLA", "COST", "NFLX", "PEP", "AZN", "TMUS", "CSCO", "QCOM", "INTU", 
    "ADBE", "AMAT", "ASML.AS", "MC.PA", "SAP.DE", "AZN.L", "NOVN.SW", "SHEL.L", 
    "ROG.SW", "OR.PA", "RMS.PA", "SIE.DE", "TTE.PA", "ITX.MC", "HSBA.L", "ULVR.L", 
    "DTE.DE", "SAN.PA", "SU.PA", "ALV.DE", "AIR.PA", "RACE.MI", "AXSM", "TVTX", 
    "BBAI", "AMLX", "NUVL", "ACMR", "XENE", "AAOI", "OPEN", "UBER", "RDDT", "ORCL", 
    "VKTX", "AVAV", "PLTR", "SMCI", "ENPH", "RCKT", "DNLI", "MNMD", "LLY", "WULF", 
    "CRWD", "NET", "IOT", "APP", "ELF", "DDOG", "ZS", "NTSK", "NOW", "S", "ASUR", 
    "PAYC", "CDLX", "MTSI", "POET", "LASR", "IT", "EPAM", "DOCU", "WDAY", "HRI", 
    "MIDD", "BWMX", "BLD", "AEO", "FBIN", "FMC", "AOS", "ARE",
    
    # --- NUEVOS TICKERS: SAAS E IA ---
    "SNOW", "MNDY", "TWLO", "SHOP", "SAP", 
    
    # --- NUEVOS TICKERS: SEMICONDUCTORES JAPÓN (.T) Y EUROPA ---
    "285A.T", "8035.T", "6857.T", "6146.T", "6723.T", "6920.T", "7735.T", "6525.T",
    "ASM.AS", "BESI.AS", "STMPA.PA",
    
    # --- NUEVOS TICKERS: BIOTECNOLOGÍA Y MEDTECH ---
    "BEAM", "INTLA", "NTLA", "CLLS", "ADPT", "VRTX", "SANA", "CRBU",
    "LONN.SW", "BANB.SW", "NOVO-B.CO", "ARGX.BR", "PME.AX", "ARX.AX",
    
    # --- NUEVOS TICKERS: DEEP TECH (CUÁNTICA Y AEROESPACIAL) ---
    "AXE.AX", "TDG", "KTOS", 
    
    # --- NUEVOS TICKERS: APAC, AUSTRALIA Y ADRS ---
    "XRO.AX", "TNE.AX", "WTC.AX", "TCEHY", "JD"
]

# Eliminar duplicados manteniendo el orden
TICKERS = list(dict.fromkeys(TICKERS))

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

def get_data(ticker):
    df = yf.download(ticker, period="1y", interval="1d", progress=False)
    if df is None or len(df) < 210:
        return None
    return df

def check_swing_v4(ticker, df):
    try:
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
            return {"ticker": ticker, "precio": round(c, 2), "rsi": round(rsi_v, 1), "vol_rel": round(vr, 2), "stop": round(stop, 2), "tp": round(c + (c - stop) * 2, 2), "sistema": "SwingV4 - Rombo Verde"}
        return None
    except Exception as e:
        print(f"[SwingV4] Error en {ticker}: {e}")
        return None

def check_elliott_v15(ticker, df):
    try:
        close = df["Close"].squeeze()
        high = df["High"].squeeze()
        low = df["Low"].squeeze()
        volume = df["Volume"].squeeze()
        hl2 = (high + low) / 2
        sma50  = close.rolling(50).mean()
        sma150 = close.rolling(150).mean()
        ao = hl2.rolling(5).mean() - hl2.rolling(34).mean()
        vol_rel = volume / volume.rolling(50).mean()
        prev_close = close.shift(1)
        tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        maximo20d = high.shift(1).rolling(20).max()
        
        c = float(close.iloc[-1])
        c1 = float(close.iloc[-2])
        s50 = float(sma50.iloc[-1])
        s150 = float(sma150.iloc[-1])
        ao_v = float(ao.iloc[-1])
        ao_v1 = float(ao.iloc[-2])
        vr = float(vol_rel.iloc[-1])
        atr_v = float(atr.iloc[-1])
        max20 = float(maximo20d.iloc[-1])
        max20_1 = float(maximo20d.iloc[-2])
        
        tendencia = c > s50 and s50 > s150
        ruptura = (c > max20 and c1 <= max20_1)
        elliott_momentum = ao_v > 0 and ao_v > ao_v1
        senal_compra = tendencia and ruptura and elliott_momentum and vr > 1.0
        
        if senal_compra:
            stop = c - (atr_v * 2.5)
            return {"ticker": ticker, "precio": round(c, 2), "ao": round(ao_v, 4), "vol_rel": round(vr, 2), "stop": round(stop, 2), "tp": round(c + (c - stop) * 2, 2), "sistema": "EWE V15 - Onda 3"}
        return None
    except Exception as e:
        print(f"[EWE V15] Error en {ticker}: {e}")
        return None

seen_swing = set()
seen_elliott = set()
signals_swing = []
signals_elliott = []

for t in TICKERS:
    df = get_data(t)
    if df is None:
        continue
    
    r1 = check_swing_v4(t, df)
    if r1 and r1["ticker"] not in seen_swing:
        seen_swing.add(r1["ticker"])
        signals_swing.append(r1)
        
    r2 = check_elliott_v15(t, df)
    if r2 and r2["ticker"] not in seen_elliott:
        seen_elliott.add(r2["ticker"])
        signals_elliott.append(r2)

total = len(signals_swing) + len(signals_elliott)

if total > 0:
    for s in signals_swing:
        send_telegram(f"<b>COMPRA - Rombo Verde [SwingV4]</b>\n---\nTicker: <b>{s['ticker']}</b>\nPrecio: ${s['precio']}\nRSI: {s['rsi']}\nVol Relativo: {s['vol_rel']}x\nStop: ${s['stop']}\nTP (2R): ${s['tp']}\n---\nConfirmar en chart antes de entrar")
    for s in signals_elliott:
        send_telegram(f"<b>COMPRA - Onda 3 [EWE V15]</b>\n---\nTicker: <b>{s['ticker']}</b>\nPrecio: ${s['precio']}\nAO: {s['ao']}\nVol Relativo: {s['vol_rel']}x\nStop: ${s['stop']}\nTP (2R): ${s['tp']}\n---\nConfirmar en chart antes de entrar")
else:
    send_telegram("<b>Swing Trade Pro V4 + EWE V15</b>\nScan completado - Sin señales activas hoy.")
