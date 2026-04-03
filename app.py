import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# Configuração da página
st.set_page_config(page_title="Tábua da Maré - Instituto Mãe Lalu", layout="wide")

# --- CABEÇALHO PERSONALIZADO ---
# Aplicando as cores: #a8cf45 (Instituto/Lalu) e #5cc6d0 (Mãe)
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

# --- BANCO DE DADOS (Simulado em CSV) ---
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

# --- CRITÉRIOS ---
CATEGORIAS = [
    "Frequência", "Leitura", "Escrita", "Materiais", 
    "Participação", "Regras", "Clareza", "Interesse"
]

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
            st.success(f"Aluno {nome} registrado no turno {turno}!")

# --- 2. AVALIAÇÃO ---
elif menu == "Lançar Avaliação":
    st.header("📊 Verificação de Aprendizagem")
    df_alunos = pd.read_csv(ALUNOS_FILE)
    
    if df_alunos.empty:
        st.warning("Por favor, cadastre um aluno primeiro.")
    else:
        with st.form("avaliacao"):
            aluno = st.selectbox("Selecione o Aluno", df_alunos["Nome"])
            trim = st.select_slider("Trimestre", options=["1º Trim", "2º Trim", "3º Trim"])
            
            st.write("Dê uma nota de 1 a 5 para cada critério:")
            crit = {}
            col1, col2 = st.columns(2)
            for i, c in enumerate(CATEGORIAS):
                with col1 if i < 4 else col2:
                    crit[c] = st.slider(c, 1, 5, 3)
            
            if st.form_submit_button("Registrar Maré"):
                df_av = pd.read_csv(AVAL_FILE)
                # Remove avaliação anterior do mesmo aluno/trimestre se existir para evitar duplicata
                df_av = df_av[~((df_av['Aluno'] == aluno) & (df_av['Trimestre'] == trim))]
                nova_av = pd.DataFrame([[aluno, trim] + list(crit.values())], columns=df_av.columns)
                pd.concat([df_av, nova_av]).to_csv(AVAL_FILE, index=False)
                st.info(f"Dados salvos: {aluno} - {trim}")

# --- 3. DASHBOARD (O MOVIMENTO DA MARÉ) ---
elif menu == "Painel de Evolução":
    df_av = pd.read_csv(AVAL_FILE)
    
    if df_av.empty:
        st.info("Aguardando lançamentos para gerar os gráficos.")
    else:
        aluno_sel = st.selectbox("Selecione o Aluno para análise", df_av["Aluno"].unique())
        # Ordenação correta dos trimestres
        df_aluno = df_av[df_av["Aluno"] == aluno_sel].copy()
        df_aluno['Ord'] = df_aluno['Trimestre'].map({"1º Trim": 1, "2º Trim": 2, "3º Trim": 3})
        df_aluno = df_aluno.sort_values('Ord')

        # --- GRÁFICO DE MARÉ (MÚLTIPLAS ONDAS) ---
        st.subheader("🌊 Movimento da Maré Individual")
        st.caption("Evolução de cada critério ao longo dos trimestres (pontas arredondadas)")
        
        fig_mare = go.Figure()
        cores_ondas = ['#5cc6d0', '#a8cf45', '#0077b6', '#90e0ef', '#72efdd', '#48cae4', '#b5e48c', '#d9ed92']
        
        for i, crit in enumerate(CATEGORIAS):
            fig_mare.add_trace(go.Scatter(
                x=df_aluno["Trimestre"], 
                y=df_aluno[crit],
                mode='lines+markers',
                name=crit,
                line=dict(shape='spline', smoothing=1.3, width=4, color=cores_ondas[i % len(cores_ondas)]),
                fill='tozeroy',
                opacity=0.3
            ))

        fig_mare.update_layout(
            yaxis=dict(range=[0, 5.5], title="Nível de Aprendizado"),
            xaxis=dict(title="Trimestre"),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_mare, use_container_width=True)

        # --- GRÁFICO DE RADAR ---
        st.divider()
        st.subheader("🕸️ Perfil por Trimestre (Radar)")
        
        col_rad1, col_rad2 = st.columns(2)
        trim_sel = st.selectbox("Escolha o Trimestre para o Radar", df_aluno["Trimestre"].unique())
        dados_trim = df_aluno[df_aluno["Trimestre"] == trim_sel].iloc[0]
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=[dados_trim[c] for c in CATEGORIAS],
            theta=CATEGORIAS,
            fill='toself',
            fillcolor='rgba(92, 198, 208, 0.5)',
            line=dict(color='#5cc6d0')
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            showlegend=False,
            title=f"Visão Geral: {trim_sel}"
        )
        st.plotly_chart(fig_radar, use_container_width=True)
