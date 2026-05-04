import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="MS Analyzer", layout="wide")
st.title("📊 Market Structure HLHL Analyzer")
st.markdown("**Entry Beli & Exit Jual Optimal berdasarkan Higher High - Higher Low**")

# ================== SIDEBAR ==================
st.sidebar.header("⚙️ Pengaturan")

ticker_input = st.sidebar.text_input("Kode Emiten (contoh: BBCA.JK)", value="BBCA.JK").upper().strip()

st.sidebar.subheader("📌 Watchlist Populer")
watchlist = ["BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "GOTO.JK", "ASII.JK", 
             "ADRO.JK", "UNVR.JK", "PTBA.JK", "BBNI.JK"]
selected = st.sidebar.selectbox("Pilih dari Watchlist", ["--- Pilih ---"] + watchlist)

if selected != "--- Pilih ---":
    ticker_input = selected

periode = st.sidebar.selectbox("Periode Data", ["1y", "2y", "3y", "5y"], index=1)
swing_order = st.sidebar.slider("Swing Sensitivity", 4, 12, 6)

analisis = st.sidebar.button("🔍 ANALISIS SEKARANG", type="primary", use_container_width=True)

# ================== FUNGSI ==================
@st.cache_data(ttl=3600)
def ambil_data(ticker, period):
    if not ticker.endswith(".JK"):
        ticker += ".JK"
    return yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)

def hitung_structure(df, order=6):
    df = df.copy()
    
    # Deteksi Swing
    df['is_SH'] = df['High'] == df['High'].rolling(order*2+1, center=True).max()
    df['is_SL'] = df['Low']  == df['Low'].rolling(order*2+1, center=True).min()
    
    df['Last_SH'] = df['High'].where(df['is_SH']).ffill()
    df['Last_SL'] = df['Low'].where(df['is_SL']).ffill()
    
    df['Bull_BOS'] = (df['Close'] > df['Last_SH'].shift(1)) & df['is_SH']
    df['CHoCH_Bearish'] = (df['Close'] < df['Last_SL'].shift(1)) & df['is_SL']
    
    return df

# ================== MAIN ==================
if analisis and ticker_input:
    try:
        with st.spinner(f"Mengambil data {ticker_input}..."):
            df_raw = ambil_data(ticker_input, periode)
            df = hitung_structure(df_raw, swing_order)
            latest = df.iloc[-1]
            
            # Info Utama
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Harga Saat Ini", f"Rp {latest['Close']:,.0f}")
            with col2:
                # Perbaikan error alignment
                prev_last_sh = df['Last_SH'].iloc[-2] if len(df) > 1 else latest['Last_SH']
                trend = "🟢 BULLISH" if latest['Last_SH'] >= prev_last_sh else "🔴 BEARISH"
                st.metric("Struktur Saat Ini", trend)
            with col3:
                st.metric("Last Higher Low", f"Rp {latest['Last_SL']:,.0f}")
            with col4:
                st.metric("Last Higher High", f"Rp {latest['Last_SH']:,.0f}")
            
            # SINYAL ENTRY & EXIT
            st.subheader("🎯 SINYAL ENTRY & EXIT")
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("**🟢 ENTRY BELI**")
                if trend == "🟢 BULLISH":
                    if latest['Close'] <= latest['Last_SL'] * 1.04:
                        st.success("✅ **ENTRY BAGUS SEKARANG**\nHarga dekat Higher Low")
                    else:
                        st.info("🟡 Tunggu pullback ke Higher Low")
                else:
                    st.warning("❌ Hindari entry (Struktur Bearish)")
            
            with col_b:
                st.markdown("**🔴 EXIT / JUAL**")
                if latest['CHoCH_Bearish']:
                    st.error("🚨 **JUAL / KELUAR SEKARANG**\nCHoCH Bearish!")
                else:
                    st.success("✅ Hold selama struktur Bullish")
            
            # Chart
            st.subheader(f"📈 Chart Market Structure - {ticker_input}")
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                         low=df['Low'], close=df['Close'], name="Price"))
            
            fig.add_trace(go.Scatter(x=df[df['is_SH']].index, y=df[df['is_SH']]['High'],
                                     mode='markers', marker=dict(color='red', size=11, symbol='triangle-down'), name='Swing High'))
            fig.add_trace(go.Scatter(x=df[df['is_SL']].index, y=df[df['is_SL']]['Low'],
                                     mode='markers', marker=dict(color='lime', size=11, symbol='triangle-up'), name='Swing Low'))
            
            fig.update_layout(height=700, template="plotly_dark", 
                              title=f"{ticker_input} - Market Structure ({periode})")
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabel
            st.subheader("📋 Data 10 Hari Terakhir")
            st.dataframe(df[['Close', 'Last_SH', 'Last_SL', 'Bull_BOS', 'CHoCH_Bearish']].tail(10), 
                        use_container_width=True)
            
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

st.caption("Data dari Yahoo Finance • Market Structure adalah alat bantu • Gunakan dengan manajemen risiko")
