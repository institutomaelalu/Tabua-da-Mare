import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from scipy.interpolate import make_interp_spline
from streamlit_gsheets import GSheetsConnection

# 1. Configuração de Estilo e Identidade
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

COR_VERDE = "#a8cf45"
COR_AZUL = "#5cc6d0"

st.markdown(f"""
    <div style='text-align: center; padding: 10px;'>
        <h1 style='margin-bottom: 0;'>
            <span style='color: {COR_VERDE};'>Instituto</span> <span style='color: {COR_AZUL};'>Mãe</span> <span style='color: {COR_VERDE};'>Lalu</span>
        </h1>
        <h3 style='color: {COR_AZUL}; font-weight: 300; margin-top: 0;'>🌊 Sistema de Controle Integrado</h3>
    </div>
    <hr style="border: 1px solid {COR_VERDE};">
    """, unsafe_allow_html=True)

# 2. Configurações e Conexão
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
SALAS_APADRINHAMENTO = ["Sala Rosa", "Sala Amarela", "Sala Verde", "Sala Azul", "Cirand. Mundo"]

# Conexão com Google Sheets (URL deve estar nos Secrets do Streamlit Cloud)
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Navegação Lateral Estruturada
st.sidebar.title("Navegação")
# Aqui futuramente inseriremos a lógica de login para restringir estas opções
menu = st.sidebar.radio("Selecione o Canal:", [
    "🌊 Tábua da Maré (Evolução)", 
    "📝 Controle de Matrículas", 
    "🤝 Controle de Apadrinhamento",
    "📊 Lançar Avaliação"
])

# Carregamento Global de Dados
try:
    df_total = conn.read()
except:
    st.error("Erro ao conectar com a planilha. Verifique a URL nos Secrets.")
    st.stop()

# --- 1. TÁBUA DA MARÉ (Acompanhamento Alfabetização) ---
if menu == "🌊 Tábua da Maré (Evolução)":
    st.header("📈 Evolução de Alfabetização")
    
    # Filtro de alunos que já possuem alguma nota lançada
    df_notas = df_total[df_total[CATEGORIAS].sum(axis=1) > 0]
    
    if df_notas.empty:
        st.info("Ainda não há avaliações lançadas para os alunos.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            turno_sel = st.selectbox("Filtrar Turno", df_total["Turno"].unique())
        
        alunos_turno = df_notas[df_notas["Turno"] == turno_sel]
        
        if alunos_turno.empty:
            st.warning("Nenhum dado de evolução neste turno.")
        else:
            with c2:
                aluno_sel = st.selectbox("Selecionar Aluno", sorted(alunos_turno["Nome"].unique()))
            with c3:
                trims = alunos_turno[alunos_turno["Nome"] == aluno_sel]["Trimestre"].unique()
                trim_sel = st.selectbox("Trimestre", trims)

            dados = alunos_turno[(alunos_turno["Nome"] == aluno_sel) & (alunos_turno["Trimestre"] == trim_sel)].iloc[0]
            notas = [float(dados[c]) for c in CATEGORIAS]
            
            # Gráfico de Onda (Tábua da Maré)
            x = np.arange(len(CATEGORIAS))
            x_new = np.linspace(0, len(CATEGORIAS) - 1, 300) 
            spl = make_interp_spline(x, notas, k=3)
            y_smooth = np.clip(spl(x_new), 1, 5)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x_new, y=y_smooth, mode='lines', line=dict(shape='spline', width=6, color=COR_AZUL),
                                     fill='tozeroy', fillcolor=f"rgba(92, 198, 208, 0.2)", name="Maré"))
            fig.add_trace(go.Scatter(x=x, y=notas, mode='markers', marker=dict(size=10, color=COR_VERDE), name="Nota"))
            fig.update_layout(xaxis=dict(tickmode='array', tickvals=list(range(len(CATEGORIAS))), ticktext=CATEGORIAS),
                              yaxis=dict(range=[0, 5.5]), plot_bgcolor='white', height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# --- 2. CONTROLE DE MATRÍCULAS (Geral) ---
elif menu == "📝 Controle de Matrículas":
    st.header("📋 Cadastro Geral de Matrículas")
    
    aba_mat = st.tabs(["Listagem Geral", "Novo Cadastro"])
    
    with aba_mat[0]:
        # Exibe dados da coluna "GERAL" da sua planilha
        if "GERAL" in df_total.columns:
            st.write(f"Total de alunos matriculados: **{len(df_total['Nome'].unique())}**")
            st.dataframe(df_total[["Nome", "Idade", "Turno", "GERAL"]].drop_duplicates())
        else:
            st.warning("Coluna 'GERAL' não encontrada na planilha.")

    with aba_mat[1]:
        with st.form("form_matricula", clear_on_submit=True):
            n_nome = st.text_input("Nome Completo do Aluno")
            n_idade = st.number_input("Idade", 1, 18, 7)
            n_turno = st.selectbox("Turno de Matrícula", ["Matutino", "Vespertino"])
            n_geral = st.text_input("Status Geral (Ex: Ativo, Aguardando)")
            
            if st.form_submit_button("Finalizar Matrícula"):
                novo_reg = pd.DataFrame([{"Nome": n_nome, "Idade": n_idade, "Turno": n_turno, "GERAL": n_geral, "Trimestre": "Matrícula"}])
                df_up = pd.concat([df_total, novo_reg], ignore_index=True)
                conn.update(data=df_up)
                st.success("Aluno matriculado no sistema!")

# --- 3. CONTROLE DE APADRINHAMENTO (Salas) ---
elif menu == "🤝 Controle de Apadrinhamento":
    st.header("🤝 Gestão de Apadrinhamento por Salas")
    
    # KPIs de apadrinhamento
    c1, c2 = st.columns([1, 3])
    with c1:
        sala_foco = st.selectbox("Selecione a Sala", SALAS_APADRINHAMENTO)
    
    with c2:
        # Filtra os dados conforme a sala selecionada na planilha
        df_sala = df_total[df_total[sala_foco].notna()]
        st.subheader(f"Alunos na {sala_foco}")
        if not df_sala.empty:
            st.table(df_sala[["Nome", "ID_Padrinho", sala_foco]])
        else:
            st.info(f"Nenhum registro encontrado para a {sala_foco}.")

# --- MODULO DE LANÇAMENTO (ADMIN) ---
elif menu == "📊 Lançar Avaliação":
    st.header("📝 Lançamento de Evolução Pedagógica")
    aluno_nomes = sorted(df_total["Nome"].unique())
    
    with st.form("notas_evo", clear_on_submit=True):
        aluno = st.selectbox("Selecione o Aluno", aluno_nomes)
        trimestre = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
        
        st.write("Defina o nível (1 a 5) para cada critério:")
        col_a, col_b = st.columns(2)
        scores = {}
        for i, cat in enumerate(CATEGORIAS):
            with col_a if i < 4 else col_b:
                scores[cat] = st.select_slider(cat, options=[1, 2, 3, 4, 5], value=3)
        
        if st.form_submit_button("Salvar na Tábua da Maré"):
            # Pega as informações de matrícula do aluno para manter a linha completa
            info = df_total[df_total["Nome"] == aluno].iloc[0].to_dict()
            info.update(scores)
            info["Trimestre"] = trimestre
            
            # Remove registro anterior do mesmo trim para evitar duplicata
            df_total = df_total[~((df_total['Nome'] == aluno) & (df_total['Trimestre'] == trimestre))]
            
            df_final = pd.concat([df_total, pd.DataFrame([info])], ignore_index=True)
            conn.update(data=df_final)
            st.success(f"Evolução de {aluno} atualizada!")
