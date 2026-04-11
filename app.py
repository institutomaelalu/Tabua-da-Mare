import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import gspread
from google.oauth2.service_account import Credentials

# =================================================================
# 1. CONFIGURAÇÃO E CONSTANTES
# =================================================================
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

# Definições Globais
CATEGORIAS = [
    "Atividades em grupo/Proatividade", "Interesse pelo novo", "Compartilhamento de Materiais",
    "Clareza e desenvoltura", "Respeito às regras", "Vocabulário adequado",
    "Leitura e Escrita", "Compreensão de comandos", "Superação de desafios", "Assiduidade"
]

NIVEIS_ALF = [
    "1. Pré-Silábico", "2. Silábico s/ Valor", "3. Silábico c/ Valor", 
    "4. Silábico Alfabético", "5. Alfabético Inicial", "6. Alfabético Final", 
    "7. Alfabético Ortográfico"
]

MAPA_NIVEIS = {niv: i+1 for i, niv in enumerate(NIVEIS_ALF)}

CORES_EXCLUSIVAS = {
    "1. Pré-Silábico": "#FFDADA", "2. Silábico s/ Valor": "#FFE8D1", 
    "3. Silábico c/ Valor": "#FFF9DB", "4. Silábico Alfabético": "#E3FAFC", 
    "5. Alfabético Inicial": "#E3F9E5", "6. Alfabético Final": "#E7F5FF", 
    "7. Alfabético Ortográfico": "#F3F0FF"
}

MARE_LABELS = {1: "Maré Baixa", 2: "Maré Vazante", 3: "Maré Enchente", 4: "Maré Alta", 5: "Maré Cheia"}

# Cores de Identidade Visual
C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"
C_AZUL_MARE = "#8fd9fb"

TURMAS_CONFIG = {
    "SALA ROSA": {"cor": C_ROSA, "key": "sala_rosa"},
    "SALA AMARELA": {"cor": C_AMARELO, "key": "sala_amarela"},
    "SALA VERDE": {"cor": C_VERDE, "key": "sala_verde"},
    "SALA AZUL": {"cor": C_AZUL, "key": "sala_azul"},
    "CIRAND. MUNDO": {"cor": C_ROXO, "key": "cirand_mundo"},
}

# =================================================================
# 2. CONEXÃO E FUNÇÕES DE DADOS
# =================================================================
conn = st.connection("gsheets", type=GSheetsConnection)

def get_sheet_id():
    raw_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    return raw_url.split("/d/")[-1].split("/")[0] if "/d/" in raw_url else raw_url

sheet_id = get_sheet_id()

def get_text_color(nivel):
    return "#2C3E50"

def registrar_tabua_mare(aluno, sala, semestre, notas_dict, obs):
    try:
        sh = conn.client.open_by_key(sheet_id)
        ws = sh.worksheet("TABUA_MARE")
        nova_linha = [aluno, sala, semestre] + list(notas_dict.values()) + [obs, datetime.now().strftime("%d/%m/%Y")]
        ws.append_row(nova_linha)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

def registrar_turno_estendido(aluno, sala, avaliacao_tipo, nivel, evidencias_list, obs, ano):
    try:
        sh = conn.client.open_by_key(sheet_id)
        ws = sh.worksheet("TURNO_ESTENDIDO")
        ev_str = ", ".join(evidencias_list)
        ws.append_row([aluno, sala, avaliacao_tipo, nivel, ev_str, obs, ano, datetime.now().strftime("%d/%m/%Y")])
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# Carregamento Principal
try:
    df_g = conn.read(spreadsheet=sheet_id, worksheet="GERAL").fillna("")
    df_g.columns = [str(c).strip().upper() for c in df_g.columns]
    
    df_alf = conn.read(spreadsheet=sheet_id, worksheet="TURNO_ESTENDIDO").fillna("")
    df_alf.columns = [str(c).strip().upper() for c in df_alf.columns]

    df_aval = conn.read(spreadsheet=sheet_id, worksheet="TABUA_MARE").fillna("")
    df_aval.columns = [str(c).strip().upper() for c in df_aval.columns]
except:
    df_g = pd.DataFrame(columns=["ALUNO", "TURNO", "COMUNIDADE"])
    df_alf = pd.DataFrame(columns=["ALUNO", "SALA", "ANO", "NIVEL"])
    df_aval = pd.DataFrame(columns=["ALUNO"])

# =================================================================
# 3. INTERFACE E LÓGICA
# =================================================================

# Inicialização de variáveis de sessão
if "alunos_te_dict" not in st.session_state:
    st.session_state["alunos_te_dict"] = dict(zip(df_alf["ALUNO"], df_alf["SALA"])) if not df_alf.empty else {}

def render_vasilha_mare(nivel_num, titulo):
    config = {
        1: {"pct": 85, "txt": "Baixa", "seta": ""},
        2: {"pct": 70, "txt": "Vazante", "seta": "↓"},
        3: {"pct": 45, "txt": "Enchente", "seta": "↑"},
        4: {"pct": 30, "txt": "Alta", "seta": "↑"},
        5: {"pct": 10, "txt": "Cheia", "seta": "↑"}
    }
    try: n = int(float(nivel_num))
    except: n = 3
    n = max(1, min(5, n))
    c = config[n]
    return f'''
    <div style="text-align: center; margin-bottom: 10px; border: 1px solid #eee; padding: 5px; border-radius: 8px; background: #fff;">
        <div style="font-size: 10px; font-weight: bold; height: 30px; display: flex; align-items: center; justify-content: center;">{titulo}</div>
        <div style="width: 50px; height: 35px; margin: 5px auto; background: linear-gradient(to bottom, #f0f0f0 {c['pct']}%, #5DADE2 {c['pct']}%);
                    clip-path: path('M 0 10 Q 12.5 0 25 10 T 50 10 L 50 35 Q 50 40 45 40 L 5 40 Q 0 40 0 35 Z'); border: 1px solid #ddd; position: relative;">
        </div>
        <div style="font-size: 8px; color: #5DADE2; font-weight: bold;">{c['txt']}</div>
    </div>'''

def render_botoes_salas(key_prefix, session_key):
    salas = list(TURMAS_CONFIG.keys())
    cols = st.columns(len(salas))
    if session_key not in st.session_state: st.session_state[session_key] = salas[0]
    for i, sala in enumerate(salas):
        cor = TURMAS_CONFIG[sala]["cor"]
        op = "1.0" if st.session_state[session_key] == sala else "0.4"
        if cols[i].button(sala, key=f"{key_prefix}_{sala}", use_container_width=True):
            st.session_state[session_key] = sala
            st.rerun()
        st.markdown(f"<style>div[key='{key_prefix}_{sala}'] button {{ background-color: {cor} !important; opacity: {op} !important; color: white !important; font-size: 11px !important; }}</style>", unsafe_allow_html=True)

def criar_grafico_mare(categorias, valores):
    fig = go.Figure(go.Scatter(
        x=categorias, y=valores, fill='tozeroy', mode='markers+lines',
        line=dict(color=C_AZUL_MARE, width=4, shape='spline'),
        marker=dict(size=10, color=C_AZUL)
    ))
    fig.update_layout(yaxis=dict(range=[0.5, 5.5], visible=False), height=300, margin=dict(l=10, r=10, t=10, b=50))
    return fig

# --- LÓGICA DE LOGIN ---
if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
if not st.session_state.logado:
    st.title("🌊 Instituto Mãe Lalu")
    with st.form("login"):
        u = st.text_input("Usuário").strip().upper()
        s = st.text_input("Chave", type="password")
        if st.form_submit_button("ENTRAR"):
            if u == "ADMIN" and s == "123":
                st.session_state.update({"logado": True, "perfil": "admin", "nome_usuario": "COORDENAÇÃO"})
                st.rerun()
            else: st.error("Acesso negado.")
    st.stop()

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação", ["📝 Matrícula", "📊 Lançar Avaliação", "📖 Turno Estendido", "🌊 Tábua da Maré", "🤝 Canal do Apadrinhamento"])

st.markdown(f"<h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> Lalu</h1>", unsafe_allow_html=True)

if menu == "📝 Matrícula":
    st.subheader("📝 Gestão de Alunos")
    render_botoes_salas("btn_mat", "sel_mat")
    # Lógica de exibição simplificada
    df_s = conn.read(spreadsheet=sheet_id, worksheet=st.session_state.sel_mat).fillna("")
    st.dataframe(df_s, use_container_width=True)

elif menu == "📊 Lançar Avaliação":
    st.subheader("📊 Lançar Avaliação Pedagógica")
    render_botoes_salas("btn_av", "sel_aval")
    
    sala = st.session_state.sel_aval
    df_sala = conn.read(spreadsheet=sheet_id, worksheet=sala).fillna("")
    alunos = sorted(df_sala["ALUNO"].unique()) if "ALUNO" in df_sala.columns else []
    
    if alunos:
        al_sel = st.selectbox("Aluno", alunos)
        with st.form("form_av"):
            semestre = st.selectbox("Semestre", ["1º Semestre", "2º Semestre"])
            notas = {}
            c1, c2 = st.columns(2)
            opcoes = ["MARÉ BAIXA", "MARÉ VAZANTE", "MARÉ ENCHENTE", "MARÉ ALTA", "MARÉ CHEIA"]
            for i, cat in enumerate(CATEGORIAS):
                notas[cat] = (c1 if i < 5 else c2).selectbox(cat, opcoes, index=2)
            obs = st.text_area("Observações")
            if st.form_submit_button("Salvar"):
                if registrar_tabua_mare(al_sel, sala, semestre, notas, obs):
                    st.success("Salvo!")
    else: st.warning("Nenhum aluno encontrado.")

elif menu == "📖 Turno Estendido":
    st.subheader("📖 Evolução de Alfabetização")
    render_botoes_salas("btn_te", "sel_te")
    # Lógica simplificada de registro de nível de alfabetização
    st.info("Espaço para registro de níveis 1 a 7 conforme NIVEIS_ALF")

elif menu == "🌊 Tábua da Maré":
    st.subheader("🌊 Visualização da Tábua da Maré")
    render_botoes_salas("btn_tab", "sel_int")
    # Filtro e exibição dos gráficos de vasilha por aluno

elif menu == "🤝 Canal do Apadrinhamento":
    st.subheader("🤝 Espaço do Padrinho")
    # Lógica de visualização filtrada por padrinho
    st.write("Em desenvolvimento: Visualização exclusiva para padrinhos.")

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()
