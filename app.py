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
    .main-header {{ text-align: center; padding-top: 25px; padding-bottom: 5px; }}
    .main-header h1 {{ margin: 0; font-size: 38px !important; font-weight: 800; line-height: 1.1; }}
    
    .block-container {{ padding-top: 1rem !important; padding-bottom: 1rem !important; }}
    [data-testid="stVerticalBlock"] > div {{ padding-bottom: 0.4rem !important; }}
    .stSelectbox, .stCheckbox, .stSlider {{ margin-bottom: 8px !important; }}
    hr {{ margin: 0.5rem 0 !important; }}

    .custom-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        border: 1px solid #f0f0f0; border-radius: 10px;
        overflow: hidden; font-size: 13px; margin-top: 5px;
    }}
    .custom-table thead th {{ background-color: #ffffff; padding: 10px; text-align: left; border-bottom: 2px solid #f8f8f8; }}
    .th-rosa {{ color: {C_ROSA} !important; font-weight: 700; }}
    .th-verde {{ color: {C_VERDE} !important; font-weight: 700; }}
    .th-azul {{ color: {C_AZUL} !important; font-weight: 700; }}
    .th-amarelo {{ color: {C_AMARELO} !important; font-weight: 700; }}
    .custom-table tbody td {{ padding: 8px 10px; border-bottom: 1px solid #fafafa; color: #666 !important; font-weight: 500; }}
    
    div.stButton > button {{
        width: 100%; border-radius: 8px !important; border: 1px solid #eee !important;
        font-weight: 600 !important; height: 38px; font-size: 12px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. Bancos de Dados e Configurações
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

def safe_read(worksheet_name):
    df = pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])
    try:
        lista_dfs = []
        target_keys = TURMAS_CONFIG.keys() if worksheet_name == "GERAL" else [worksheet_name]
        for tk in target_keys:
            conf = TURMAS_CONFIG.get(tk)
            if conf and conf['key'] in st.secrets["connections"]["gsheets"]:
                url = st.secrets["connections"]["gsheets"][conf['key']]
                url_csv = url.split("/edit")[0] + "/export?format=csv"
                if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
                temp_df = pd.read_csv(url_csv)
                temp_df.columns = [str(c).strip().upper() for c in temp_df.columns]
                for col in temp_df.columns:
                    if "PADRINHO" in col: temp_df = temp_df.rename(columns={col: "PADRINHO/MADRINHA"})
                lista_dfs.append(temp_df)
        if lista_dfs: df = pd.concat(lista_dfs, ignore_index=True)
    except: pass
    
    try:
        df_l, df_p = pd.read_csv(ALUNOS_FILE), pd.read_csv(PADRINHOS_FILE)
        df = pd.concat([df, df_l], ignore_index=True) if worksheet_name == "GERAL" else df
        df["ALUNO"] = df["ALUNO"].astype(str).str.strip().str.upper()
        for _, r in df_p.iterrows():
            df.loc[df["ALUNO"] == str(r["ALUNO"]).strip().upper(), "PADRINHO/MADRINHA"] = r["PADRINHO_EDITADO"]
        return df.fillna("")
    except: return df.fillna("")

# 3. LOGIN
if "logado" not in st.session_state:
    st.session_state.logado, st.session_state.perfil, st.session_state.nome_usuario = False, None, ""

if not st.session_state.logado:
    st.markdown("<div class='main-header'><h1>Acesso ao Sistema</h1></div><hr>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.form("login"):
            u, s = st.text_input("Usuário (Nome)").strip().upper(), st.text_input("Chave", type="password")
            if st.form_submit_button("Entrar"):
                if u == "ADMIN" and s == "123":
                    st.session_state.logado, st.session_state.perfil, st.session_state.nome_usuario = True, "admin", "Coordenação"
                    st.rerun()
                else:
                    validos = safe_read("GERAL")["PADRINHO/MADRINHA"].astype(str).str.strip().str.upper().unique()
                    if u in validos and s == "lalu2026":
                        st.session_state.logado, st.session_state.perfil, st.session_state.nome_usuario = True, "padrinho", u
                        st.rerun()
                    else: st.error("Acesso negado.")
    st.stop()

# 4. DASHBOARD PRINCIPAL
st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)
st.sidebar.write(f"👤 **{st.session_state.nome_usuario}**")
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

if st.session_state.perfil == "admin":
    menu = st.sidebar.radio("Navegação", ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução Individual"])
else:
    menu = "🌊 Evolução Individual"

# --- Lógica das Abas ---
if menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE}'>📋 Quadro de Matrículas</h3>", unsafe_allow_html=True)
    df = safe_read("GERAL")
    cols = ["ALUNO", "TURMA", "IDADE", "COMUNIDADE"]
    html = '<table class="custom-table"><thead><tr>' + "".join([f'<th>{c}</th>' for c in cols]) + '</tr></thead><tbody>'
    for _, r in df.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🤝 Apadrinhamento</h3>", unsafe_allow_html=True)
    df = safe_read("GERAL")
    cols = ["ALUNO", "TURMA", "PADRINHO/MADRINHA"]
    html = '<table class="custom-table"><thead><tr>' + "".join([f'<th>{c}</th>' for c in cols]) + '</tr></thead><tbody>'
    for _, r in df.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
    with st.expander("📝 Editar Padrinho"):
        with st.form("edp"):
            al = st.selectbox("Aluno", sorted(df["ALUNO"].unique()))
            npad = st.text_input("Novo Padrinho")
            if st.form_submit_button("Salvar"):
                df_p = pd.read_csv(PADRINHOS_FILE)
                df_p = df_p[df_p["ALUNO"] != al]
                pd.concat([df_p, pd.DataFrame([[al, npad]], columns=["ALUNO", "PADRINHO_EDITADO"])], ignore_index=True).to_csv(PADRINHOS_FILE, index=False)
                st.rerun()

elif menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO}'>📊 Lançar Notas</h3>", unsafe_allow_html=True)
    df = safe_read("GERAL")
    with st.form("f_av"):
        al = st.selectbox("Aluno", sorted(df["ALUNO"].unique()))
        tri = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
        notas = {cat: st.slider(cat, 1, 5, 3) for cat in CATEGORIAS}
        if st.form_submit_button("Salvar"):
            df_av = pd.read_csv(AVAL_FILE)
            df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tri))]
            pd.concat([df_av, pd.DataFrame([[al, tri] + [float(v) for v in notas.values()]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
            st.success("Salvo!")

elif menu == "🌊 Evolução Individual":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🌊 Tábua da Maré (Evolução)</h3>", unsafe_allow_html=True)
    if os.path.exists(AVAL_FILE):
        df_av = pd.read_csv(AVAL_FILE)
        df_g = safe_read("GERAL")
        if st.session_state.perfil == "admin": visiveis = sorted(df_av["Aluno"].unique())
        else:
            afilhados = df_g[df_g["PADRINHO/MADRINHA"].astype(str).str.strip().str.upper() == st.session_state.nome_usuario]["ALUNO"].unique()
            visiveis = [a for a in df_av["Aluno"].unique() if a in afilhados]
        
        if visiveis:
            al_s = st.selectbox("Aluno", visiveis)
            df_al = df_av[df_av["Aluno"] == al_s]
            tri_s = st.selectbox("Trimestre", df_al["Trimestre"].unique())
            row = df_al[df_al["Trimestre"] == tri_s].iloc[0]
            y = [float(row[c]) for c in CATEGORIAS]
            fig = go.Figure(go.Scatter(x=CATEGORIAS, y=y, mode='lines+markers+text', text=[str(int(v)) for v in y], textposition="top center", fill='tozeroy', line=dict(color=C_AZUL, width=4, shape='spline')))
            fig.update_layout(yaxis=dict(range=[0, 5.5], tickvals=[1,2,3,4,5]), height=400, margin=dict(t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Nenhuma avaliação disponível.")

elif menu == "👤 Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA}'>👤 Novo Cadastro</h3>", unsafe_allow_html=True)
    with st.form("c"):
        n, i, c = st.text_input("Nome"), st.text_input("Idade"), st.text_input("Comunidade")
        t, tn = st.selectbox("Sala", list(TURMAS_CONFIG.keys())), st.selectbox("Turno", ["A", "B"])
        if st.form_submit_button("Cadastrar"):
            df_l = pd.read_csv(ALUNOS_FILE)
            pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, c]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Cadastrado!")
