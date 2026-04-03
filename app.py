import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# Configuração da página
st.set_page_config(page_title="Tábua da Maré - Instituto Mãe Lalu", layout="wide")

# --- CABEÇALHO PERSONALIZADO ---
st.markdown(f"""
    <div style='text-align: center; padding: 10px;'>
        <h1 style='font-size: 50px; margin-bottom: 0;'>
            <span style='color: #a8cf45;'>Instituto</span> 
            <span style='color: #5cc6d0;'>Mãe</span> 
            <span style='color: #a8cf45;'>Lalu</span>
        </h1>
        <h3 style='color: #5cc6d0; font-weight: 300; margin-top: 0;'>🌊 Tábua da Maré</h3>
    </div>
    <hr style="border: 1px solid #a8cf45;">
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"

def init_db():
    if not os.path.exists(ALUNOS_FILE):
        pd.DataFrame(columns=["Nome", "Idade", "Turno"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE):
        pd.DataFrame(columns=[
            "Aluno", "Trimestre", "Frequência", "Leitura", "Escrita", 
            "Materiais", "Participação", "Regras", "Clareza", "Interesse"
        ]).to_csv(AVAL_FILE, index=False)

init_db()

CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação", ["Painel de Evolução", "Cadastrar Aluno", "Lançar Avaliação"])

# --- 1. CADASTRO ---
if menu == "Cadastrar Aluno":
    st.header("📝 Registro do Aluno")
    with st.form("cadastro"):
        nome = st.text_input("Nome Completo")
        idade = st.number_input("Idade", 4, 12)
        turno = st.selectbox("Turno", ["Matutino", "Vespertino"])
        if st.form_submit_button("Salvar Registro"):
            df = pd.read_csv(ALUNOS_FILE)
            novo = pd.DataFrame([[nome, idade, turno]], columns=df.columns)
            pd.concat([df, novo]).to_csv(ALUNOS_FILE, index=False)
            st.success(f"Aluno {nome} registrado!")

# --- 2. AVALIAÇÃO ---
elif menu == "Lançar Avaliação":
    st.header("📊 Verificação de Aprendizagem")
    df_alunos = pd.read_csv(ALUNOS_FILE)
    if df_alunos.empty:
        st.warning("Cadastre um aluno primeiro.")
    else:
        with st.form("avaliacao"):
            aluno = st.selectbox("Selecione o Aluno", df_alunos["Nome"])
            trim = st.select_slider("Trimestre", options=["1º Trim", "2º Trim", "3º Trim"])
            crit = {}
            col1, col2 = st.columns(2)
            for i, c in enumerate(CATEGORIAS):
                with col1 if i < 4 else col2:
                    crit[c] = st.slider(c, 1, 5, 3)
            if st.form_submit_button("Registrar Maré"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == aluno) & (df_av['Trimestre'] == trim))]
                nova_av = pd.DataFrame([[aluno, trim] + list(crit.values())], columns=df_av.columns)
                pd.concat([df_av, nova_av]).to_csv(AVAL_FILE, index=False)
                st.info("Dados registrados!")

# --- 3. DASHBOARD ---
elif menu == "Painel de Evolução":
    df_av = pd.read_csv(AVAL_FILE)
    if df_av.empty:
        st.info("Aguardando lançamentos.")
    else:
        aluno_sel = st.selectbox("Selecione o Aluno", df_av["Aluno"].unique())
        df_aluno = df_av[df_av["Aluno"] == aluno_sel].copy()
        df_aluno['Ord'] = df_aluno['Trimestre'].map({"1º Trim": 1, "2º Trim": 2, "3º Trim": 3})
        df_aluno = df_aluno.sort_values('Ord')

        # GRÁFICO DE MARÉ (SENO/COSSENO)
        st.subheader("🌊 Movimento da Maré Individual")
        fig_mare = go.Figure()
        cores = ['#5cc6d0', '#a8cf45', '#0077b6', '#00b4d8', '#90e0ef', '#72efdd', '#48cae4', '#b5e48c']
        
        for i, crit in enumerate(CATEGORIAS):
            fig_mare.add_trace(go.Scatter(
                x=df_aluno["Trimestre"], 
                y=df_aluno[crit],
                mode='lines+markers',
                name=crit,
                line=dict(shape='spline', smoothing=1.3, width=4, color=cores[i % len(cores)]),
                fill='tozeroy',
                fillcolor=f"rgba{tuple(list(int(cores[i % len(cores)].lstrip('#')[j:j+2], 16) for j in (0, 2, 4)) + [0.15])}"
            ))
        fig_mare.update_layout(yaxis=dict(range=[0, 5.5]), plot_bgcolor='white')
        st.plotly_chart(fig_mare, use_container_width=True)

        # GRÁFICO RADAR
        st.divider()
        st.subheader("🕸️ Perfil por Trimestre (Radar)")
        trim_sel = st.selectbox("Escolha o Trimestre", df_aluno["Trimestre"].unique())
        dados_trim = df_aluno[df_aluno["Trimestre"] == trim_sel].iloc[0]
        
        fig_radar = go.Figure(go.Scatterpolar(
            r=[dados_trim[c] for c in CATEGORIAS],
            theta=CATEGORIAS,
            fill='toself',
            fillcolor='rgba(168, 207, 69, 0.4)',
            line=dict(color='#a8cf45')
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])))
        st.plotly_chart(fig_radar, use_container_width=True)
