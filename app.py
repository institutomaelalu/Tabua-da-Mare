import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Configuração e Estilo
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp {{ background-color: #ffffff; font-family: 'Inter', sans-serif; }}
    .main-header {{ text-align: center; padding: 20px 0; }}
    .main-header h1 {{ font-size: 42px !important; font-weight: 800; }}

    .custom-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        border: 1px solid #f0f0f0; border-radius: 10px;
        overflow: hidden; font-size: 13px; margin-top: 5px;
    }}
    .custom-table thead th {{ padding: 12px 10px; text-align: left; color: white !important; font-weight: 700; border: none; }}
    .custom-table tbody td {{ padding: 8px 10px; border-bottom: 1px solid #fafafa; color: #444 !important; font-weight: 500; }}
    
    div.stButton > button {{
        width: 100%; border-radius: 8px !important; font-weight: 700 !important; 
        height: 42px; font-size: 11px !important; border: none !important;
        transition: all 0.3s;
    }}

    .login-card {{
        background: linear-gradient(135deg, {C_AZUL}22, {C_ROSA}22);
        padding: 30px; border-radius: 20px; border: 2px solid #f0f0f0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. Banco de Dados
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE, AVAL_FILE, PADRINHOS_FILE = "alunos.csv", "avaliacoes.csv", "padrinhos_local.csv"

def init_db():
    for f, cols in {ALUNOS_FILE: ["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"], 
                    AVAL_FILE: ["Aluno", "Trimestre"] + CATEGORIAS, 
                    PADRINHOS_FILE: ["ALUNO", "PADRINHO_EDITADO"]}.items():
        if not os.path.exists(f): pd.DataFrame(columns=cols).to_csv(f, index=False)
init_db()

TURMAS_CONFIG = {
    "SALA ROSA": {"cor": C_ROSA, "key": "sala_rosa"},
    "SALA AMARELA": {"cor": C_AMARELO, "key": "sala_amarela"},
    "SALA VERDE": {"cor": C_VERDE, "key": "sala_verde"},
    "SALA AZUL": {"cor": C_AZUL, "key": "sala_azul"},
    "CIRAND. MUNDO": {"cor": C_ROXO, "key": "cirand_mundo"},
}

def safe_read(worksheet_name):
    df = pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])
    try:
        if worksheet_name == "GERAL":
            dfs = []
            for k, conf in TURMAS_CONFIG.items():
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
        full = pd.concat([df, df_l], ignore_index=True) if worksheet_name == "GERAL" else df.copy()
        full["ALUNO"] = full["ALUNO"].astype(str).str.strip().str.upper()
        for _, r in df_p.iterrows():
            full.loc[full["ALUNO"] == str(r["ALUNO"]).strip().upper(), "PADRINHO/MADRINHA"] = r["PADRINHO_EDITADO"]
        return full.fillna("")
    except: return df.fillna("")

# 3. Autenticação
if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
if 'sel_mat' not in st.session_state: st.session_state.sel_mat = "SALA ROSA"
if 'sel_pad' not in st.session_state: st.session_state.sel_pad = "SALA ROSA"

if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown(f'<div class="login-card"><h2 style="text-align: center; color: {C_AZUL}; margin:0;">Bem-vindo!</h2></div>', unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("👤 Usuário").strip().upper()
            s = st.text_input("🔑 Chave", type="password")
            if st.form_submit_button("ENTRAR NO SISTEMA"):
                if u == "ADMIN" and s == "123":
                    st.session_state.update({"logado": True, "perfil": "admin", "nome_usuario": "Coordenação"})
                    st.rerun()
                else:
                    validos = safe_read("GERAL")["PADRINHO/MADRINHA"].astype(str).str.strip().str.upper().unique()
                    if u in validos and s == "lalu2026":
                        st.session_state.update({"logado": True, "perfil": "padrinho", "nome_usuario": u})
                        st.rerun()
                    else: st.error("Acesso negado.")
    st.stop()

# --- SIDEBAR & SAIR ---
st.sidebar.write(f"👤 **{st.session_state.nome_usuario}**")
if st.sidebar.button("🚪 Sair"):
    st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
    st.rerun()

if st.session_state.perfil == "admin":
    menu = st.sidebar.radio("Navegação", ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução (Padrinhos)", "🌊 Tábua da Maré - Interno"])
else:
    menu = "🌊 Evolução (Padrinhos)"

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- FUNCIONALIDADES ---

if menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE}'>📋 Quadro de Matrículas</h3>", unsafe_allow_html=True)
    cols = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        opacity = "1.0" if st.session_state.sel_mat == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {opacity}; }}</style>', unsafe_allow_html=True)
        if cols[i].button(sala, key=f"btn_mat_{sala}"): 
            st.session_state.sel_mat = sala
            st.rerun()
    
    df = safe_read(st.session_state.sel_mat)
    cor_h = TURMAS_CONFIG[st.session_state.sel_mat]["cor"]
    
    f1, f2 = st.columns(2)
    f_tn = f1.selectbox("Filtrar Turno", ["Todos", "A", "B"])
    f_cm = f2.selectbox("Filtrar Comunidade", ["Todas"] + sorted(list(df["COMUNIDADE"].unique())))
    
    df_f = df.copy()
    if f_tn != "Todos": df_f = df_f[df_f["TURNO"].astype(str).str.contains(f_tn)]
    if f_cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm]
    
    v_cols = ["ALUNO", "TURMA", "IDADE", "COMUNIDADE"]
    html = f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
    for _, r in df_f.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in v_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🤝 Gestão de Apadrinhamento</h3>", unsafe_allow_html=True)
    
    cols_btn = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        opacity = "1.0" if st.session_state.sel_pad == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {opacity}; }}</style>', unsafe_allow_html=True)
        if cols_btn[i].button(sala, key=f"btn_pad_{sala}"): 
            st.session_state.sel_pad = sala
            st.rerun()

    df = safe_read(st.session_state.sel_pad)
    cor_h = TURMAS_CONFIG[st.session_state.sel_pad]["cor"]

    # --- NOVO: SEÇÃO DE VINCULAÇÃO ACIMA DA TABELA ---
    with st.expander("✨ Vincular Novo Padrinho/Madrinha", expanded=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        al_vinc = c1.selectbox("Selecionar Aluno", sorted(df["ALUNO"].unique()), key="sel_al_vinc")
        pad_nome = c2.text_input("Nome do Padrinho/Madrinha", key="input_pad_nome")
        if c3.button("Confirmar Vínculo", use_container_width=True):
            if pad_nome:
                df_p = pd.read_csv(PADRINHOS_FILE)
                df_p = df_p[df_p["ALUNO"] != al_vinc.upper()]
                pd.concat([df_p, pd.DataFrame([[al_vinc.upper(), pad_nome.upper()]], columns=["ALUNO", "PADRINHO_EDITADO"])], ignore_index=True).to_csv(PADRINHOS_FILE, index=False)
                st.success(f"Vínculo de {al_vinc} atualizado!")
                st.rerun()
            else: st.warning("Digite o nome do padrinho.")

    f1, f2, f3 = st.columns(3)
    f_tn = f1.selectbox("Turno ", ["Todos", "A", "B"])
    f_cm = f2.selectbox("Comunidade ", ["Todas"] + sorted(list(df["COMUNIDADE"].unique())))
    f_sp = f3.checkbox("Apenas sem padrinho")
    
    df_f = df.copy()
    if f_tn != "Todos": df_f = df_f[df_f["TURNO"].astype(str).str.contains(f_tn)]
    if f_cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm]
    if f_sp: df_f = df_f[df_f["PADRINHO/MADRINHA"].isin(["", "0", "nan", "NAN"])]
    
    v_cols = ["ALUNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
    html = f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
    for _, r in df_f.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in v_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

elif menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO}'>📊 Lançar Notas</h3>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    with st.form("aval"):
        al = st.selectbox("Aluno", sorted(df_g["ALUNO"].unique()))
        tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
        st.write("---")
        cols_nt = st.columns(2)
        notas = {}
        for idx, cat in enumerate(CATEGORIAS):
            notas[cat] = cols_nt[idx % 2].slider(cat, 1, 5, 3)
        if st.form_submit_button("Salvar Avaliação"):
            df_av = pd.read_csv(AVAL_FILE)
            df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
            pd.concat([df_av, pd.DataFrame([[al, tr] + [float(v) for v in notas.values()]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
            st.success(f"Avaliação de {al} registrada!")

elif menu == "🌊 Evolução (Padrinhos)":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🌊 Evolução dos Afilhados</h3>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    df_av = pd.read_csv(AVAL_FILE) if os.path.exists(AVAL_FILE) else pd.DataFrame()
    
    if st.session_state.perfil == "admin":
        lista_p = sorted([p for p in df_g["PADRINHO/MADRINHA"].unique() if str(p) not in ["", "0", "nan", "NAN"]])
        padrinho_alvo = st.selectbox("🎯 Simular visão do Padrinho:", lista_p)
    else: padrinho_alvo = st.session_state.nome_usuario

    afilhas = df_g[df_g["PADRINHO/MADRINHA"].astype(str).str.upper() == padrinho_alvo.upper()]
    if not afilhas.empty:
        st.markdown(f"#### Olá, **{padrinho_alvo}**! ✨")
        st.write("É uma alegria ter você conosco. Acompanhe abaixo o desenvolvimento das crianças que você apoia:")
        
        al_s = st.selectbox("Selecione o afilhado para ver o gráfico:", afilhas["ALUNO"].unique())
        df_al = df_av[df_av["Aluno"] == al_s]
        
        if not df_al.empty:
            tri = st.selectbox("Selecione o Trimestre:", df_al["Trimestre"].unique())
            row = df_al[df_al["Trimestre"] == tri].iloc[0]
            fig = go.Figure(go.Scatter(x=CATEGORIAS, y=[float(row[c]) for c in CATEGORIAS], fill='tozeroy', line=dict(color=C_AZUL, width=4, shape='spline')))
            fig.update_layout(yaxis=dict(range=[0, 5.5], tickvals=[1,2,3,4,5]), height=400, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else: st.info(f"As avaliações de **{al_s}** ainda estão sendo processadas pela coordenação.")
    else: st.warning("Não encontramos afilhados vinculados ao seu usuário.")

elif menu == "🌊 Tábua da Maré - Interno":
    st.markdown(f"<h3 style='color:{C_VERDE}'>🌊 Tábua da Maré - Interno</h3>", unsafe_allow_html=True)
    if os.path.exists(AVAL_FILE):
        df_av = pd.read_csv(AVAL_FILE)
        if not df_av.empty:
            al_s = st.selectbox("Pesquisar Aluno:", sorted(df_av["Aluno"].unique()))
            df_al = df_av[df_av["Aluno"] == al_s]
            if not df_al.empty:
                tri = st.selectbox("Trimestre", df_al["Trimestre"].unique(), key="tri_tabua")
                row = df_al[df_al["Trimestre"] == tri].iloc[0]
                y_vals = [float(row[c]) for c in CATEGORIAS]
                fig = go.Figure(go.Scatter(x=CATEGORIAS, y=y_vals, mode='lines+markers+text', text=[str(int(v)) for v in y_vals], textposition="top center", fill='tozeroy', line=dict(color=C_VERDE, width=4, shape='spline')))
                fig.update_layout(yaxis=dict(range=[0, 5.5], tickvals=[1,2,3,4,5]), height=450)
                st.plotly_chart(fig, use_container_width=True)
            else: st.warning("Este aluno ainda não possui notas lançadas.")
        else: st.info("O banco de dados de avaliações está vazio.")

elif menu == "👤 Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA}'>👤 Novo Cadastro</h3>", unsafe_allow_html=True)
    with st.form("cad_form"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nome do Aluno")
        i = c2.text_input("Idade")
        comu = c1.text_input("Comunidade")
        t = c2.selectbox("Sala", list(TURMAS_CONFIG.keys()))
        tn = c1.selectbox("Turno", ["A", "B"])
        if st.form_submit_button("Finalizar Cadastro"):
            if n:
                df_l = pd.read_csv(ALUNOS_FILE)
                pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
                st.success(f"Aluno {n.upper()} cadastrado com sucesso!")
            else: st.error("O nome é obrigatório.")
