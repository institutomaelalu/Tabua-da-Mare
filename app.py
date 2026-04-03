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

# 2. Definição Absoluta dos Critérios (Baseado no seu Excel)
CATEGORIAS = [
    "Aprendizagem de Leitura e Escrita",
    "Organização e cuidado com os materiais de uso individual ou coletivo",
    "Participação, resolução e envolvimento nas atividades propostas",
    "Respeito aos combinados/regras",
    "Pergunta e responde questões com clareza e desenvoltura",
    "Compartilha materiais, brinquedos, jogos, etc.",
    "Demonstra interesse por coisas novas",
    "Participa de atividades em grupo com respeito, opinião própria, liderança e proatividade"
]

ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"

# FUNÇÃO CRÍTICA: Cria os arquivos se não existirem no GitHub/Streamlit
def verificar_banco_de_dados():
    # Verifica arquivo de Alunos
    if not os.path.exists(ALUNOS_FILE):
        df_init_alunos = pd.DataFrame(columns=["Nome", "Idade", "Turno"])
        df_init_alunos.to_csv(ALUNOS_FILE, index=False)
    
    # Verifica arquivo de Avaliações
    if not os.path.exists(AVAL_FILE):
        df_init_aval = pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS)
        df_init_aval.to_csv(AVAL_FILE, index=False)
    else:
        # Se existir, garante que as colunas estão certas (Auto-correção)
        df_temp = pd.read_csv(AVAL_FILE)
        if "Aluno" not in df_temp.columns:
            pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)

verificar_banco_de_dados()

# 3. Navegação
menu = st.sidebar.radio("Navegação", ["Painel de Evolução", "Registrar Aluno", "Lançar Avaliação"])

# --- ABA: REGISTRAR ALUNO ---
if menu == "Registrar Aluno":
    st.header("📝 Registro de Aluno")
    with st.form("form_reg", clear_on_submit=True):
        nome = st.text_input("Nome Completo")
        idade = st.number_input("Idade", 4, 18, 7)
        turno = st.selectbox("Turno", ["Matutino", "Vespertino"])
        if st.form_submit_button("Salvar Registro"):
            if nome:
                df = pd.read_csv(ALUNOS_FILE)
                # Limpa espaços extras no nome
                novo = pd.DataFrame([[nome.strip(), idade, turno]], columns=["Nome", "Idade", "Turno"])
                pd.concat([df, novo], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
                st.success(f"Aluno {nome} registrado!")
            else:
                st.warning("O nome não pode estar vazio.")

# --- ABA: LANÇAR NOTAS ---
elif menu == "Lançar Avaliação":
    st.header("📊 Lançar Avaliação")
    df_alunos = pd.read_csv(ALUNOS_FILE)
    
    if df_alunos.empty:
        st.info("Nenhum aluno cadastrado. Vá em 'Registrar Aluno' primeiro.")
    else:
        with st.form("form_notas"):
            aluno = st.selectbox("Aluno", sorted(df_alunos["Nome"].unique()))
            trim = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            
            st.write("---")
            notas = {}
            for c in CATEGORIAS:
                notas[c] = st.slider(c, 1, 5, 3)
            
            if st.form_submit_button("Salvar Avaliação"):
                df_av = pd.read_csv(AVAL_FILE)
                # Remove avaliação antiga se existir para evitar duplicata
                df_av = df_av[~((df_av['Aluno'] == aluno) & (df_av['Trimestre'] == trim))]
                
                nova_nota = pd.DataFrame([[aluno, trim] + list(notas.values())], 
                                         columns=["Aluno", "Trimestre"] + CATEGORIAS)
                
                pd.concat([df_av, nova_nota], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success(f"Notas de {aluno} salvas com sucesso!")

# --- ABA: PAINEL DE EVOLUÇÃO ---
elif menu == "Painel de Evolução":
    df_alunos = pd.read_csv(ALUNOS_FILE)
    df_av = pd.read_csv(AVAL_FILE)

    if df_alunos.empty or df_av.empty:
        st.info("Aguardando registros e avaliações para gerar os gráficos.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            turno_f = st.selectbox("1. Turno", ["Matutino", "Vespertino"])
        
        alunos_do_turno = df_alunos[df_alunos["Turno"] == turno_f]["Nome"].unique()
        
        if len(alunos_do_turno) == 0:
            st.warning(f"Sem alunos no turno {turno_f}.")
        else:
            with col2:
                aluno_f = st.selectbox("2. Aluno", sorted(alunos_do_turno))
            
            trims_disponiveis = df_av[df_av["Aluno"] == aluno_f]["Trimestre"].unique()
            
            if len(trims_disponiveis) == 0:
                st.error("Este aluno ainda não possui avaliações.")
            else:
                with col3:
                    trim_f = st.selectbox("3. Trimestre", trims_disponiveis)

                # Coleta de dados para o gráfico
                dados_aluno = df_av[(df_av["Aluno"] == aluno_f) & (df_av["Trimestre"] == trim_f)].iloc[0]
                valores = [dados_aluno[c] for c in CATEGORIAS]

                # --- GRÁFICO DE MARÉ (SENOIDAL) ---
                st.subheader(f"🌊 Maré: {aluno_f}")
                
                x_idx = np.arange(len(CATEGORIAS))
                x_smooth = np.linspace(0, len(CATEGORIAS) - 1, 300)
                y_smooth = np.interp(x_smooth, x_idx, valores)

                fig_wave = go.Figure(go.Scatter(
                    x=x_smooth, y=y_smooth, mode='lines',
                    line=dict(shape='spline', smoothing=1.3, width=6, color=COR_AZUL),
                    fill='tozeroy', fillcolor=f"rgba(92, 198, 208, 0.2)"
                ))
                
                # Nomes curtos para o eixo X
                labels_x = [c[:15]+"..." for c in CATEGORIAS]
                
                fig_wave.update_layout(
                    xaxis=dict(tickmode='array', tickvals=list(range(len(CATEGORIAS))), ticktext=labels_x),
                    yaxis=dict(range=[0, 5.5]), plot_bgcolor='white', height=400
                )
                st.plotly_chart(fig_wave, use_container_width=True)

                # --- RADAR ---
                st.divider()
                fig_radar = go.Figure(go.Scatterpolar(
                    r=valores, theta=CATEGORIAS, fill='toself',
                    fillcolor=f"rgba(168, 207, 69, 0.4)", line=dict(color=COR_VERDE)
                ))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
                st.plotly_chart(fig_radar, use_container_width=True)
