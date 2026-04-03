import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from scipy.interpolate import make_interp_spline # Para a suavização real

# 1. Configuração de Estilo
st.set_page_config(page_title="Tábua da Maré - Instituto Mãe Lalu", layout="wide")

COR_VERDE = "#a8cf45"
COR_AZUL = "#5cc6d0"

st.markdown(f"""
    <div style='text-align: center; padding: 10px;'>
        <h1 style='margin-bottom: 0;'>
            <span style='color: {COR_VERDE};'>Instituto</span> <span style='color: {COR_AZUL};'>Mãe</span> <span style='color: {COR_VERDE};'>Lalu</span>
        </h1>
        <h3 style='color: {COR_AZUL}; font-weight: 300; margin-top: 0;'>🌊 Tábua da Maré</h3>
    </div>
    <hr style="border: 1px solid {COR_VERDE};">
    """, unsafe_allow_html=True)

# 2. Critérios e Banco de Dados Local
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"

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
    with st.form("cadastro", clear_on_submit=True):
        nome = st.text_input("Nome do Aluno")
        idade = st.number_input("Idade", 4, 15, 7)
        turno = st.selectbox("Turno", ["Matutino", "Vespertino"])
        if st.form_submit_button("Salvar"):
            if nome:
                df = pd.read_csv(ALUNOS_FILE)
                novo = pd.DataFrame([[nome.strip(), idade, turno]], columns=["Nome", "Idade", "Turno"])
                pd.concat([df, novo], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
                st.success(f"Aluno {nome} registrado!")

# --- MODULO DE LANÇAMENTO ---
elif menu == "Lançar Avaliação":
    st.header("📊 Lançar Notas")
    df_alunos = pd.read_csv(ALUNOS_FILE)
    if df_alunos.empty:
        st.info("Cadastre um aluno primeiro.")
    else:
        with st.form("notas", clear_on_submit=True):
            aluno = st.selectbox("Selecione o Aluno", df_alunos["Nome"].unique())
            trim = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            scores = {c: st.slider(c, 1, 5, 3) for c in CATEGORIAS}
            if st.form_submit_button("Salvar Avaliação"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == aluno) & (df_av['Trimestre'] == trim))]
                nova_av = pd.DataFrame([[aluno, trim] + list(scores.values())], columns=["Aluno", "Trimestre"] + CATEGORIAS)
                pd.concat([df_av, nova_av], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Avaliação salva!")

# --- PAINEL DE EVOLUÇÃO (DASHBOARD) ---
elif menu == "Painel de Evolução":
    df_alunos = pd.read_csv(ALUNOS_FILE)
    df_av = pd.read_csv(AVAL_FILE)
    
    if df_av.empty:
        st.info("Aguardando registros e avaliações.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            turno_sel = st.selectbox("1. Filtrar Turno", ["Matutino", "Vespertino"])
        
        alunos_turno = df_alunos[df_alunos["Turno"] == turno_sel]["Nome"].unique()
        avaliados = df_av[df_av["Aluno"].isin(alunos_turno)]["Aluno"].unique()
        
        if len(avaliados) == 0:
            st.warning("Nenhum dado neste turno.")
        else:
            with c2:
                aluno_sel = st.selectbox("2. Selecionar Aluno", sorted(avaliados))
            with c3:
                trims = df_av[df_av["Aluno"] == aluno_sel]["Trimestre"].unique()
                trim_sel = st.selectbox("3. Trimestre de Avaliação", trims)

            # Processamento da Onda (Matemática de Senoide)
            dados = df_av[(df_av["Aluno"] == aluno_sel) & (df_av["Trimestre"] == trim_sel)].iloc[0]
            notas = [dados[c] for c in CATEGORIAS]
            
            x = np.arange(len(CATEGORIAS))
            x_new = np.linspace(0, len(CATEGORIAS) - 1, 300) 
            
            # Gerando a Spline Cúbica (Suavização de Seno/Cosseno)
            spl = make_interp_spline(x, notas, k=3)
            y_smooth = spl(x_new)
            y_smooth = np.clip(y_smooth, 1, 5) # Mantém a onda dentro do limite 1-5

            st.subheader(f"🌊 Tábua da Maré: {aluno_sel} ({trim_sel})")
            
            fig = go.Figure()
            # A linha suave (A Maré)
            fig.add_trace(go.Scatter(
                x=x_new, y=y_smooth,
                mode='lines',
                line=dict(shape='spline', width=6, color=COR_AZUL),
                fill='tozeroy',
                fillcolor=f"rgba(92, 198, 208, 0.2)",
                name="Fluxo"
            ))
            # Os pontos reais (As boias)
            fig.add_trace(go.Scatter(
                x=x, y=notas,
                mode='markers',
                marker=dict(size=10, color=COR_VERDE),
                name="Nota Real"
            ))

            fig.update_layout(
                xaxis=dict(tickmode='array', tickvals=list(range(len(CATEGORIAS))), ticktext=CATEGORIAS),
                yaxis=dict(range=[0, 5.5], gridcolor="#f0f0f0"),
                plot_bgcolor='white', height=400, showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

            # Radar (Ficha técnica)
            st.divider()
            fig_radar = go.Figure(go.Scatterpolar(r=notas, theta=CATEGORIAS, fill='toself', fillcolor='rgba(168, 207, 69, 0.4)', line=dict(color=COR_VERDE)))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
            st.plotly_chart(fig_radar, use_container_width=True)
