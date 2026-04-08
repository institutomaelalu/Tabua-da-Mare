import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Configuração e Identidade Visual
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

C_ROSA, C_VERDE, C_AZUL, C_AMARELO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp {{ background-color: #ffffff; font-family: 'Inter', sans-serif; }}
    
    /* Cabeçalho */
    .main-title {{ text-align: center; padding: 10px 0; }}
    .main-title h1 {{ font-size: 32px; margin: 0; font-weight: 800; }}
    
    /* Tabelas */
    .custom-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        border: 1px solid #f2f2f2; border-radius: 10px;
        font-size: 13px; margin-top: 5px;
    }}
    .custom-table thead th {{ background-color: #fafafa; color: #888; padding: 10px; text-align: left; }}
    .custom-table tbody td {{ padding: 8px 10px; border-bottom: 1px solid #f8f8f8; }}
    
    /* Cores das Fontes */
    .txt-rosa {{ color: {C_ROSA} !important; font-weight: 600; }}
    .txt-verde {{ color: {C_VERDE} !important; font-weight: 600; }}
    .txt-azul {{ color: {C_AZUL} !important; font-weight: 600; }}
    .txt-amarelo {{ color: {C_AMARELO} !important; font-weight: 600; }}

    /* Botões de Sala - Alinhamento Horizontal Real */
    div[data-testid="stHorizontalBlock"] {{
        align-items: center !important;
        gap: 0.3rem !important;
    }}
    div.stButton > button {{
        width: 100%; border-radius: 8px !important; border: 1px solid #eee !important;
        font-weight: 700 !important; height: 38px; font-size: 10px !important;
        text-transform: uppercase;
    }}
    
    /* SLIDERS: GROSSOS PORÉM SUAVES */
    /* Barra de fundo (vazia) */
    .stSlider [data-baseweb="slider"] {{ 
        height: 12px !important; 
        background: #f0f2f6 !important; 
        border-radius: 10px !important; 
    }}
    /* Barra de preenchimento (progresso) */
    .stSlider [data-baseweb="slider"] > div > div {{ 
        background: {C_AZUL} !important; 
        height: 12px !important;
        border-radius: 10px 0 0 10px !important;
    }}
    /* Bolinha de arraste */
    .stSlider [data-baseweb="slider"] [role="slider"] {{
        background-color: {C_ROSA} !important; 
        border: 3px solid white !important; 
        width: 24px !important; 
        height: 24px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15) !important;
        margin-top: -6px !important; /* Centraliza na barra grossa */
    }}
    
    hr {{ margin: 0.5rem 0 !important; border: 0; height: 2px; background: linear-gradient(to right, {C_ROSA}, {C_VERDE}, {C_AZUL}, {C_AMARELO}); }}
    </style>
    
    <div class="main-title">
        <h1>
            <span style='color: {C_VERDE};'>Instituto</span> 
            <span style='color: {C_AZUL};'>Mãe</span> 
            <span style='color: {C_VERDE};'>Lalu</span>
        </h1>
    </div>
    <hr>
    """, unsafe_allow_html=True)

# 2. Inicialização de Dados e Funções
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE, AVAL_FILE, PADRINHOS_FILE = "alunos.csv", "avaliacoes.csv", "padrinhos_local.csv"

def init_db():
    if not os.path.exists(ALUNOS_FILE): pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE): pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)
    if not os.path.exists(PADRINHOS_FILE): pd.DataFrame(columns=["ALUNO", "PADRINHO_EDITADO"]).to_csv(PADRINHOS_FILE, index=False)
init_db()

def set_mat(t): st.session_state.f_mat = t
def set_pad(t): st.session_state.f_pad = t
if 'f_mat' not in st.session_state: st.session_state.f_mat = "Todas"
if 'f_pad' not in st.session_state: st.session_state.f_pad = "SALA ROSA"

TURMAS_CONFIG = {
    "SALA ROSA": {"cor": C_ROSA, "key": "sala_rosa", "txt": "#ffffff"},
    "SALA AMARELA": {"cor": C_AMARELO, "key": "sala_amarela", "txt": "#000000"},
    "SALA VERDE": {"cor": C_VERDE, "key": "sala_verde", "txt": "#ffffff"},
    "SALA AZUL": {"cor": C_AZUL, "key": "sala_azul", "txt": "#ffffff"},
    "CIRAND. MUNDO": {"cor": "#6741d9", "key": "cirand_mundo", "txt": "#ffffff"},
}

def safe_read(worksheet_name):
    df = pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])
    try:
        sheet_key = "geral" if worksheet_name == "GERAL" else TURMAS_CONFIG.get(worksheet_name, {}).get("key")
        if sheet_key in st.secrets.get("connections", {}).get("gsheets", {}):
            url = st.secrets["connections"]["gsheets"][sheet_key]
            url_csv = url.split("/edit")[0] + "/export?format=csv"
            if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
            df_sheet = pd.read_csv(url_csv)
            df_sheet.columns = [str(c).strip().upper() for c in df_sheet.columns]
            df = df_sheet
    except: pass
    try:
        df_l, df_p = pd.read_csv(ALUNOS_FILE), pd.read_csv(PADRINHOS_FILE)
        if worksheet_name == "GERAL": full = pd.concat([df, df_l], ignore_index=True)
        else:
            sala_f = worksheet_name.replace("SALA ", "")
            full = pd.concat([df, df_l[df_l["TURMA"].str.contains(sala_f, na=False, case=False)]], ignore_index=True)
        full["ALUNO"] = full["ALUNO"].astype(str).str.strip().str.upper()
        for _, r in df_p.iterrows():
            full.loc[full["ALUNO"] == str(r["ALUNO"]).strip().upper(), "PADRINHO/MADRINHA"] = r["PADRINHO_EDITADO"]
        return full.fillna("")
    except: return df.fillna("")

def render_styled_table(df):
    if df.empty: return st.info("Nenhum dado encontrado.")
    font_colors = ["txt-rosa", "txt-verde", "txt-azul", "txt-amarelo"]
    cols = [c for c in df.columns if "UNNAMED" not in c.upper()]
    html = '<table class="custom-table"><thead><tr>' + "".join([f'<th>{c}</th>' for c in cols]) + '</tr></thead><tbody>'
    for i, row in df.iterrows():
        c_class = font_colors[i % len(font_colors)]
        html += f'<tr>' + "".join([f'<td class="{c_class}">{row[v]}</td>' for v in cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# 3. Navegação (Novo Cadastro como Primeiro)
menu = st.sidebar.radio("Navegação", ["👤 Novo Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução Individual"])

if menu == "👤 Novo Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA};'>👤 Matricular Novo Aluno</h3>", unsafe_allow_html=True)
    with st.form("cad_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: n, i, comu = st.text_input("Nome Completo"), st.text_input("Idade"), st.text_input("Comunidade")
        with c2: t, tn = st.selectbox("Turma", list(TURMAS_CONFIG.keys())), st.selectbox("Turno", ["MATUTINO", "VESPERTINO"])
        if st.form_submit_button("Concluir Matrícula"):
            df_l = pd.read_csv(ALUNOS_FILE)
            pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Matrícula realizada com sucesso!")

elif menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE};'>📋 Quadro de Matrículas</h3>", unsafe_allow_html=True)
    cols_t = st.columns(6)
    cols_t[0].button("Todas", on_click=set_mat, args=("Todas",))
    st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child(1) button {{ background-color: {'#333' if st.session_state.f_mat == 'Todas' else '#eee'} !important; color: white !important; }}</style>", unsafe_allow_html=True)
    for i, (sala, conf) in enumerate(TURMAS_CONFIG.items(), 2):
        cols_t[i-1].button(sala, key=f"m_{sala}", on_click=set_mat, args=(sala,))
        is_sel = st.session_state.f_mat == sala
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({i}) button {{ background-color: {conf['cor'] if is_sel else '#eee'} !important; color: {conf['txt'] if is_sel else '#888'} !important; border:none; }}</style>", unsafe_allow_html=True)
    
    df = safe_read(st.session_state.f_mat if st.session_state.f_mat != "Todas" else "GERAL")
    f_cm = st.selectbox("Filtrar por Comunidade", ["Todas"] + sorted([str(x) for x in df["COMUNIDADE"].unique() if x]))
    df_f = df[df["COMUNIDADE"] == f_cm] if f_cm != "Todas" else df
    render_styled_table(df_f[["ALUNO", "TURMA", "IDADE", "COMUNIDADE"]])

elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL};'>🤝 Gestão de Apadrinhamento</h3>", unsafe_allow_html=True)
    cols_p = st.columns(5)
    for i, (sala, conf) in enumerate(TURMAS_CONFIG.items()):
        cols_p[i].button(sala, key=f"p_{sala}", on_click=set_pad, args=(sala,))
        is_sel = st.session_state.f_pad == sala
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({i+1}) button {{ background-color: {conf['cor'] if is_sel else '#eee'} !important; color: {conf['txt'] if is_sel else '#888'} !important; }}</style>", unsafe_allow_html=True)
    
    df = safe_read(st.session_state.f_pad)
    c1, c2 = st.columns(2)
    with c1: f_cm_p = st.selectbox("Comunidade ", ["Todas"] + sorted([str(x) for x in df["COMUNIDADE"].unique() if x]))
    with c2: check = st.checkbox("Somente sem padrinho/madrinha")
    
    df_f = df.copy()
    if f_cm_p != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm_p]
    if check: df_f = df_f[df_f["PADRINHO/MADRINHA"].astype(str).str.strip().isin(["", "nan", "None", "0"])]
    render_styled_table(df_f[["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]])
    
    with st.expander("📝 Editar Padrinho/Madrinha"):
        with st.form("edit_pad"):
            al_e = st.selectbox("Selecione o Aluno", sorted([str(x) for x in df["ALUNO"].unique() if x]))
            novo_p = st.text_input("Novo Nome do Padrinho/Madrinha")
            if st.form_submit_button("Salvar"):
                df_p = pd.read_csv(PADRINHOS_FILE)
                df_p = pd.concat([df_p[df_p["ALUNO"] != al_e], pd.DataFrame([[al_e, novo_p]], columns=["ALUNO", "PADRINHO_EDITADO"])], ignore_index=True)
                df_p.to_csv(PADRINHOS_FILE, index=False); st.rerun()

elif menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO};'>📊 Avaliação Trimestral</h3>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    if not df_g.empty:
        with st.form("aval_form"):
            c1, c2 = st.columns(2)
            with c1: al = st.selectbox("Aluno", sorted([str(x) for x in df_g["ALUNO"].unique() if x]))
            with c2: tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            st.write("---")
            notas = {}
            for cat in CATEGORIAS: notas[cat] = st.slider(cat, 1, 5, 3)
            if st.form_submit_button("Gravar Notas"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
                pd.concat([df_av, pd.DataFrame([[al, tr] + [float(v) for v in notas.values()]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success(f"Notas de {al} gravadas!")

elif menu == "🌊 Evolução Individual":
    st.markdown(f"<h3 style='color:{C_AZUL};'>🌊 Acompanhamento de Evolução</h3>", unsafe_allow_html=True)
    if os.path.exists(AVAL_FILE):
        df_av = pd.read_csv(AVAL_FILE)
        if not df_av.empty:
            al_s = st.selectbox("Escolha o Aluno", sorted(df_av["Aluno"].unique()))
            df_al = df_av[df_av["Aluno"] == al_s]
            if not df_al.empty:
                tri_s = st.selectbox("Escolha o Trimestre", df_al["Trimestre"].unique())
                row = df_al[df_al["Trimestre"] == tri_s].iloc[0]
                y_vals = [float(row[cat]) for cat in CATEGORIAS]
                
                fig = go.Figure(go.Scatter(x=CATEGORIAS, y=y_vals, mode='lines+markers+text', text=[str(v) for v in y_vals], textposition="top center", fill='tozeroy', line=dict(color=C_AZUL, width=4, shape='spline')))
                fig.update_layout(yaxis=dict(range=[0, 5.5], tickvals=[1,2,3,4,5]), height=400, margin=dict(t=30, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
        else: st.info("Ainda não há dados de avaliações para gerar o gráfico.")
