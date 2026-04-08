import streamlit as st
import pandas as pd
import os

# 1. Configuração e Estilo Visual
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

C_ROSA, C_VERDE, C_AZUL, C_AMARELO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp {{ background-color: #ffffff; font-family: 'Inter', sans-serif; }}
    
    .main-title {{ text-align: center; padding: 10px 0; }}
    .main-title h1 {{ font-size: 30px; margin: 0; font-weight: 800; }}
    
    /* Botões de Sala com Cores Reativadas */
    div[data-testid="stHorizontalBlock"] {{ align-items: center !important; gap: 0.3rem !important; }}
    .stButton > button {{
        width: 100%; border-radius: 8px !important; 
        font-weight: 700 !important; height: 35px; font-size: 10px !important;
        text-transform: uppercase; border: none !important;
    }}
    
    /* Tabelas */
    .custom-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        border: 1px solid #f2f2f2; border-radius: 10px; font-size: 13px; margin-top: 10px;
    }}
    .custom-table thead th {{ padding: 12px; text-align: left; border-bottom: 2px solid #eee; background-color: #fafafa; }}
    
    /* Cabeçalho Colorido */
    .th-aluno {{ color: {C_AZUL} !important; }}
    .th-turma {{ color: {C_VERDE} !important; }}
    .th-idade {{ color: {C_AMARELO} !important; }}
    .th-comunidade {{ color: {C_ROSA} !important; }}
    .th-padrinho {{ color: {C_AZUL} !important; }}

    /* Fonte Cinza Escuro para o Corpo da Tabela */
    .td-cinza {{ color: #444444 !important; font-weight: 500; }}

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

# 2. Banco de Dados
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE, AVAL_FILE, PADRINHOS_FILE = "alunos.csv", "avaliacoes.csv", "padrinhos_local.csv"

def init_db():
    if not os.path.exists(ALUNOS_FILE): pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE): pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)
    if not os.path.exists(PADRINHOS_FILE): pd.DataFrame(columns=["ALUNO", "PADRINHO_EDITADO"]).to_csv(PADRINHOS_FILE, index=False)
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
        if sheet_key in st.secrets.get("connections", {}).get("gsheets", {}):
            url = st.secrets["connections"]["gsheets"][sheet_key]
            url_csv = url.split("/edit")[0] + "/export?format=csv"
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
    header_map = {"ALUNO": "th-aluno", "TURMA": "th-turma", "IDADE": "th-idade", "COMUNIDADE": "th-comunidade", "PADRINHO/MADRINHA": "th-padrinho"}
    cols = [c for c in df.columns if "UNNAMED" not in c.upper()]
    html = '<table class="custom-table"><thead><tr>'
    for c in cols: html += f'<th class="{header_map.get(c, "")}">{c}</th>'
    html += '</tr></thead><tbody>'
    for _, row in df.iterrows():
        html += f'<tr>' + "".join([f'<td class="td-cinza">{row[v]}</td>' for v in cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# 3. Navegação (ABA EVOLUÇÃO REMOVIDA)
menu = st.sidebar.radio("Navegação", ["👤 Novo Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação"])

if menu == "👤 Novo Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA};'>👤 Novo Cadastro</h3>", unsafe_allow_html=True)
    with st.form("cad_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: n, i, comu = st.text_input("Nome Completo"), st.text_input("Idade"), st.text_input("Comunidade")
        with c2: t, tn = st.selectbox("Turma", ["1º ANO A", "1º ANO B", "2º ANO A", "2º ANO B", "3º ANO A", "3º ANO B", "4º ANO A", "4º ANO B", "5º ANO A", "5º ANO B"]), st.selectbox("Turno", ["MATUTINO", "VESPERTINO"])
        if st.form_submit_button("Salvar Matrícula"):
            df_l = pd.read_csv(ALUNOS_FILE)
            pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Salvo!")

elif menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE};'>📋 Quadro de Matrículas</h3>", unsafe_allow_html=True)
    if 'f_mat' not in st.session_state: st.session_state.f_mat = "Todas"
    cols_t = st.columns(6)
    if cols_t[0].button("Todas"): st.session_state.f_mat = "Todas"
    st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child(1) button {{ background-color: #333 !important; color: white !important; }}</style>", unsafe_allow_html=True)
    for i, (sala, conf) in enumerate(TURMAS_CONFIG.items(), 2):
        if cols_t[i-1].button(sala): st.session_state.f_mat = sala
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({i}) button {{ background-color: {conf['cor']} !important; color: {conf['txt']} !important; }}</style>", unsafe_allow_html=True)
    
    df = safe_read(st.session_state.f_mat if st.session_state.f_mat != "Todas" else "GERAL")
    c1, c2 = st.columns(2)
    with c1: f_turma = st.selectbox("Filtrar Turma (A/B)", ["Todas"] + sorted([str(x) for x in df["TURMA"].unique() if x]))
    with c2: f_cm = st.selectbox("Filtrar Comunidade", ["Todas"] + sorted([str(x) for x in df["COMUNIDADE"].unique() if x]))
    df_f = df.copy()
    if f_turma != "Todas": df_f = df_f[df_f["TURMA"] == f_turma]
    if f_cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm]
    render_styled_table(df_f[["ALUNO", "TURMA", "IDADE", "COMUNIDADE"]])

elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL};'>🤝 Apadrinhamento</h3>", unsafe_allow_html=True)
    if 'f_pad' not in st.session_state: st.session_state.f_pad = "SALA ROSA"
    cols_p = st.columns(5)
    for i, (sala, conf) in enumerate(TURMAS_CONFIG.items(), 1):
        if cols_p[i-1].button(sala, key=f"btn_p_{sala}"): st.session_state.f_pad = sala
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({i}) button {{ background-color: {conf['cor']} !important; color: {conf['txt']} !important; }}</style>", unsafe_allow_html=True)
    
    df = safe_read(st.session_state.f_pad)
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1: f_turma_p = st.selectbox("Filtrar Turma (A/B)", ["Todas"] + sorted([str(x) for x in df["TURMA"].unique() if x]), key="p_t")
    with c2: f_cm_p = st.selectbox("Filtrar Comunidade", ["Todas"] + sorted([str(x) for x in df["COMUNIDADE"].unique() if x]), key="p_c")
    with c3: sem_p = st.checkbox("Sem Padrinho")
    df_f = df.copy()
    if f_turma_p != "Todas": df_f = df_f[df_f["TURMA"] == f_turma_p]
    if f_cm_p != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm_p]
    if sem_p: df_f = df_f[df_f["PADRINHO/MADRINHA"].astype(str).str.strip().isin(["", "nan", "0"])]
    render_styled_table(df_f[["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]])
    
    with st.expander("📝 Editar Padrinho"):
        with st.form("edit_pad"):
            al_e = st.selectbox("Aluno", sorted([str(x) for x in df["ALUNO"].unique() if x]))
            novo_p = st.text_input("Nome do Padrinho/Madrinha")
            if st.form_submit_button("Atualizar"):
                df_p = pd.read_csv(PADRINHOS_FILE)
                df_p = pd.concat([df_p[df_p["ALUNO"] != al_e], pd.DataFrame([[al_e, novo_p]], columns=["ALUNO", "PADRINHO_EDITADO"])], ignore_index=True)
                df_p.to_csv(PADRINHOS_FILE, index=False); st.rerun()

elif menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO};'>📊 Lançar Notas</h3>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    with st.form("aval"):
        c1, c2 = st.columns(2)
        with c1: al = st.selectbox("Aluno", sorted([str(x) for x in df_g["ALUNO"].unique() if x]))
        with c2: tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
        st.write("---")
        notas = {}
        sc1, sc2 = st.columns(2)
        for i, cat in enumerate(CATEGORIAS):
            with sc1 if i < 4 else sc2: notas[cat] = st.slider(cat, 1, 5, 3)
        if st.form_submit_button("Salvar Avaliação"):
            df_av = pd.read_csv(AVAL_FILE)
            df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
            pd.concat([df_av, pd.DataFrame([[al, tr] + [float(v) for v in notas.values()]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
            st.success("Avaliação salva!")
