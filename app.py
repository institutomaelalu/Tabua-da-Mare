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
    .custom-table thead th {{ background-color: #ffffff; padding: 10px; text-align: left; border-bottom: 2px solid #f8f8f8; color: #444; }}
    .custom-table tbody td {{ padding: 8px 10px; border-bottom: 1px solid #fafafa; color: #666 !important; font-weight: 500; }}
    
    div.stButton > button {{
        width: 100%; border-radius: 8px !important; border: 1px solid #eee !important;
        font-weight: 600 !important; height: 38px; font-size: 12px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. Inicialização de Arquivos Locais
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

# 3. Funções de Leitura
def safe_read(worksheet_name):
    df = pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])
    try:
        if worksheet_name == "GERAL":
            dfs = []
            for k in TURMAS_CONFIG:
                conf = TURMAS_CONFIG[k]
                if conf['key'] in st.secrets["connections"]["gsheets"]:
                    url = st.secrets["connections"]["gsheets"][conf['key']]
                    url_csv = url.split("/edit")[0] + "/export?format=csv"
                    if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
                    temp = pd.read_csv(url_csv)
                    temp.columns = [str(c).strip().upper() for c in temp.columns]
                    if "PADRINHO" in temp.columns: temp = temp.rename(columns={"PADRINHO": "PADRINHO/MADRINHA"})
                    dfs.append(temp)
            df = pd.concat(dfs, ignore_index=True) if dfs else df
        else:
            conf = TURMAS_CONFIG.get(worksheet_name)
            if conf and conf['key'] in st.secrets["connections"]["gsheets"]:
                url = st.secrets["connections"]["gsheets"][conf['key']]
                url_csv = url.split("/edit")[0] + "/export?format=csv"
                if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
                df = pd.read_csv(url_csv)
                df.columns = [str(c).strip().upper() for c in df.columns]
                if "PADRINHO" in df.columns: df = df.rename(columns={"PADRINHO": "PADRINHO/MADRINHA"})
    except: pass
    
    try:
        df_l, df_p = pd.read_csv(ALUNOS_FILE), pd.read_csv(PADRINHOS_FILE)
        if worksheet_name == "GERAL": full = pd.concat([df, df_l], ignore_index=True)
        else: full = df.copy()
        
        full["ALUNO"] = full["ALUNO"].astype(str).str.strip().str.upper()
        for _, r in df_p.iterrows():
            full.loc[full["ALUNO"] == str(r["ALUNO"]).strip().upper(), "PADRINHO/MADRINHA"] = r["PADRINHO_EDITADO"]
        return full.fillna("")
    except: return df.fillna("")

# 4. LOGIN
if "logado" not in st.session_state:
    st.session_state.logado, st.session_state.perfil, st.session_state.nome_usuario = False, None, ""

if not st.session_state.logado:
    st.markdown("<div class='main-header'><h1>Acesso ao Sistema</h1></div><hr>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.form("login"):
            u = st.text_input("Seu nome (como na planilha)").strip().upper()
            s = st.text_input("Chave de Acesso", type="password")
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

# --- HEADER ---
st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

st.sidebar.write(f"👤 **{st.session_state.nome_usuario}**")
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# 5. NAVEGAÇÃO
if st.session_state.perfil == "admin":
    menu = st.sidebar.radio("Navegação", ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução (Padrinhos)", "📊 Controle Interno"])
else:
    menu = "🌊 Evolução (Padrinhos)"

# --- ABAS ---

if menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE}'>📋 Quadro de Matrículas</h3>", unsafe_allow_html=True)
    df = safe_read("GERAL")
    view_cols = ["ALUNO", "TURMA", "IDADE", "COMUNIDADE"]
    html = '<table class="custom-table"><thead><tr>' + "".join([f'<th>{c}</th>' for c in view_cols]) + '</tr></thead><tbody>'
    for _, r in df.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in view_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🤝 Apadrinhamento</h3>", unsafe_allow_html=True)
    df = safe_read("GERAL")
    view_cols = ["ALUNO", "TURMA", "PADRINHO/MADRINHA"]
    html = '<table class="custom-table"><thead><tr>' + "".join([f'<th>{c}</th>' for c in view_cols]) + '</tr></thead><tbody>'
    for _, r in df.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in view_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

elif menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO}'>📊 Lançar Notas</h3>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    with st.form("aval"):
        al = st.selectbox("Aluno", sorted(df_g["ALUNO"].unique()))
        tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
        notas = {cat: st.slider(cat, 1, 5, 3) for cat in CATEGORIAS}
        if st.form_submit_button("Salvar"):
            df_av = pd.read_csv(AVAL_FILE)
            df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
            pd.concat([df_av, pd.DataFrame([[al, tr] + [float(v) for v in notas.values()]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
            st.success("Salvo!")

elif menu == "🌊 Evolução (Padrinhos)":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🤝 Área do Padrinho: Meus Afilhados</h3>", unsafe_allow_html=True)
    df_geral = safe_read("GERAL")
    df_av = pd.read_csv(AVAL_FILE) if os.path.exists(AVAL_FILE) else pd.DataFrame()
    
    if st.session_state.perfil == "admin":
        lista_padrinhos = sorted(df_geral["PADRINHO/MADRINHA"].unique())
        padrinho_alvo = st.selectbox("Simular visão do Padrinho:", lista_padrinhos)
    else:
        padrinho_alvo = st.session_state.nome_usuario

    afilhados_df = df_geral[df_geral["PADRINHO/MADRINHA"].astype(str).str.strip().str.upper() == padrinho_alvo.strip().upper()]
    
    if not afilhados_df.empty:
        st.write(f"Olá **{padrinho_alvo}**, aqui estão as crianças que você apadrinha:")
        view = afilhados_df[["ALUNO", "TURMA", "IDADE"]].copy()
        html = '<table class="custom-table"><thead><tr><th>AFILHADO</th><th>TURMA</th><th>IDADE</th></tr></thead><tbody>'
        for _, r in view.iterrows(): html += f'<tr><td>{r["ALUNO"]}</td><td>{r["TURMA"]}</td><td>{r["IDADE"]}</td></tr>'
        st.markdown(html + '</tbody></table><br>', unsafe_allow_html=True)
        
        al_visiveis = [a for a in afilhados_df["ALUNO"].unique() if not df_av.empty and a in df_av["Aluno"].unique()]
        if al_visiveis:
            al_s = st.selectbox("Ver evolução detalhada de:", al_visiveis)
            df_al = df_av[df_av["Aluno"] == al_s]
            tri_s = st.selectbox("Trimestre", df_al["Trimestre"].unique())
            df_filtrado = df_al[df_al["Trimestre"] == tri_s]
            if not df_filtrado.empty:
                row = df_filtrado.iloc[0]
                y_vals = [float(row[c]) for c in CATEGORIAS]
                fig = go.Figure(go.Scatter(x=CATEGORIAS, y=y_vals, mode='lines+markers+text', text=[str(int(v)) for v in y_vals], textposition="top center", fill='tozeroy', line=dict(color=C_AZUL, width=4, shape='spline')))
                fig.update_layout(yaxis=dict(range=[0, 5.5], tickvals=[1,2,3,4,5]), height=350, margin=dict(t=20, b=0))
                st.plotly_chart(fig, use_container_width=True)
        else: st.info("As avaliações desses afilhados ainda não foram lançadas no sistema.")
    else: st.warning("Não encontramos afilhados vinculados ao seu nome.")

elif menu == "📊 Controle Interno":
    st.markdown(f"<h3 style='color:{C_VERDE}'>📊 Evolução Geral (Controle Interno)</h3>", unsafe_allow_html=True)
    if os.path.exists(AVAL_FILE):
        df_av = pd.read_csv(AVAL_FILE)
        if not df_av.empty:
            al_s = st.selectbox("Escolha qualquer aluno da rede:", sorted(df_av["Aluno"].unique()))
            df_al = df_av[df_av["Aluno"] == al_s]
            if not df_al.empty:
                tri_s = st.selectbox("Selecione o Trimestre", df_al["Trimestre"].unique(), key="int_tri")
                df_filtrado = df_al[df_al["Trimestre"] == tri_s]
                if not df_filtrado.empty:
                    row = df_filtrado.iloc[0]
                    y_vals = [float(row[c]) for c in CATEGORIAS]
                    fig = go.Figure(go.Scatter(x=CATEGORIAS, y=y_vals, mode='lines+markers+text', text=[str(int(v)) for v in y_vals], textposition="top center", fill='tozeroy', line=dict(color=C_VERDE, width=4, shape='spline')))
                    fig.update_layout(yaxis=dict(range=[0, 5.5], tickvals=[1,2,3,4,5]), height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else: st.warning("Nenhum dado encontrado para este trimestre.")
            else: st.warning("Este aluno ainda não possui avaliações lançadas.")
        else: st.info("O banco de dados de avaliações está vazio.")
    else: st.info("Nenhuma avaliação cadastrada no banco de dados.")

elif menu == "👤 Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA}'>👤 Novo Cadastro</h3>", unsafe_allow_html=True)
    with st.form("cad"):
        n, i, comu = st.text_input("Nome"), st.text_input("Idade"), st.text_input("Comunidade")
        t, tn = st.selectbox("Sala", list(TURMAS_CONFIG.keys())), st.selectbox("Turma", ["A", "B"])
        if st.form_submit_button("Cadastrar"):
            df_l = pd.read_csv(ALUNOS_FILE)
            pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Cadastrado!")
