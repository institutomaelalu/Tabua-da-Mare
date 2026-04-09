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
    </style>
    """, unsafe_allow_html=True)

# 2. Definições
CATEGORIAS = [
    "1. Atividades em Grupo/Proatividade", "2. Interesse pelo Novo",
    "3. Compartilhamento de Materiais", "4. Clareza e Desenvoltura",
    "5. Respeito às Regras", "6. Vocabulário Adequado",
    "7. Leitura e Escrita", "8. Compreensão de Comandos",
    "9. Superação de Desafios", "10. Assiduidade"
]
MARE_OPCOES = {"Maré Cheia": 4, "Maré Enchente": 3, "Maré Vazante": 2, "Maré Baixa": 1}
AVAL_FILE = "avaliacoes.csv"
if not os.path.exists(AVAL_FILE):
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
        if worksheet_name == "GERAL": url = st.secrets["connections"]["gsheets"]["geral"]
        else: url = st.secrets["connections"]["gsheets"][TURMAS_CONFIG[worksheet_name]['key']]
        url_csv = url.split("/edit")[0] + "/export?format=csv"
        if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
        df = pd.read_csv(url_csv)
        df.columns = [str(c).strip().upper() for c in df.columns]
        if "PADRINHO" in df.columns: df = df.rename(columns={"PADRINHO": "PADRINHO/MADRINHA"})
        return df.fillna("")
    except: return pd.DataFrame()

# 3. Estados de Sessão
if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
for k in ['sel_mat', 'sel_pad', 'sel_aval', 'sel_int']:
    if k not in st.session_state: st.session_state[k] = "SALA ROSA"

# 4. Login
if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        with st.form("login"):
            u = st.text_input("👤 Usuário").strip().upper()
            s = st.text_input("🔑 Chave", type="password")
            if st.form_submit_button("ENTRAR"):
                if u == "ADMIN" and s == "123":
                    st.session_state.update({"logado": True, "perfil": "admin", "nome_usuario": "Coordenação"})
                    st.rerun()
                else:
                    encontrado = False
                    for sala in TURMAS_CONFIG.keys():
                        df_s = safe_read(sala)
                        if not df_s.empty and "PADRINHO/MADRINHA" in df_s.columns:
                            if u in df_s["PADRINHO/MADRINHA"].astype(str).str.strip().str.upper().unique():
                                encontrado = True; break
                    if encontrado:
                        st.session_state.update({"logado": True, "perfil": "padrinho", "nome_usuario": u})
                        st.rerun()
                    else: st.error("Usuário não localizado.")
    st.stop()

# --- FUNÇÕES DE INTERFACE ---
def render_filtros(df_geral, key_suffix):
    f1, f2 = st.columns(2)
    tn = f1.selectbox("Filtrar Turno", ["Todos", "A", "B"], key=f"tn_{key_suffix}")
    comu_list = ["Todas"] + sorted([c for c in df_geral["COMUNIDADE"].unique() if str(c).strip()])
    cm = f2.selectbox("Filtrar Comunidade", comu_list, key=f"cm_{key_suffix}")
    return tn, cm

def aplicar_filtros(df_alvo, df_geral, tn, cm):
    df_f = df_alvo.copy()
    if tn != "Todos":
        alunos_turno = df_geral[df_geral["TURNO"].astype(str).str.contains(tn)]["ALUNO"].unique()
        df_f = df_f[df_f["ALUNO"].isin(alunos_turno)]
    if cm != "Todas":
        df_f = df_f[df_f["COMUNIDADE"] == cm]
    return df_f

def render_botoes_salas(key_prefix, session_key):
    cols = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        op = "1.0" if st.session_state[session_key] == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {op}; }}</style>', unsafe_allow_html=True)
        if cols[i].button(sala, key=f"{key_prefix}_{sala}"):
            st.session_state[session_key] = sala; st.rerun()

# --- SIDEBAR ---
menu_options = ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução (Padrinhos)", "🌊 Tábua da Maré - Interno"] if st.session_state.perfil == "admin" else ["🌊 Evolução (Padrinhos)"]
menu = st.sidebar.radio("Navegação", menu_options)
if st.sidebar.button("🚪 Sair"):
    st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""}); st.rerun()

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- ABAS ---

if menu == "🌊 Evolução (Padrinhos)":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🌊 Evolução dos Afilhados</h3>", unsafe_allow_html=True)
    dfs = [safe_read(s) for s in TURMAS_CONFIG.keys()]
    df_full = pd.concat(dfs, ignore_index=True)
    
    if st.session_state.perfil == "admin":
        padrinhos_list = sorted([p for p in df_full["PADRINHO/MADRINHA"].unique() if str(p).strip() not in ["", "0", "nan"]])
        p_sel = st.selectbox("Simular Padrinho:", padrinhos_list)
    else: p_sel = st.session_state.nome_usuario
    
    if p_sel:
        st.write(f"#### Olá, **{p_sel}**! ✨")
        df_av = pd.read_csv(AVAL_FILE)
        afilhas = df_full[df_full["PADRINHO/MADRINHA"].astype(str).str.upper() == p_sel.upper()]
        afilhas_f = afilhas[afilhas["ALUNO"].isin(df_av["Aluno"].unique())]
        
        if not afilhas_f.empty:
            al_s = st.selectbox("Selecione o Afilhado:", sorted(afilhas_f["ALUNO"].unique()))
            df_al = df_av[df_av["Aluno"] == al_s]
            tri = st.selectbox("Semestre", df_al["Periodo"].unique())
            row = df_al[df_al["Periodo"] == tri].iloc[0]
            fig = go.Figure(go.Scatter(x=CATEGORIAS, y=[float(row[c]) for c in CATEGORIAS], fill='tozeroy', mode='lines+markers', line=dict(color=C_AZUL_MARE, width=4, shape='spline')))
            fig.update_layout(yaxis=dict(range=[0.5, 4.5], showticklabels=False, gridcolor="#f0f0f0", griddash='dot'), xaxis=dict(showgrid=True, gridcolor="#f8f8f8", griddash='dot'), height=500)
            st.plotly_chart(fig, use_container_width=True)
            st.info(f"**Observações:** {row['Observacoes']}")
        else: st.warning("Ainda não há avaliações para seus afilhados!")

elif menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE}'>📋 Quadro de Matrículas</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_mat", "sel_mat")
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_mat)
    tn, cm = render_filtros(df_g, "mat")
    df_f = aplicar_filtros(df_s, df_g, tn, cm)
    cor_h = TURMAS_CONFIG[st.session_state.sel_mat]["cor"]
    v_cols = ["ALUNO", "IDADE", "COMUNIDADE"]
    html = f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
    for _, r in df_f.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in v_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

elif menu == "👤 Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA}'>👤 Novo Cadastro</h3>", unsafe_allow_html=True)
    with st.form("cad_form"):
        c1, c2 = st.columns(2)
        n, i = c1.text_input("Nome").strip(), c2.text_input("Idade").strip()
        comu, t = c1.text_input("Comunidade").strip(), c2.selectbox("Sala", list(TURMAS_CONFIG.keys()))
        tn = c1.selectbox("Turno", ["A", "B"])
        if st.form_submit_button("Cadastrar Aluno"):
            if n and i:
                client = get_gspread_client()
                sh = client.open_by_key("1MBAvQB5xGhE7OAHGWdFPvGfwqzP9SpiaIW4OEl2Mgk4")
                nova_linha = [n.upper(), t, tn, i, comu.upper(), ""]
                sh.worksheet(t).append_row(nova_linha); sh.worksheet("GERAL").append_row(nova_linha)
                st.success("Cadastro realizado com sucesso!"); st.rerun()

elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🤝 Gestão de Apadrinhamento</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_pad", "sel_pad")
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_pad)
    tn, cm = render_filtros(df_g, "pad")
    df_f = aplicar_filtros(df_s, df_g, tn, cm)
    cor_h = TURMAS_CONFIG[st.session_state.sel_pad]["cor"]
    v_cols = ["ALUNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
    html = f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
    for _, r in df_f.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in v_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

elif menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO}'>📊 Lançar Tábua da Maré</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_aval", "sel_aval")
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_aval)
    tn, cm = render_filtros(df_g, "aval")
    df_f = aplicar_filtros(df_s, df_g, tn, cm)
    with st.form("aval"):
        c1, c2 = st.columns(2)
        al, tr = c1.selectbox("Aluno", sorted(df_f["ALUNO"].unique())), c2.selectbox("Semestre", ["1º Semestre", "2º Semestre"])
        st.markdown("<h4 style='text-align: center; color: #444; margin: 20px 0;'>10 motivos para avaliar!</h4>", unsafe_allow_html=True)
        col_esq, col_dir = st.columns(2)
        notas_letras = {}
        for idx, cat in enumerate(CATEGORIAS):
            notas_letras[cat] = (col_esq if idx < 5 else col_dir).selectbox(cat, list(MARE_OPCOES.keys()), key=f"sel_{idx}")
        obs = st.text_area("Observações sobre o desenvolvimento:")
        if st.form_submit_button("Salvar Avaliação"):
            df_av = pd.read_csv(AVAL_FILE)
            df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Periodo'] == tr))]
            valores_num = [MARE_OPCOES[notas_letras[c]] for c in CATEGORIAS]
            pd.concat([df_av, pd.DataFrame([[al, tr] + valores_num + [obs]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
            st.success("Avaliação salva!")

elif menu == "🌊 Tábua da Maré - Interno":
    st.markdown(f"<h3 style='color:{C_VERDE}'>🌊 Tábua da Maré</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_int", "sel_int")
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_int)
    tn, cm = render_filtros(df_g, "int")
    df_f = aplicar_filtros(df_s, df_g, tn, cm)
    df_av = pd.read_csv(AVAL_FILE)
    alunos_lista = sorted(df_f[df_f["ALUNO"].isin(df_av["Aluno"].unique())]["ALUNO"].unique())
    if alunos_lista:
        al_s = st.selectbox("Selecione o Aluno:", alunos_lista)
        df_al = df_av[df_av["Aluno"] == al_s]
        tri = st.selectbox("Semestre ", df_al["Periodo"].unique())
        row = df_al[df_al["Periodo"] == tri].iloc[0]
        fig = go.Figure(go.Scatter(x=CATEGORIAS, y=[float(row[c]) for c in CATEGORIAS], mode='lines+markers', fill='tozeroy', line=dict(color=C_AZUL_MARE, width=4, shape='spline')))
        fig.update_layout(yaxis=dict(range=[0.5, 4.5], showticklabels=False, gridcolor="#f0f0f0", griddash='dot'), xaxis=dict(showgrid=True, gridcolor="#f8f8f8", griddash='dot'), height=450)
        st.plotly_chart(fig, use_container_width=True)
