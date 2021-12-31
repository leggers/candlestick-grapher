import streamlit as st
import plotly.graph_objects as go
import plotly.subplots as sp
import pandas as pd
from datetime import timedelta
import json

import re
from pathlib import Path

################################################################################
# Date and ticker selector

ORDERS_RE = re.compile("orders")
CSV_NAME_RE = re.compile("([A-Z]+)_*\d+_S.csv")
DATA_DIR = Path("/Users/leggers/Documents/stonk_data")

date_folders = [x for x in DATA_DIR.iterdir() if x.is_dir()]
dates_available = list(map(lambda d: d.name, date_folders))
dates_available.sort()
dates_available.reverse()
dates_to_tickers = {}
for date_folder in date_folders:
  csvs = filter(lambda f: CSV_NAME_RE.match(f.name), list(date_folder.glob('**/*.csv')))
  unique_tickers = list(set(map(lambda f: CSV_NAME_RE.search(f.name).group(1), csvs)))
  unique_tickers.sort()
  dates_to_tickers[date_folder.name] = unique_tickers

data_date = st.selectbox("Data date:", dates_available)
symbol = st.selectbox("Symbol:", dates_to_tickers[data_date])

################################################################################
# Read data

one_min_data = pd.read_csv(f"~/Documents/stonk_data/{data_date}/{symbol}_60_S.csv")
one_minute = timedelta(minutes=1)
# this will cause the 5 minute bar to overlap with the _last_ one minute bar it
# contains, instead of the first, which is confusing to look at.
one_min_data['adjusted_time'] = pd.to_datetime(one_min_data['time']) + one_minute

five_min_data = pd.read_csv(f"~/Documents/stonk_data/{data_date}/{symbol}_300_S.csv")
five_and_a_half_minutes = timedelta(minutes=5, seconds=30)
# this will cause the 5 minute bar to overlap with the _last_ one minute bar it
# contains, instead of the first, which is confusing to look at.
five_min_data['adjusted_time'] = pd.to_datetime(five_min_data['time']) + five_and_a_half_minutes

tick_data_list = []
with open(f"/Users/leggers/Documents/stonk_data/{data_date}/{symbol}_ticks.json") as f:
    for line in f:
        tick_data_list.append(json.loads(line))

tick_data = pd.DataFrame(tick_data_list)
tick_data['price'] = list(map(lambda t: float(t.split(';')[0]), tick_data['tick']))
tick_data['vwap'] = list(map(lambda t: float(t.split(';')[4]), tick_data['tick']))
tick_data['time'] = pd.to_datetime(tick_data['recordedAt'])

################################################################################
# Draw plots

fig = sp.make_subplots(
  rows=2, cols=1,
  shared_xaxes=True,
  row_width=[0.2, 0.7]
)

# one minute data
fig.add_trace(go.Candlestick(
                x=one_min_data['adjusted_time'],
                open=one_min_data['open'],
                high=one_min_data['high'],
                low=one_min_data['low'],
                close=one_min_data['close'],
                name=symbol + ' 1m'),
              row=1,
              col=1)

# five minute data
fig.add_trace(go.Candlestick(
                  x=five_min_data['adjusted_time'],
                  open=five_min_data['open'],
                  high=five_min_data['high'],
                  low=five_min_data['low'],
                  close=five_min_data['close'],
                  name=symbol + ' 5m',
                  ),
                row=1,
                col=1)

# tick data
fig.add_trace(go.Scatter(
  x=tick_data['time'],
  y=tick_data['price'],
  line=go.scatter.Line(color='black', width=0.3),
  name=f"{symbol} ticks"),
  row=1,
  col=1)

# VWAP
fig.add_trace(go.Scatter(
  x=tick_data['time'],
  y=tick_data['vwap'],
  line=go.scatter.Line(color='orange', width=0.3),
  name=f"{symbol} reported VWAP"),
  row=1,
  col=1)

# Candle-computed VWAP
fig.add_trace(go.Scatter(
  x=one_min_data['adjusted_time'],
  y=one_min_data['vwap'],
  line=go.scatter.Line(color='green', width=0.3),
  name=f"{symbol} computed VWAP"),
  row=1,
  col=1)

# One minute volume
fig.add_trace(go.Bar(
    x=one_min_data['adjusted_time'],
    y=one_min_data['volume'],
    showlegend=False,
    name = f"{symbol} ticks"),
  row=2,
  col=1)

fig.update_layout(
    title=f"{symbol} Price and Volume on {data_date}",
    yaxis_title="Price ($)",
    font=dict(
        family="Courier New, monospace",
        size=12,
        color="black"
    ),
    xaxis_rangeslider_visible=False,
    xaxis_showspikes=True,
    shapes = [dict(
        x0=f"{data_date}T09:29:30", x1=f"{data_date}T09:29:30", y0=0, y1=1, xref='x1', yref='paper',
        line_width=2)],
    annotations=[dict(
        x=f"{data_date}T09:29", y=0.05, xref='x1', yref='paper',
        showarrow=False, xanchor='right', text='Market Open')]
)

st.plotly_chart(fig, use_container_width=True)
