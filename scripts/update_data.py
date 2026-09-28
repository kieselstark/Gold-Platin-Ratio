"""Aktualisiert die Monatsdaten (MONTHLY) in index.html mit den Futures-Monatsschlusskursen.

Quelle: Yahoo Finance via yfinance (GC=F Gold, SI=F Silber, PL=F Platin, PA=F Palladium).
Nur abgeschlossene Monate. Bestehende Werte bleiben erhalten, neue werden ergänzt
bzw. überschrieben – ein Ausfall der Datenquelle kann also keine Historie löschen.
"""
import datetime as dt
import json
import pathlib
import re
import sys

import pandas as pd
import yfinance as yf

MONATE = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
          'August', 'September', 'Oktober', 'November', 'Dezember']
TICKER = {'g': 'GC=F', 's': 'SI=F', 'p': 'PL=F', 'd': 'PA=F'}
DIGITS = {'g': 2, 's': 3, 'p': 2, 'd': 2}
OPTIONAL = {'d'}  # Palladium darf in einzelnen Monaten fehlen (null)

INDEX = pathlib.Path(__file__).resolve().parents[1] / 'index.html'
html = INDEX.read_text(encoding='utf-8')

m = re.search(r'^(\s*const MONTHLY = )(\[.*\]);$', html, flags=re.M)
if not m:
    sys.exit('MONTHLY-Zeile in index.html nicht gefunden')
old = json.loads(m.group(2))
rows = {r[0]: r for r in old}

# Die letzten 24 Monate neu laden reicht; ältere Daten bleiben unverändert
start = (pd.Timestamp.today() - pd.DateOffset(months=24)).strftime('%Y-%m-01')
closes = {}
for key, ticker in TICKER.items():
    df = yf.download(ticker, start=start, interval='1mo', progress=False, auto_adjust=False)
    c = df['Close']
    if isinstance(c, pd.DataFrame):
        c = c.iloc[:, 0]
    closes[key] = c
new = pd.DataFrame(closes).dropna(subset=[k for k in TICKER if k not in OPTIONAL])
new = new[new.index < pd.Timestamp(dt.date.today().replace(day=1))]  # nur abgeschlossene Monate
if new.empty:
    sys.exit('Keine neuen Daten erhalten – index.html bleibt unverändert')

for ts, r in new.iterrows():
    ym = ts.strftime('%Y-%m')
    vals = [None if pd.isna(r[k]) else round(float(r[k]), DIGITS[k]) for k in TICKER]
    if min(v for v in vals if v is not None) <= 0:
        sys.exit(f'Unplausible Werte für {ym}: {vals}')
    rows[ym] = [ym, *vals]

merged = [rows[k] for k in sorted(rows)]
last = merged[-1][0]
y, mo = map(int, last.split('-'))
stand = f'{MONATE[mo - 1]} {y}'

html = html[:m.start(2)] + json.dumps(merged, separators=(',', ':')) + html[m.end(2):]
html = re.sub(r"(const LAST_HIST = ')[^']*(')", rf"\g<1>{stand}\g<2>", html)
html = re.sub(r'(Stand der historischen Daten: )[^.<]*(\.)', rf'\g<1>{stand}\g<2>', html)
INDEX.write_text(html, encoding='utf-8')
print(f'{len(merged) - len(old)} neue Monate, letzter Monat: {last} ({stand})')
