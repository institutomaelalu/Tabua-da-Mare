import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuração e Estilo
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"
C_AZUL_MARE = "#8fd9fb" 

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
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. Conexões e Banco de Dados
CATEGORIAS = [
    "1. Atividades em Grupo/Proatividade", "2. Interesse pelo Novo",
    "3. Compartilhamento de Materiais", "4. Clareza e Desenvoltura",
    "5. Respeito às Regras", "6. Vocabulário Adequado",
    "7. Leitura e Escrita", "8. Compreensão de Comandos",
    "9. Superação de Desafios", "10. Assiduidade"
]

AVAL_FILE = "avaliacoes.csv"
if not os.path.exists(AVAL_FILE):
    # Criar com a coluna Observacoes para evitar o erro de KeyError
    pd.DataFrame(columns=["Aluno", "Periodo"] + CATEGORIAS + ["Observacoes"]).to_csv(AVAL_FILE, index=False)

TURMAS_CONFIG = {
    "SALA ROSA": {"cor": C_ROSA, "key": "sala_rosa"},
    "SALA AMARELA": {"cor": C_AMARELO, "key": "sala_amarela"},
    "SALA VERDE": {"cor": C_VERDE, "key": "sala_verde"},
    "SALA AZUL": {"cor": C_AZUL, "key": "sala_azul"},
    "CIRAND. MUNDO": {"cor": C_ROXO, "key": "cirand_mundo"},
}

def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

def safe_read(worksheet_name):
    try:
        if worksheet_name == "GERAL":
            url = st.secrets["connections"]["gsheets"]["geral"]
        else:
            url = st.secrets["connections"]["gsheets"][TURMAS_CONFIG[worksheet_name]['key']]
        url_csv = url.split("/edit")[0] + "/export?format=csv"
        if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
        df = pd.read_csv(url_csv)
        df.columns = [str(c).strip().upper() for c in df.columns]
        if "PADRINHO" in df.columns: df = df.rename(columns={"PADRINHO": "PADRINHO/MADRINHA"})
        return df.fillna("")
    except:
        return pd.DataFrame()

# 3. Estados de Sessão
if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
if 'sel_mat' not in st.session_state: st.session_state.sel_mat = "SALA ROSA"
if 'sel_pad' not in st.session_state: st.session_state.sel_pad = "SALA ROSA"
if 'sel_aval' not in st.session_state: st.session_state.sel_aval = "SALA ROSA"

# 4. Login
if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown(f'<div class="login-card"><h2 style="text-align: center; color: {C_AZUL}; margin:0;">Acesso</h2></div>', unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("👤 Usuário").strip().upper()
            s = st.text_input("🔑 Chave", type="password")
            if st.form_submit_button("ENTRAR"):
                if u == "ADMIN" and s == "123":
                    st.session_state.update({"logado": True, "perfil": "admin", "nome_usuario": "Coordenação"})
                    st.rerun()
                else:
                    df_g = safe_read("GERAL")
                    if not df_g.empty and u in df_g["PADRINHO/MADRINHA"].astype(str).str.upper().unique() and s == "lalu2026":
                        st.session_state.update({"logado": True, "perfil": "padrinho", "nome_usuario": u})
                        st.rerun()
                    else: st.error("Acesso negado.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.write(f"👤 **{st.session_state.nome_usuario}**")
if st.session_state.perfil == "admin":
    menu = st.sidebar.radio("Navegação", ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução (Padrinhos)", "🌊 Tábua da Maré - Interno"])
else:
    menu = "🌊 Evolução (Padrinhos)"

if st.sidebar.button("🚪 Sair"):
    st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
    st.rerun()

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- ABA: CADASTRO ---
if menu == "👤 Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA}'>👤 Novo Cadastro</h3>", unsafe_allow_html=True)
    with st.form("cad_form"):
        c1, c2 = st.columns(2)
        n, i = c1.text_input("Nome"), c2.text_input("Idade")
        comu, t = c1.text_input("Comunidade"), c2.selectbox("Sala", list(TURMAS_CONFIG.keys()))
        tn = c1.selectbox("Turno", ["A", "B"])
        if st.form_submit_button("Cadastrar"):
            if n and i:
                client = get_gspread_client()
                sh = client.open_by_key("1MBAvQB5xGhE7OAHGWdFPvGfwqzP9SpiaIW4OEl2Mgk4")
                nova_linha = [n.upper(), t, tn, i, comu.upper(), ""]
                sh.worksheet(t).append_row(nova_linha)
                sh.worksheet("GERAL").append_row(nova_linha)
                st.success("Matrícula realizada!"); st.rerun()

# --- ABA: MATRÍCULAS ---
elif menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE}'>📋 Quadro de Matrículas</h3>", unsafe_allow_html=True)
    cols = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        opacity = "1.0" if st.session_state.sel_mat == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {opacity}; }}</style>', unsafe_allow_html=True)
        if cols[i].button(sala, key=f"btn_mat_{sala}"): 
            st.session_state.sel_mat = sala
            st.rerun()
    
    df_geral = safe_read("GERAL")
    df_sala = safe_read(st.session_state.sel_mat)
    cor_h = TURMAS_CONFIG[st.session_state.sel_mat]["cor"]

    f1, f2 = st.columns(2)
    f_tn = f1.selectbox("Turno", ["Todos", "A", "B"])
    f_cm = f2.selectbox("Comunidade", ["Todas"] + sorted(list(df_geral["COMUNIDADE"].unique())))
    
    df_f = df_sala.copy()
    if f_tn != "Todos":
        alunos_turno = df_geral[df_geral["TURNO"].astype(str).str.contains(f_tn)]["ALUNO"].unique()
        df_f = df_f[df_f["ALUNO"].isin(alunos_turno)]
    if f_cm != "Todas":
        df_f = df_f[df_f["COMUNIDADE"] == f_cm]
    
    v_cols = ["ALUNO", "IDADE", "COMUNIDADE"]
    html = f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
    for _, r in df_f.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in v_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# --- ABA: APADRINHAMENTO ---
elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🤝 Gestão de Apadrinhamento</h3>", unsafe_allow_html=True)
    cols_btn = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        opacity = "1.0" if st.session_state.sel_pad == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {opacity}; }}</style>', unsafe_allow_html=True)
        if cols_btn[i].button(sala, key=f"btn_pad_{sala}"): 
            st.session_state.sel_pad = sala
            st.rerun()

    df_geral = safe_read("GERAL")
    df_sala = safe_read(st.session_state.sel_pad)
    cor_h = TURMAS_CONFIG[st.session_state.sel_pad]["cor"]

    f1, f2, f3 = st.columns(3)
    f_tn = f1.selectbox("Turno", ["Todos", "A", "B"])
    f_cm = f2.selectbox("Comunidade", ["Todas"] + sorted(list(df_geral["COMUNIDADE"].unique())))
    f_sp = f3.checkbox("Apenas sem padrinho")
    
    df_f = df_sala.copy()
    if f_tn != "Todos":
        alunos_turno = df_geral[df_geral["TURNO"].astype(str).str.contains(f_tn)]["ALUNO"].unique()
        df_f = df_f[df_f["ALUNO"].isin(alunos_turno)]
    if f_cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm]
    if f_sp: df_f = df_f[df_f["PADRINHO/MADRINHA"].isin(["", "0", "nan", "NAN", None])]

    with st.expander("✨ Vincular Novo Padrinho", expanded=False):
        sem_pad_lista = df_f[df_f["PADRINHO/MADRINHA"].isin(["", "0", "nan", "NAN", None])]
        if not sem_pad_lista.empty:
            c1, c2, c3 = st.columns([2, 2, 1])
            al_vinc = c1.selectbox("Aluno", sorted(sem_pad_lista["ALUNO"].unique()))
            pad_nome = c2.text_input("Nome do Padrinho").upper()
            if c3.button("Vincular"):
                client = get_gspread_client()
                sh = client.open_by_key("1MBAvQB5xGhE7OAHGWdFPvGfwqzP9SpiaIW4OEl2Mgk4")
                sh.worksheet("GERAL").update_cell(sh.worksheet("GERAL").find(al_vinc).row, 6, pad_nome)
                sh.worksheet(st.session_state.sel_pad).update_cell(sh.worksheet(st.session_state.sel_pad).find(al_vinc).row, 6, pad_nome)
                st.success("Vínculo OK!"); st.rerun()

    v_cols = ["ALUNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
    html = f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
    for _, r in df_f.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in v_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# --- ABA: LANÇAR AVALIAÇÃO ---
elif menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO}'>📊 Lançar Tábua da Maré</h3>", unsafe_allow_html=True)
    cols_btn = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        opacity = "1.0" if st.session_state.sel_aval == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {opacity}; }}</style>', unsafe_allow_html=True)
        if cols_btn[i].button(sala, key=f"btn_aval_{sala}"): 
            st.session_state.sel_aval = sala
            st.rerun()

    df_g = safe_read("GERAL")
    df_s = safe_read(st.session_state.sel_aval)
    
    with st.form("aval"):
        al = st.selectbox("Aluno", sorted(df_s["ALUNO"].unique()))
        tr = st.selectbox("Semestre", ["1º Semestre", "2º Semestre"])
        st.write("---")
        # Dicionário para converter marés em números
        MARE_MAP = {"Maré Cheia": 4, "Maré Enchente": 3, "Maré Vazante": 2, "Maré Baixa": 1}
        cols_nt = st.columns(2)
        notas_dict = {}
        for idx, cat in enumerate(CATEGORIAS):
            notas_dict[cat] = cols_nt[idx % 2].selectbox(cat, list(MARE_MAP.keys()))
        
        obs = st.text_area("Observações sobre o desenvolvimento:")
        
        if st.form_submit_button("Salvar Avaliação"):
            df_av = pd.read_csv(AVAL_FILE)
            df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Periodo'] == tr))]
            valores_num = [MARE_MAP[notas_dict[c]] for c in CATEGORIAS]
            pd.concat([df_av, pd.DataFrame([[al, tr] + valores_num + [obs]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
            st.success("Salvo!")

# --- AJUSTE 1: ABA EVOLUÇÃO (LISTA DE PADRINHOS E GRÁFICO AZUL) ---
elif menu == "🌊 Evolução (Padrinhos)":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🌊 Evolução dos Afilhados</h3>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    df_av = pd.read_csv(AVAL_FILE)
    
    # AJUSTE 1.1: Garantir que a lista de padrinhos seja carregada corretamente
    # Limpamos valores vazios ou nulos da lista
    lista_padrinhos = sorted([p for p in df_g["PADRINHO/MADRINHA"].unique() if str(p).strip() not in ["", "0", "nan", "NAN", "None"]])
    
    if st.session_state.perfil == "admin":
        padrinho = st.selectbox("Selecione o Padrinho:", [""] + lista_padrinhos)
    else: 
        padrinho = st.session_state.nome_usuario

    if padrinho:
        afilhas = df_g[df_g["PADRINHO/MADRINHA"].astype(str).str.upper() == padrinho.upper()]
        if not afilhas.empty:
            st.write(f"#### Olá, **{padrinho}**! ✨")
            al_s = st.selectbox("Afilhado:", sorted(afilhas["ALUNO"].unique()))
            df_al = df_av[df_av["Aluno"] == al_s]
            if not df_al.empty:
                tri = st.selectbox("Semestre", df_al["Periodo"].unique())
                row = df_al[df_al["Periodo"] == tri].iloc[0]
                
                # AJUSTE 1.2: Gráfico com a cor Azul Maré (C_AZUL_MARE) em vez de verde
                fig = go.Figure(go.Scatter(
                    x=CATEGORIAS, 
                    y=[float(row[c]) for c in CATEGORIAS], 
                    fill='tozeroy', 
                    line=dict(color=C_AZUL_MARE, width=4, shape='spline')
                ))
                fig.update_layout(yaxis=dict(range=[0.5, 4.5], showticklabels=False), height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                if "Observacoes" in row and str(row["Observacoes"]).strip() not in ["nan", ""]:
                    st.info(f"**Observações:** {row['Observacoes']}")
            else: 
                st.info("Avaliações ainda não lançadas para este aluno.")
        else: 
            st.warning("Nenhum afilhado vinculado a este padrinho.")

# --- ABA: TÁBUA DA MARÉ INTERNO (MANTÉM O VERDE) ---
elif menu == "🌊 Tábua da Maré - Interno":
    st.markdown(f"<h3 style='color:{C_VERDE}'>🌊 Tábua da Maré</h3>", unsafe_allow_html=True)
    df_av = pd.read_csv(AVAL_FILE)
    if not df_av.empty:
        al_s = st.selectbox("Pesquisar Aluno:", sorted(df_av["Aluno"].unique()))
        df_al = df_av[df_av["Aluno"] == al_s]
        if not df_al.empty:
            tri = st.selectbox("Semestre ", df_al["Periodo"].unique())
            row = df_al[df_al["Periodo"] == tri].iloc[0]
            # Aqui permanece Verde conforme solicitado para a visão interna
            fig = go.Figure(go.Scatter(
                x=CATEGORIAS, 
                y=[float(row[c]) for c in CATEGORIAS], 
                mode='lines+markers+text', 
                text=[str(int(row[c])) for c in CATEGORIAS], 
                fill='tozeroy', 
                line=dict(color=C_VERDE, width=4, shape='spline')
            ))
            fig.update_layout(yaxis=dict(range=[0.5, 4.5], showticklabels=False), height=450)
            st.plotly_chart(fig, use_container_width=True)
