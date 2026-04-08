import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Configuração e Estilo
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp {{ background-color: #ffffff; font-family: 'Inter', sans-serif; }}
    .main-header {{ text-align: center; padding-top: 25px; padding-bottom: 5px; }}
    .main-header h1 {{ margin: 0; font-size: 38px !important; font-weight: 800; line-height: 1.1; }}
    
    .custom-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        border: 1px solid #f0f0f0; border-radius: 10px;
        overflow: hidden; font-size: 13px; margin-top: 5px;
    }}
    .custom-table thead th {{ padding: 12px 10px; text-align: left; color: white !important; font-weight: 700; border: none; }}
    .custom-table tbody td {{ padding: 8px 10px; border-bottom: 1px solid #fafafa; color: #666 !important; font-weight: 500; }}
    
    /* Estilização dos Botões de Sala */
    div.stButton > button {{
        width: 100%; border-radius: 8px !important; font-weight: 700 !important; 
        height: 42px; font-size: 11px !important; border: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. Inicialização e Configuração
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE, AVAL_FILE, PADRINHOS_FILE = "alunos.csv", "avaliacoes.csv", "padrinhos_local.csv"

def init_db():
    for f, cols in {ALUNOS_FILE: ["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"], 
                    AVAL_FILE: ["Aluno", "Trimestre"] + CATEGORIAS, 
                    PADRINHOS_FILE: ["ALUNO", "PADRINHO_EDITADO"]}.items():
        if not os.path.exists(f): pd.DataFrame(columns=cols).to_csv(f, index=False)
init_db()

TURMAS_CONFIG = {
    "SALA ROSA": {"cor": C_ROSA, "key": "sala_rosa"},
    "SALA AMARELA": {"cor": C_AMARELO, "key": "sala_amarela"},
    "SALA VERDE": {"cor": C_VERDE, "key": "sala_verde"},
    "SALA AZUL": {"cor": C_AZUL, "key": "sala_azul"},
    "CIRAND. MUNDO": {"cor": C_ROXO, "key": "cirand_mundo"},
}

# 3. Funções de Suporte
def safe_read(worksheet_name):
    df = pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])
    try:
        if worksheet_name == "GERAL":
            dfs = []
            for k, conf in TURMAS_CONFIG.items():
                if conf['key'] in st.secrets["connections"]["gsheets"]:
                    url = st.secrets["connections"]["gsheets"][conf['key']]
                    url_csv = url.split("/edit")[0] + "/export?format=csv"
                    if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
                    temp = pd.read_csv(url_csv)
                    temp.columns = [str(c).strip().upper() for c in temp.columns]
                    if "PADRINHO" in temp.columns: temp = temp.rename(columns={"PADRINHO": "PADRINHO/MADRINHA"})
                    dfs.append(temp)
            df = pd.concat(dfs, ignore_index=True) if dfs else df
        else:
            conf = TURMAS_CONFIG.get(worksheet_name)
            if conf and conf['key'] in st.secrets["connections"]["gsheets"]:
                url = st.secrets["connections"]["gsheets"][conf['key']]
                url_csv = url.split("/edit")[0] + "/export?format=csv"
                if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
                df = pd.read_csv(url_csv)
                df.columns = [str(c).strip().upper() for c in df.columns]
                if "PADRINHO" in df.columns: df = df.rename(columns={"PADRINHO": "PADRINHO/MADRINHA"})
    except: pass
    
    try:
        df_l, df_p = pd.read_csv(ALUNOS_FILE), pd.read_csv(PADRINHOS_FILE)
        full = pd.concat([df, df_l], ignore_index=True) if worksheet_name == "GERAL" else df.copy()
        full["ALUNO"] = full["ALUNO"].astype(str).str.strip().str.upper()
        for _, r in df_p.iterrows():
            full.loc[full["ALUNO"] == str(r["ALUNO"]).strip().upper(), "PADRINHO/MADRINHA"] = r["PADRINHO_EDITADO"]
        return full.fillna("")
    except: return df.fillna("")

# 4. Estado da Sessão
if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
if 'sel_mat' not in st.session_state: st.session_state.sel_mat = "SALA ROSA"
if 'sel_pad' not in st.session_state: st.session_state.sel_pad = "SALA ROSA"

if not st.session_state.logado:
    st.markdown("<div class='main-header'><h1>Acesso ao Sistema</h1></div><hr>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Usuário").strip().upper()
        s = st.text_input("Chave", type="password")
        if st.form_submit_button("Entrar"):
            if u == "ADMIN" and s == "123":
                st.session_state.update({"logado": True, "perfil": "admin", "nome_usuario": "Coordenação"})
                st.rerun()
            else: st.error("Acesso negado.")
    st.stop()

# --- HEADER ---
st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

if st.session_state.perfil == "admin":
    menu = st.sidebar.radio("Navegação", ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução (Padrinhos)", "🌊 Tábua da Maré - Interno"])
else:
    menu = "🌊 Evolução (Padrinhos)"

# --- LÓGICA DE ABAS ---

if menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE}'>📋 Quadro de Matrículas</h3>", unsafe_allow_html=True)
    
    cols = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        opacity = "1.0" if st.session_state.sel_mat == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {opacity}; }}</style>', unsafe_allow_html=True)
        if cols[i].button(sala, key=f"btn_mat_{sala}"): 
            st.session_state.sel_mat = sala
            st.rerun()

    df = safe_read(st.session_state.sel_mat)
    cor_header = TURMAS_CONFIG[st.session_state.sel_mat]["cor"]
    
    c1, c2 = st.columns(2)
    f_tn = c1.selectbox("Filtrar Turno", ["Todos", "A", "B"])
    f_cm = c2.selectbox("Filtrar Comunidade", ["Todas"] + sorted(list(df["COMUNIDADE"].unique())))
    
    df_f = df.copy()
    if f_tn != "Todos": df_f = df_f[df_f["TURNO"].astype(str).str.contains(f_tn)]
    if f_cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm]
    
    v_cols = ["ALUNO", "TURMA", "IDADE", "COMUNIDADE"]
    html = f'<table class="custom-table"><thead style="background-color:{cor_header}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
    for _, r in df_f.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in v_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🤝 Gestão de Apadrinhamento</h3>", unsafe_allow_html=True)
    
    cols = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        opacity = "1.0" if st.session_state.sel_pad == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {opacity}; }}</style>', unsafe_allow_html=True)
        if cols[i].button(sala, key=f"btn_pad_{sala}"): 
            st.session_state.sel_pad = sala
            st.rerun()

    df = safe_read(st.session_state.sel_pad)
    cor_header = TURMAS_CONFIG[st.session_state.sel_pad]["cor"]
    
    c1, c2, c3 = st.columns([1, 1, 1])
    f_tn = c1.selectbox("Filtrar Turno ", ["Todos", "A", "B"])
    f_cm = c2.selectbox("Filtrar Comunidade ", ["Todas"] + sorted(list(df["COMUNIDADE"].unique())))
    f_sp = c3.checkbox("Mostrar apenas sem padrinho")
    
    df_f = df.copy()
    if f_tn != "Todos": df_f = df_f[df_f["TURNO"].astype(str).str.contains(f_tn)]
    if f_cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm]
    if f_sp: df_f = df_f[df_f["PADRINHO/MADRINHA"].isin(["", "0", "nan"])]
    
    v_cols = ["ALUNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
    html = f'<table class="custom-table"><thead style="background-color:{cor_header}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
    for _, r in df_f.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in v_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

elif menu == "🌊 Tábua da Maré - Interno":
    st.markdown(f"<h3 style='color:{C_VERDE}'>🌊 Tábua da Maré - Interno</h3>", unsafe_allow_html=True)
    # Lógica de controle interno...
