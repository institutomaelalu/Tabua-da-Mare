import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuração e Estilo (PRESERVADO)
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp {{ background-color: #ffffff; font-family: 'Inter', sans-serif; }}
    .main-header {{ text-align: center; padding: 20px 0; }}
    .main-header h1 {{ font-size: 42px !important; font-weight: 800; }}
    .custom-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        border: 1px solid #f0f0f0; border-radius: 10px;
        overflow: hidden; font-size: 13px; margin-top: 5px;
    }}
    .custom-table thead th {{ padding: 12px 10px; text-align: left; color: white !important; font-weight: 700; border: none; }}
    .custom-table tbody td {{ padding: 8px 10px; border-bottom: 1px solid #fafafa; color: #444 !important; font-weight: 500; }}
    div.stButton > button {{
        width: 100%; border-radius: 8px !important; font-weight: 700 !important; 
        height: 42px; font-size: 11px !important; border: none !important;
        transition: all 0.3s;
    }}
    .login-card {{
        background: linear-gradient(135deg, {C_AZUL}22, {C_ROSA}22);
        padding: 30px; border-radius: 20px; border: 2px solid #f0f0f0;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. Conexões
TURMAS_CONFIG = {
    "SALA ROSA": {"cor": C_ROSA, "key": "sala_rosa"},
    "SALA AMARELA": {"cor": C_AMARELO, "key": "sala_amarela"},
    "SALA VERDE": {"cor": C_VERDE, "key": "sala_verde"},
    "SALA AZUL": {"cor": C_AZUL, "key": "sala_azul"},
    "CIRAND. MUNDO": {"cor": C_ROXO, "key": "cirand_mundo"},
}

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

def safe_read(worksheet_name):
    try:
        if worksheet_name == "GERAL":
            url = st.secrets["connections"]["gsheets"]["geral"]
        else:
            url = st.secrets["connections"]["gsheets"][TURMAS_CONFIG[worksheet_name]['key']]
        url_csv = url.split("/edit")[0] + "/export?format=csv"
        if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
        df = pd.read_csv(url_csv)
        df.columns = [str(c).strip().upper() for c in df.columns]
        if "PADRINHO" in df.columns: df = df.rename(columns={"PADRINHO": "PADRINHO/MADRINHA"})
        return df.fillna("")
    except:
        return pd.DataFrame()

# 3. Estados de Sessão
if 'sel_pad' not in st.session_state: st.session_state.sel_pad = "SALA ROSA"
if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})

# --- LOGIN (Simplificado para o exemplo) ---
if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown(f'<div class="login-card"><h2 style="text-align: center; color: {C_AZUL}; margin:0;">Acesso</h2></div>', unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("👤 Usuário").strip().upper()
            s = st.text_input("🔑 Chave", type="password")
            if st.form_submit_button("ENTRAR"):
                if u == "ADMIN" and s == "123":
                    st.session_state.update({"logado": True, "perfil": "admin", "nome_usuario": "Coordenação"})
                    st.rerun()
                else: st.error("Acesso negado.")
    st.stop()

menu = st.sidebar.radio("Navegação", ["📝 Matrículas", "🤝 Apadrinhamento"])

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- ABA APADRINHAMENTO REAJUSTADA ---
if menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🤝 Gestão de Apadrinhamento</h3>", unsafe_allow_html=True)
    
    # Navegação por botões (Salas)
    cols_btn = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        opacity = "1.0" if st.session_state.sel_pad == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {opacity}; }}</style>', unsafe_allow_html=True)
        if cols_btn[i].button(sala, key=f"btn_pad_{sala}"): 
            st.session_state.sel_pad = sala
            st.rerun()

    # Base de dados
    df_geral = safe_read("GERAL")
    df_sala = safe_read(st.session_state.sel_pad)
    cor_h = TURMAS_CONFIG[st.session_state.sel_pad]["cor"]

    # FILTROS SOLICITADOS: Turno e Comunidade
    f1, f2, f3 = st.columns(3)
    f_tn = f1.selectbox("Turno", ["Todos", "A", "B"])
    f_cm = f2.selectbox("Comunidade", ["Todas"] + sorted(list(df_geral["COMUNIDADE"].unique())))
    f_sp = f3.checkbox("Apenas sem padrinho")
    
    # Lógica de Filtro cruzada com a aba Geral
    df_f = df_sala.copy()
    
    # Filtra por Turno (buscando a informação na Geral)
    if f_tn != "Todos":
        alunos_no_turno = df_geral[df_geral["TURNO"].astype(str).str.contains(f_tn)]["ALUNO"].unique()
        df_f = df_f[df_f["ALUNO"].isin(alunos_no_turno)]
    
    # Filtra por Comunidade
    if f_cm != "Todas":
        df_f = df_f[df_f["COMUNIDADE"] == f_cm]
        
    # Filtra por Padrinho Vazio
    if f_sp:
        df_f = df_f[df_f["PADRINHO/MADRINHA"].isin(["", "0", "nan", "NAN", None])]

    # --- Seção de Vínculo ---
    with st.expander("✨ Vincular Novo Padrinho/Madrinha", expanded=False):
        sem_pad = df_f[df_f["PADRINHO/MADRINHA"].isin(["", "0", "nan", "NAN", None])]
        if not sem_pad.empty:
            c1, c2, c3 = st.columns([2, 2, 1])
            al_vinc = c1.selectbox("Aluno Selecionado", sorted(sem_pad["ALUNO"].unique()))
            pad_nome = c2.text_input("Nome do Padrinho/Madrinha").upper()
            if c3.button("Confirmar vínculo"):
                if pad_nome:
                    client = get_gspread_client()
                    sh = client.open_by_key("1MBAvQB5xGhE7OAHGWdFPvGfwqzP9SpiaIW4OEl2Mgk4")
                    # Atualiza Aba GERAL
                    aba_g = sh.worksheet("GERAL"); cell = aba_g.find(al_vinc)
                    aba_g.update_cell(cell.row, 6, pad_nome)
                    # Atualiza Aba da SALA
                    aba_s = sh.worksheet(st.session_state.sel_pad); cell_s = aba_s.find(al_vinc)
                    aba_s.update_cell(cell_s.row, 6, pad_nome)
                    st.success("Vínculo registrado!"); st.rerun()
        else: st.info("Não há alunos sem padrinhos nestes filtros.")

    # Tabela de Exibição
    v_cols = ["ALUNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
    html = f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
    for _, r in df_f.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in v_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
