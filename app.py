import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import numpy as np
import os
from dotenv import load_dotenv


load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")


st.set_page_config(layout="wide", page_title="QUANT_GENESIS", page_icon="🧬")


st.markdown("""
    <style>
        .stApp { background-color: #0E1117; }
        .block-container { padding-top: 1rem; padding-bottom: 0rem; }
        
        div[data-testid="stMetric"] {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-left: 5px solid #00c853;
            padding: 10px;
            border-radius: 8px;
        }
        div[data-testid="stMetricLabel"] { color: #8b949e; font-size: 12px; }
        div[data-testid="stMetricValue"] { color: white; font-family: 'Roboto Mono', monospace; }
        
        .js-plotly-plot .plotly .main-svg {
            border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def init_connection():
    try:
        return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
    except Exception as e:
        return None

conn = init_connection()

def load_and_process():
    if conn is None: return pd.DataFrame()
    query = "SELECT trade_time, price, quantity FROM trade_data ORDER BY trade_time DESC LIMIT 3000;"
    try:
        df = pd.read_sql(query, conn)
    except:
        return pd.DataFrame()
    
    if df.empty: return df
    
    df = df.sort_values("trade_time").reset_index(drop=True)
    
    # Calculations
    df['cum_vol'] = df['quantity'].cumsum()
    df['cum_pv'] = (df['price'] * df['quantity']).cumsum()
    df['vwap'] = df['cum_pv'] / df['cum_vol']
    
    df['delta_price'] = df['price'].diff()
    df['side'] = np.where(df['delta_price'] >= 0, 1, -1)
    df['cvd'] = (df['side'] * df['quantity']).cumsum()
    
    df['std'] = df['price'].rolling(100).std()
    df['upper'] = df['vwap'] + (2 * df['std'])
    df['lower'] = df['vwap'] - (2 * df['std'])
    
    return df


st.title("Real-Time Crypto Trade Analytics")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
p1 = kpi1.empty()
p2 = kpi2.empty()
p3 = kpi3.empty()
p4 = kpi4.empty()
p5 = kpi5.empty()

main_col, side_col = st.columns([0.75, 0.25])

with main_col:
    chart_placeholder = st.empty() 

with side_col:
    st.caption("🌊 LIVE MARKET TAPE")
    tape_placeholder = st.empty() 


while True:
    try:
        df = load_and_process()
        
        if not df.empty:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # KPI UPDATES
            p1.metric("MARKET PRICE", f"${latest['price']:,.2f}", f"{latest['price'] - prev['price']:.2f}")
            p2.metric("VWAP (FAIR)", f"${latest['vwap']:,.2f}", delta_color="off")
            cvd_val = df['cvd'].iloc[-1]
            p3.metric("CVD (FLOW)", f"{cvd_val:.2f} ₿", delta_color="normal" if cvd_val > 0 else "inverse")
            p4.metric("VOLATILITY", f"{latest['std']:.2f}")
            p5.metric("TICK SPEED", f"{len(df)}")

            
            chart_df = df.set_index('trade_time').resample('1S').agg({
                'price': 'ohlc', 'vwap': 'last', 'upper': 'last', 'lower': 'last', 'cvd': 'last'
            }).dropna()
            chart_df.columns = ['open', 'high', 'low', 'close', 'vwap', 'upper', 'lower', 'cvd']
            chart_df = chart_df.tail(100)

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.05, row_heights=[0.7, 0.3],
                                subplot_titles=("Price Action & Algo Bands", "Cumulative Volume Delta"))
            
            
            fig.add_trace(go.Candlestick(
                x=chart_df.index,
                open=chart_df['open'], high=chart_df['high'],
                low=chart_df['low'], close=chart_df['close'],
                name='Price',
                increasing_line_color='#00E676', decreasing_line_color='#FF1744'
            ), row=1, col=1)
            
            
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['vwap'], mode='lines', line=dict(color='#2979FF', width=2), name='VWAP'), row=1, col=1)
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['upper'], mode='lines', line=dict(color='gray', width=1, dash='dot'), showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['lower'], mode='lines', line=dict(color='gray', width=1, dash='dot'), showlegend=False), row=1, col=1)

            
            fig.add_trace(go.Scatter(
                x=chart_df.index, y=chart_df['cvd'],
                mode='lines', name='CVD',
                line=dict(color='#FFEA00', width=1.5),
                fill='tozeroy', fillcolor='rgba(255, 234, 0, 0.1)'
            ), row=2, col=1)

            fig.update_layout(
                height=600,
                paper_bgcolor='#0E1117', plot_bgcolor='#0E1117',
                margin=dict(l=0, r=50, t=30, b=0),
                showlegend=False,
                xaxis=dict(visible=True, showgrid=False, color='#666', type='date'),
                xaxis_rangeslider_visible=False,
                yaxis=dict(showgrid=True, gridcolor='#222', side='right', tickfont=dict(color='gray')),
                yaxis2=dict(showgrid=True, gridcolor='#222', side='right', tickfont=dict(color='gray'))
            )
            chart_placeholder.plotly_chart(fig, use_container_width=True, key=f"c_{time.time()}")

            
            tape_html = "<div style='font-family: monospace; font-size: 12px;'>"
            recent = df.tail(18).iloc[::-1]
            
            for _, row in recent.iterrows():
                color = "#00E676" if row['price'] > prev['price'] else "#FF1744"
                time_str = row['trade_time'].strftime('%H:%M:%S')
                
                
                tape_html += f"<div style='display: flex; justify-content: space-between; border-bottom: 1px solid #222; padding: 4px;'><span style='color: #666;'>{time_str}</span><span style='color: {color}; font-weight: bold;'>{row['price']:.2f}</span><span style='color: #bbb;'>{row['quantity']:.4f}</span></div>"
            
            tape_html += "</div>"
            
            tape_placeholder.markdown(tape_html, unsafe_allow_html=True)

        time.sleep(0.5)

    except Exception as e:
        time.sleep(1)