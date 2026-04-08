import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Configuração de Estilo e Cabeçalho
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

COR_VERDE_INST = "#a8cf45"
COR_AZUL_INST = "#5cc6d0"

st.markdown(f"""
    <style>
    .custom-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        font-family: 'Segoe UI', sans-serif; color: #31333F;
        border: 1px solid #e6e9ef; border-radius: 8px;
        overflow: hidden; font-size: 12px; margin-top: 15px;
    }}
    .custom-table thead th {{
        background-color: #f0f2f6; color: #555; padding: 8px 12px;
        text-align: left; font-weight: 600; border-bottom: 2px solid #e6e9ef;
    }}
    .custom-table tbody td {{ padding: 6px 12px; border-bottom: 1px solid #f0f2f6; }}
    .row-rosa {{ background-color: #ffeef2 !important; color: #d63384 !important; font-weight: 500; }}
    .row-amarela {{ background-color: #fff9db !important; color: #856404 !important; font-weight: 500; }}
    .row-verde {{ background-color: #ebfbee !important; color: #087f5b !important; font-weight: 500; }}
    .row-azul {{ background-color: #e7f5ff !important; color: #1971c2 !important; font-weight: 500; }}
    .row-ciranda {{ background-color: #3f51b5 !important; color: #ffffff !important; font-weight: 500; }}
    </style>
    
    <div style='text-align: center; padding: 5px;'>
        <h1 style='margin-bottom: 0; font-size: 26px;'>
            <span style='color: {COR_VERDE_INST};'>Instituto</span> <span style='color: {COR_AZUL_INST};'>Mãe</span> <span style='color: {COR_VERDE_INST};'>Lalu</span>
        </h1>
    </div>
    <hr style="border: 0.5px solid {COR_VERDE_INST}; margin: 10px 0;">
    """, unsafe_allow_html=True)

# 2. Bancos Locais
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"

def init_db():
    if not os.path.exists(ALUNOS_FILE):
        pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE):
        pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)

init_db()

# 3. Mapeamento Google Sheets
MAPA_LINKS = {
    "GERAL": "geral", "SALA ROSA": "sala_rosa", "SALA AMARELA": "sala_amarela",
    "SALA VERDE": "sala_verde", "SALA AZUL": "sala_azul", "CIRAND. MUNDO": "cirand_mundo"
}

def safe_read(worksheet_name):
    try:
        secret_key = MAPA_LINKS.get(worksheet_name)
        url_original = st.secrets["connections"]["gsheets"][secret_key]
        url_export = url_original.split("/edit")[0] + "/export?format=csv"
        if "gid=" in url_original:
            url_export += f"&gid={url_original.split('gid=')[1]}"
        df = pd.read_csv(url_export)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Unir com Local
        df_local = pd.read_csv(ALUNOS_FILE)
        if worksheet_name == "GERAL":
            df = pd.concat([df, df_local], ignore_index=True)
        else:
            sala_sufixo = worksheet_name.replace("SALA ", "")
            df_local_sala = df_local[df_local["TURMA"].str.contains(sala_sufixo, na=False, case=False)]
            df = pd.concat([df, df_local_sala], ignore_index=True)
        return df.fillna("")
    except:
        # Retorna DataFrame vazio com colunas padrão para evitar erros de filtro
        return pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])

def render_styled_table(df, context_color=None):
    if df.empty:
        st.warning("Nenhum dado para exibir.")
        return
    def get_row_class(row_val, context):
        val = (context if context else str(row_val)).upper()
        if 'ROSA' in val: return 'row-rosa'
        if 'AMARELA' in val: return 'row-amarela'
        if 'VERDE' in val: return 'row-verde'
        if 'AZUL' in val: return 'row-azul'
        if 'CIRAND' in val: return 'row-ciranda'
        return ''
    html = '<table class="custom-table"><thead><tr>' + "".join([f'<th>{c}</th>' for c in df.columns]) + '</tr></thead><tbody>'
    for _, row in df.iterrows():
        row_class = get_row_class(row.get('TURMA', ''), context_color)
        html += f'<tr class="{row_class}">' + "".join([f'<td>{("" if pd.isna(v) else v)}</td>' for v in row]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# 4. Navegação
menu = st.sidebar.radio("Navegação", ["👤 1. Novo Cadastro", "📝 2. Controle de Matrículas", "🤝 3. Controle de Apadrinhamento", "📊 4. Avaliação - Tábua da Maré", "🌊 5. Tábua da Maré"])

if menu == "👤 1. Novo Cadastro":
    st.header("📝 Registro de Novo Aluno")
    with st.form("f_cad"):
        c1, c2 = st.columns(2)
        with c1: n, i, comu = st.text_input("Nome"), st.text_input("Idade"), st.text_input("Comunidade")
        with c2: t, tn = st.selectbox("Turma", ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"]), st.selectbox("Turno", ["MATUTINO", "VESPERTINO"])
        if st.form_submit_button("Salvar"):
            df_l = pd.read_csv(ALUNOS_FILE)
            pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Salvo!")

elif menu == "📝 2. Controle de Matrículas":
    st.header("📋 Quadro de Matrículas")
    df = safe_read("GERAL")
    f1, f2 = st.columns(2)
    with f1: f_n = st.text_input("Filtrar Nome")
    with f2:
        opcoes_turno = ["Todos"] + sorted([str(x) for x in df["TURNO"].unique() if x]) if not df.empty else ["Todos"]
        f_t = st.selectbox("Filtrar Turno", opcoes_turno)
    
    df_f = df.copy()
    if f_n: df_f = df_f[df_f["ALUNO"].str.contains(f_n, case=False, na=False)]
    if f_t != "Todos": df_f = df_f[df_f["TURNO"] == f_t]
    render_styled_table(df_f[["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]])

elif menu == "🤝 3. Controle de Apadrinhamento":
    st.header("🤝 Gestão de Apadrinhamento")
    sala = st.selectbox("Selecione a Sala", ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"])
    df = safe_read(sala)
    check = st.checkbox("Somente sem Padrinho")
    df_f = df.copy()
    if check and "PADRINHO/MADRINHA" in df_f.columns:
        df_f = df_f[df_f["PADRINHO/MADRINHA"].astype(str).str.strip().isin(["", "nan", "None"])]
    
    cols = [c for c in ["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"] if c in df_f.columns]
    render_styled_table(df_f[cols], context_color=sala)

elif menu == "📊 4. Avaliação - Tábua da Maré":
    st.header("📊 Lançar Notas")
    df_g = safe_read("GERAL")
    # Correção do Erro de Redação/Tipo:
    if not df_g.empty and "ALUNO" in df_g.columns:
        lista_alunos = sorted([str(x) for x in df_g["ALUNO"].unique() if x])
        with st.form("f_av"):
            al = st.selectbox("Selecionar Aluno", lista_alunos)
            tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            notas = {c: st.slider(c, 1, 5, 3) for c in CATEGORIAS}
            if st.form_submit_button("Gravar"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
                pd.concat([df_av, pd.DataFrame([[al, tr] + list(notas.values())], columns=["Aluno", "Trimestre"] + CATEGORIAS)], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Gravado!")
    else:
        st.error("Dados da planilha não carregados corretamente.")

elif menu == "🌊 5. Tábua da Maré":
    st.header("🌊 Evolução")
    df_av = pd.read_csv(AVAL_FILE)
    if not df_av.empty:
        al_s = st.selectbox("Aluno", sorted(df_av["Aluno"].unique()))
        df_al = df_av[df_av["Aluno"] == al_s]
        tri_s = st.selectbox("Trimestre", df_al["Trimestre"].unique())
        row = df_al[df_al["Trimestre"] == tri_s].iloc[0]
        v = [float(row[c]) for c in CATEGORIAS]
        fig = go.Figure(go.Scatter(x=CATEGORIAS, y=v, mode='lines+markers', fill='tozeroy', line=dict(color=COR_AZUL_INST)))
        st.plotly_chart(fig, use_container_width=True)
