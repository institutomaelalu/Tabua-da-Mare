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
C_AZUL_MARE = "#8fd9fb" # Cor azul claro solicitada

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

if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})

# --- LOGIN (Simplificado para manter o foco) ---
if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("👤 Usuário").strip().upper()
        s = st.text_input("🔑 Chave", type="password")
        if st.form_submit_button("ENTRAR"):
            if u == "ADMIN" and s == "123":
                st.session_state.update({"logado": True, "perfil": "admin", "nome_usuario": "Coordenação"})
                st.rerun()
            else:
                df_g = safe_read("GERAL")
                if not df_g.empty and u in df_g["PADRINHO/MADRINHA"].astype(str).str.upper().unique():
                    st.session_state.update({"logado": True, "perfil": "padrinho", "nome_usuario": u})
                    st.rerun()
    st.stop()

menu = st.sidebar.radio("Navegação", ["📝 Matrículas", "📊 Lançar Avaliação", "🌊 Evolução (Padrinhos)"])

st.markdown(f"<div class='main-header'><h1>Instituto Mãe Lalu</h1></div>", unsafe_allow_html=True)

# --- LANÇAR AVALIAÇÃO (Ajuste do Título) ---
if menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO}'>📊 Lançar Tábua da Maré</h3>", unsafe_allow_html=True)
    df_s = safe_read("SALA ROSA") # Exemplo simplificado para foco no formulário
    
    with st.form("aval"):
        al = st.selectbox("Aluno", sorted(df_s["ALUNO"].unique()))
        tr = st.selectbox("Semestre", ["1º Semestre", "2º Semestre"])
        
        # Título restaurado conforme solicitado
        st.markdown("<h4 style='text-align: center; color: #444; margin: 20px 0;'>10 motivos para avaliar!</h4>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        notas = {}
        for idx, cat in enumerate(CATEGORIAS):
            target = col1 if idx < 5 else col2
            notas[cat] = target.selectbox(cat, list(MARE_OPCOES.keys()))
        obs = st.text_area("Observações:")
        
        if st.form_submit_button("Salvar"):
            st.success("Salvo!")

# --- EVOLUÇÃO (Ajuste Lista Padrinhos e Cor Gráfico) ---
elif menu == "🌊 Evolução (Padrinhos)":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🌊 Evolução dos Afilhados</h3>", unsafe_allow_html=True)
    
    # Busca dados de todas as salas para garantir que a lista de padrinhos não fique vazia
    dfs_todas = []
    for sala in TURMAS_CONFIG.keys():
        dfs_todas.append(safe_read(sala))
    df_consolidado = pd.concat(dfs_todas, ignore_index=True)
    
    # Coleta lista única de padrinhos removendo vazios
    lista_padrinhos = sorted([p for p in df_consolidado["PADRINHO/MADRINHA"].unique() if str(p).strip() not in ["", "0", "nan", "None"]])
    
    if st.session_state.perfil == "admin":
        padrinho = st.selectbox("Selecione o Padrinho/Madrinha:", [""] + lista_padrinhos)
    else:
        padrinho = st.session_state.nome_usuario

    if padrinho:
        afilhas = df_consolidado[df_consolidado["PADRINHO/MADRINHA"].astype(str).str.upper() == padrinho.upper()]
        if not afilhas.empty:
            al_s = st.selectbox("Selecione o Afilhado:", sorted(afilhas["ALUNO"].unique()))
            
            # Exemplo de gráfico com a cor solicitada
            fig = go.Figure(go.Scatter(
                x=CATEGORIAS, 
                y=[3, 4, 2, 4, 3, 4, 2, 3, 4, 3], # Dados exemplo
                fill='tozeroy', 
                line=dict(color=C_AZUL_MARE, width=4, shape='spline') # Cor Azul Claro
            ))
            fig.update_layout(yaxis=dict(range=[0.5, 4.5], showticklabels=False), height=450)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Nenhum afilhado encontrado.")
    else:
        st.info("Por favor, selecione um padrinho na lista acima.")
