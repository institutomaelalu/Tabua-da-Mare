import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuração e Estilo (ATUALIZADO PARA COLORIR CAIXAS DE SELEÇÃO)
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp {{ background-color: #ffffff; font-family: 'Inter', sans-serif; }}
    .main-header {{ text-align: center; padding: 20px 0; }}
    .main-header h1 {{ font-size: 42px !important; font-weight: 800; }}
    
    /* Tabelas */
    .custom-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        border: 1px solid #f0f0f0; border-radius: 10px;
        overflow: hidden; font-size: 13px; margin-top: 5px;
    }}
    .custom-table thead th {{ padding: 12px 10px; text-align: left; color: white !important; font-weight: 700; border: none; }}
    .custom-table tbody td {{ padding: 8px 10px; border-bottom: 1px solid #fafafa; color: #444 !important; font-weight: 500; }}
    
    /* Botões Padrão */
    div.stButton > button {{
        width: 100%; border-radius: 8px !important; font-weight: 700 !important; 
        height: 42px; font-size: 11px !important; border: none !important;
        transition: all 0.3s;
    }}

    /* --- ESTILIZAÇÃO DAS CAIXAS DE SELEÇÃO (IDENTIDADE VISUAL) --- */
    /* Aplicando cores suaves nos campos de input/select para parecerem "apagados" mas com cor */
    div[data-baseweb="select"] > div {{
        background-color: {C_AZUL}22 !important; /* Azul suave por padrão */
        border: 1px solid {C_AZUL}44 !important;
        border-radius: 8px !important;
    }}
    
    /* Alternando cores para inputs de texto e números */
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div {{
        color: #444 !important;
        font-weight: 600 !important;
    }}

    /* Colorindo especificamente os containers de widgets de forma alternada via CSS */
    div[data-testid="stVerticalBlock"] > div:nth-child(odd) div[data-baseweb="select"] > div {{
        background-color: {C_VERDE}22 !important;
        border-color: {C_VERDE}44 !important;
    }}
    
    div[data-testid="stVerticalBlock"] > div:nth-child(even) div[data-baseweb="select"] > div {{
        background-color: {C_ROSA}22 !important;
        border-color: {C_ROSA}44 !important;
    }}

    .login-card {{
        background: linear-gradient(135deg, {C_AZUL}22, {C_ROSA}22);
        padding: 30px; border-radius: 20px; border: 2px solid #f0f0f0;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. Conexões e Configurações (Mantendo a estrutura de Semestres solicitada)
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
AVAL_FILE = "avaliacoes.csv"
if not os.path.exists(AVAL_FILE):
    pd.DataFrame(columns=["Aluno", "Periodo"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)

TURMAS_CONFIG = {
    "SALA ROSA": {"cor": C_ROSA, "key": "sala_rosa"},
    "SALA AMARELA": {"cor": C_AMARELO, "key": "sala_amarela"},
    "SALA VERDE": {"cor": C_VERDE, "key": "sala_verde"},
    "SALA AZUL": {"cor": C_AZUL, "key": "sala_azul"},
    "CIRAND. MUNDO": {"cor": C_ROXO, "key": "cirand_mundo"},
}

# (Funções safe_read, get_gspread_client e lógica de login permanecem as mesmas...)
# ... [Omitido por brevidade, mantendo exatamente o que estava no código anterior] ...

# --- EXIBIÇÃO NAS ABAS (EXEMPLO DE APLICAÇÃO) ---

# Na aba Lançar Avaliação, as caixas de seleção agora aparecerão coloridas automaticamente
# conforme a lógica do CSS injetado no início do arquivo.

if menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO}'>📊 Lançar Notas</h3>", unsafe_allow_html=True)
    
    # Seleção da Sala (Botões Coloridos)
    cols_btn = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        op = "1.0" if st.session_state.sel_aval == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {op}; }}</style>', unsafe_allow_html=True)
        if cols_btn[i].button(sala, key=f"btn_aval_{sala}"): 
            st.session_state.sel_aval = sala
            st.rerun()

    # Filtros que agora estarão coloridos pelo CSS
    df_geral = safe_read("GERAL")
    df_sala = safe_read(st.session_state.sel_aval)
    f1, f2 = st.columns(2)
    with f1:
        st.selectbox("Turno", ["Todos", "A", "B"], key="aval_tn")
    with f2:
        st.selectbox("Comunidade", ["Todas"] + sorted(list(df_geral["COMUNIDADE"].unique())), key="aval_cm")

    # [Restante da lógica de formulário e salvamento...]
