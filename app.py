import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from scipy.interpolate import make_interp_spline

# 1. Configuração de Estilo e Cabeçalho
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

COR_VERDE = "#a8cf45"
COR_AZUL = "#5cc6d0"

st.markdown(f"""
    <div style='text-align: center; padding: 10px;'>
        <h1 style='margin-bottom: 0;'>
            <span style='color: {COR_VERDE};'>Instituto</span> <span style='color: {COR_AZUL};'>Mãe</span> <span style='color: {COR_VERDE};'>Lalu</span>
        </h1>
        <h3 style='color: {COR_AZUL}; font-weight: 300; margin-top: 0;'>🌊 Painel de Controle Integrado</h3>
    </div>
    <hr style="border: 1px solid {COR_VERDE};">
    """, unsafe_allow_html=True)

# 2. Configurações Tábua da Maré (Original Local via CSV)
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"

def init_db():
    if not os.path.exists(ALUNOS_FILE):
        pd.DataFrame(columns=["Nome", "Idade", "Turno"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE):
        pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)

init_db()

# 3. Mapeamento de Abas do Google Sheets (Baseado nos seus Secrets)
MAPA_LINKS = {
    "GERAL": "geral",
    "SALA ROSA": "sala_rosa",
    "SALA AMARELA": "sala_amarela",
    "SALA VERDE": "sala_verde",
    "SALA AZUL": "sala_azul",
    "CIRAND. MUNDO": "cirand_mundo"
}

def safe_read(worksheet_name):
    try:
        # Busca a chave correspondente no Secrets
        secret_key = MAPA_LINKS.get(worksheet_name)
        if secret_key:
            url_original = st.secrets["connections"]["gsheets"][secret_key]
            # Converte o link de edição para link de exportação direta de CSV
            url_export = url_original.replace("/edit#gid=", "/export?format=csv&gid=")
            # Se não houver o marcador de gid no replace, tenta o formato padrão
            if "/export" not in url_export:
                url_export = url_original.split("/edit")[0] + "/export?format=csv"
            
            df = pd.read_csv(url_export)
            # Limpa espaços em branco dos nomes das colunas
            df.columns = [str(c).strip() for c in df.columns]
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao acessar {worksheet_name}. Verifique o GID no Secrets.")
        return pd.DataFrame()

# 4. Navegação Lateral
menu = st.sidebar.radio("Menu de Navegação", [
    "🌊 Painel de Evolução", 
    "📝 Controle de Matrículas (GERAL)", 
    "🤝 Controle de Apadrinhamento",
    "👤 Cadastrar Aluno (Local)", 
    "📊 Lançar Avaliação (Local)"
])

# --- 1. PAINEL DE EVOLUÇÃO (Tábua da Maré) ---
if menu == "🌊 Painel de Evolução":
    df_alunos = pd.read_csv(ALUNOS_FILE)
    df_av = pd.read_csv(AVAL_FILE)
    
    if df_av.empty:
        st.info("Aguardando registros e avaliações locais.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            turno_sel = st.selectbox("1. Turno", ["Matutino", "Vespertino"])
        
        alunos_turno = df_alunos[df_alunos["Turno"] == turno_sel]["Nome"].unique()
        avaliados = df_av[df_av["Aluno"].isin(alunos_turno)]["Aluno"].unique()
        
        if len(avaliados) == 0:
            st.warning("Nenhum aluno deste turno possui avaliação.")
        else:
            with c2:
                aluno_sel = st.selectbox("2. Aluno", sorted(avaliados))
            with c3:
                trims = df_av[df_av["Aluno"] == aluno_sel]["Trimestre"].unique()
                trim_sel = st.selectbox("3. Trimestre", trims)

            dados = df_av[(df_av["Aluno"] == aluno_sel) & (df_av["Trimestre"] == trim_sel)].iloc[0]
            notas = [float(dados[c]) for c in CATEGORIAS]
            
            x = np.arange(len(CATEGORIAS))
            x_new = np.linspace(0, len(CATEGORIAS) - 1, 300) 
            spl = make_interp_spline(x, notas, k=3)
            y_smooth = np.clip(spl(x_
