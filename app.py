import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
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

# --- CADASTRO E LANÇAMENTO (Simplificados para focar no gráfico) ---
if menu == "Cadastrar Aluno":
    st.header("📝 Registro do Aluno")
    with st.form("cadastro"):
        nome = st.text_input("Nome Completo")
        idade = st.number_input("Idade", 4, 12)
        turno = st.selectbox("Turno", ["Matutino", "Vespertino"])
        if st.form_submit_button("Salvar Registro"):
            df = pd.read_csv(ALUNOS_FILE)
            pd.concat([df, pd.DataFrame([[nome, idade, turno]], columns=df.columns)]).to_csv(ALUNOS_FILE, index=False)
            st.success("Aluno registrado!")

elif menu == "Lançar Avaliação":
    st.header("📊 Verificação de Aprendizagem")
    df_alunos = pd.read_csv(ALUNOS_FILE)
    if not df_alunos.empty:
        with st.form("avaliacao"):
            aluno = st.selectbox("Aluno", df_alunos["Nome"])
            trim = st.selectbox("Trimestre", ["1º Trim", "2º Trim", "3º Trim"])
            crit = {c: st.slider(c, 1, 5, 3) for c in CATEGORIAS}
            if st.form_submit_button("Registrar"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == aluno) & (df_av['Trimestre'] == trim))]
                pd.concat([df_av, pd.DataFrame([[aluno, trim] + list(crit.values())], columns=df_av.columns)]).to_csv(AVAL_FILE, index=False)
                st.success("Avaliação salva!")

# --- O QUE VOCÊ PRECISA: GRÁFICO DE ONDAS REAIS ---
elif menu == "Painel de Evolução":
    df_av = pd.read_csv(AVAL_FILE)
    if not df_av.empty:
        aluno_sel = st.selectbox("Selecione o Aluno", df_av["Aluno"].unique())
        trim_sel = st.radio("Selecione o Trimestre para Visualizar a Maré", ["1º Trim", "2º Trim", "3º Trim"], horizontal=True)
        
        df_aluno = df_av[(df_av["Aluno"] == aluno_sel) & (df_av["Trimestre"] == trim_sel)]
        
        if not df_aluno.empty:
            st.subheader(f"🌊 Tábua da Maré: {aluno_sel} ({trim_sel})")
            
            fig_mare = go.Figure()
            x = np.linspace(0, 10, 500) # O "comprimento" do mar
            
            cores = ['#5cc6d0', '#a8cf45', '#0077b6', '#00b4d8', '#90e0ef', '#72efdd', '#48cae4', '#b5e48c']
            
            for i, crit in enumerate(CATEGORIAS):
                nota = df_aluno.iloc[0][crit]
                # Criando a função seno: Amplitude baseada na nota, fase deslocada para não encavalar
                y = (nota / 2) * np.sin(x + i*0.8) + (nota / 2)
                
                fig_mare.add_trace(go.Scatter(
                    x=x, y=y,
                    mode='lines',
                    name=f"{crit}: {nota}",
                    line=dict(width=3, color=cores[i % len(cores)]),
                    fill='tozeroy',
                    fillcolor=f"rgba{tuple(list(int(cores[i % len(cores)].lstrip('#')[j:j+2], 16) for j in (0, 2, 4)) + [0.15])}",
                    hoverinfo='name'
                ))
            
            fig_mare.update_layout(
                xaxis=dict(visible=False),
                yaxis=dict(range=[0, 6], title="Nível da Maré", gridcolor="#eee"),
                plot_bgcolor='white',
                height=500,
                legend=dict(orientation="h", y=-0.1),
                margin=dict(l=0, r=0, t=20, b=0)
            )
            st.plotly_chart(fig_mare, use_container_width=True)
            
            # Gráfico Radar para comparar
            st.divider()
            st.subheader("🕸️ Gráfico Radar (Ficha Individual)")
            fig_radar = go.Figure(go.Scatterpolar(
                r=[df_aluno.iloc[0][c] for c in CATEGORIAS],
                theta=CATEGORIAS,
                fill='toself',
                fillcolor='rgba(168, 207, 69, 0.4)',
                line=dict(color='#a8cf45')
            ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("Nenhuma avaliação encontrada para este trimestre.")
