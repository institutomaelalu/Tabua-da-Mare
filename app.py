import streamlit as st

import pandas as pd

import plotly.graph_objects as go

import numpy as np

import os



# 1. Configuração e Estilo

st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")



C_ROSA, C_VERDE, C_AZUL, C_AMARELO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713"



st.markdown(f"""

    <style>

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    .stApp {{ background-color: #ffffff; font-family: 'Inter', sans-serif; }}

    .main-header {{ text-align: center; padding-top: 25px; padding-bottom: 5px; }}

    .main-header h1 {{ margin: 0; font-size: 38px !important; font-weight: 800; line-height: 1.1; }}



    /* Espaçamentos equilibrados e scannability */

    .block-container {{ padding-top: 1rem !important; padding-bottom: 1rem !important; }}

    [data-testid="stVerticalBlock"] > div {{ padding-bottom: 0.4rem !important; }}

    .stSelectbox, .stCheckbox, .stSlider {{ margin-bottom: 8px !important; }}

    [data-testid="stHorizontalBlock"] {{ gap: 0.8rem !important; margin-bottom: 5px !important; }}

    hr {{ margin: 0.5rem 0 !important; }}



    .custom-table {{

        width: 100%; border-collapse: separate; border-spacing: 0;

        border: 1px solid #f0f0f0; border-radius: 10px;

        overflow: hidden; font-size: 13px; margin-top: 5px;

    }}

    .custom-table thead th {{ background-color: #ffffff; padding: 10px; text-align: left; border-bottom: 2px solid #f8f8f8; }}

    .th-rosa {{ color: {C_ROSA} !important; font-weight: 700; }}

    .th-verde {{ color: {C_VERDE} !important; font-weight: 700; }}

    .th-azul {{ color: {C_AZUL} !important; font-weight: 700; }}

    .th-amarelo {{ color: {C_AMARELO} !important; font-weight: 700; }}

    .custom-table tbody td {{ padding: 8px 10px; border-bottom: 1px solid #fafafa; color: #666 !important; font-weight: 500; }}

    

    div.stButton > button {{

        width: 100%; border-radius: 8px !important; border: 1px solid #eee !important;

        font-weight: 600 !important; height: 38px; font-size: 12px !important;

    }}

    </style>

    """, unsafe_allow_html=True)



# 2. Inicialização de Arquivos Locais

CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]

ALUNOS_FILE, AVAL_FILE, PADRINHOS_FILE = "alunos.csv", "avaliacoes.csv", "padrinhos_local.csv"



def init_db():

    for f, cols in {ALUNOS_FILE: ["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"], 

                    AVAL_FILE: ["Aluno", "Trimestre"] + CATEGORIAS, 

                    PADRINHOS_FILE: ["ALUNO", "PADRINHO_EDITADO"]}.items():

        if not os.path.exists(f): pd.DataFrame(columns=cols).to_csv(f, index=False)

init_db()



TURMAS_CONFIG = {

    "SALA ROSA": {"cor": C_ROSA, "key": "sala_rosa", "txt": "#ffffff"},

    "SALA AMARELA": {"cor": C_AMARELO, "key": "sala_amarela", "txt": "#000000"},

    "SALA VERDE": {"cor": C_VERDE, "key": "sala_verde", "txt": "#ffffff"},

    "SALA AZUL": {"cor": C_AZUL, "key": "sala_azul", "txt": "#ffffff"},

    "CIRAND. MUNDO": {"cor": "#6741d9", "key": "cirand_mundo", "txt": "#ffffff"},

}



# 3. Funções de Leitura

def safe_read(worksheet_name):

    df = pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])

    try:

        sheet_key = "geral" if worksheet_name == "GERAL" else TURMAS_CONFIG.get(worksheet_name, {}).get("key")

        if sheet_key in st.secrets["connections"]["gsheets"]:

            url = st.secrets["connections"]["gsheets"][sheet_key]

            url_csv = url.split("/edit")[0] + "/export?format=csv"

            if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"

            df_sheet = pd.read_csv(url_csv)

            df_sheet.columns = [str(c).strip().upper() for c in df_sheet.columns]

            # Mapeamento dinâmico para garantir que "Padrinho/Madrinha" seja encontrado

            if "PADRINHO/MADRINHA" in df_sheet.columns:

                df = df_sheet

            elif "PADRINHO" in df_sheet.columns:

                df_sheet = df_sheet.rename(columns={"PADRINHO": "PADRINHO/MADRINHA"})

                df = df_sheet

    except: pass

    

    try:

        df_l, df_p = pd.read_csv(ALUNOS_FILE), pd.read_csv(PADRINHOS_FILE)

        if worksheet_name == "GERAL": full = pd.concat([df, df_l], ignore_index=True)

        else:

            sala_f = worksheet_name.replace("SALA ", "")

            full = pd.concat([df, df_l[df_l["TURMA"].astype(str).str.contains(sala_f, na=False, case=False)]], ignore_index=True)

        

        full["ALUNO"] = full["ALUNO"].astype(str).str.strip().str.upper()

        # Sobrescreve com edições locais se existirem

        for _, r in df_p.iterrows():

            full.loc[full["ALUNO"] == str(r["ALUNO"]).strip().upper(), "PADRINHO/MADRINHA"] = r["PADRINHO_EDITADO"]

        return full.fillna("")

    except: return df.fillna("")



# 4. SISTEMA DE LOGIN INTEGRADO AO GSHEETS

if "logado" not in st.session_state:

    st.session_state.logado = False

    st.session_state.perfil = None

    st.session_state.nome_usuario = ""



if not st.session_state.logado:

    st.markdown("<div class='main-header'><h1>Acesso ao Sistema</h1></div><hr>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:

        with st.form("login_form"):

            user_input = st.text_input("Seu nome (como está na planilha)").strip().upper()

            senha_input = st.text_input("Chave de Acesso", type="password")

            

            if st.form_submit_button("Entrar"):

                # Lógica ADMIN estática

                if user_input == "ADMIN" and senha_input == "123":

                    st.session_state.logado = True

                    st.session_state.perfil = "admin"

                    st.session_state.nome_usuario = "Coordenação"

                    st.rerun()

                

                # Lógica PADRINHO dinâmica: busca em todas as abas

                else:

                    df_geral = safe_read("GERAL")

                    padrinhos_validos = df_geral["PADRINHO/MADRINHA"].astype(str).str.strip().str.upper().unique()

                    

                    if user_input in padrinhos_validos and senha_input == "lalu2026": # Chave temporária para todos os padrinhos

                        st.session_state.logado = True

                        st.session_state.perfil = "padrinho"

                        st.session_state.nome_usuario = user_input

                        st.rerun()

                    else:

                        st.error("Nome não localizado ou chave incorreta.")

    st.stop()



# --- CONTEÚDO PÓS-LOGIN ---

st.markdown(f"""

    <div class="main-header">

        <h1><span style='color: {C_VERDE};'>Instituto</span> <span style='color: {C_AZUL};'>Mãe</span> <span style='color: {C_VERDE};'>Lalu</span></h1>

    </div>

    <hr style="border: 0; height: 2px; background-image: linear-gradient(to right, {C_ROSA}, {C_VERDE}, {C_AZUL}, {C_AMARELO});">

    """, unsafe_allow_html=True)



# Sidebar

st.sidebar.write(f"👤 **{st.session_state.nome_usuario}**")

if st.sidebar.button("Sair"):

    st.session_state.logado = False

    st.rerun()



# 5. Navegação e Regras de Visibilidade

def set_mat(t): st.session_state.f_mat = t

def set_pad(t): st.session_state.f_pad = t



if 'f_mat' not in st.session_state: st.session_state.f_mat = "Todas"

if 'f_pad' not in st.session_state: st.session_state.f_pad = "SALA ROSA"



if st.session_state.perfil == "admin":

    menu = st.sidebar.radio("Navegação", ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução Individual"])

else:

    menu = "🌊 Evolução Individual" # Padrinho entra direto aqui



# --- ABAS ESPECÍFICAS (Somente Admin vê as primeiras 4) ---



if menu == "📝 Matrículas":

    st.markdown(f"<h3 style='color:{C_VERDE}; margin-bottom:5px;'>📋 Quadro de Matrículas</h3>", unsafe_allow_html=True)

    cols_t = st.columns(6)

    cols_t[0].button("Todas", on_click=set_mat, args=("Todas",))

    st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child(1) button {{ background-color: {'#333' if st.session_state.f_mat == 'Todas' else '#eee'} !important; color: white !important; }}</style>", unsafe_allow_html=True)

    for i, (sala, conf) in enumerate(TURMAS_CONFIG.items(), 2):

        cols_t[i-1].button(sala, key=f"m_{sala}", on_click=set_mat, args=(sala,))

        is_sel = st.session_state.f_mat == sala

        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({i}) button {{ background-color: {conf['cor'] if is_sel else '#eee'} !important; color: {conf['txt'] if is_sel else '#888'} !important; border:none; }}</style>", unsafe_allow_html=True)

    

    df = safe_read(st.session_state.f_mat if st.session_state.f_mat != "Todas" else "GERAL")

    f1, f2 = st.columns(2)

    with f1: f_tn = st.selectbox("Turno (A/B)", ["Todos", "A", "B"])

    with f2: f_cm = st.selectbox("Comunidade", ["Todas"] + sorted([str(x) for x in df["COMUNIDADE"].unique() if x]))

    

    df_f = df.copy()

    if f_tn != "Todos": df_f = df_f[df_f["TURNO"].astype(str).str.strip().str.upper() == f_tn]

    if f_cm != "Todas": df_f = df_f[df_f["COMUNIDADE"]
