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

CORES_TRILHA = {
    "1. Pré-Silábico": {"ativo": "#d9e6f2", "inativo": "#f1f6fb"},
    "2. Silábico s/ Valor": {"ativo": "#5cc6d0", "inativo": "#d2eff2"},
    "3. Silábico c/ Valor": {"ativo": "#a8cf45", "inativo": "#e5f0cc"},
    "4. Silábico Alfabético": {"ativo": "#ffc713", "inativo": "#fff1c2"},
    "5. Alfabético Inicial": {"ativo": "#ff81ba", "inativo": "#ffd9ea"},
    "6. Alfabético Final": {"ativo": "#5cc6d0", "inativo": "#d2eff2"},
    "7. Alfabético Ortográfico": {"ativo": "#ff81ba", "inativo": "#ffd9ea"}
}
NIVEIS_ALF = list(CORES_TRILHA.keys())
ALF_FILE = "alfabetizacao.csv"

# Lista de evidências (sinais de avanço) para os Checkboxes
EVIDENCIAS_PADRAO = [
    "Reconhece letras do nome", 
    "Diferencia desenhos de letras", 
    "Identifica rimas", 
    "Relaciona som à letra", 
    "Lê palavras simples", 
    "Escreve frases curtas"
]

if not os.path.exists(ALF_FILE):
    pd.DataFrame(columns=["Aluno", "Avaliacao", "Nivel", "Gatilho", "Evidencias", "Obs", "Sala"]).to_csv(ALF_FILE, index=False)

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

    .trilha-container {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;
        padding: 10px 0;
    }}
    .caixa-trilha {{
        flex: 1;
        height: 85px;
        border-radius: 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        font-size: 10px;
        font-weight: 800;
        padding: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 2px solid transparent;
        line-height: 1.2;
    }}
    .seta-trilha {{
        padding: 0 5px;
        color: #ccc;
        font-size: 18px;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS (BASE 0804) ---
CATEGORIAS = ["1. Atividades em Grupo/Proatividade", "2. Interesse pelo Novo", "3. Compartilhamento de Materiais", "4. Clareza e Desenvoltura", "5. Respeito às Regras", "6. Vocabulário Adequado", "7. Leitura e Escrita", "8. Compreensão de Comandos", "9. Superação de Desafios", "10. Assiduidade"]
MARE_OPCOES = {"Maré Cheia": 4, "Maré Enchente": 3, "Maré Vazante": 2, "Maré Baixa": 1}
MARE_LABELS = {4: "Maré Cheia", 3: "Maré Enchente", 2: "Maré Vazante", 1: "Maré Baixa"}
AVAL_FILE = "avaliacoes.csv"

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

def render_botoes_salas(key_prefix, session_key):
    cols = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        op = "1.0" if st.session_state[session_key] == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {op}; }}</style>', unsafe_allow_html=True)
        if cols[i].button(sala, key=f"{key_prefix}_{sala}"):
            st.session_state[session_key] = sala; st.rerun()

# --- LOGIN E NAVEGAÇÃO ---
if "logado" not in st.session_state: st.session_state.update({"logado": False})
for k in ['sel_mat', 'sel_pad', 'sel_aval', 'sel_int', 'sel_alf', 'sel_ind']:
    if k not in st.session_state: st.session_state[k] = "SALA ROSA"

if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        with st.form("login"):
            u, s = st.text_input("👤 Usuário").upper(), st.text_input("🔑 Chave", type="password")
            if st.form_submit_button("ENTRAR"):
                if u == "ADMIN" and s == "123":
                    st.session_state.logado = True; st.rerun()
    st.stop()

menu = st.sidebar.radio("Navegação", ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "📖 Programa Alfabetização", "📈 Indicadores Pedagógicos", "🌊 Evolução (Padrinhos)", "🌊 Tábua da Maré - Interno"])
st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- ABA: PROGRAMA ALFABETIZAÇÃO (FOCO NA SOLICITAÇÃO) ---
if menu == "📖 Programa Alfabetização":
    st.markdown(f"<h3 style='color:{C_ROXO}'>📖 Trilha de Alfabetização</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_alf", "sel_alf")
    df_s = safe_read(st.session_state.sel_alf)
    
    if not df_s.empty:
        al = st.selectbox("Aluno:", sorted(df_s["ALUNO"].unique()))
        df_h = pd.read_csv(ALF_FILE)
        diag = df_h[df_h["Aluno"] == al].iloc[-1] if not df_h[df_h["Aluno"] == al].empty else None
        
        # 1. Trilha Visual com Setas
        html_trilha = '<div class="trilha-container">'
        for i, n_text in enumerate(NIVEIS_ALF):
            ativo = (diag is not None and diag["Nivel"] == n_text)
            cor_bg = CORES_TRILHA[n_text]["ativo"] if ativo else CORES_TRILHA[n_text]["inativo"]
            cor_txt = "#444" if not ativo else "white"
            label = n_text.split(". ")[1]
            html_trilha += f'<div class="caixa-trilha" style="background-color:{cor_bg}; color:{cor_txt}; border-color:{"#aaa" if ativo else "transparent"}">{label}</div>'
            if i < len(NIVEIS_ALF) - 1: html_trilha += '<div class="seta-trilha">→</div>'
        html_trilha += '</div>'
        st.markdown(html_trilha, unsafe_allow_html=True)
        
        # 2. Formulário de Diagnóstico com Evidências
        with st.form("form_alf"):
            c1, c2 = st.columns(2)
            novo_nv = c1.selectbox("Novo Nível:", NIVEIS_ALF, index=NIVEIS_ALF.index(diag["Nivel"]) if diag is not None else 0)
            tipo = c2.selectbox("Avaliação:", ["1ª Avaliação", "2ª Avaliação", "Avaliação Final"])
            
            st.markdown("---")
            st.markdown("**Sinais de Avanço (Evidências):**")
            
            # Gerando as colunas de Checkboxes
            evid_cols = st.columns(3)
            selecionadas = []
            for idx, evid in enumerate(EVIDENCIAS_PADRAO):
                if evid_cols[idx % 3].checkbox(evid):
                    selecionadas.append(evid)
            
            outro_evid = st.text_input("Outro (especificar manualmente):")
            if outro_evid: selecionadas.append(outro_evid)
            
            evid_final = ", ".join(selecionadas)
            
            st.markdown("---")
            gatilho = st.checkbox("Atende Critério de Gatilho de Passagem?")
            obs = st.text_area("Observações Pedagógicas Adicionais:")
            
            if st.form_submit_button("Registrar Diagnóstico"):
                df_h = df_h[~((df_h["Aluno"] == al) & (df_h["Avaliacao"] == tipo))]
                novo_reg = pd.DataFrame([[al, tipo, novo_nv, gatilho, evid_final, obs, st.session_state.sel_alf]], columns=df_h.columns)
                pd.concat([df_h, novo_reg], ignore_index=True).to_csv(ALF_FILE, index=False)
                st.success("Diagnóstico e Evidências salvos!"); st.rerun()

# --- DEMAIS ABAS (MANTIDAS DO CÓDIGO FUNCIONAL) ---
elif menu == "👤 Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA}'>👤 Novo Cadastro</h3>", unsafe_allow_html=True)
    with st.form("cad"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nome").strip().upper()
        i = c2.text_input("Idade").strip()
        com = c1.text_input("Comunidade").strip().upper()
        t = c2.selectbox("Sala", list(TURMAS_CONFIG.keys()))
        tn = c1.selectbox("Turno", ["A", "B"])
        if st.form_submit_button("Cadastrar"):
            if n and i:
                sh = get_gspread_client().open_by_key("1MBAvQB5xGhE7OAHGWdFPvGfwqzP9SpiaIW4OEl2Mgk4")
                sh.worksheet(t).append_row([n, t, tn, i, com, ""])
                sh.worksheet("GERAL").append_row([n, t, tn, i, com, ""])
                st.success("Cadastrado!"); st.rerun()

elif menu == "📊 Lançar Avaliação":
    # Mantém a estrutura de 2 colunas para as 10 categorias
    st.markdown(f"<h3 style='color:{C_AMARELO}'>📊 Tábua da Maré</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_av", "sel_aval")
    df_s = safe_read(st.session_state.sel_aval)
    with st.form("aval"):
        al = st.selectbox("Aluno", sorted(df_s["ALUNO"].unique()))
        tr = st.selectbox("Período", ["1º Semestre", "2º Semestre"])
        c_e, c_d = st.columns(2); n_l = {}
        for i, cat in enumerate(CATEGORIAS):
            n_l[cat] = (c_e if i < 5 else c_d).selectbox(cat, list(MARE_OPCOES.keys()))
        obs = st.text_area("Observações:")
        if st.form_submit_button("Salvar"):
            df_av = pd.read_csv(AVAL_FILE)
            df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Periodo'] == tr))]
            pd.concat([df_av, pd.DataFrame([[al, tr] + [MARE_OPCOES[n_l[c]] for c in CATEGORIAS] + [obs]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
            st.success("Salvo!")
