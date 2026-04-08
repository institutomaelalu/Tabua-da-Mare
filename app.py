import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from scipy.interpolate import make_interp_spline
from streamlit_gsheets import GSheetsConnection

# 1. Configuração e Estilo
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")
COR_VERDE, COR_AZUL = "#a8cf45", "#5cc6d0"

st.markdown(f"<div style='text-align: center; padding: 10px;'><h1 style='margin-bottom: 0;'><span style='color: {COR_VERDE};'>Instituto</span> <span style='color: {COR_AZUL};'>Mãe</span> <span style='color: {COR_VERDE};'>Lalu</span></h1><h3 style='color: {COR_AZUL}; font-weight: 300; margin-top: 0;'>🌊 Painel de Controle Integrado</h3></div><hr style='border: 1px solid {COR_VERDE};'>", unsafe_allow_html=True)

# 2. Configurações Tábua da Maré (Original Local)
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE, AVAL_FILE = "alunos.csv", "avaliacoes.csv"

def init_db():
    if not os.path.exists(ALUNOS_FILE): pd.DataFrame(columns=["Nome", "Idade", "Turno"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE): pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)

init_db()
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Navegação
menu = st.sidebar.radio("Menu", ["🌊 Painel de Evolução", "📝 Controle de Matrículas (GERAL)", "🤝 Controle de Apadrinhamento", "👤 Cadastrar Aluno (Local)", "📊 Lançar Avaliação (Local)"])

# --- FUNÇÃO AUXILIAR DE LEITURA (Evita HTTPError) ---
def safe_read(worksheet_name):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=0)
        if df is not None:
            df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao acessar a aba '{worksheet_name}'. Verifique o link no Secrets e se a aba existe.")
        return pd.DataFrame()

# --- 1. PAINEL DE EVOLUÇÃO (Tábua da Maré) ---
if menu == "🌊 Painel de Evolução":
    df_alunos, df_av = pd.read_csv(ALUNOS_FILE), pd.read_csv(AVAL_FILE)
    if df_av.empty: st.info("Sem avaliações.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: t_sel = st.selectbox("Turno", ["Matutino", "Vespertino"])
        avaliados = df_av[df_av["Aluno"].isin(df_alunos[df_alunos["Turno"] == t_sel]["Nome"])]["Aluno"].unique()
        if len(avaliados) == 0: st.warning("Sem dados.")
        else:
            with c2: a_sel = st.selectbox("Aluno", sorted(avaliados))
            with c3: trim_sel = st.selectbox("Trimestre", df_av[df_av["Aluno"] == a_sel]["Trimestre"].unique())
            dados = df_av[(df_av["Aluno"] == a_sel) & (df_av["Trimestre"] == trim_sel)].iloc[0]
            notas = [float(dados[c]) for c in CATEGORIAS]
            x, x_new = np.arange(len(CATEGORIAS)), np.linspace(0, len(CATEGORIAS) - 1, 300)
            y_smooth = np.clip(make_interp_spline(x, notas, k=3)(x_new), 1, 5)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x_new, y=y_smooth, mode='lines', line=dict(width=6, color=COR_AZUL), fill='tozeroy', fillcolor="rgba(92, 198, 208, 0.2)"))
            fig.add_trace(go.Scatter(x=x, y=notas, mode='markers', marker=dict(size=10, color=COR_VERDE)))
            fig.update_layout(xaxis=dict(tickmode='array', tickvals=list(range(len(CATEGORIAS))), ticktext=CATEGORIAS), yaxis=dict(range=[0, 5.5]), plot_bgcolor='white', height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# --- 2. MATRÍCULAS (GERAL) ---
elif menu == "📝 Controle de Matrículas (GERAL)":
    st.header("📋 Lista Geral (Nuvem)")
    df = safe_read("GERAL")
    if not df.empty:
        cols = [c for c in ["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"] if c in df.columns]
        st.dataframe(df[cols].dropna(subset=["ALUNO"]), use_container_width=True)

# --- 3. APADRINHAMENTO ---
elif menu == "🤝 Controle de Apadrinhamento":
    st.header("🤝 Gestão por Salas")
    sala = st.selectbox("Sala:", ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"])
    df_s = safe_read(sala)
    if not df_s.empty:
        cols = [c for c in ["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"] if c in df_s.columns]
        st.dataframe(df_s[cols].dropna(subset=["ALUNO"]), use_container_width=True)

# --- 4 & 5 (CADASTRO E LANÇAMENTO LOCAL MANTIDOS) ---
elif menu == "👤 Cadastrar Aluno (Local)":
    with st.form("cad"):
        n = st.text_input("Nome")
        i = st.number_input("Idade", 4, 15, 7)
        t = st.selectbox("Turno", ["Matutino", "Vespertino"])
        if st.form_submit_button("Salvar"):
            df = pd.read_csv(ALUNOS_FILE)
            pd.concat([df, pd.DataFrame([[n.strip(), i, t]], columns=["Nome", "Idade", "Turno"])], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Salvo!")

elif menu == "📊 Lançar Avaliação (Local)":
    df_al = pd.read_csv(ALUNOS_FILE)
    with st.form("notas"):
        al = st.selectbox("Aluno", df_al["Nome"].unique())
        tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
        sc = {c: st.slider(c, 1, 5, 3) for c in CATEGORIAS}
        if st.form_submit_button("Salvar"):
            df_v = pd.read_csv(AVAL_FILE)
            df_v = df_v[~((df_v['Aluno'] == al) & (df_v['Trimestre'] == tr))]
            pd.concat([df_v, pd.DataFrame([[al, tr] + list(sc.values())], columns=["Aluno", "Trimestre"] + CATEGORIAS)], ignore_index=True).to_csv(AVAL_FILE, index=False)
            st.success("Avaliação salva!")
