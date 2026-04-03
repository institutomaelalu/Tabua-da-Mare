import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# Configuração da página e Identidade Visual
st.set_page_config(page_title="Tábua da Maré - Instituto Mãe Lalu", layout="wide")

st.markdown(f"""
    <div style='text-align: center; padding: 10px;'>
        <h1 style='font-size: 45px; margin-bottom: 0;'>
            <span style='color: #a8cf45;'>Instituto</span> <span style='color: #5cc6d0;'>Mãe</span> <span style='color: #a8cf45;'>Lalu</span>
        </h1>
        <h2 style='color: #5cc6d0; font-weight: 300; margin-top: 0;'>🌊 Tábua da Maré: Acompanhamento Único</h2>
    </div>
    <hr style="border: 1px solid #a8cf45;">
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÕES DE DADOS ---
ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]

def init_db():
    if not os.path.exists(ALUNOS_FILE):
        pd.DataFrame(columns=["Nome", "Idade", "Turno"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE):
        pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)

init_db()

# --- MENU ---
menu = st.sidebar.radio("Navegação", ["Painel de Evolução", "Cadastrar Aluno", "Lançar Avaliação"])

# [Omissão das funções de cadastro e lançamento por brevidade - permanecem as mesmas]

if menu == "Painel de Evolução":
    df_av = pd.read_csv(AVAL_FILE)
    if not df_av.empty:
        aluno_sel = st.selectbox("Selecione o Aluno", df_av["Aluno"].unique())
        
        # Filtro de Trimestres (Multiselect para comparar)
        trims_sel = st.multiselect("Selecione os Trimestres para comparar", 
                                   ["1º Trim", "2º Trim", "3º Trim"], 
                                   default=df_av[df_av["Aluno"] == aluno_sel]["Trimestre"].unique())
        
        st.subheader(f"📊 Movimento da Maré: {aluno_sel}")
        
        fig = go.Figure()
        cores_trim = {"1º Trim": "#5cc6d0", "2º Trim": "#a8cf45", "3º Trim": "#0077b6"}
        
        for trim in trims_sel:
            df_trim = df_av[(df_av["Aluno"] == aluno_sel) & (df_av["Trimestre"] == trim)]
            
            if not df_trim.empty:
                notas = [df_trim.iloc[0][c] for c in CATEGORIAS]
                
                # Criando a curva suave (Interpolação para parecer onda de seno)
                x_indices = np.arange(len(CATEGORIAS))
                x_suave = np.linspace(0, len(CATEGORIAS) - 1, 200)
                y_suave = np.interp(x_suave, x_indices, notas)
                
                # Adicionando a linha da Maré
                fig.add_trace(go.Scatter(
                    x=x_suave, 
                    y=y_suave,
                    mode='lines',
                    name=trim,
                    line=dict(shape='spline', smoothing=1.3, width=5, color=cores_trim[trim]),
                    fill='tozeroy',
                    fillcolor=f"rgba{tuple(list(int(cores_trim[trim].lstrip('#')[j:j+2], 16) for j in (0, 2, 4)) + [0.1])}"
                ))

        fig.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=list(range(len(CATEGORIAS))),
                ticktext=CATEGORIAS,
                gridcolor='#eee'
            ),
            yaxis=dict(range=[0, 5.5], title="Nível de Desenvolvimento", gridcolor='#eee'),
            plot_bgcolor='white',
            height=500,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Gráfico Radar Individual de cada trimestre abaixo
        st.divider()
        st.subheader("🕸️ Ficha Individual (Radar)")
        cols = st.columns(len(trims_sel))
        for idx, trim in enumerate(trims_sel):
            with cols[idx]:
                df_trim = df_av[(df_av["Aluno"] == aluno_sel) & (df_av["Trimestre"] == trim)]
                fig_radar = go.Figure(go.Scatterpolar(
                    r=[df_trim.iloc[0][c] for c in CATEGORIAS],
                    theta=CATEGORIAS,
                    fill='toself',
                    fillcolor=f"rgba{tuple(list(int(cores_trim[trim].lstrip('#')[j:j+2], 16) for j in (0, 2, 4)) + [0.4])}",
                    line=dict(color=cores_trim[trim])
                ))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False, title=trim)
                st.plotly_chart(fig_radar, use_container_width=True)
    else:
        st.info("Nenhum dado lançado.")
