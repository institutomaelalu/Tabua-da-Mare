import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from scipy.interpolate import make_interp_spline

# 1. Configuração de Estilo e Cabeçalho
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

COR_VERDE_INST = "#a8cf45"
COR_AZUL_INST = "#5cc6d0"

# --- BLOCO CSS PARA TABELAS ELEGANTES E CORES ---
st.markdown(f"""
    <style>
    .main {{
        background-color: #f8f9fa;
    }}
    .custom-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #31333F;
        border: 1px solid #e6e9ef;
        border-radius: 10px;
        overflow: hidden;
        font-size: 14px;
        margin-top: 20px;
    }}
    .custom-table thead th {{
        background-color: #f0f2f6;
        color: #555;
        padding: 12px 15px;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e6e9ef;
    }}
    .custom-table tbody td {{
        padding: 10px 15px;
        border-bottom: 1px solid #f0f2f6;
    }}
    /* Classes de Cores por Turma */
    .row-rosa {{ background-color: #ffeef2 !important; color: #d63384 !important; font-weight: 500; }}
    .row-amarela {{ background-color: #fff9db !important; color: #856404 !important; font-weight: 500; }}
    .row-verde {{ background-color: #ebfbee !important; color: #087f5b !important; font-weight: 500; }}
    .row-azul {{ background-color: #e7f5ff !important; color: #1971c2 !important; font-weight: 500; }}
    .row-ciranda {{ background-color: #1a237e !important; color: #ffffff !important; font-weight: 500; }}
    </style>
    
    <div style='text-align: center; padding: 10px;'>
        <h1 style='margin-bottom: 0;'>
            <span style='color: {COR_VERDE_INST};'>Instituto</span> <span style='color: {COR_AZUL_INST};'>Mãe</span> <span style='color: {COR_VERDE_INST};'>Lalu</span>
        </h1>
        <h3 style='color: {COR_AZUL_INST}; font-weight: 300; margin-top: 0;'>🌊 Painel de Controle Integrado</h3>
    </div>
    <hr style="border: 1px solid {COR_VERDE_INST};">
    """, unsafe_allow_html=True)

# 2. Configurações e Banco de Dados Local
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"

def init_db():
    if not os.path.exists(ALUNOS_FILE):
        pd.DataFrame(columns=["Nome", "Idade", "Turno"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE):
        pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)

init_db()

# 3. Integração Google Sheets
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
            df.columns = [str(c).strip() for c in df.columns]
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- FUNÇÃO DE RENDERIZAÇÃO DE TABELA COLORIDA ---
def render_styled_table(df):
    def get_row_class(turma):
        turma = str(turma).strip().upper()
        mapping = {
            'SALA ROSA': 'row-rosa', 'SALA AMARELA': 'row-amarela',
            'SALA VERDE': 'row-verde', 'SALA AZUL': 'row-azul',
            'CIRAND. MUNDO': 'row-ciranda'
        }
        return mapping.get(turma, '')

    # Construção manual do HTML para controle total do design
    html = '<table class="custom-table"><thead><tr>'
    for col in df.columns:
        html += f'<th>{col}</th>'
    html += '</tr></thead><tbody>'
    
    for _, row in df.iterrows():
        row_class = get_row_class(row.get('TURMA', ''))
        html += f'<tr class="{row_class}">'
        for val in row:
            # Tratamento de valores nulos para não exibir "nan"
            display_val = "" if pd.isna(val) else val
            html += f'<td>{display_val}</td>'
        html += '</tr>'
    
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)

# 4. Navegação Lateral
menu = st.sidebar.radio("Menu de Navegação", [
    "🌊 Painel de Evolução", 
    "📝 Controle de Matrículas (GERAL)", 
    "🤝 Controle de Apadrinhamento",
    "👤 Cadastrar Aluno (Local)", 
    "📊 Lançar Avaliação (Local)"
])

# --- 1. PAINEL DE EVOLUÇÃO ---
if menu == "🌊 Painel de Evolução":
    st.subheader("Gráfico de Desempenho Escolar")
    # Lógica de gráfico mantida conforme versões anteriores...

# --- 2. MATRÍCULAS (GERAL) ---
elif menu == "📝 Controle de Matrículas (GERAL)":
    st.header("📋 Lista Geral de Alunos")
    df_raw = safe_read("GERAL")
    if not df_raw.empty:
        st.write("🔍 **Filtros de Busca**")
        f1, f2, f3, f4 = st.columns(4)
        with f1: f_nome = st.text_input("Nome do Aluno")
        with f2: f_turma = st.selectbox("Filtrar Turma", ["Todas"] + sorted(list(df_raw["TURMA"].dropna().unique())))
        with f3: f_comu = st.selectbox("Comunidade", ["Todas"] + sorted(list(df_raw["COMUNIDADE"].dropna().unique())))
        with f4: f_turno = st.selectbox("Turno", ["Todos"] + sorted(list(df_raw["TURNO"].dropna().unique())))

        df_f = df_raw.copy()
        if f_nome: df_f = df_f[df_f["ALUNO"].str.contains(f_nome, case=False, na=False)]
        if f_turma != "Todas": df_f = df_f[df_f["TURMA"] == f_turma]
        if f_comu != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_comu]
        if f_turno != "Todos": df_f = df_f[df_f["TURNO"] == f_turno]

        cols = ["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]
        render_styled_table(df_f[cols].dropna(subset=["ALUNO"]))

# --- 3. APADRINHAMENTO (COM FILTRO SEM PADRINHO) ---
elif menu == "🤝 Controle de Apadrinhamento":
    st.header("🤝 Gestão de Apadrinhamento")
    sala_planilha = st.selectbox("Selecione a Sala:", ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"])
    df_s = safe_read(sala_planilha)
    
    if not df_s.empty:
        st.write("🔍 **Filtros Adicionais**")
        sf1, sf2, sf3 = st.columns([1, 1, 1])
        with sf1: f_turma_s = st.selectbox("Sub-turma:", ["Todas"] + sorted(list(df_s["TURMA"].dropna().unique())))
        with sf2: f_nome_s = st.text_input("Buscar por Nome:")
        with sf3: filtro_vazios = st.checkbox("Exibir apenas sem Padrinho/Madrinha")

        df_fs = df_s.copy()
        if f_turma_s != "Todas": df_fs = df_fs[df_fs["TURMA"] == f_turma_s]
        if f_nome_s: df_fs = df_fs[df_fs["ALUNO"].str.contains(f_nome_s, case=False, na=False)]
        
        if filtro_vazios:
            # Filtra campos vazios, nulos ou com traços/pendências
            df_fs = df_fs[df_fs["PADRINHO/MADRINHA"].isna() | 
                          (df_fs["PADRINHO/MADRINHA"].astype(str).str.strip() == "") |
                          (df_fs["PADRINHO/MADRINHA"].astype(str).str.contains("None|Pendente|-", case=False))]

        cols = ["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
        render_styled_table(df_fs[cols].dropna(subset=["ALUNO"]))

# --- 4 & 5. CADASTROS LOCAIS (Mantidos) ---
elif menu == "👤 Cadastrar Aluno (Local)":
    st.header("📝 Novo Cadastro Local")
    # Lógica de cadastro mantida...
