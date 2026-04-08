import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from scipy.interpolate import make_interp_spline

# 1. Configuração de Estilo e Cabeçalho
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

COR_VERDE_INST = "#a8cf45"
COR_AZUL_INST = "#5cc6d0"

st.markdown(f"""
    <div style='text-align: center; padding: 10px;'>
        <h1 style='margin-bottom: 0;'>
            <span style='color: {COR_VERDE_INST};'>Instituto</span> <span style='color: {COR_AZUL_INST};'>Mãe</span> <span style='color: {COR_VERDE_INST};'>Lalu</span>
        </h1>
        <h3 style='color: {COR_AZUL_INST}; font-weight: 300; margin-top: 0;'>🌊 Painel de Controle Integrado</h3>
    </div>
    <hr style="border: 1px solid {COR_VERDE_INST};">
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

# 3. Mapeamento de Abas do Google Sheets
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
        secret_key = MAPA_LINKS.get(worksheet_name)
        if secret_key:
            url_original = st.secrets["connections"]["gsheets"][secret_key]
            if "/edit" in url_original:
                url_export = url_original.split("/edit")[0] + "/export?format=csv"
                if "gid=" in url_original:
                    gid = url_original.split("gid=")[1]
                    url_export += f"&gid={gid}"
            else:
                url_export = url_original
            df = pd.read_csv(url_export)
            df.columns = [str(c).strip() for c in df.columns]
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao acessar {worksheet_name}.")
        return pd.DataFrame()

# --- FUNÇÃO DE ESTILIZAÇÃO ---
def stylize_df(df):
    def apply_room_color(row):
        turma = str(row.get('TURMA', '')).strip().upper()
        colors = {
            'SALA ROSA': 'background-color: #ffd1dc; color: #000000',
            'SALA AMARELA': 'background-color: #fff9c4; color: #000000',
            'SALA VERDE': 'background-color: #c8e6c9; color: #000000',
            'SALA AZUL': 'background-color: #e3f2fd; color: #000000',
            'CIRAND. MUNDO': 'background-color: #1a237e; color: #ffffff',
        }
        style = colors.get(turma, '')
        return [style] * len(row)
    
    return df.style.apply(apply_room_color, axis=1)

# 4. Navegação Lateral
menu = st.sidebar.radio("Menu de Navegação", [
    "🌊 Painel de Evolução", 
    "📝 Controle de Matrículas (GERAL)", 
    "🤝 Controle de Apadrinhamento",
    "👤 Cadastrar Aluno (Local)", 
    "📊 Lançar Avaliação (Local)"
])

# --- 1. PAINEL DE EVOLUÇÃO ---
if menu == "🌊 Painel de Evolução":
    df_alunos = pd.read_csv(ALUNOS_FILE)
    df_av = pd.read_csv(AVAL_FILE)
    if df_av.empty:
        st.info("Aguardando registros locais.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1: turno_sel = st.selectbox("1. Turno", ["Matutino", "Vespertino"])
        alunos_turno = df_alunos[df_alunos["Turno"] == turno_sel]["Nome"].unique()
        avaliados = df_av[df_av["Aluno"].isin(alunos_turno)]["Aluno"].unique()
        if len(avaliados) == 0:
            st.warning("Sem avaliações neste turno.")
        else:
            with c2: aluno_sel = st.selectbox("2. Aluno", sorted(avaliados))
            with c3: trim_sel = st.selectbox("3. Trimestre", df_av[df_av["Aluno"] == aluno_sel]["Trimestre"].unique())
            dados = df_av[(df_av["Aluno"] == aluno_sel) & (df_av["Trimestre"] == trim_sel)].iloc[0]
            notas = [float(dados[c]) for c in CATEGORIAS]
            x, x_new = np.arange(len(CATEGORIAS)), np.linspace(0, len(CATEGORIAS) - 1, 300) 
            spl = make_interp_spline(x, notas, k=3)
            y_smooth = np.clip(spl(x_new), 1, 5)
            st.subheader(f"Evolução: {aluno_sel}")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x_new, y=y_smooth, mode='lines', line=dict(width=6, color=COR_AZUL_INST), fill='tozeroy', fillcolor="rgba(92, 198, 208, 0.2)"))
            fig.add_trace(go.Scatter(x=x, y=notas, mode='markers', marker=dict(size=12, color=COR_VERDE_INST)))
            fig.update_layout(xaxis=dict(tickmode='array', tickvals=list(range(len(CATEGORIAS))), ticktext=CATEGORIAS), yaxis=dict(range=[0, 5.5]), plot_bgcolor='white', height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# --- 2. MATRÍCULAS (GERAL) - FILTROS ATUALIZADOS ---
elif menu == "📝 Controle de Matrículas (GERAL)":
    st.header("📋 Lista Geral de Alunos")
    df_raw = safe_read("GERAL")
    
    if not df_raw.empty:
        st.write("🔍 **Filtros de Busca**")
        # Layout de 4 colunas para os filtros
        f1, f2, f3, f4 = st.columns(4)
        with f1: f_nome = st.text_input("Nome do Aluno")
        with f2: f_turma = st.selectbox("Turma", ["Todas"] + sorted(list(df_raw["TURMA"].dropna().unique())))
        with f3: f_comu = st.selectbox("Comunidade", ["Todas"] + sorted(list(df_raw["COMUNIDADE"].dropna().unique())))
        with f4: f_turno = st.selectbox("Turno", ["Todos"] + sorted(list(df_raw["TURNO"].dropna().unique())))

        df_f = df_raw.copy()
        if f_nome: df_f = df_f[df_f["ALUNO"].str.contains(f_nome, case=False, na=False)]
        if f_turma != "Todas": df_f = df_f[df_f["TURMA"] == f_turma]
        if f_comu != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_comu]
        if f_turno != "Todos": df_f = df_f[df_f["TURNO"] == f_turno]

        cols = ["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]
        df_final = df_f[cols].dropna(subset=["ALUNO"])
        
        st.dataframe(stylize_df(df_final), use_container_width=True, height=500)

# --- 3. APADRINHAMENTO ---
elif menu == "🤝 Controle de Apadrinhamento":
    st.header("🤝 Gestão por Salas")
    sala_sel = st.selectbox("Selecione a Sala:", ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"])
    df_s = safe_read(sala_sel)
    if not df_s.empty:
        cols = ["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
        df_final_s = df_s[cols].dropna(subset=["ALUNO"])
        st.dataframe(stylize_df(df_final_s), use_container_width=True, height=500)

# --- 4 & 5 (CADASTROS LOCAIS) ---
elif menu == "👤 Cadastrar Aluno (Local)":
    st.header("📝 Novo Cadastro Local")
    with st.form("cad_l", clear_on_submit=True):
        n, i, t = st.text_input("Nome"), st.number_input("Idade", 0, 20, 7), st.selectbox("Turno", ["Matutino", "Vespertino"])
        if st.form_submit_button("Salvar"):
            df = pd.read_csv(ALUNOS_FILE)
            pd.concat([df, pd.DataFrame([[n.strip(), i, t]], columns=["Nome", "Idade", "Turno"])], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Cadastrado!")

elif menu == "📊 Lançar Avaliação (Local)":
    st.header("📊 Registro de Notas")
    df_al = pd.read_csv(ALUNOS_FILE)
    if not df_al.empty:
        with st.form("notas_l", clear_on_submit=True):
            al, tr = st.selectbox("Aluno", sorted(df_al["Nome"].unique())), st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            sc = {c: st.slider(c, 1, 5, 3) for c in CATEGORIAS}
            if st.form_submit_button("Confirmar"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
                pd.concat([df_av, pd.DataFrame([[al, tr] + list(sc.values())], columns=["Aluno", "Trimestre"] + CATEGORIAS)], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Salvo!")
