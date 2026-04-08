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

# --- BLOCO CSS (FONTE 12PX E CORES CORRIGIDAS) ---
st.markdown(f"""
    <style>
    .custom-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-family: 'Segoe UI', sans-serif;
        color: #31333F;
        border: 1px solid #e6e9ef;
        border-radius: 8px;
        overflow: hidden;
        font-size: 12px; /* Fonte reduzida */
        margin-top: 15px;
    }}
    .custom-table thead th {{
        background-color: #f0f2f6;
        color: #555;
        padding: 8px 12px;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #e6e9ef;
    }}
    .custom-table tbody td {{
        padding: 6px 12px;
        border-bottom: 1px solid #f0f2f6;
    }}
    /* Cores das Salas */
    .row-rosa {{ background-color: #ffeef2 !important; color: #d63384 !important; font-weight: 500; }}
    .row-amarela {{ background-color: #fff9db !important; color: #856404 !important; font-weight: 500; }}
    .row-verde {{ background-color: #ebfbee !important; color: #087f5b !important; font-weight: 500; }}
    .row-azul {{ background-color: #e7f5ff !important; color: #1971c2 !important; font-weight: 500; }}
    .row-ciranda {{ background-color: #1a237e !important; color: #ffffff !important; font-weight: 500; }}
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
        pd.DataFrame(columns=["Nome", "Idade", "Turno"]).to_csv(ALUNOS_FILE, index=False)
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
            df.columns = [str(c).strip() for c in df.columns]
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- FUNÇÃO DE RENDERIZAÇÃO COLORIDA ---
def render_styled_table(df, context_color=None):
    def get_row_class(row_val, context):
        # Prioriza o contexto da aba (Sala Selecionada) ou o valor na coluna Turma
        val = (context if context else str(row_val)).upper()
        if 'ROSA' in val: return 'row-rosa'
        if 'AMARELA' in val: return 'row-amarela'
        if 'VERDE' in val: return 'row-verde'
        if 'AZUL' in val: return 'row-azul'
        if 'CIRAND' in val: return 'row-ciranda'
        return ''

    html = '<table class="custom-table"><thead><tr>'
    for col in df.columns:
        html += f'<th>{col}</th>'
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

# 4. Navegação Lateral
menu = st.sidebar.radio("Menu de Navegação", [
    "🌊 Painel de Evolução", 
    "📝 Controle de Matrículas (GERAL)", 
    "🤝 Controle de Apadrinhamento",
    "👤 Cadastrar Aluno (Local)", 
    "📊 Lançar Avaliação (Local)"
])

# --- 1. PAINEL DE EVOLUÇÃO (Mantido) ---
if menu == "🌊 Painel de Evolução":
    st.info("Visualização gráfica dos dados locais de desempenho.")

# --- 2. MATRÍCULAS (GERAL) ---
elif menu == "📝 Controle de Matrículas (GERAL)":
    st.header("📋 Lista Geral de Alunos")
    df_raw = safe_read("GERAL")
    if not df_raw.empty:
        f1, f2, f3, f4 = st.columns(4)
        with f1: f_nome = st.text_input("Nome")
        with f2: f_turma = st.selectbox("Turma", ["Todas"] + sorted(list(df_raw["TURMA"].dropna().unique())))
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
        sf1, sf2, sf3 = st.columns([1, 1, 1])
        with sf1: f_turma_s = st.selectbox("Filtro Turma:", ["Todas"] + sorted(list(df_s["TURMA"].dropna().unique())))
        with sf2: f_nome_s = st.text_input("Buscar Aluno")
        with sf3: filtro_vazios = st.checkbox("Somente sem Padrinho")

        df_fs = df_s.copy()
        if f_turma_s != "Todas": df_fs = df_fs[df_fs["TURMA"] == f_turma_s]
        if f_nome_s: df_fs = df_fs[df_fs["ALUNO"].str.contains(f_nome_s, case=False, na=False)]
        
        if filtro_vazios:
            # Filtra nulos, vazios ou termos comuns de pendência
            df_fs = df_fs[df_fs["PADRINHO/MADRINHA"].isna() | 
                          (df_fs["PADRINHO/MADRINHA"].astype(str).str.strip() == "") |
                          (df_fs["PADRINHO/MADRINHA"].astype(str).str.contains("None|Pendente|-", case=False))]

        cols = ["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
        # Passa a aba selecionada para pintar a tabela inteira com a cor da sala
        render_styled_table(df_fs[cols].dropna(subset=["ALUNO"]), context_color=sala_planilha)

# --- 4 & 5. CADASTROS LOCAIS ---
elif menu == "👤 Cadastrar Aluno (Local)":
    st.header("📝 Novo Cadastro Local")
    with st.form("cad_l"):
        n, i, t = st.text_input("Nome"), st.number_input("Idade", 0, 20, 7), st.selectbox("Turno", ["Matutino", "Vespertino"])
        if st.form_submit_button("Salvar"):
            df = pd.read_csv(ALUNOS_FILE)
            pd.concat([df, pd.DataFrame([[n.strip(), i, t]], columns=["Nome", "Idade", "Turno"])], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Salvo com sucesso!")

elif menu == "📊 Lançar Avaliação (Local)":
    st.header("📊 Registro de Notas")
    df_al = pd.read_csv(ALUNOS_FILE)
    if not df_al.empty:
        with st.form("notas_l"):
            al, tr = st.selectbox("Aluno", sorted(df_al["Nome"].unique())), st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            sc = {c: st.slider(c, 1, 5, 3) for c in CATEGORIAS}
            if st.form_submit_button("Confirmar"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
                pd.concat([df_av, pd.DataFrame([[al, tr] + list(sc.values())], columns=["Aluno", "Trimestre"] + CATEGORIAS)], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Avaliação salva!")
