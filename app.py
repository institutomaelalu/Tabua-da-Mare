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

# 2. Conexões e Configurações
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
AVAL_FILE = "avaliacoes.csv"

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

# 3. Autenticação
if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
if 'sel_mat' not in st.session_state: st.session_state.sel_mat = "SALA ROSA"
if 'sel_pad' not in st.session_state: st.session_state.sel_pad = "SALA ROSA"

if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown(f'<div class="login-card"><h2 style="text-align: center; color: {C_AZUL}; margin:0;">Bem-vindo!</h2></div>', unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("👤 Usuário").strip().upper()
            s = st.text_input("🔑 Chave", type="password")
            if st.form_submit_button("ENTRAR"):
                if u == "ADMIN" and s == "123":
                    st.session_state.update({"logado": True, "perfil": "admin", "nome_usuario": "Coordenação"})
                    st.rerun()
                else:
                    df_g = safe_read("GERAL")
                    if not df_g.empty and u in df_g["PADRINHO/MADRINHA"].astype(str).str.upper().unique() and s == "lalu2026":
                        st.session_state.update({"logado": True, "perfil": "padrinho", "nome_usuario": u})
                        st.rerun()
                    else: st.error("Acesso negado.")
    st.stop()

# --- SIDEBAR ---
if st.session_state.perfil == "admin":
    menu = st.sidebar.radio("Navegação", ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução (Padrinhos)", "🌊 Tábua da Maré - Interno"])
else:
    menu = "🌊 Evolução (Padrinhos)"

if st.sidebar.button("🚪 Sair"):
    st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
    st.rerun()

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- MATRÍCULAS ---
if menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE}'>📋 Quadro de Matrículas</h3>", unsafe_allow_html=True)
    
    # Lógica de seleção por botões coloridos
    cols = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        opacity = "1.0" if st.session_state.sel_mat == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {opacity}; }}</style>', unsafe_allow_html=True)
        if cols[i].button(sala, key=f"btn_mat_{sala}"): 
            st.session_state.sel_mat = sala
            st.rerun()
    
    # Dados da aba Geral para o filtro de turno
    df_geral = safe_read("GERAL")
    df_sala = safe_read(st.session_state.sel_mat)
    cor_h = TURMAS_CONFIG[st.session_state.sel_mat]["cor"]

    f1, f2 = st.columns(2)
    f_tn = f1.selectbox("Turno", ["Todos", "A", "B"])
    f_cm = f2.selectbox("Comunidade", ["Todas"] + sorted(list(df_geral["COMUNIDADE"].unique())))
    
    # Sincronização: Filtra os alunos da sala selecionada com base nos turnos da aba Geral
    df_f = df_sala.copy()
    if f_tn != "Todos":
        alunos_turno = df_geral[df_geral["TURNO"].astype(str).str.contains(f_tn)]["ALUNO"].unique()
        df_f = df_f[df_f["ALUNO"].isin(alunos_turno)]
    if f_cm != "Todas":
        df_f = df_f[df_f["COMUNIDADE"] == f_cm]
    
    v_cols = ["ALUNO", "TURMA", "IDADE", "COMUNIDADE"]
    # Garante que a coluna TURMA exista para exibição
    if "TURMA" not in df_f.columns: df_f["TURMA"] = st.session_state.sel_mat
    
    html = f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
    for _, r in df_f.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in v_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# --- APADRINHAMENTO ---
elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🤝 Gestão de Apadrinhamento</h3>", unsafe_allow_html=True)
    
    cols_btn = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        opacity = "1.0" if st.session_state.sel_pad == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {opacity}; }}</style>', unsafe_allow_html=True)
        if cols_btn[i].button(sala, key=f"btn_pad_{sala}"): 
            st.session_state.sel_pad = sala
            st.rerun()

    df_sala = safe_read(st.session_state.sel_pad)
    cor_h = TURMAS_CONFIG[st.session_state.sel_pad]["cor"]

    # Restauração do Filtro "Turma" e "Turno"
    f1, f2, f3 = st.columns(3)
    f_tr = f1.selectbox("Turma", ["Todas"] + list(TURMAS_CONFIG.keys()), index=0)
    f_tn = f2.selectbox("Turno ", ["Todos", "A", "B"])
    f_sp = f3.checkbox("Apenas sem padrinho")
    
    # Vínculo direto no Sheets
    sem_pad = df_sala[df_sala["PADRINHO/MADRINHA"].isin(["", "0", "nan", "NAN", None])]
    with st.expander("✨ Vincular Novo Padrinho/Madrinha", expanded=True):
        if not sem_pad.empty:
            c1, c2, c3 = st.columns([2, 2, 1])
            al_vinc = c1.selectbox("Alunos sem Padrinho", sorted(sem_pad["ALUNO"].unique()))
            pad_nome = c2.text_input("Nome do Padrinho/Madrinha").upper()
            if c3.button("Confirmar vínculo"):
                if pad_nome:
                    client = get_gspread_client()
                    sh = client.open_by_key("1MBAvQB5xGhE7OAHGWdFPvGfwqzP9SpiaIW4OEl2Mgk4")
                    aba_g = sh.worksheet("GERAL"); cell = aba_g.find(al_vinc)
                    aba_g.update_cell(cell.row, 6, pad_nome)
                    aba_s = sh.worksheet(st.session_state.sel_pad); cell_s = aba_s.find(al_vinc)
                    aba_s.update_cell(cell_s.row, 6, pad_nome)
                    st.success("Vínculo registrado!"); st.rerun()

    # Aplicação dos Filtros na Tabela de Visualização
    df_f = df_sala.copy()
    if f_tr != "Todas":
        # Se selecionar uma turma diferente da aba atual, o app avisa ou você pode mudar a aba
        if f_tr != st.session_state.sel_pad: st.info(f"Mostrando dados da {st.session_state.sel_pad}. Para ver a {f_tr}, use os botões coloridos.")
    if f_sp:
        df_f = df_f[df_f["PADRINHO/MADRINHA"].isin(["", "0", "nan", "NAN", None])]
    
    v_cols = ["ALUNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
    html = f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
    for _, r in df_f.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in v_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# --- EVOLUÇÃO (Com Saudação ao Padrinho) ---
elif menu == "🌊 Evolução (Padrinhos)":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🌊 Evolução dos Afilhados</h3>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    df_av = pd.read_csv(AVAL_FILE) if os.path.exists(AVAL_FILE) else pd.DataFrame()
    
    if st.session_state.perfil == "admin":
        lista_p = sorted([p for p in df_g["PADRINHO/MADRINHA"].unique() if str(p) not in ["", "0", "nan", "NAN", "None"]])
        padrinho_alvo = st.selectbox("🎯 Simular visão do Padrinho:", lista_p)
    else: padrinho_alvo = st.session_state.nome_usuario

    afilhas = df_g[df_g["PADRINHO/MADRINHA"].astype(str).str.upper() == padrinho_alvo.upper()]
    if not afilhas.empty:
        st.markdown(f"#### Olá, **{padrinho_alvo}**! ✨") # Saudação preservada
        al_s = st.selectbox("Afilhado:", afilhas["ALUNO"].unique())
        df_al = df_av[df_av["Aluno"] == al_s] if not df_av.empty else pd.DataFrame()
        if not df_al.empty:
            tri = st.selectbox("Trimestre", df_al["Trimestre"].unique())
            row = df_al[df_al["Trimestre"] == tri].iloc[0]
            fig = go.Figure(go.Scatter(x=CATEGORIAS, y=[float(row[c]) for c in CATEGORIAS], fill='tozeroy', line=dict(color=C_AZUL, width=4, shape='spline')))
            fig.update_layout(yaxis=dict(range=[0, 5.5], tickvals=[1,2,3,4,5]), height=400)
            st.plotly_chart(fig, use_container_width=True)
    else: st.warning("Nenhum afilhado vinculado.")

# (Lógica de Cadastro e Tábua da Maré seguem o padrão de escrita no Sheets)
