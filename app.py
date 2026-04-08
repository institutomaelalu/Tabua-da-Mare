import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Configuração de Estilo e Cabeçalho
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

COR_VERDE_INST = "#a8cf45"
COR_AZUL_INST = "#5cc6d0"

# --- BLOCO CSS (FONTE 12PX E CORES CORRIGIDAS) ---
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
    /* Cores das Salas */
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

# 2. Configurações Iniciais e CSVs Locais
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
        if secret_key:
            url_original = st.secrets["connections"]["gsheets"][secret_key]
            url_export = url_original.split("/edit")[0] + "/export?format=csv"
            if "gid=" in url_original:
                url_export += f"&gid={url_original.split('gid=')[1]}"
            df = pd.read_csv(url_export)
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # --- INTEGRAÇÃO COM CADASTRO LOCAL ---
            df_local = pd.read_csv(ALUNOS_FILE)
            if worksheet_name == "GERAL":
                df = pd.concat([df, df_local], ignore_index=True)
            else:
                sala_sufixo = worksheet_name.replace("SALA ", "")
                df_local_sala = df_local[df_local["TURMA"].str.contains(sala_sufixo, na=False, case=False)]
                df = pd.concat([df, df_local_sala], ignore_index=True)
            
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- FUNÇÃO DE RENDERIZAÇÃO COLORIDA ---
def render_styled_table(df, context_color=None):
    def get_row_class(row_val, context):
        val = (context if context else str(row_val)).upper()
        if 'ROSA' in val: return 'row-rosa'
        if 'AMARELA' in val: return 'row-amarela'
        if 'VERDE' in val: return 'row-verde'
        if 'AZUL' in val: return 'row-azul'
        if 'CIRAND' in val: return 'row-ciranda'
        return ''

    html = '<table class="custom-table"><thead><tr>'
    for col in df.columns: html += f'<th>{col}</th>'
    html += '</tr></thead><tbody>'
    
    for _, row in df.iterrows():
        row_class = get_row_class(row.get('TURMA', ''), context_color)
        html += f'<tr class="{row_class}">'
        for val in row:
            display_val = "" if pd.isna(val) else val
            html += f'<td>{display_val}</td>'
        html += '</tr>'
    
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)

# 4. Navegação Lateral (Ordem Ajustada)
menu = st.sidebar.radio("Navegação", [
    "👤 1. Novo Cadastro",
    "📝 2. Controle de Matrículas", 
    "🤝 3. Controle de Apadrinhamento",
    "📊 4. Avaliação - Tábua da Maré",
    "🌊 5. Tábua da Maré"
])

# --- 1. NOVO CADASTRO ---
if menu == "👤 1. Novo Cadastro":
    st.header("📝 Registro de Novo Aluno")
    with st.form("form_cad", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Nome Completo")
            i = st.text_input("Idade")
            comu = st.text_input("Comunidade")
        with c2:
            t = st.selectbox("Turma", ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"])
            tn = st.selectbox("Turno", ["MATUTINO", "VESPERTINO"])
        
        if st.form_submit_button("Salvar Registro"):
            if n:
                df_l = pd.read_csv(ALUNOS_FILE)
                pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
                st.success("Registrado!")

# --- 2. MATRÍCULAS (GERAL) ---
elif menu == "📝 2. Controle de Matrículas":
    st.header("📋 Quadro de Matrículas")
    df_raw = safe_read("GERAL")
    if not df_raw.empty:
        f1, f2 = st.columns(2)
        with f1: f_nome = st.text_input("Nome")
        with f2: f_turno = st.selectbox("Turno", ["Todos"] + sorted(list(df_raw["TURNO"].dropna().unique())))

        df_f = df_raw.copy()
        if f_nome: df_f = df_f[df_f["ALUNO"].str.contains(f_nome, case=False, na=False)]
        if f_turno != "Todos": df_f = df_f[df_f["TURNO"] == f_turno]

        cols = ["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]
        render_styled_table(df_f[cols].dropna(subset=["ALUNO"]))

# --- 3. APADRINHAMENTO ---
elif menu == "🤝 3. Controle de Apadrinhamento":
    st.header("🤝 Gestão de Apadrinhamento")
    sala_planilha = st.selectbox("Selecione a Sala:", ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"])
    df_s = safe_read(sala_planilha)
    
    if not df_s.empty:
        filtro_vazios = st.checkbox("Somente sem Padrinho")
        df_fs = df_s.copy()
        if filtro_vazios:
            df_fs = df_fs[df_fs["PADRINHO/MADRINHA"].isna() | (df_fs["PADRINHO/MADRINHA"].astype(str).str.strip() == "")]

        cols = ["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
        render_styled_table(df_fs[cols].dropna(subset=["ALUNO"]), context_color=sala_planilha)

# --- 4. AVALIAÇÃO ---
elif menu == "📊 4. Avaliação - Tábua da Maré":
    st.header("📊 Registro de Notas")
    df_g = safe_read("GERAL")
    if not df_g.empty:
        with st.form("notas_l"):
            al = st.selectbox("Aluno", sorted(df_g["ALUNO"].unique()))
            tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            sc = {c: st.slider(c, 1, 5, 3) for c in CATEGORIAS}
            if st.form_submit_button("Confirmar"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
                pd.concat([df_av, pd.DataFrame([[al, tr] + list(sc.values())], columns=["Aluno", "Trimestre"] + CATEGORIAS)], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Avaliação salva!")

# --- 5. PAINEL DE EVOLUÇÃO ---
elif menu == "🌊 5. Tábua da Maré":
    st.header("🌊 Evolução Individual")
    df_av = pd.read_csv(AVAL_FILE)
    if not df_av.empty:
        al_s = st.selectbox("Aluno", sorted(df_av["Aluno"].unique()))
        df_al = df_av[df_av["Aluno"] == al_s]
        tri_s = st.selectbox("Trimestre", df_al["Trimestre"].unique())
        row = df_al[df_al["Trimestre"] == tri_s].iloc[0]
        v = [float(row[c]) for c in CATEGORIAS]
        fig = go.Figure(go.Scatter(x=CATEGORIAS, y=v, mode='lines+markers', fill='tozeroy', line=dict(color=COR_AZUL_INST)))
        fig.update_layout(yaxis=dict(range=[0, 5.5]))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma avaliação encontrada.")
