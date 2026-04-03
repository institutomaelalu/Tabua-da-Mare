import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Identidade Visual
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

# 2. Configuração de Critérios e Banco de Dados
CATEGORIAS = [
    "Frequência", "Aprendizagem de leitura", "Aprendizagem de escrita", 
    "Organização e cuidado com materiais", "Participação e envolvimento", 
    "Respeito aos combinados", "Clareza e desenvoltura", "Interesse por coisas novas"
]

ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"

def inicializar_arquivos():
    # Garantir arquivo de ALUNOS
    if not os.path.exists(ALUNOS_FILE):
        pd.DataFrame(columns=["Nome", "Idade", "Turno"]).to_csv(ALUNOS_FILE, index=False)
    else:
        df_check = pd.read_csv(ALUNOS_FILE)
        # Se a coluna 'Turno' não existir no arquivo salvo, nós a adicionamos
        if "Turno" not in df_check.columns:
            df_check["Turno"] = "Matutino" # Valor padrão para não quebrar
            df_check.to_csv(ALUNOS_FILE, index=False)

    # Garantir arquivo de AVALIAÇÕES
    if not os.path.exists(AVAL_FILE):
        pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)

inicializar_arquivos()

# 3. Menu
menu = st.sidebar.radio("Navegação", ["Painel de Evolução", "Registrar Aluno", "Lançar Avaliação"])

# --- REGISTRAR ALUNO ---
if menu == "Registrar Aluno":
    st.header("📝 Registro de Aluno")
    with st.form("form_reg", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        idade = st.number_input("Idade", 4, 18, 7)
        turno = st.selectbox("Turno", ["Matutino", "Vespertino"])
        if st.form_submit_button("Salvar Registro"):
            if nome:
                df = pd.read_csv(ALUNOS_FILE)
                novo = pd.DataFrame([[nome, idade, turno]], columns=["Nome", "Idade", "Turno"])
                pd.concat([df, novo], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
                st.success(f"{nome} cadastrado!")
            else:
                st.warning("Digite o nome.")

# --- LANÇAR NOTAS ---
elif menu == "Lançar Avaliação":
    st.header("📊 Lançar Avaliação")
    df_alunos = pd.read_csv(ALUNOS_FILE)
    if df_alunos.empty:
        st.info("Cadastre um aluno primeiro.")
    else:
        with st.form("form_notas"):
            aluno = st.selectbox("Aluno", df_alunos["Nome"].unique())
            trim = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            notas = {c: st.slider(c, 1, 5, 3) for c in CATEGORIAS}
            if st.form_submit_button("Salvar Notas"):
                df_av = pd.read_csv(AVAL_FILE)
                # Remove se já existir nota idêntica para atualizar
                df_av = df_av[~((df_av['Aluno'] == aluno) & (df_av['Trimestre'] == trim))]
                nova_nota = pd.DataFrame([[aluno, trim] + list(notas.values())], columns=["Aluno", "Trimestre"] + CATEGORIAS)
                pd.concat([df_av, nova_nota], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Notas salvas!")

# --- PAINEL DE EVOLUÇÃO (FILTROS) ---
elif menu == "Painel de Evolução":
    df_alunos = pd.read_csv(ALUNOS_FILE)
    df_av = pd.read_csv(AVAL_FILE)

    if df_alunos.empty:
        st.warning("Nenhum aluno registrado.")
    elif df_av.empty:
        st.info("Nenhuma avaliação lançada.")
    else:
        # Filtros encadeados
        col1, col2, col3 = st.columns(3)
        with col1:
            turno_f = st.selectbox("1. Filtrar Turno", ["Matutino", "Vespertino"])
        
        # Filtro de alunos do turno escolhido
        alunos_turno = df_alunos[df_alunos["Turno"] == turno_f]["Nome"].unique()
        
        if len(alunos_turno) == 0:
            st.error(f"Não há alunos no turno {turno_f}.")
        else:
            with col2:
                aluno_f = st.selectbox("2. Selecionar Aluno", alunos_turno)
            
            # Filtro de trimestres disponíveis para o aluno
            trims_aluno = df_av[df_av["Aluno"] == aluno_f]["Trimestre"].unique()
            
            if len(trims_aluno) == 0:
                st.error("Este aluno não tem avaliações.")
            else:
                with col3:
                    trim_f = st.selectbox("3. Escolha o Trimestre", trims_aluno)

                # DADOS E GRÁFICOS
                dados = df_av[(df_av["Aluno"] == aluno_f) & (df_av["Trimestre"] == trim_f)].iloc[0]
                valores = [dados[c] for c in CATEGORIAS]

                st.subheader(f"🌊 Maré: {aluno_f} - {trim_f}")
                
                # Gráfico Senoidal Suave
                x_idx = np.arange(len(CATEGORIAS))
                x_smooth = np.linspace(0, len(CATEGORIAS) - 1, 300)
                y_smooth = np.interp(x_smooth, x_idx, valores)

                fig_wave = go.Figure(go.Scatter(
                    x=x_smooth, y=y_smooth, mode='lines',
                    line=dict(shape='spline', smoothing=1.5, width=6, color=COR_AZUL),
                    fill='tozeroy', fillcolor=f"rgba(92, 198, 208, 0.2)"
                ))
                fig_wave.update_layout(
                    xaxis=dict(tickmode='array', tickvals=list(range(len(CATEGORIAS))), ticktext=CATEGORIAS),
                    yaxis=dict(range=[0, 5.5]), plot_bgcolor='white', height=400
                )
                st.plotly_chart(fig_wave, use_container_width=True)

                # Radar
                st.divider()
                fig_radar = go.Figure(go.Scatterpolar(
                    r=valores, theta=CATEGORIAS, fill='toself',
                    fillcolor=f"rgba(168, 207, 69, 0.4)", line=dict(color=COR_VERDE)
                ))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
                st.plotly_chart(fig_radar, use_container_width=True)
