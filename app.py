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
        secret_key = MAPA_LINKS.get(worksheet_name)
        if secret_key:
            # Puxa a URL do Secrets do Streamlit Cloud
            url_original = st.secrets["connections"]["gsheets"][secret_key]
            
            # Converte link de edição para link de exportação CSV para evitar erros de conexão
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
            
            # Interpolação para curva suave
            spl = make_interp_spline(x, notas, k=3)
            y_smooth = np.clip(spl(x_new), 1, 5)

            st.subheader(f"Evolução: {aluno_sel}")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x_new, y=y_smooth, mode='lines', 
                                     line=dict(width=6, color=COR_AZUL), 
                                     fill='tozeroy', fillcolor="rgba(92, 198, 208, 0.2)"))
            fig.add_trace(go.Scatter(x=x, y=notas, mode='markers', 
                                     marker=dict(size=12, color=COR_VERDE)))
            fig.update_layout(xaxis=dict(tickmode='array', tickvals=list(range(len(CATEGORIAS))), ticktext=CATEGORIAS),
                              yaxis=dict(range=[0, 5.5]), plot_bgcolor='white', height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# --- 2. CONTROLE DE MATRÍCULAS (Aba GERAL) ---
elif menu == "📝 Controle de Matrículas (GERAL)":
    st.header("📋 Lista Geral de Alunos")
    df_geral = safe_read("GERAL")
    if not df_geral.empty:
        cols_geral = ["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
        cols_validas = [c for c in cols_geral if c in df_geral.columns]
        st.dataframe(df_geral[cols_validas].dropna(subset=["ALUNO"]), use_container_width=True)

# --- 3. CONTROLE DE APADRINHAMENTO (Abas de Salas) ---
elif menu == "🤝 Controle de Apadrinhamento":
    st.header("🤝 Gestão por Salas")
    lista_salas = ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"]
    sala_sel = st.selectbox("Selecione a Sala:", lista_salas)
    
    df_sala = safe_read(sala_sel)
    if not df_sala.empty:
        cols_sala = ["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
        cols_v = [c for c in cols_sala if c in df_sala.columns]
        st.dataframe(df_sala[cols_v].dropna(subset=["ALUNO"]), use_container_width=True)

# --- 4. CADASTRAR ALUNO (Local) ---
elif menu == "👤 Cadastrar Aluno (Local)":
    st.header("📝 Novo Cadastro Local")
    with st.form("cad_local", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        idade = st.number_input("Idade", 0, 100, 7)
        turno = st.selectbox("Turno", ["Matutino", "Vespertino"])
        if st.form_submit_button("Salvar Registro"):
            if nome:
                df = pd.read_csv(ALUNOS_FILE)
                novo = pd.DataFrame([[nome.strip(), idade, turno]], columns=["Nome", "Idade", "Turno"])
                pd.concat([df, novo], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
                st.success(f"Aluno {nome} cadastrado com sucesso!")

# --- 5. LANÇAR AVALIAÇÃO (Local) ---
elif menu == "📊 Lançar Avaliação (Local)":
    st.header("📊 Registro de Notas")
    df_alunos = pd.read_csv(ALUNOS_FILE)
    if df_alunos.empty:
        st.warning("Cadastre um aluno localmente antes de avaliar.")
    else:
        with st.form("notas_local", clear_on_submit=True):
            aluno = st.selectbox("Aluno", sorted(df_alunos["Nome"].unique()))
            trim = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            
            c1, c2 = st.columns(2)
            scores = {}
            for i, cat in enumerate(CATEGORIAS):
                with c1 if i < 4 else c2:
                    scores[cat] = st.slider(cat, 1, 5, 3)
            
            if st.form_submit_button("Confirmar Avaliação"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == aluno) & (df_av['Trimestre'] == trim))]
                nova_linha = pd.DataFrame([[aluno, trim] + list(scores.values())], columns=["Aluno", "Trimestre"] + CATEGORIAS)
                pd.concat([df_av, nova_linha], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Avaliação salva com sucesso!")
