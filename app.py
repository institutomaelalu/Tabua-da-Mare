import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Configuração de Estilo e Identidade Visual (Instituto Mãe Lalu)
st.set_page_config(page_title="Tábua da Maré - Instituto Mãe Lalu", layout="wide")

COR_VERDE = "#a8cf45"
COR_AZUL = "#5cc6d0"

st.markdown(f"""
    <div style='text-align: center; padding: 10px;'>
        <h1 style='margin-bottom: 0;'>
            <span style='color: {COR_VERDE};'>Instituto</span> 
            <span style='color: {COR_AZUL};'>Mãe</span> 
            <span style='color: {COR_VERDE};'>Lalu</span>
        </h1>
        <h3 style='color: {COR_AZUL}; font-weight: 300; margin-top: 0;'>🌊 Tábua da Maré</h3>
    </div>
    <hr style="border: 1px solid {COR_VERDE};">
    """, unsafe_allow_html=True)

# 2. Definição dos Critérios de Avaliação (Conforme solicitado)
CATEGORIAS = [
    "Frequência", 
    "Aprendizagem de leitura", 
    "Aprendizagem de escrita", 
    "Organização e cuidado com materiais", 
    "Participação e envolvimento", 
    "Respeito aos combinados", 
    "Clareza e desenvoltura", 
    "Interesse por coisas novas"
]

# Arquivos de dados
ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"

# Função para garantir que os arquivos existam com as colunas certas
def inicializar_arquivos():
    if not os.path.exists(ALUNOS_FILE):
        pd.DataFrame(columns=["Nome", "Idade", "Turno"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE):
        pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)

inicializar_arquivos()

# 3. Navegação Lateral
menu = st.sidebar.radio("Menu Principal", ["Painel de Evolução", "Registrar Aluno", "Lançar Avaliação"])

# --- ABA 1: REGISTRO MANUAL DE ALUNOS ---
if menu == "Registrar Aluno":
    st.header("📝 Registro de Alunos")
    with st.form("form_registro", clear_on_submit=True):
        nome = st.text_input("Nome Completo do Aluno")
        idade = st.number_input("Idade", min_value=0, max_value=100, value=7)
        turno = st.selectbox("Turno", ["Matutino", "Vespertino"])
        
        if st.form_submit_button("Salvar Registro"):
            if nome:
                df_alunos = pd.read_csv(ALUNOS_FILE)
                novo_aluno = pd.DataFrame([[nome, idade, turno]], columns=["Nome", "Idade", "Turno"])
                pd.concat([df_alunos, novo_aluno], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
                st.success(f"Aluno {nome} registrado com sucesso!")
            else:
                st.error("Por favor, digite o nome do aluno.")

# --- ABA 2: LANÇAMENTO DE NOTAS ---
elif menu == "Lançar Avaliação":
    st.header("📊 Verificação de Aprendizagem")
    try:
        df_alunos = pd.read_csv(ALUNOS_FILE)
    except:
        df_alunos = pd.DataFrame()

    if df_alunos.empty:
        st.info("Nenhum aluno cadastrado. Vá na aba 'Registrar Aluno'.")
    else:
        with st.form("form_notas"):
            aluno_escolhido = st.selectbox("Selecione o Aluno", df_alunos["Nome"].unique())
            trimestre = st.selectbox("Trimestre de Avaliação", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            
            st.write("Atribua uma nota de 1 a 5 para cada critério:")
            notas = {}
            col1, col2 = st.columns(2)
            for i, cat in enumerate(CATEGORIAS):
                with col1 if i < 4 else col2:
                    notas[cat] = st.slider(cat, 1, 5, 3)
            
            if st.form_submit_button("Salvar Avaliação"):
                df_av = pd.read_csv(AVAL_FILE)
                # Remove se já existir nota para o mesmo aluno/trimestre
                df_av = df_av[~((df_av['Aluno'] == aluno_escolhido) & (df_av['Trimestre'] == trimestre))]
                
                nova_linha = pd.DataFrame([[aluno_escolhido, trimestre] + list(notas.values())], 
                                         columns=["Aluno", "Trimestre"] + CATEGORIAS)
                
                pd.concat([df_av, nova_linha], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success(f"Avaliação do {trimestre} de {aluno_escolhido} salva!")

# --- ABA 3: PAINEL DE EVOLUÇÃO (DASHBOARD) ---
elif menu == "Painel de Evolução":
    try:
        df_alunos = pd.read_csv(ALUNOS_FILE)
        df_av = pd.read_csv(AVAL_FILE)
    except:
        df_alunos = pd.DataFrame()
        df_av = pd.DataFrame()

    if df_alunos.empty or df_av.empty:
        st.info("Aguardando registros de alunos e avaliações para gerar a Tábua da Maré.")
    else:
        # Filtros
        c1, c2, c3 = st.columns(3)
        with c1:
            turno_f = st.selectbox("Filtrar Turno", ["Matutino", "Vespertino"])
        
        # Filtra nomes baseados no turno
        nomes_turno = df_alunos[df_alunos["Turno"] == turno_f]["Nome"].unique()
        
        if len(nomes_turno) == 0:
            st.warning("Nenhum aluno cadastrado neste turno.")
        else:
            with c2:
                aluno_f = st.selectbox("Selecionar Aluno", nomes_turno)
            
            # Filtra trimestres disponíveis para esse aluno
            trims_f = df_av[df_av["Aluno"] == aluno_f]["Trimestre"].unique()
            
            if len(trims_f) == 0:
                st.warning("Este aluno ainda não possui avaliações lançadas.")
            else:
                with c3:
                    trim_f = st.selectbox("Escolha o Trimestre", trims_f)

                # Recupera os dados
                dados = df_av[(df_av["Aluno"] == aluno_f) & (df_av["Trimestre"] == trim_f)].iloc[0]
                valores = [dados[c] for c in CATEGORIAS]

                # --- GRÁFICO DE MARÉ (SENOIDAL SUAVE) ---
                st.subheader(f"🌊 Movimento da Maré: {aluno_f}")
                
                # Gerar curva suave (senoide)
                x_idx = np.arange(len(CATEGORIAS))
                x_smooth = np.linspace(0, len(CATEGORIAS) - 1, 300)
                y_smooth = np.interp(x_smooth, x_idx, valores)

                fig_wave = go.Figure()
                fig_wave.add_trace(go.Scatter(
                    x=x_smooth, y=y_smooth,
                    mode='lines',
                    line=dict(shape='spline', smoothing=1.5, width=6, color=COR_AZUL),
                    fill='tozeroy',
                    fillcolor=f"rgba(92, 198, 208, 0.2)",
                    name="Nível de Aprendizado"
                ))

                fig_wave.update_layout(
                    xaxis=dict(tickmode='array', tickvals=list(range(len(CATEGORIAS))), ticktext=CATEGORIAS),
                    yaxis=dict(range=[0, 5.5], title="Intensidade"),
                    plot_bgcolor='white', height=450
                )
                st.plotly_chart(fig_wave, use_container_width=True)

                # --- GRÁFICO RADAR ---
                st.divider()
                st.subheader("🕸️ Perfil de Competências (Radar)")
                fig_radar = go.Figure(go.Scatterpolar(
                    r=valores, theta=CATEGORIAS, fill='toself',
                    fillcolor=f"rgba(168, 207, 69, 0.4)",
                    line=dict(color=COR_VERDE)
                ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                    showlegend=False
                )
                st.plotly_chart(fig_radar, use_container_width=True)
