import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
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
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão de Escrita (Google Sheets API)
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

# 3. Definições de Banco de Dados
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
AVAL_FILE = "avaliacoes.csv" # Avaliações podem continuar em CSV ou migrar depois
if not os.path.exists(AVAL_FILE): pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)

TURMAS_CONFIG = {
    "SALA ROSA": {"cor": C_ROSA, "key": "sala_rosa"},
    "SALA AMARELA": {"cor": C_AMARELO, "key": "sala_amarela"},
    "SALA VERDE": {"cor": C_VERDE, "key": "sala_verde"},
    "SALA AZUL": {"cor": C_AZUL, "key": "sala_azul"},
    "CIRAND. MUNDO": {"cor": C_ROXO, "key": "cirand_mundo"},
}

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
    except Exception as e:
        st.error(f"Erro ao ler planilha: {e}")
        return pd.DataFrame()

# 4. Autenticação básica
if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
if 'sel_mat' not in st.session_state: st.session_state.sel_mat = "SALA ROSA"
if 'sel_pad' not in st.session_state: st.session_state.sel_pad = "SALA ROSA"

if not st.session_state.logado:
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown(f'<h2 style="text-align: center; color: {C_AZUL};">Acesso</h2>', unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuário").strip().upper()
            s = st.text_input("Chave", type="password")
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

# --- MENU ---
st.sidebar.write(f"👤 **{st.session_state.nome_usuario}**")
if st.session_state.perfil == "admin":
    menu = st.sidebar.radio("Navegação", ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Avaliações", "🌊 Evolução", "🌊 Tábua da Maré"])
else:
    menu = "🌊 Evolução"

if st.sidebar.button("🚪 Sair"):
    st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
    st.rerun()

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- LÓGICA DE CADASTRO DIRETO NO GOOGLE SHEETS ---
if menu == "👤 Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA}'>👤 Novo Cadastro de Aluno</h3>", unsafe_allow_html=True)
    with st.form("cad_sheets"):
        n = st.text_input("Nome Completo do Aluno").upper()
        i = st.text_input("Idade")
        comu = st.text_input("Comunidade").upper()
        t = st.selectbox("Sala Destino", list(TURMAS_CONFIG.keys()))
        tn = st.selectbox("Turno", ["A", "B"])
        
        if st.form_submit_button("Realizar Matrícula"):
            if n and i:
                with st.spinner("Gravando no Google Sheets..."):
                    try:
                        client = get_gspread_client()
                        # ID da sua planilha (extraído da URL que você passou)
                        sh = client.open_by_key("1MBAvQB5xGhE7OAHGWdFPvGfwqzP9SpiaIW4OEl2Mgk4")
                        
                        # Dados formatados para a linha
                        nova_linha = [n, t, tn, i, comu, ""] # Nome, Turma, Turno, Idade, Comunidade, Padrinho vazio
                        
                        # 1. Grava na aba da Sala Específica
                        sh.worksheet(t).append_row(nova_linha)
                        
                        # 2. Grava na aba GERAL
                        sh.worksheet("GERAL").append_row(nova_linha)
                        
                        st.success(f"Matrícula de {n} realizada com sucesso em ambas as abas!")
                    except Exception as e:
                        st.error(f"Erro ao gravar: {e}")
            else: st.warning("Preencha Nome e Idade.")

elif menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE}'>📋 Quadro de Matrículas (Tempo Real)</h3>", unsafe_allow_html=True)
    sel = st.selectbox("Selecione a Sala para Visualizar", ["GERAL"] + list(TURMAS_CONFIG.keys()))
    df = safe_read(sel)
    if not df.empty:
        st.dataframe(df, use_container_width=True)

elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🤝 Gestão de Apadrinhamento</h3>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    
    # Filtro apenas para quem não tem padrinho
    sem_pad = df_g[df_g["PADRINHO/MADRINHA"].isin(["", "0", "nan", "NAN", None])]
    
    with st.expander("✨ Vincular Novo Padrinho/Madrinha", expanded=True):
        if not sem_pad.empty:
            c1, c2, c3 = st.columns([2, 2, 1])
            al_sel = c1.selectbox("Aluno sem Padrinho", sorted(sem_pad["ALUNO"].unique()))
            pad_nome = c2.text_input("Nome do Padrinho/Madrinha").upper()
            
            if c3.button("Vincular"):
                if pad_nome:
                    with st.spinner("Atualizando planilhas..."):
                        client = get_gspread_client()
                        sh = client.open_by_key("1MBAvQB5xGhE7OAHGWdFPvGfwqzP9SpiaIW4OEl2Mgk4")
                        
                        # Precisamos achar a linha do aluno na aba GERAL e na aba da SALA dele
                        # Para simplificar, vamos atualizar na aba GERAL (Coluna F)
                        aba_g = sh.worksheet("GERAL")
                        celula = aba_g.find(al_sel)
                        aba_g.update_cell(celula.row, 6, pad_nome) # Coluna 6 é Padrinho
                        
                        # Tenta atualizar na aba da sala também
                        info_aluno = sem_pad[sem_pad["ALUNO"] == al_sel].iloc[0]
                        aba_s = sh.worksheet(info_aluno["TURMA"])
                        celula_s = aba_s.find(al_sel)
                        aba_s.update_cell(celula_s.row, 6, pad_nome)
                        
                        st.success(f"{pad_nome} agora é padrinho de {al_sel}!")
                        st.rerun()
                else: st.warning("Digite o nome do padrinho.")
        else: st.info("Todos os alunos já possuem padrinhos.")

# ... (Restante do código de Avaliações e Gráficos permanece igual ao anterior)
