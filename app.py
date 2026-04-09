import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuração e Estilo
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

    /* Identidade Visual nas Caixas de Seleção (Efeito Apagado) */
    div[data-baseweb="select"] > div {{
        background-color: {C_AZUL}22 !important;
        border: 1px solid {C_AZUL}44 !important;
        border-radius: 8px !important;
    }}
    
    div[data-testid="stVerticalBlock"] > div:nth-child(even) div[data-baseweb="select"] > div {{
        background-color: {C_VERDE}22 !important;
        border-color: {C_VERDE}44 !important;
    }}

    .login-card {{
        background: linear-gradient(135deg, {C_AZUL}22, {C_ROSA}22);
        padding: 30px; border-radius: 20px; border: 2px solid #f0f0f0;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. Critérios e Lógica de Maré
CATEGORIAS = [
    "1. Atividades em Grupo/Proatividade", "2. Interesse pelo Novo",
    "3. Compartilhamento de Materiais", "4. Clareza e Desenvoltura",
    "5. Respeito às Regras", "6. Vocabulário Adequado",
    "7. Leitura e Escrita", "8. Compreensão de Comandos",
    "9. Superação de Desafios", "10. Assiduidade"
]

MARE_OPCOES = {
    "C: Maré Cheia (Muito Bem)": 4,
    "E: Enchente (Em Evolução)": 3,
    "V: Vazante (Teve Declínio)": 2,
    "B: Maré Baixa (Atenção)": 1
}
MARE_REVERSO = {v: k[0] for k, v in MARE_OPCOES.items()}

# Correção Automática do Banco de Dados
AVAL_FILE = "avaliacoes.csv"
COLUNAS_CERTAS = ["Aluno", "Periodo"] + CATEGORIAS

def verificar_banco():
    if not os.path.exists(AVAL_FILE):
        pd.DataFrame(columns=COLUNAS_CERTAS).to_csv(AVAL_FILE, index=False)
    else:
        df = pd.read_csv(AVAL_FILE)
        if "Periodo" not in df.columns or len(df.columns) != len(COLUNAS_CERTAS):
            pd.DataFrame(columns=COLUNAS_CERTAS).to_csv(AVAL_FILE, index=False)

verificar_banco()

TURMAS_CONFIG = {
    "SALA ROSA": {"cor": C_ROSA, "key": "sala_rosa"},
    "SALA AMARELA": {"cor": C_AMARELO, "key": "sala_amarela"},
    "SALA VERDE": {"cor": C_VERDE, "key": "sala_verde"},
    "SALA AZUL": {"cor": C_AZUL, "key": "sala_azul"},
    "CIRAND. MUNDO": {"cor": C_ROXO, "key": "cirand_mundo"},
}

# 3. Funções de Conexão
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

def safe_read(worksheet_name):
    try:
        if worksheet_name == "GERAL": url = st.secrets["connections"]["gsheets"]["geral"]
        else: url = st.secrets["connections"]["gsheets"][TURMAS_CONFIG[worksheet_name]['key']]
        url_csv = url.split("/edit")[0] + "/export?format=csv"
        if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
        df = pd.read_csv(url_csv)
        df.columns = [str(c).strip().upper() for c in df.columns]
        if "PADRINHO" in df.columns: df = df.rename(columns={"PADRINHO": "PADRINHO/MADRINHA"})
        return df.fillna("")
    except: return pd.DataFrame()

# 4. Estados e Login
if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
for k in ['sel_mat', 'sel_pad', 'sel_aval']:
    if k not in st.session_state: st.session_state[k] = "SALA ROSA"

if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown(f'<div class="login-card"><h2 style="text-align: center; color: {C_AZUL}; margin:0;">Acesso</h2></div>', unsafe_allow_html=True)
        with st.form("login"):
            u, s = st.text_input("👤 Usuário").strip().upper(), st.text_input("🔑 Chave", type="password")
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

# --- MENU ---
st.sidebar.write(f"👤 **{st.session_state.nome_usuario}**")
if st.session_state.perfil == "admin":
    menu = st.sidebar.radio("Navegação", ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução", "🌊 Tábua da Maré - Interno"])
else: menu = "🌊 Evolução"

if st.sidebar.button("🚪 Sair"):
    st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
    st.rerun()

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- 👤 ABA: CADASTRO ---
if menu == "👤 Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA}'>👤 Novo Cadastro</h3>", unsafe_allow_html=True)
    with st.form("cad_form"):
        c1, c2 = st.columns(2)
        n, i = c1.text_input("Nome"), c2.text_input("Idade")
        comu, t = c1.text_input("Comunidade"), c2.selectbox("Sala", list(TURMAS_CONFIG.keys()))
        tn = c1.selectbox("Turno", ["A", "B"])
        if st.form_submit_button("Cadastrar"):
            if n and i:
                client = get_gspread_client()
                sh = client.open_by_key("1MBAvQB5xGhE7OAHGWdFPvGfwqzP9SpiaIW4OEl2Mgk4")
                nova_linha = [n.upper(), t, tn, i, comu.upper(), ""]
                sh.worksheet(t).append_row(nova_linha); sh.worksheet("GERAL").append_row(nova_linha)
                st.success("Cadastrado!"); st.rerun()

# --- 📝 ABA: MATRÍCULAS ---
elif menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE}'>📋 Matrículas</h3>", unsafe_allow_html=True)
    cols = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        op = "1.0" if st.session_state.sel_mat == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {op}; }}</style>', unsafe_allow_html=True)
        if cols[i].button(sala, key=f"btn_mat_{sala}"): st.session_state.sel_mat = sala; st.rerun()
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_mat)
    f1, f2 = st.columns(2)
    f_tn, f_cm = f1.selectbox("Turno", ["Todos", "A", "B"]), f2.selectbox("Comunidade", ["Todas"] + sorted(list(df_g["COMUNIDADE"].unique())))
    df_f = df_s.copy()
    if f_tn != "Todos": df_f = df_f[df_f["ALUNO"].isin(df_g[df_g["TURNO"].astype(str).str.contains(f_tn)]["ALUNO"])]
    if f_cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm]
    st.table(df_f[["ALUNO", "IDADE", "COMUNIDADE"]])

# --- 🤝 ABA: APADRINHAMENTO ---
elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🤝 Apadrinhamento</h3>", unsafe_allow_html=True)
    cols = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        op = "1.0" if st.session_state.sel_pad == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {op}; }}</style>', unsafe_allow_html=True)
        if cols[i].button(sala, key=f"btn_pad_{sala}"): st.session_state.sel_pad = sala; st.rerun()
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_pad)
    f_sp = st.checkbox("Apenas sem padrinho")
    df_f = df_s.copy()
    if f_sp: df_f = df_f[df_f["PADRINHO/MADRINHA"].isin(["", "0", "nan", None])]
    st.table(df_f[["ALUNO", "COMUNIDADE", "PADRINHO/MADRINHA"]])

# --- 📊 ABA: LANÇAR AVALIAÇÃO (5 DE CADA LADO + LEGENDAS) ---
elif menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO}'>📊 Lançar Tábua da Maré</h3>", unsafe_allow_html=True)
    cols_btn = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        op = "1.0" if st.session_state.sel_aval == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {op}; }}</style>', unsafe_allow_html=True)
        if cols_btn[i].button(sala, key=f"btn_aval_{sala}"): st.session_state.sel_aval = sala; st.rerun()
    
    df_s = safe_read(st.session_state.sel_aval)
    with st.form("aval_form"):
        c1, c2 = st.columns(2)
        al = c1.selectbox("Aluno", sorted(df_s["ALUNO"].unique()))
        tr = c2.selectbox("Semestre", ["1º Semestre", "2º Semestre"])
        st.info("C: Cheia | E: Enchente | V: Vazante | B: Baixa")
        col_esq, col_dir = st.columns(2)
        notas = {}
        for idx, cat in enumerate(CATEGORIAS):
            target = col_esq if idx < 5 else col_dir
            notas[cat] = target.selectbox(cat, list(MARE_OPCOES.keys()))
        if st.form_submit_button("Salvar"):
            df_av = pd.read_csv(AVAL_FILE)
            df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Periodo'] == tr))]
            nova = pd.DataFrame([[al, tr] + [MARE_OPCOES[notas[c]] for c in CATEGORIAS]], columns=COLUNAS_CERTAS)
            pd.concat([df_av, nova], ignore_index=True).to_csv(AVAL_FILE, index=False)
            st.success("Salvo!")

# --- 🌊 ABA: EVOLUÇÃO / TÁBUA ---
elif menu in ["🌊 Evolução", "🌊 Tábua da Maré - Interno"]:
    st.markdown(f"<h3 style='color:{C_AZUL}'>🌊 Visualização da Maré</h3>", unsafe_allow_html=True)
    df_av = pd.read_csv(AVAL_FILE)
    if not df_av.empty:
        al_s = st.selectbox("Aluno", sorted(df_av["Aluno"].unique()))
        df_al = df_av[df_av["Aluno"] == al_s]
        if not df_al.empty:
            tri = st.selectbox("Semestre", df_al["Periodo"].unique())
            row = df_al[df_al["Periodo"] == tri].iloc[0]
            y_vals = [float(row[c]) for c in CATEGORIAS]
            fig = go.Figure(go.Scatter(x=CATEGORIAS, y=y_vals, mode='lines+markers+text', text=[MARE_REVERSO[v] for v in y_vals], textposition="top center", fill='tozeroy', line=dict(color=C_AZUL, width=4, shape='spline')))
            fig.update_layout(yaxis=dict(range=[0, 4.5], tickvals=[1,2,3,4], ticktext=["B","V","E","C"]), height=500)
            st.plotly_chart(fig, use_container_width=True)
