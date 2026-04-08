import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Configuração de Estilo e Cabeçalho
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

C_ROSA, C_VERDE, C_AZUL, C_AMARELO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    .custom-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        font-family: 'Segoe UI', sans-serif; border: 1px solid #eee; border-radius: 12px;
        overflow: hidden; font-size: 13px; margin-top: 20px;
    }}
    .custom-table thead th {{ background-color: #ffffff; color: #888; padding: 15px; text-align: left; border-bottom: 2px solid #f1f1f1; }}
    .custom-table tbody td {{ padding: 12px 15px; border-bottom: 1px solid #fafafa; }}
    .txt-rosa {{ color: {C_ROSA} !important; font-weight: 600; }}
    .txt-verde {{ color: {C_VERDE} !important; font-weight: 600; }}
    .txt-azul {{ color: {C_AZUL} !important; font-weight: 600; }}
    .txt-amarelo {{ color: {C_AMARELO} !important; font-weight: 600; }}

    /* Botões com resposta imediata e sem borda de foco persistente */
    div.stButton > button {{
        width: 100%; border-radius: 10px !important; border: 2px solid #f1f1f1 !important;
        font-weight: 700 !important; height: 48px; transition: all 0.2s;
    }}
    div.stButton > button:active {{ transform: scale(0.98); }}
    div.stButton > button:focus:not(:active) {{ border-color: #f1f1f1 !important; box-shadow: none !important; }}
    </style>
    
    <div style='text-align: center; padding: 10px;'>
        <h1 style='margin-bottom: 0; font-size: 32px;'>
            <span style='color: {C_VERDE};'>Instituto</span> <span style='color: {C_AZUL};'>Mãe</span> <span style='color: {C_VERDE};'>Lalu</span>
        </h1>
    </div>
    <hr style="border: 0; height: 2px; background-image: linear-gradient(to right, {C_ROSA}, {C_VERDE}, {C_AZUL}, {C_AMARELO});">
    """, unsafe_allow_html=True)

# 2. Callbacks para Clique Único (A Mágica do Clique Único)
def set_mat_filter(turma):
    st.session_state.f_mat = turma

def set_pad_filter(turma):
    st.session_state.f_pad = turma

# Inicialização de Estados
if 'f_mat' not in st.session_state: st.session_state.f_mat = "Todas"
if 'f_pad' not in st.session_state: st.session_state.f_pad = "SALA ROSA"

# 3. Funções de Dados (Mantidas)
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE, AVAL_FILE, PADRINHOS_FILE = "alunos.csv", "avaliacoes.csv", "padrinhos_local.csv"

def init_db():
    for f in [ALUNOS_FILE, AVAL_FILE, PADRINHOS_FILE]:
        if not os.path.exists(f): 
            cols = ["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"] if f == ALUNOS_FILE else \
                   (["Aluno", "Trimestre"] + CATEGORIAS if f == AVAL_FILE else ["ALUNO", "PADRINHO_EDITADO"])
            pd.DataFrame(columns=cols).to_csv(f, index=False)
init_db()

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
    if df.empty: return st.warning("Nenhum dado encontrado.")
    font_colors = ["txt-rosa", "txt-verde", "txt-azul", "txt-amarelo"]
    cols = [c for c in df.columns if "UNNAMED" not in c.upper()]
    html = '<table class="custom-table"><thead><tr>' + "".join([f'<th>{c}</th>' for c in cols]) + '</tr></thead><tbody>'
    for i, row in df.iterrows():
        c_class = font_colors[i % len(font_colors)]
        html += f'<tr>' + "".join([f'<td class="{c_class}">{row[v]}</td>' for v in cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# 4. Interface Principal
menu = st.sidebar.radio("Navegação", ["👤 Novo Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução Individual"])

if menu == "📝 Matrículas":
    st.markdown(f"<h2 style='color:{C_VERDE};'>📋 Quadro de Matrículas</h2>", unsafe_allow_html=True)
    cols_t = st.columns(6)
    
    # Botão TODAS com callback
    cols_t[0].button("Todas", on_click=set_mat_filter, args=("Todas",))
    st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child(1) button {{ background-color: {'#333' if st.session_state.f_mat == 'Todas' else '#eee'} !important; color: white !important; }}</style>", unsafe_allow_html=True)

    for i, (sala, conf) in enumerate(TURMAS_CONFIG.items(), 2):
        is_sel = st.session_state.f_mat == sala
        # Botões de Sala com callback (on_click) para clique único
        cols_t[i-1].button(sala, key=f"mat_{sala}", on_click=set_mat_filter, args=(sala,))
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({i}) button {{ background-color: {conf['cor'] if is_sel else '#eee'} !important; color: {conf['txt'] if is_sel else '#888'} !important; border: none !important; }}</style>", unsafe_allow_html=True)

    df = safe_read(st.session_state.f_mat if st.session_state.f_mat != "Todas" else "GERAL")
    f1, f2 = st.columns(2)
    with f1: f_tn = st.selectbox("Turno", ["Todos"] + sorted([str(x) for x in df["TURNO"].unique() if x]))
    with f2: f_cm = st.selectbox("Comunidade", ["Todas"] + sorted([str(x) for x in df["COMUNIDADE"].unique() if x]))
    df_f = df[df["TURNO"] == f_tn] if f_tn != "Todos" else df
    if f_cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm]
    render_styled_table(df_f[["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]])

elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h2 style='color:{C_AZUL};'>🤝 Apadrinhamento</h2>", unsafe_allow_html=True)
    cols_p = st.columns(5)
    for i, (sala, conf) in enumerate(TURMAS_CONFIG.items()):
        is_sel = st.session_state.f_pad == sala
        # Botão com callback para clique único
        cols_p[i].button(sala, key=f"pad_btn_{sala}", on_click=set_pad_filter, args=(sala,))
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({i+1}) button {{ background-color: {conf['cor'] if is_sel else '#eee'} !important; color: {conf['txt'] if is_sel else '#888'} !important; }}</style>", unsafe_allow_html=True)

    df = safe_read(st.session_state.f_pad)
    check = st.checkbox("Apenas sem padrinho/madrinha")
    df_f = df[df["PADRINHO/MADRINHA"].astype(str).str.strip().isin(["", "nan", "None", "0"])] if check else df
    render_styled_table(df_f[["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]])

# (As outras abas permanecem com a mesma lógica de gravação e evolução)
elif menu == "👤 Novo Cadastro":
    st.markdown(f"<h2 style='color:{C_ROSA};'>📝 Novo Aluno</h2>", unsafe_allow_html=True)
    with st.form("cad_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: n, i, comu = st.text_input("Nome"), st.text_input("Idade"), st.text_input("Comunidade")
        with c2: t, tn = st.selectbox("Turma", list(TURMAS_CONFIG.keys())), st.selectbox("Turno", ["MATUTINO", "VESPERTINO"])
        if st.form_submit_button("Finalizar"):
            df_l = pd.read_csv(ALUNOS_FILE)
            pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Salvo!")

elif menu == "📊 Lançar Avaliação":
    st.markdown(f"<h2 style='color:{C_AMARELO};'>📊 Avaliação</h2>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    if not df_g.empty:
        with st.form("aval_form"):
            al = st.selectbox("Aluno", sorted([str(x) for x in df_g["ALUNO"].unique() if x]))
            tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            notas = {cat: st.select_slider(cat, options=[1, 2, 3, 4, 5], value=3) for cat in CATEGORIAS}
            if st.form_submit_button("Salvar"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
                pd.concat([df_av, pd.DataFrame([[al, tr] + [float(v) for v in notas.values()]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Gravado!")

elif menu == "🌊 Evolução Individual":
    st.markdown(f"<h2 style='color:{C_AZUL};'>🌊 Evolução</h2>", unsafe_allow_html=True)
    if os.path.exists(AVAL_FILE):
        df_av = pd.read_csv(AVAL_FILE)
        if not df_av.empty:
            al_s = st.selectbox("Aluno", sorted(df_av["Aluno"].unique()))
            df_al = df_av[df_av["Aluno"] == al_s]
            tri_s = st.selectbox("Trimestre", df_al["Trimestre"].unique())
            row = df_al[df_al["Trimestre"] == tri_s].iloc[0]
            y_vals = [float(row[cat]) for cat in CATEGORIAS]
            fig = go.Figure(go.Scatter(x=CATEGORIAS, y=y_vals, mode='lines+markers+text', text=[str(v) for v in y_vals], textposition="top center", fill='tozeroy', line=dict(color=C_AZUL, width=4, shape='spline')))
            fig.update_layout(yaxis=dict(range=[0, 5.5], tickvals=[1,2,3,4,5]), height=450, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
