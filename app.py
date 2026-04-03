import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuração da página
st.set_page_config(page_title="Tábua da Maré - Alfabetização", layout="wide")

# Estilização para tons de azul (Maré)
st.markdown("""
    <style>
    .main { background-color: #f0faff; }
    .stButton>button { background-color: #0077b6; color: white; border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS SIMPLIFICADO ---
ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"

def init_db():
    if not os.path.exists(ALUNOS_FILE):
        pd.DataFrame(columns=["Nome", "Idade", "Turma"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE):
        pd.DataFrame(columns=[
            "Aluno", "Trimestre", "Frequência", "Leitura", "Escrita", 
            "Materiais", "Participação", "Regras", "Clareza", "Interesse"
        ]).to_csv(AVAL_FILE, index=False)

init_db()

# --- NAVEGAÇÃO ---
st.sidebar.title("🌊 Tábua da Maré")
menu = st.sidebar.radio("Navegação", ["Painel de Evolução", "Cadastrar Aluno", "Lançar Avaliação"])

# --- 1. CADASTRO ---
if menu == "Cadastrar Aluno":
    st.header("📝 Registro do Aluno")
    with st.form("cadastro"):
        nome = st.text_input("Nome Completo")
        idade = st.number_input("Idade", 4, 10)
        turma = st.selectbox("Turma", ["1º Ano A", "1º Ano B", "2º Ano A", "Reforço"])
        if st.form_submit_button("Salvar Registro"):
            df = pd.read_csv(ALUNOS_FILE)
            novo = pd.DataFrame([[nome, idade, turma]], columns=df.columns)
            pd.concat([df, novo]).to_csv(ALUNOS_FILE, index=False)
            st.success("Aluno registrado no sistema!")

# --- 2. AVALIAÇÃO ---
elif menu == "Lançar Avaliação":
    st.header("📊 Verificação de Aprendizagem (1 a 5)")
    df_alunos = pd.read_csv(ALUNOS_FILE)
    
    if df_alunos.empty:
        st.warning("Nenhum aluno cadastrado.")
    else:
        with st.form("avaliacao"):
            aluno = st.selectbox("Selecione o Aluno", df_alunos["Nome"])
            trim = st.select_slider("Trimestre", options=["1º Trim", "2º Trim", "3º Trim"])
            
            st.divider()
            crit = {}
            col1, col2 = st.columns(2)
            categorias = [
                "Frequência", "Leitura", "Escrita", "Materiais", 
                "Participação", "Regras", "Clareza", "Interesse"
            ]
            
            for i, c in enumerate(categorias):
                with col1 if i < 4 else col2:
                    crit[c] = st.slider(c, 1, 5, 3)
            
            if st.form_submit_button("Registrar Maré"):
                df_av = pd.read_csv(AVAL_FILE)
                nova_av = pd.DataFrame([[aluno, trim] + list(crit.values())], columns=df_av.columns)
                pd.concat([df_av, nova_av]).to_csv(AVAL_FILE, index=False)
                st.info(f"Avaliação de {trim} concluída para {aluno}")

# --- 3. DASHBOARD (O GRÁFICO DE ONDAS E RADAR) ---
elif menu == "Painel de Evolução":
    st.header("🌊 Evolução Individual")
    df_av = pd.read_csv(AVAL_FILE)
    
    if df_av.empty:
        st.info("Aguardando lançamentos para gerar gráficos.")
    else:
        aluno_sel = st.selectbox("Selecione o Aluno para análise", df_av["Aluno"].unique())
        dados_aluno = df_av[df_av["Aluno"] == aluno_sel].sort_values("Trimestre")

        # --- GRÁFICO DE RADAR (Situação Atual) ---
        st.subheader("🕸️ Perfil de Habilidades (Radar)")
        
        # Pegar o último trimestre avaliado
        ultimo_trim = dados_aluno.iloc[-1]
        categorias = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
        valores = [ultimo_trim[c] for c in categorias]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=valores,
            theta=categorias,
            fill='toself',
            name=ultimo_trim["Trimestre"],
            line_color='#0077b6'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            showlegend=True
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        st.divider()

        # --- GRÁFICO DE MARÉ (Evolução em Ondas) ---
        st.subheader("🌊 Movimento da Maré (Evolução Temporal)")
        
        # Calculamos a média de aprendizado por trimestre para ver a "altura da maré"
        dados_aluno["Média Global"] = dados_aluno[categorias].mean(axis=1)
        
        fig_mare = px.area(
            dados_aluno, 
            x="Trimestre", 
            y="Média Global",
            title=f"Nível da Maré de Aprendizagem: {aluno_sel}",
            line_shape="spline", # Aqui cria o efeito de "Onda" suavizada
            markers=True,
            color_discrete_sequence=['#90e0ef']
        )
        fig_mare.update_yaxes(range=[0, 5.5])
        fig_mare.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_mare, use_container_width=True)

        st.table(dados_aluno)
