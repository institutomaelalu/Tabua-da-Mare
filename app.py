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
    /* Estilização para a trilha de alfabetização */
    .stSelectSlider label {{ font-weight: 700 !important; color: {C_AZUL} !important; }}
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

MARE_LABELS = {4: "Muito bom (Maré Cheia)", 3: "Em evolução (Maré Enchente)", 2: "Requer atenção (Maré Vazante)", 1: "Início (Maré Baixa)"}
MARE_OPCOES = {"Maré Cheia": 4, "Maré Enchente": 3, "Maré Vazante": 2, "Maré Baixa": 1}

# Níveis Alfabetização
NIVEIS_ALF = [
    "1. Pré-Silábico", "2. Silábico s/ Valor", "3. Silábico c/ Valor", 
    "4. Silábico Alfabético", "5. Alfabético", "6. Alfabético Ortográfico"
]

AVAL_FILE = "avaliacoes.csv"
ALF_FILE = "alfabetizacao.csv"

# Inicialização de arquivos
for f, cols in {AVAL_FILE: ["Aluno", "Periodo"] + CATEGORIAS + ["Observacoes"], 
                ALF_FILE: ["Aluno", "Nivel", "Gatilho", "Evidencias", "Obs"]}.items():
    if not os.path.exists(f): pd.DataFrame(columns=cols).to_csv(f, index=False)

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
for k in ['sel_mat', 'sel_pad', 'sel_aval', 'sel_int', 'sel_alf']:
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
    if cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == cm]
    return df_f

def render_botoes_salas(key_prefix, session_key):
    cols = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        op = "1.0" if st.session_state[session_key] == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {op}; }}</style>', unsafe_allow_html=True)
        if cols[i].button(sala, key=f"{key_prefix}_{sala}"):
            st.session_state[session_key] = sala; st.rerun()

def criar_grafico_mare(categorias, valores):
    fig = go.Figure(go.Scatter(
        x=categorias, y=valores, fill='tozeroy', mode='lines',
        line=dict(color=C_AZUL_MARE, width=5, shape='spline'),
        text=[MARE_LABELS[int(v)] for v in valores], hoverinfo="text+x"
    ))
    fig.update_layout(
        paper_bgcolor='white', plot_bgcolor='white',
        yaxis=dict(range=[0.5, 4.5], visible=False),
        xaxis=dict(showgrid=False, zeroline=False, showspikes=True, spikemode='toaxis', spikedash='dot', spikecolor="#d1d1d1", spikethickness=1),
        height=450, margin=dict(l=20, r=20, t=30, b=80), hovermode="x"
    )
    return fig

# --- SIDEBAR ---
menu_options = ["👤 Cadastro", "📝 Matrículas", "📊 Lançar Avaliação", "📖 Programa Alfabetização", "🌊 Evolução (Padrinhos)", "🌊 Tábua da Maré - Interno"] if st.session_state.perfil == "admin" else ["🌊 Evolução (Padrinhos)"]
menu = st.sidebar.radio("Navegação", menu_options)
if st.sidebar.button("🚪 Sair"):
    st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""}); st.rerun()

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- LOGICA DE ABAS ---

if menu == "📖 Programa Alfabetização":
    st.markdown(f"<h3 style='color:{C_ROXO}'>📖 Trilha de Alfabetização</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_alf", "sel_alf")
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_alf)
    tn, cm = render_filtros(df_g, "alf")
    df_f = aplicar_filtros(df_s, df_g, tn, cm)
    
    with st.form("form_alf"):
        al = st.selectbox("Aluno", sorted(df_f["ALUNO"].unique()))
        
        st.markdown("---")
        # Trilha Visual
        nivel_atual = st.select_slider("Nível de Diagnóstico Atual:", options=NIVEIS_ALF)
        
        c1, c2 = st.columns(2)
        gatilho = c1.checkbox("Atende o Gatilho de Passagem?")
        evidencias = c2.multiselect("Sinais de Avanço (Evidências):", 
                                   ["Leitura de sílabas simples", "Diferenciação letra/desenho", 
                                    "Escrita fonética completa", "Uso de dígrafos", "Consciência fonológica"])
        
        obs_alf = st.text_area("Observações (Ex: Percepção em palavras complexas, travamentos):")
        
        if st.form_submit_button("Salvar Progresso na Trilha"):
            df_alf = pd.read_csv(ALF_FILE)
            # Remove anterior para atualizar
            df_alf = df_alf[df_alf["Aluno"] != al]
            nova_data = pd.DataFrame([[al, nivel_atual, gatilho, ", ".join(evidencias), obs_alf]], columns=df_alf.columns)
            pd.concat([df_alf, nova_data], ignore_index=True).to_csv(ALF_FILE, index=False)
            st.success(f"Evolução de {al} registrada!")

elif menu == "🌊 Evolução (Padrinhos)":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🌊 Evolução dos Afilhados</h3>", unsafe_allow_html=True)
    dfs = [safe_read(s) for s in TURMAS_CONFIG.keys()]
    df_full = pd.concat(dfs, ignore_index=True)
    p_sel = st.selectbox("Simular Padrinho:", sorted([p for p in df_full["PADRINHO/MADRINHA"].unique() if str(p).strip() not in ["", "0", "nan"]])) if st.session_state.perfil == "admin" else st.session_state.nome_usuario
    
    if p_sel:
        df_av = pd.read_csv(AVAL_FILE)
        afilhas_f = df_full[(df_full["PADRINHO/MADRINHA"].astype(str).str.upper() == p_sel.upper()) & (df_full["ALUNO"].isin(df_av["Aluno"].unique()))]
        if not afilhas_f.empty:
            al_s = st.selectbox("Selecione o Afilhado:", sorted(afilhas_f["ALUNO"].unique()))
            df_al = df_av[df_av["Aluno"] == al_s]
            tri = st.selectbox("Semestre", df_al["Periodo"].unique())
            row = df_al[df_al["Periodo"] == tri].iloc[0]
            st.plotly_chart(criar_grafico_mare(CATEGORIAS, [float(row[c]) for c in CATEGORIAS]), use_container_width=True)
            st.info(f"**Observações:** {row['Observacoes']}")
            
            # Mostrar trilha de alfabetização se existir
            df_alf_view = pd.read_csv(ALF_FILE)
            if al_s in df_alf_view["Aluno"].values:
                alf_row = df_alf_view[df_alf_view["Aluno"] == al_s].iloc[0]
                st.markdown(f"**Nível de Alfabetização:** `{alf_row['Nivel']}`")
        else: st.warning("Ainda não há avaliações disponíveis.")

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
        c1, c2 = st.columns(2); n, i = c1.text_input("Nome").strip(), c2.text_input("Idade").strip()
        comu, t = c1.text_input("Comunidade").strip(), c2.selectbox("Sala", list(TURMAS_CONFIG.keys()))
        tn = c1.selectbox("Turno", ["A", "B"])
        if st.form_submit_button("Cadastrar Aluno"):
            if n and i:
                client = get_gspread_client(); sh = client.open_by_key("1MBAvQB5xGhE7OAHGWdFPvGfwqzP9SpiaIW4OEl2Mgk4")
                nl = [n.upper(), t, tn, i, comu.upper(), ""]
                sh.worksheet(t).append_row(nl); sh.worksheet("GERAL").append_row(nl)
                st.success("Cadastro realizado!"); st.rerun()

elif menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO}'>📊 Lançar Tábua da Maré</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_aval", "sel_aval")
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_aval)
    tn, cm = render_filtros(df_g, "aval")
    df_f = aplicar_filtros(df_s, df_g, tn, cm)
    with st.form("aval"):
        al, tr = st.selectbox("Aluno", sorted(df_f["ALUNO"].unique())), st.selectbox("Semestre", ["1º Semestre", "2º Semestre"])
        col_esq, col_dir = st.columns(2); n_l = {}
        for idx, cat in enumerate(CATEGORIAS): n_l[cat] = (col_esq if idx < 5 else col_dir).selectbox(cat, list(MARE_OPCOES.keys()), key=f"sel_{idx}")
        obs = st.text_area("Observações:"); 
        if st.form_submit_button("Salvar Avaliação"):
            df_av = pd.read_csv(AVAL_FILE); df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Periodo'] == tr))]
            pd.concat([df_av, pd.DataFrame([[al, tr] + [MARE_OPCOES[n_l[c]] for c in CATEGORIAS] + [obs]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
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
        df_al = df_av[df_av["Aluno"] == al_s]; tri = st.selectbox("Semestre ", df_al["Periodo"].unique())
        row = df_al[df_al["Periodo"] == tri].iloc[0]
        st.plotly_chart(criar_grafico_mare(CATEGORIAS, [float(row[c]) for c in CATEGORIAS]), use_container_width=True)
