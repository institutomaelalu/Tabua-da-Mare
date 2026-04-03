import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Configuração de Estilo e Identidade Visual
st.set_page_config(page_title="Tábua da Maré - Instituto Mãe Lalu", layout="wide")

# Cores oficiais
COR_VERDE = "#a8cf45"
COR_AZUL = "#5cc6d0"

st.markdown(f"""
    <div style='text-align: center; padding: 20px;'>
        <h1 style='margin-bottom: 0;'>
            <span style='color: {COR_VERDE};'>Instituto</span> 
            <span style='color: {COR_AZUL};'>Mãe</span> 
            <span style='color: {COR_VERDE};'>Lalu</span>
        </h1>
        <h3 style='color: {COR_AZUL}; font-weight: 300; margin-top: 0;'>🌊 Tábua da Maré</h3>
    </div>
    <hr style="border: 1px solid {COR_VERDE};">
    """, unsafe_allow_html=True)

# 2. Inicialização do Banco de Dados
ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]

def init_db():
    if not os.path.exists(ALUNOS_FILE):
        pd.DataFrame(columns=["Nome", "Idade", "Turno"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE):
        pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)

init_db()

# 3. Navegação Lateral
menu = st.sidebar.radio("Menu", ["Painel de Evolução", "Cadastrar Aluno", "Lançar Avaliação"])

# --- MODULO DE CADASTRO ---
if menu == "Cadastrar Aluno":
    st.header("📝 Novo Registro")
    with st.form("cadastro"):
        nome = st.text_input("Nome do Aluno")
        idade = st.number_input("Idade", 4, 15)
        turno = st.selectbox("Turno", ["Matutino", "Vespertino"])
        if st.form_submit_button("Salvar"):
            df = pd.read_csv(ALUNOS_FILE)
            pd.concat([df, pd.DataFrame([[nome, idade, turno]], columns=df.columns)]).to_csv(ALUNOS_FILE, index=False)
            st.success("Registrado!")

# --- MODULO DE LANÇAMENTO ---
elif menu == "Lançar Avaliação":
    st.header("📊 Lançar Notas")
    df_alunos = pd.read_csv(ALUNOS_FILE)
    if not df_alunos.empty:
        with st.form("notas"):
            aluno = st.selectbox("Selecione o Aluno", df_alunos["Nome"])
            trim = st.selectbox("Trimestre", ["1º Trim", "2º Trim", "3º Trim"])
            scores = {c: st.slider(c, 1, 5, 3) for c in CATEGORIAS}
            if st.form_submit_button("Salvar Avaliação"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == aluno) & (df_av['Trimestre'] == trim))]
                pd.concat([df_av, pd.DataFrame([[aluno, trim] + list(scores.values())], columns=df_av.columns)]).to_csv(AVAL_FILE, index=False)
                st.info("Notas salvas!")

# --- PAINEL DE EVOLUÇÃO (FILTROS SOLICITADOS) ---
elif menu == "Painel de Evolução":
    df_alunos = pd.read_csv(ALUNOS_FILE)
    df_av = pd.read_csv(AVAL_FILE)
    
    if df_av.empty:
        st.warning("Nenhum dado encontrado.")
    else:
        # Filtros em Colunas
        c1, c2, c3 = st.columns(3)
        with c1:
            turno_sel = st.selectbox("1. Filtrar Turno", ["Matutino", "Vespertino"])
        
        # Filtrar alunos que pertencem ao turno e possuem avaliação
        alunos_do_turno = df_alunos[df_alunos["Turno"] == turno_sel]["Nome"].tolist()
        avaliados = df_av[df_av["Aluno"].isin(alunos_do_turno)]["Aluno"].unique()
        
        with c2:
            aluno_sel = st.selectbox("2. Selecionar Aluno", avaliados)
        
        with c3:
            trimestres_disp = df_av[df_av["Aluno"] == aluno_sel]["Trimestre"].unique()
            trim_sel = st.selectbox("3. Escolha o Trimestre", trimestres_disp)

        # Dados para o gráfico
        row = df_av[(df_av["Aluno"] == aluno_sel) & (df_av["Trimestre"] == trim_sel)].iloc[0]
        notas = [row[c] for c in CATEGORIAS]

        # Gráfico de Maré Senoidal (Suavizado)
        st.subheader(f"🌊 Tábua da Maré Individual: {aluno_sel}")
        
        fig = go.Figure()
        
        # Interpolação Spline para criar a curva de seno/cosseno
        x_indices = np.arange(len(CATEGORIAS))
        x_suave = np.linspace(0, len(CATEGORIAS) - 1, 300)
        y_suave = np.interp(x_suave, x_indices, notas) # Base
        
        fig.add_trace(go.Scatter(
            x=x_suave, y=y_suave,
            mode='lines',
            line=dict(shape='spline', smoothing=1.5, width=6, color=COR_AZUL),
            fill='tozeroy',
            fillcolor=f"rgba(92, 198, 208, 0.2)",
            name=trim_sel
        ))

        fig.update_layout(
            xaxis=dict(tickmode='array', tickvals=list(range(len(CATEGORIAS))), ticktext=CATEGORIAS),
            yaxis=dict(range=[0, 5.5], title="Nível"),
            plot_bgcolor='white', height=450
        )
        st.plotly_chart(fig, use_container_width=True)

        # Gráfico Radar (Ficha de Apoio)
        st.divider()
        st.subheader("🕸️ Gráfico Radar de Competências")
        fig_radar = go.Figure(go.Scatterpolar(
            r=notas, theta=CATEGORIAS, fill='toself',
            fillcolor=f"rgba(168, 207, 69, 0.4)", line=dict(color=COR_VERDE)
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
        st.plotly_chart(fig_radar, use_container_width=True)
