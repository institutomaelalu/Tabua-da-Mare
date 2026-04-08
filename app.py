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
    
    /* Estilo para botões de rádio horizontais (Turmas) */
    div.stButton > button {{ width: 100%; border-radius: 20px; }}
    </style>
    <div style='text-align: center; padding: 5px;'>
        <h1 style='margin-bottom: 0; font-size: 26px;'>
            <span style='color: {COR_VERDE_INST};'>Instituto</span> <span style='color: {COR_AZUL_INST};'>Mãe</span> <span style='color: {COR_VERDE_INST};'>Lalu</span>
        </h1>
    </div>
    <hr style="border: 0.5px solid {COR_VERDE_INST}; margin: 10px 0;">
    """, unsafe_allow_html=True)

# 2. Configurações de Dados
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"
PADRINHOS_FILE = "padrinhos_local.csv"

def init_db():
    for f, cols in {ALUNOS_FILE: ["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"], 
                    AVAL_FILE: ["Aluno", "Trimestre"] + CATEGORIAS,
                    PADRINHOS_FILE: ["ALUNO", "PADRINHO_EDITADO"]}.items():
        if not os.path.exists(f): pd.DataFrame(columns=cols).to_csv(f, index=False)

init_db()

MAPA_LINKS = {
    "GERAL": "geral", "SALA ROSA": "sala_rosa", "SALA AMARELA": "sala_amarela",
    "SALA VERDE": "sala_verde", "SALA AZUL": "sala_azul", "CIRAND. MUNDO": "cirand_mundo"
}

def safe_read(worksheet_name):
    try:
        secret_key = MAPA_LINKS.get(worksheet_name)
        url = st.secrets["connections"]["gsheets"][secret_key].split("/edit")[0] + "/export?format=csv"
        if "gid=" in st.secrets["connections"]["gsheets"][secret_key]:
            url += f"&gid={st.secrets['connections']['gsheets'][secret_key].split('gid=')[1]}"
        
        df = pd.read_csv(url)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Unir com Local e Padrinhos Editados
        df_local = pd.read_csv(ALUNOS_FILE)
        df_pad = pd.read_csv(PADRINHOS_FILE)
        
        full_df = pd.concat([df, df_local], ignore_index=True) if worksheet_name == "GERAL" else \
                  pd.concat([df, df_local[df_local["TURMA"].str.contains(worksheet_name.replace("SALA ", ""), na=False, case=False)]], ignore_index=True)
        
        if "ALUNO" in full_df.columns:
            for _, row_p in df_pad.iterrows():
                full_df.loc[full_df["ALUNO"] == row_p["ALUNO"], "PADRINHO/MADRINHA"] = row_p["PADRINHO_EDITADO"]
        
        return full_df.fillna("")
    except:
        return pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])

def render_styled_table(df, context_color=None):
    if df.empty: return st.info("Sem dados para os filtros selecionados.")
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
        html += f'<tr class="{row_class}">' + "".join([f'<td>{v}</td>' for v in row]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# 4. Navegação
menu = st.sidebar.radio("Navegação", ["👤 Novo Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Avaliação", "🌊 Evolução"])

# --- ABA 1: NOVO CADASTRO ---
if menu == "👤 Novo Cadastro":
    st.header("📝 Registro de Novo Aluno")
    with st.form("cad"):
        c1, c2 = st.columns(2)
        with c1: n, i, comu = st.text_input("Nome"), st.text_input("Idade"), st.text_input("Comunidade")
        with c2: t, tn = st.selectbox("Turma", ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"]), st.selectbox("Turno", ["MATUTINO", "VESPERTINO"])
        if st.form_submit_button("Salvar"):
            df_l = pd.read_csv(ALUNOS_FILE)
            pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Salvo!")

# --- ABA 2: MATRÍCULAS ---
elif menu == "📝 Matrículas":
    st.header("📋 Quadro de Matrículas")
    df = safe_read("GERAL")
    
    # Filtros em Colunas
    f1, f2, f3 = st.columns(3)
    with f1: f_turma = st.selectbox("Turma", ["Todas"] + sorted([x for x in df["TURMA"].unique() if x]))
    with f2: f_turno = st.selectbox("Turno", ["Todos"] + sorted([x for x in df["TURNO"].unique() if x]))
    with f3: f_comu = st.selectbox("Comunidade", ["Todas"] + sorted([x for x in df["COMUNIDADE"].unique() if x]))
    
    df_f = df.copy()
    if f_turma != "Todas": df_f = df_f[df_f["TURMA"] == f_turma]
    if f_turno != "Todos": df_f = df_f[df_f["TURNO"] == f_turno]
    if f_comu != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_comu]
    
    render_styled_table(df_f[["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]])

# --- ABA 3: APADRINHAMENTO ---
elif menu == "🤝 Apadrinhamento":
    st.header("🤝 Gestão de Apadrinhamento")
    
    # Botões coloridos para Turmas
    st.write("Selecione a Sala:")
    c_rosa, c_ama, c_ver, c_azu, c_cir = st.columns(5)
    if 'sala_sel' not in st.session_state: st.session_state.sala_sel = "SALA ROSA"
    
    if c_rosa.button("SALA ROSA", type="secondary"): st.session_state.sala_sel = "SALA ROSA"
    if c_ama.button("SALA AMARELA", type="secondary"): st.session_state.sala_sel = "SALA AMARELA"
    if c_ver.button("SALA VERDE", type="secondary"): st.session_state.sala_sel = "SALA VERDE"
    if c_azu.button("SALA AZUL", type="secondary"): st.session_state.sala_sel = "SALA AZUL"
    if c_cir.button("CIRAND. MUNDO", type="secondary"): st.session_state.sala_sel = "CIRAND. MUNDO"

    df = safe_read(st.session_state.sala_sel)
    
    # Filtros de Comunidade e Padrinho
    f1, f2 = st.columns(2)
    with f1: f_comu = st.selectbox("Comunidade", ["Todas"] + sorted([x for x in df["COMUNIDADE"].unique() if x]))
    with f2: check = st.checkbox("Somente sem Padrinho")
    
    df_f = df.copy()
    if f_comu != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_comu]
    if check: df_f = df_f[df_f["PADRINHO/MADRINHA"].astype(str).str.strip().isin(["", "nan", "None"])]
    
    render_styled_table(df_f[["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]], context_color=st.session_state.sala_sel)
    
    # Edição de Padrinho
    st.divider()
    with st.expander("📝 Editar Padrinho/Madrinha"):
        with st.form("edit_pad"):
            al_edit = st.selectbox("Selecionar Aluno", sorted(df["ALUNO"].unique()))
            novo_p = st.text_input("Nome do Padrinho/Madrinha")
            if st.form_submit_button("Salvar Alteração"):
                df_p = pd.read_csv(PADRINHOS_FILE)
                df_p = df_p[df_p["ALUNO"] != al_edit]
                pd.concat([df_p, pd.DataFrame([[al_edit, novo_p]], columns=df_p.columns)], ignore_index=True).to_csv(PADRINHOS_FILE, index=False)
                st.success("Atualizado!")
                st.rerun()

# --- ABA 4 & 5: AVALIAÇÃO E EVOLUÇÃO ---
elif menu == "📊 Avaliação":
    st.header("📊 Registro de Notas")
    df_g = safe_read("GERAL")
    if not df_g.empty:
        with st.form("av"):
            al = st.selectbox("Aluno", sorted([x for x in df_g["ALUNO"].unique() if x]))
            tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            notas = {c: st.slider(c, 1, 5, 3) for c in CATEGORIAS}
            if st.form_submit_button("Gravar"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
                pd.concat([df_av, pd.DataFrame([[al, tr] + list(notas.values())], columns=["Aluno", "Trimestre"] + CATEGORIAS)], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Gravado!")

elif menu == "🌊 Evolução":
    st.header("🌊 Evolução Individual")
    df_av = pd.read_csv(AVAL_FILE)
    if not df_av.empty:
        al_s = st.selectbox("Aluno", sorted(df_av["Aluno"].unique()))
        df_al = df_av[df_av["Aluno"] == al_s]
        tri_s = st.selectbox("Trimestre", df_al["Trimestre"].unique())
        row = df_al[df_al["Trimestre"] == tri_s].iloc[0]
        fig = go.Figure(go.Scatter(x=CATEGORIAS, y=[float(row[c]) for c in CATEGORIAS], mode='lines+markers', fill='tozeroy', line=dict(color=COR_AZUL_INST)))
        fig.update_layout(yaxis=dict(range=[0, 5.5]))
        st.plotly_chart(fig, use_container_width=True)
