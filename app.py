import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Configuração e Estilo
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

C_ROSA, C_VERDE, C_AZUL, C_AMARELO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp {{ background-color: #ffffff; font-family: 'Inter', sans-serif; }}
    
    /* Tabelas e Espaçamento */
    .custom-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        border: 1px solid #f0f0f0; border-radius: 10px;
        overflow: hidden; font-size: 13px; margin-top: 5px;
    }}
    .custom-table thead th {{ background-color: #ffffff; color: #999; padding: 10px; text-align: left; border-bottom: 2px solid #f8f8f8; }}
    .custom-table tbody td {{ padding: 8px 10px; border-bottom: 1px solid #fafafa; }}
    
    /* Fontes Coloridas */
    .txt-rosa {{ color: {C_ROSA} !important; font-weight: 600; }}
    .txt-verde {{ color: {C_VERDE} !important; font-weight: 600; }}
    .txt-azul {{ color: {C_AZUL} !important; font-weight: 600; }}
    .txt-amarelo {{ color: {C_AMARELO} !important; font-weight: 600; }}

    /* Botões de Filtro - Mais Próximos */
    div.stButton > button {{
        width: 100%; border-radius: 8px !important; border: 1px solid #eee !important;
        font-weight: 600 !important; height: 40px; font-size: 12px !important;
    }}
    [data-testid="stHorizontalBlock"] {{ gap: 0.5rem !important; }}
    
    /* Ajuste de Sliders para Identidade Visual */
    .stSlider [data-baseweb="slider"] [role="slider"] {{ background-color: {C_AZUL}; border: 2px solid {C_ROSA}; }}
    .stSlider [data-baseweb="slider"] [data-testid="stTickBar"] {{ background-color: {C_VERDE}; }}
    
    /* Redução de espaços entre elementos */
    .block-container {{ padding-top: 2rem !important; }}
    hr {{ margin: 0.5rem 0 !important; }}
    </style>
    
    <div style='text-align: center;'>
        <h1 style='margin: 0; font-size: 28px;'>
            <span style='color: {C_VERDE};'>Instituto</span> <span style='color: {C_AZUL};'>Mãe</span> <span style='color: {C_VERDE};'>Lalu</span>
        </h1>
    </div>
    <hr style="border: 0; height: 2px; background-image: linear-gradient(to right, {C_ROSA}, {C_VERDE}, {C_AZUL}, {C_AMARELO});">
    """, unsafe_allow_html=True)

# 2. Callbacks e Inicialização
def set_mat(t): st.session_state.f_mat = t
def set_pad(t): st.session_state.f_pad = t

if 'f_mat' not in st.session_state: st.session_state.f_mat = "Todas"
if 'f_pad' not in st.session_state: st.session_state.f_pad = "SALA ROSA"

CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE, AVAL_FILE, PADRINHOS_FILE = "alunos.csv", "avaliacoes.csv", "padrinhos_local.csv"

def init_db():
    for f, cols in {ALUNOS_FILE: ["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"], 
                    AVAL_FILE: ["Aluno", "Trimestre"] + CATEGORIAS, 
                    PADRINHOS_FILE: ["ALUNO", "PADRINHO_EDITADO"]}.items():
        if not os.path.exists(f): pd.DataFrame(columns=cols).to_csv(f, index=False)
init_db()

TURMAS_CONFIG = {
    "SALA ROSA": {"cor": C_ROSA, "key": "sala_rosa", "txt": "#ffffff"},
    "SALA AMARELA": {"cor": C_AMARELO, "key": "sala_amarela", "txt": "#000000"},
    "SALA VERDE": {"cor": C_VERDE, "key": "sala_verde", "txt": "#ffffff"},
    "SALA AZUL": {"cor": C_AZUL, "key": "sala_azul", "txt": "#ffffff"},
    "CIRAND. MUNDO": {"cor": "#6741d9", "key": "cirand_mundo", "txt": "#ffffff"},
}

# 3. Funções de leitura e renderização
def safe_read(worksheet_name):
    df = pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])
    try:
        sheet_key = "geral" if worksheet_name == "GERAL" else TURMAS_CONFIG.get(worksheet_name, {}).get("key")
        if sheet_key in st.secrets["connections"]["gsheets"]:
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
    if df.empty: return st.warning("Sem dados.")
    font_colors = ["txt-rosa", "txt-verde", "txt-azul", "txt-amarelo"]
    cols = [c for c in df.columns if "UNNAMED" not in c.upper()]
    html = '<table class="custom-table"><thead><tr>' + "".join([f'<th>{c}</th>' for c in cols]) + '</tr></thead><tbody>'
    for i, row in df.iterrows():
        c_class = font_colors[i % len(font_colors)]
        html += f'<tr>' + "".join([f'<td class="{c_class}">{row[v]}</td>' for v in cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# 4. Interface e Navegação
menu = st.sidebar.radio("Navegação", ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Avaliação", "🌊 Evolução"])

if menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE}; margin-bottom:5px;'>📋 Quadro de Matrículas</h3>", unsafe_allow_html=True)
    cols_t = st.columns(6)
    cols_t[0].button("Todas", on_click=set_mat, args=("Todas",))
    st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child(1) button {{ background-color: {'#333' if st.session_state.f_mat == 'Todas' else '#eee'} !important; color: white !important; }}</style>", unsafe_allow_html=True)
    for i, (sala, conf) in enumerate(TURMAS_CONFIG.items(), 2):
        cols_t[i-1].button(sala, key=f"m_{sala}", on_click=set_mat, args=(sala,))
        is_sel = st.session_state.f_mat == sala
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({i}) button {{ background-color: {conf['cor'] if is_sel else '#eee'} !important; color: {conf['txt'] if is_sel else '#888'} !important; border:none; }}</style>", unsafe_allow_html=True)
    
    df = safe_read(st.session_state.f_mat if st.session_state.f_mat != "Todas" else "GERAL")
    f1, f2 = st.columns(2)
    with f1: f_tn = st.selectbox("Turno", ["Todos"] + sorted([str(x) for x in df["TURNO"].unique() if x]))
    with f2: f_cm = st.selectbox("Comunidade", ["Todas"] + sorted([str(x) for x in df["COMUNIDADE"].unique() if x]))
    df_f = df[df["TURNO"] == f_tn] if f_tn != "Todos" else df
    if f_cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm]
    render_styled_table(df_f[["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]])

elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL}; margin-bottom:5px;'>🤝 Apadrinhamento</h3>", unsafe_allow_html=True)
    cols_p = st.columns(5)
    for i, (sala, conf) in enumerate(TURMAS_CONFIG.items()):
        cols_p[i].button(sala, key=f"p_{sala}", on_click=set_pad, args=(sala,))
        is_sel = st.session_state.f_pad == sala
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({i+1}) button {{ background-color: {conf['cor'] if is_sel else '#eee'} !important; color: {conf['txt'] if is_sel else '#888'} !important; }}</style>", unsafe_allow_html=True)
    
    df = safe_read(st.session_state.f_pad)
    # RESTAURAÇÃO DOS FILTROS
    f1, f2 = st.columns(2)
    with f1: f_cm_p = st.selectbox("Comunidade ", ["Todas"] + sorted([str(x) for x in df["COMUNIDADE"].unique() if x]))
    with f2: check = st.checkbox("Sem padrinho/madrinha")
    
    df_f = df.copy()
    if f_cm_p != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm_p]
    if check: df_f = df_f[df_f["PADRINHO/MADRINHA"].astype(str).str.strip().isin(["", "nan", "None", "0"])]
    render_styled_table(df_f[["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]])

elif menu == "📊 Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO};'>📊 Lançar Notas</h3>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    if not df_g.empty:
        with st.form("aval_form"):
            al = st.selectbox("Aluno", sorted([str(x) for x in df_g["ALUNO"].unique() if x]))
            tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            st.write("---")
            notas = {cat: st.slider(cat, 1, 5, 3) for cat in CATEGORIAS}
            if st.form_submit_button("Salvar Avaliação"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
                pd.concat([df_av, pd.DataFrame([[al, tr] + [float(v) for v in notas.values()]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Salvo!")

elif menu == "🌊 Evolução":
    st.markdown(f"<h3 style='color:{C_AZUL};'>🌊 Evolução Individual</h3>", unsafe_allow_html=True)
    if os.path.exists(AVAL_FILE):
        df_av = pd.read_csv(AVAL_FILE)
        if not df_av.empty:
            al_s = st.selectbox("Escolha o Aluno", sorted(df_av["Aluno"].unique()))
            df_al = df_av[df_av["Aluno"] == al_s]
            tri_s = st.selectbox("Trimestre", df_al["Trimestre"].unique())
            row = df_al[df_al["Trimestre"] == tri_s].iloc[0]
            y_vals = [float(row[cat]) for cat in CATEGORIAS]
            fig = go.Figure(go.Scatter(x=CATEGORIAS, y=y_vals, mode='lines+markers+text', text=[str(v) for v in y_vals], textposition="top center", fill='tozeroy', line=dict(color=C_AZUL, width=4, shape='spline')))
            fig.update_layout(yaxis=dict(range=[0, 5.5], tickvals=[1,2,3,4,5]), height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Sem dados.")

elif menu == "👤 Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA};'>👤 Novo Cadastro</h3>", unsafe_allow_html=True)
    with st.form("cad"):
        n, i, comu = st.text_input("Nome"), st.text_input("Idade"), st.text_input("Comunidade")
        t, tn = st.selectbox("Turma", list(TURMAS_CONFIG.keys())), st.selectbox("Turno", ["MATUTINO", "VESPERTINO"])
        if st.form_submit_button("Cadastrar"):
            df_l = pd.read_csv(ALUNOS_FILE)
            pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Cadastrado!")
