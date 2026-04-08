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
    <div style='text-align: center;'>
        <h1 style='color: {COR_VERDE_INST}; font-size: 26px;'>Instituto Mãe Lalu</h1>
    </div>
    """, unsafe_allow_html=True)

# 2. Banco de Dados Local
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"
PADRINHOS_LOCAL = "padrinhos_extra.csv"

def init_db():
    if not os.path.exists(ALUNOS_FILE):
        pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE):
        pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)
    if not os.path.exists(PADRINHOS_LOCAL):
        pd.DataFrame(columns=["ALUNO", "PADRINHO_EDITADO"]).to_csv(PADRINHOS_LOCAL, index=False)

init_db()

# 3. Funções de Dados
MAPA_LINKS = {
    "GERAL": "geral", "SALA ROSA": "sala_rosa", "SALA AMARELA": "sala_amarela",
    "SALA VERDE": "sala_verde", "SALA AZUL": "sala_azul", "CIRAND. MUNDO": "cirand_mundo"
}

def safe_read(worksheet_name):
    try:
        secret_key = MAPA_LINKS.get(worksheet_name)
        url_original = st.secrets["connections"]["gsheets"][secret_key]
        url_export = url_original.split("/edit")[0] + "/export?format=csv"
        if "gid=" in url_original: url_export += f"&gid={url_original.split('gid=')[1]}"
        
        df = pd.read_csv(url_export)
        df.columns = [str(c).strip().upper() for c in df.columns]
        df = df.dropna(subset=["ALUNO"]) # Remove linhas fantasmas sem nome
        
        # Integrar locais
        df_local = pd.read_csv(ALUNOS_FILE)
        if worksheet_name == "GERAL":
            df = pd.concat([df, df_local], ignore_index=True)
        else:
            sala_clean = worksheet_name.replace("SALA ", "")
            df_local_sala = df_local[df_local["TURMA"].str.contains(sala_clean, na=False, case=False)]
            df = pd.concat([df, df_local_sala], ignore_index=True)
            
        # Padrinhos
        df_pad = pd.read_csv(PADRINHOS_LOCAL)
        if 'PADRINHO/MADRINHA' not in df.columns: df['PADRINHO/MADRINHA'] = ""
        for _, row_p in df_pad.iterrows():
            df.loc[df['ALUNO'] == row_p['ALUNO'], 'PADRINHO/MADRINHA'] = row_p['PADRINHO_EDITADO']
            
        return df.fillna("")
    except:
        return pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])

def render_styled_table(df, context=None):
    if df.empty:
        st.info("Nenhum dado encontrado para os filtros atuais.")
        return
    
    def get_class(val, ctx):
        v = (ctx if ctx else str(val)).upper()
        if 'ROSA' in v: return 'row-rosa'
        if 'AMARELA' in v: return 'row-amarela'
        if 'VERDE' in v: return 'row-verde'
        if 'AZUL' in v: return 'row-azul'
        if 'CIRAND' in v: return 'row-ciranda'
        return ''

    html = '<table class="custom-table"><thead><tr>' + "".join([f'<th>{c}</th>' for c in df.columns]) + '</tr></thead><tbody>'
    for _, row in df.iterrows():
        cl = get_class(row.get('TURMA', ''), context)
        html += f'<tr class="{cl}">' + "".join([f'<td>{v}</td>' for v in row]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# 4. Navegação
menu = st.sidebar.radio("Navegação", [
    "👤 1. Novo Cadastro",
    "📝 2. Controle de Matrículas", 
    "🤝 3. Controle de Apadrinhamento",
    "📊 4. Avaliação - Tábua da Maré",
    "🌊 5. Tábua da Maré"
])

# --- ABA 1 ---
if menu == "👤 1. Novo Cadastro":
    st.header("📝 Registro de Novo Aluno")
    with st.form("cad_l", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            n, i, comu = st.text_input("Nome Completo"), st.text_input("Idade"), st.text_input("Comunidade")
        with c2:
            t = st.selectbox("Turma", ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"])
            tn = st.selectbox("Turno", ["MATUTINO", "VESPERTINO"])
        if st.form_submit_button("Salvar Registro"):
            df_l = pd.read_csv(ALUNOS_FILE)
            pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Salvo!")
            st.rerun()

# --- ABA 2 ---
elif menu == "📝 2. Controle de Matrículas":
    st.header("📋 Quadro de Matrículas")
    df = safe_read("GERAL")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1: f_n = st.text_input("Buscar por Nome")
    with col_f2:
        # Filtro de Turno Blindado
        opcoes = ["Todos"] + sorted([str(x) for x in df["TURNO"].unique() if x and str(x).strip() != ""])
        f_t = st.selectbox("Filtrar Turno", opcoes)

    df_f = df.copy()
    if f_n: df_f = df_f[df_f["ALUNO"].str.contains(f_n, case=False, na=False)]
    if f_t != "Todos": df_f = df_f[df_f["TURNO"] == f_t]
    
    render_styled_table(df_f[["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]])

# --- ABA 3 ---
elif menu == "🤝 3. Controle de Apadrinhamento":
    st.header("🤝 Gestão de Apadrinhamento")
    sala_sel = st.selectbox("Selecione a Sala", ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"])
    df = safe_read(sala_sel)
    
    check = st.checkbox("Somente sem Padrinho")
    df_f = df.copy()
    if check:
        df_f = df_f[df_f["PADRINHO/MADRINHA"].astype(str).str.strip().isin(["", "None", "nan"])]
    
    render_styled_table(df_f[["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]], context=sala_sel)
    
    if not df.empty:
        st.divider()
        with st.form("edit_p"):
            al_edit = st.selectbox("Selecione o Aluno para atualizar padrinho", sorted([str(x) for x in df["ALUNO"].unique() if x]))
            novo_p = st.text_input("Novo Padrinho/Madrinha")
            if st.form_submit_button("Atualizar Dados"):
                df_p = pd.read_csv(PADRINHOS_LOCAL)
                df_p = df_p[df_p["ALUNO"] != al_edit]
                pd.concat([df_p, pd.DataFrame([[al_edit, novo_p]], columns=df_p.columns)], ignore_index=True).to_csv(PADRINHOS_LOCAL, index=False)
                st.success("Atualizado!")
                st.rerun()

# --- ABA 4 ---
elif menu == "📊 4. Avaliação - Tábua da Maré":
    st.header("📊 Registro de Notas")
    df_g = safe_read("GERAL")
    lista = sorted([str(x) for x in df_g["ALUNO"].unique() if x])
    if lista:
        with st.form("av"):
            al, tr = st.selectbox("Aluno", lista), st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            notas = {c: st.slider(c, 1, 5, 3) for c in CATEGORIAS}
            if st.form_submit_button("Salvar"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
                pd.concat([df_av, pd.DataFrame([[al, tr] + list(notas.values())], columns=["Aluno", "Trimestre"] + CATEGORIAS)], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Salvo!")

# --- ABA 5 ---
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
