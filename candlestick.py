from enum import unique
import streamlit as st
import plotly.graph_objects as go
import plotly.subplots as sp
import pandas as pd

import re
from pathlib import Path

ORDERS_RE = re.compile("orders")
CSV_NAME_RE = re.compile("([A-Z]+)_*\d+_S.csv")
DATA_DIR = Path("/Users/leggers/Documents/stonk_data")

date_folders = [x for x in DATA_DIR.iterdir() if x.is_dir()]
dates_available = list(map(lambda d: d.name, date_folders))
dates_to_tickers = {}
for date_folder in date_folders:
  csvs = filter(lambda f: CSV_NAME_RE.match(f.name), list(date_folder.glob('**/*.csv')))
  unique_tickers = set(map(lambda f: CSV_NAME_RE.search(f.name).group(1), csvs))
  dates_to_tickers[date_folder.name] = unique_tickers

data_date = st.selectbox("Data date:", dates_available)
symbol = st.selectbox("Symbol:", dates_to_tickers[data_date])

data = pd.read_csv(f"~/Documents/stonk_data/{data_date}/{symbol}_60_S.csv")
five_min_data = pd.read_csv(f"~/Documents/stonk_data/{data_date}/{symbol}_300_S.csv")

fig = sp.make_subplots(
  rows=2, cols=1,
  shared_xaxes=True,
  row_width=[0.2, 0.7]
)

fig.add_trace(go.Candlestick(
                  x=five_min_data['time'],
                  open=five_min_data['open'],
                  high=five_min_data['high'],
                  low=five_min_data['low'],
                  close=five_min_data['close'],
                  name=symbol + ' 5m',
                  increasing_line_color= 'cyan', decreasing_line_color= 'orange'),
                row=1,
                col=1)

fig.add_trace(go.Bar(x=five_min_data['time'], y=five_min_data['volume'], showlegend=False),
               row=2,
               col=1)

fig.add_trace(go.Candlestick(
                x=data['time'],
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                name=symbol + ' 1m'),
              row=1,
              col=1)

fig.add_trace(go.Bar(x=data['time'], y=data['volume'], showlegend=False),
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
    shapes = [dict(
        x0=f"{data_date}T09:29:30", x1=f"{data_date}T09:29:30", y0=0, y1=1, xref='x1', yref='paper',
        line_width=2)],
    annotations=[dict(
        x=f"{data_date}T09:29", y=0.05, xref='x1', yref='paper',
        showarrow=False, xanchor='right', text='Market Open')]
)

st.plotly_chart(fig, use_container_width=True)
