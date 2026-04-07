import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy.interpolate import make_interp_spline
from streamlit_gsheets import GSheetsConnection

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

# 2. Configuração de Critérios (Exatamente como as colunas da sua Planilha)
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]

# Conexão com Google Sheets
# Lembre-se de colocar a URL da planilha nos Secrets do Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Navegação Lateral
menu = st.sidebar.radio("Menu", ["Painel de Evolução", "Cadastrar Novo Aluno", "Lançar Avaliação"])

# --- MODULO DE CADASTRO ---
if menu == "Cadastrar Novo Aluno":
    st.header("📝 Novo Registro de Aluno")
    with st.form("cadastro", clear_on_submit=True):
        nome = st.text_input("Nome do Aluno")
        padrinho = st.text_input("ID do Padrinho / Madrinha (ex: padrinho_jose)")
        idade = st.number_input("Idade", 4, 15, 7)
        turno = st.selectbox("Turno", ["Matutino", "Vespertino"])
        
        if st.form_submit_button("Salvar Aluno"):
            if nome and padrinho:
                df_atual = conn.read()
                # Cria nova linha respeitando as colunas da sua planilha
                novo_aluno = pd.DataFrame([{
                    "Nome": nome.strip(),
                    "ID_Padrinho": padrinho.strip(),
                    "Idade": idade,
                    "Turno": turno,
                    "Trimestre": "Cadastro Inicial" # Preenchimento básico
                }])
                
                # Preenche as categorias com 0 ou vazio para o cadastro inicial
                for cat in CATEGORIAS:
                    novo_aluno[cat] = 0
                
                df_novo = pd.concat([df_atual, novo_aluno], ignore_index=True)
                conn.update(data=df_novo)
                st.success(f"Aluno {nome} registrado com sucesso!")
            else:
                st.error("Por favor, preencha o Nome e o ID do Padrinho.")

# --- MODULO DE LANÇAMENTO ---
elif menu == "Lançar Avaliação":
    st.header("📊 Lançar Notas de Desenvolvimento")
    df_total = conn.read()
    
    if df_total.empty:
        st.info("Nenhum aluno cadastrado.")
    else:
        with st.form("notas", clear_on_submit=True):
            # Busca nomes únicos na coluna 'Nome'
            aluno = st.selectbox("Selecione o Aluno", df_total["Nome"].unique())
            trim = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            
            st.write("---")
            scores = {c: st.slider(c, 1, 5, 3) for c in CATEGORIAS}
            
            if st.form_submit_button("Salvar Avaliação"):
                # Captura os dados fixos do aluno (padrinho, idade, turno) para manter a linha completa
                info_aluno = df_total[df_total["Nome"] == aluno].iloc[0]
                
                # Remove avaliação anterior do mesmo trimestre se existir para não duplicar
                df_total = df_total[~((df_total['Nome'] == aluno) & (df_total['Trimestre'] == trim))]
                
                nova_av = pd.DataFrame([{
                    "Nome": aluno,
                    "ID_Padrinho": info_aluno["ID_Padrinho"],
                    "Idade": info_aluno["Idade"],
                    "Turno": info_aluno["Turno"],
                    "Trimestre": trim,
                    **scores
                }])
                
                df_final = pd.concat([df_total, nova_av], ignore_index=True)
                conn.update(data=df_final)
                st.success(f"Avaliação de {aluno} enviada!")

# --- PAINEL DE EVOLUÇÃO (DASHBOARD) ---
elif menu == "Painel de Evolução":
    df_av = conn.read()
    
    # Filtra apenas linhas que possuem notas (maiores que 0) ou que não sejam apenas cadastro
    df_com_notas = df_av[df_av[CATEGORIAS].sum(axis=1) > 0]
    
    if df_com_notas.empty:
        st.info("Aguardando lançamentos de avaliações na planilha.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            turno_sel = st.selectbox("1. Filtrar Turno", df_av["Turno"].unique())
        
        avaliados_turno = df_com_notas[df_com_notas["Turno"] == turno_sel]
        
        if avaliados_turno.empty:
            st.warning("Nenhum aluno avaliado neste turno.")
        else:
            with c2:
                aluno_sel = st.selectbox("2. Selecionar Aluno", sorted(avaliados_turno["Nome"].unique()))
            with c3:
                trims = avaliados_turno[avaliados_turno["Nome"] == aluno_sel]["Trimestre"].unique()
                trim_sel = st.selectbox("3. Trimestre", trims)

            # Processamento da Maré
            dados = avaliados_turno[(avaliados_turno["Nome"] == aluno_sel) & (avaliados_turno["Trimestre"] == trim_sel)].iloc[0]
            notas = [float(dados[c]) for c in CATEGORIAS]
            
            x = np.arange(len(CATEGORIAS))
            x_new = np.linspace(0, len(CATEGORIAS) - 1, 300) 
            
            spl = make_interp_spline(x, notas, k=3)
            y_smooth = np.clip(spl(x_new), 1, 5)

            st.subheader(f"🌊 Tábua da Maré: {aluno_sel} ({trim_sel})")
            
            fig = go.Figure()
            # Onda
            fig.add_trace(go.Scatter(
                x=x_new, y=y_smooth, mode='lines',
                line=dict(shape='spline', width=6, color=COR_AZUL),
                fill='tozeroy', fillcolor=f"rgba(92, 198, 208, 0.2)",
                name="Maré"
            ))
            # Pontos
            fig.add_trace(go.Scatter(
                x=x, y=notas, mode='markers',
                marker=dict(size=10, color=COR_VERDE),
                name="Nota"
            ))

            fig.update_layout(
                xaxis=dict(tickmode='array', tickvals=list(range(len(CATEGORIAS))), ticktext=CATEGORIAS),
                yaxis=dict(range=[0, 5.5], gridcolor="#f0f0f0"),
                plot_bgcolor='white', height=400, showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

            # Radar Visual
            st.divider()
            fig_radar = go.Figure(go.Scatterpolar(
                r=notas, theta=CATEGORIAS, fill='toself', 
                fillcolor='rgba(168, 207, 69, 0.4)', 
                line=dict(color=COR_VERDE)
            ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False)
            st.plotly_chart(fig_radar, use_container_width=True)
