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
    .row-ciranda {{ background-color: #3f51b5 !important; color: #ffffff !important; font-weight: 500; }} /* Azul Suave */
    </style>
    <div style='text-align: center;'>
        <h1 style='color: {COR_VERDE_INST}; font-size: 26px;'>Instituto Mãe Lalu</h1>
    </div>
    """, unsafe_allow_html=True)

# 2. Banco de Dados Local (CSVs)
ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"
PADRINHOS_LOCAL = "padrinhos_extra.csv" # Para salvar edições de padrinhos localmente

def init_db():
    if not os.path.exists(ALUNOS_FILE):
        pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE):
        pd.DataFrame(columns=["Aluno", "Trimestre", "Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]).to_csv(AVAL_FILE, index=False)
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
        
        # Integrar alunos cadastrados localmente
        df_local = pd.read_csv(ALUNOS_FILE)
        if worksheet_name == "GERAL":
            df = pd.concat([df, df_local], ignore_index=True)
        else:
            # Filtrar locais que pertencem à sala específica
            df_local_sala = df_local[df_local["TURMA"].str.contains(worksheet_name.replace("SALA ", ""), na=False, case=False)]
            df = pd.concat([df, df_local_sala], ignore_index=True)
            
        # Aplicar edições locais de padrinhos
        df_pad = pd.read_csv(PADRINHOS_LOCAL)
        for _, row_p in df_pad.iterrows():
            df.loc[df['ALUNO'] == row_p['ALUNO'], 'PADRINHO/MADRINHA'] = row_p['PADRINHO_EDITADO']
            
        return df
    except: return pd.DataFrame()

def render_styled_table(df, context=None):
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
        html += f'<tr class="{cl}">' + "".join([f'<td>{("" if pd.isna(v) else v)}</td>' for v in row]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# 4. Navegação
menu = st.sidebar.radio("Navegação", [
    "👤 1. Novo Cadastro (Local)",
    "📝 2. Controle de Matrículas (Geral)", 
    "🤝 3. Controle de Apadrinhamento",
    "📊 4. Avaliação - Tábua da Maré",
    "🌊 5. Tábua da Maré (Evolução)"
])

# --- ABA 1: NOVO CADASTRO ---
if menu == "👤 1. Novo Cadastro (Local)":
    st.header("📝 Registro de Novo Aluno")
    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo")
            idade = st.text_input("Idade (ex: 05 ANOS)")
            comu = st.text_input("Comunidade")
        with col2:
            turma = st.selectbox("Turma", ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"])
            turno = st.selectbox("Turno", ["MATUTINO", "VESPERTINO"])
        
        if st.form_submit_button("Finalizar Registro"):
            df_l = pd.read_csv(ALUNOS_FILE)
            novo = pd.DataFrame([[nome.upper(), turma, turno, idade, comu]], columns=df_l.columns)
            pd.concat([df_l, novo], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success(f"Aluno {nome} registrado e integrado ao sistema!")

# --- ABA 2: MATRÍCULAS GERAL ---
elif menu == "📝 2. Controle de Matrículas (Geral)":
    st.header("📋 Quadro Geral de Matrículas")
    df = safe_read("GERAL")
    if not df.empty:
        c1, c2 = st.columns(2)
        with c1: f_n = st.text_input("Buscar Nome")
        with c2: f_t = st.selectbox("Filtrar Turno", ["Todos", "MATUTINO", "VESPERTINO"])
        
        df_f = df.copy()
        if f_n: df_f = df_f[df_f["ALUNO"].str.contains(f_n, case=False, na=False)]
        if f_t != "Todos": df_f = df_f[df_f["TURNO"] == f_t]
        
        render_styled_table(df_f[["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]].dropna(subset=["ALUNO"]))

# --- ABA 3: APADRINHAMENTO ---
elif menu == "🤝 3. Controle de Apadrinhamento":
    st.header("🤝 Gestão de Apadrinhamento")
    sala = st.selectbox("Selecione a Sala", ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"])
    df = safe_read(sala)
    if not df.empty:
        check = st.checkbox("Mostrar apenas sem Padrinho/Madrinha")
        if check:
            df = df[df["PADRINHO/MADRINHA"].isna() | (df["PADRINHO/MADRINHA"].astype(str).str.strip() == "")]
        
        render_styled_table(df[["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]].dropna(subset=["ALUNO"]), context=sala)
        
        st.divider()
        st.subheader("✍️ Adicionar/Editar Padrinho")
        with st.form("edit_padrinho"):
            aluno_edit = st.selectbox("Selecione o Aluno", df["ALUNO"].unique())
            novo_pad = st.text_input("Nome do Padrinho/Madrinha")
            if st.form_submit_button("Salvar Padrinho"):
                df_p = pd.read_csv(PADRINHOS_LOCAL)
                df_p = df_p[df_p["ALUNO"] != aluno_edit] # Remove se já existia
                pd.concat([df_p, pd.DataFrame([[aluno_edit, novo_pad]], columns=df_p.columns)], ignore_index=True).to_csv(PADRINHOS_LOCAL, index=False)
                st.success("Informação atualizada!")
                st.rerun()

# --- ABA 4: AVALIAÇÃO ---
elif menu == "📊 4. Avaliação - Tábua da Maré":
    st.header("📊 Lançar Avaliação Trimestral")
    df_geral = safe_read("GERAL")
    if not df_geral.empty:
        with st.form("form_aval"):
            aluno = st.selectbox("Aluno", sorted(df_geral["ALUNO"].unique()))
            tri = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            cats = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
            notas = {c: st.slider(c, 1, 5, 3) for c in cats}
            if st.form_submit_button("Salvar Avaliação"):
                df_av = pd.read_csv(AVAL_FILE)
                # Remove duplicata se existir
                df_av = df_av[~((df_av["Aluno"] == aluno) & (df_av["Trimestre"] == tri))]
                nova_av = pd.DataFrame([[aluno, tri] + list(notas.values())], columns=df_av.columns)
                pd.concat([df_av, nova_av], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Avaliação registrada!")

# --- ABA 5: EVOLUÇÃO ---
elif menu == "🌊 5. Tábua da Maré (Evolução)":
    st.header("🌊 Tábua da Maré - Evolução Individual")
    df_av = pd.read_csv(AVAL_FILE)
    if df_av.empty: st.warning("Nenhuma avaliação registrada ainda.")
    else:
        al_sel = st.selectbox("Escolha o Aluno", df_av["Aluno"].unique())
        tri_sel = st.selectbox("Trimestre", df_av[df_av["Aluno"] == al_sel]["Trimestre"].unique())
        
        dados = df_av[(df_av["Aluno"] == al_sel) & (df_av["Trimestre"] == tri_sel)].iloc[0]
        cats = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
        notas = [float(dados[c]) for c in cats]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=cats, y=notas, mode='lines+markers', line=dict(color=COR_AZUL_INST, width=4), fill='tozeroy'))
        fig.update_layout(yaxis=dict(range=[0, 5.5]), height=400)
        st.plotly_chart(fig, use_container_width=True)
