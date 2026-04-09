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

MARE_LABELS = {4: "Muito bom (Maré Cheia)", 3: "Em evolução (Maré Enchente)", 2: "Requer atenção (Maré Vazante)", 1: "Início (Maré Baixa)"}
MARE_OPCOES = {"Maré Cheia": 4, "Maré Enchente": 3, "Maré Vazante": 2, "Maré Baixa": 1}

NIVEIS_ALF = [
    "1. Pré-Silábico", "2. Silábico s/ Valor", "3. Silábico c/ Valor", 
    "4. Silábico Alfabético", "5. Alfabético Inicial", "6. Alfabético Final", "7. Alfabético Ortográfico"
]

AVAL_FILE = "avaliacoes.csv"
ALF_FILE = "alfabetizacao.csv"

# Inicialização de arquivos com colunas corretas para evitar KeyError
for f, cols in {AVAL_FILE: ["Aluno", "Periodo"] + CATEGORIAS + ["Observacoes"], 
                ALF_FILE: ["Aluno", "Avaliacao", "Nivel", "Gatilho", "Evidencias", "Obs", "Sala"]}.items():
    if not os.path.exists(f): 
        pd.DataFrame(columns=cols).to_csv(f, index=False)
    else:
        # Verifica se a coluna Sala existe (correção para o erro do print)
        temp_df = pd.read_csv(f)
        if f == ALF_FILE and "Sala" not in temp_df.columns:
            temp_df["Sala"] = "SALA ROSA"
            temp_df.to_csv(f, index=False)

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
for k in ['sel_mat', 'sel_pad', 'sel_aval', 'sel_int', 'sel_alf', 'sel_ind', 'temp_nivel']:
    if k not in st.session_state: st.session_state[k] = "SALA ROSA"
if st.session_state.temp_nivel not in NIVEIS_ALF: st.session_state.temp_nivel = NIVEIS_ALF[0]

# --- LOGIN (Simplificado para o exemplo) ---
if not st.session_state.logado:
    st.session_state.update({"logado": True, "perfil": "admin", "nome_usuario": "Coordenação"})
    st.rerun()

# --- FUNÇÕES DE INTERFACE ---
def render_botoes_salas(key_prefix, session_key):
    cols = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        op = "1.0" if st.session_state[session_key] == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {op}; }}</style>', unsafe_allow_html=True)
        if cols[i].button(sala, key=f"{key_prefix}_{sala}"):
            st.session_state[session_key] = sala; st.rerun()

# --- SIDEBAR ---
menu = st.sidebar.radio("Navegação", ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "📖 Programa Alfabetização", "📈 Indicadores Pedagógicos", "🌊 Evolução (Padrinhos)"])

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- CORREÇÃO DA ABA ALFABETIZAÇÃO (Botoes Fora do Form) ---
if menu == "📖 Programa Alfabetização":
    st.markdown(f"<h3 style='color:{C_ROXO}'>📖 Trilha de Alfabetização</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_alf", "sel_alf")
    
    df_s = safe_read(st.session_state.sel_alf)
    if not df_s.empty:
        # Seleção de Nível (FORA DO FORM para evitar StreamlitAPIException)
        st.write("**Selecione o Nível de Diagnóstico:**")
        cols_n = st.columns(len(NIVEIS_ALF))
        for i, n_text in enumerate(NIVEIS_ALF):
            btn_color = C_ROXO if st.session_state.temp_nivel == n_text else "#f0f0f0"
            btn_txt_color = "white" if st.session_state.temp_nivel == n_text else "#666"
            st.markdown(f'<style>div[data-testid="column"]:nth-child({i+1}) button {{ background-color: {btn_color} !important; color: {btn_txt_color} !important; font-size: 10px !important; }}</style>', unsafe_allow_html=True)
            if cols_n[i].button(n_text.split(". ")[1], key=f"btn_nv_{i}"):
                st.session_state.temp_nivel = n_text; st.rerun()

        st.success(f"Nível selecionado: **{st.session_state.temp_nivel}**")

        with st.form("form_alf_save"):
            c_top1, c_top2 = st.columns([2, 1])
            al = c_top1.selectbox("Aluno", sorted(df_s["ALUNO"].unique()))
            num_aval = c_top2.selectbox("Avaliação", ["1ª Avaliação", "2ª Avaliação", "Avaliação Final"])
            
            c1, c2 = st.columns(2)
            gatilho = c1.checkbox("Atende o Gatilho de Passagem?")
            evidencias = c2.multiselect("Sinais de Avanço:", ["Leitura de sílabas", "Diferenciação letra/desenho", "Escrita fonética", "Uso de dígrafos"])
            obs_alf = st.text_area("Observações:")
            
            if st.form_submit_button("Registrar na Trilha"):
                df_alf = pd.read_csv(ALF_FILE)
                # Remove registro anterior do mesmo aluno/avaliação para atualizar
                df_alf = df_alf[~((df_alf["Aluno"] == al) & (df_alf["Avaliacao"] == num_aval))]
                nova_l = pd.DataFrame([[al, num_aval, st.session_state.temp_nivel, gatilho, ", ".join(evidencias), obs_alf, st.session_state.sel_alf]], columns=df_alf.columns)
                pd.concat([df_alf, nova_l], ignore_index=True).to_csv(ALF_FILE, index=False)
                st.success("Progresso Salvo!")

# --- CORREÇÃO DA ABA INDICADORES (KeyError Sala) ---
elif menu == "📈 Indicadores Pedagógicos":
    st.markdown(f"<h3 style='color:{C_VERDE}'>📈 Indicadores de Alfabetização</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_ind", "sel_ind")
    
    df_alf = pd.read_csv(ALF_FILE)
    df_sala = df_alf[df_alf["Sala"] == st.session_state.sel_ind]
    
    if not df_sala.empty:
        # Lógica de comparação (1ª vs Última registrada)
        df_1 = df_sala[df_sala["Avaliacao"] == "1ª Avaliação"]
        df_ult = df_sala.sort_values("Avaliacao").groupby("Aluno").last().reset_index()
        
        # Filtros para indicadores
        iniciais = ["1. Pré-Silábico", "2. Silábico s/ Valor"]
        consolidados = ["6. Alfabético Final", "7. Alfabético Ortográfico"]
        
        red_iniciais = len(df_1[df_1["Nivel"].isin(iniciais)]) - len(df_ult[df_ult["Nivel"].isin(iniciais)])
        aum_cons = len(df_ult[df_ult["Nivel"].isin(consolidados)])
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Queda Níveis Iniciais", f"-{red_iniciais}" if red_iniciais > 0 else "0")
        m2.metric("Níveis Consolidados", aum_cons)
        m3.metric("Nível Ortográfico", len(df_ult[df_ult["Nivel"] == "7. Alfabético Ortográfico"]))
        
        # Cálculo de avanço
        avancou = 0
        for _, r in df_ult.iterrows():
            v1 = df_1[df_1["Aluno"] == r["Aluno"]]
            if not v1.empty:
                if NIVEIS_ALF.index(r["Nivel"]) > NIVEIS_ALF.index(v1.iloc[0]["Nivel"]): avancou += 1
        m4.metric("% Alunos que Avançaram", f"{(avancou/len(df_ult)*100):.1f}%" if len(df_ult)>0 else "0%")
        
        st.write("---")
        st.dataframe(df_ult[["Aluno", "Avaliacao", "Nivel", "Gatilho", "Obs"]], use_container_width=True)
    else: st.info("Sem dados para esta sala.")

# --- RESTAURAR APADRINHAMENTO ---
elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🤝 Gestão de Apadrinhamento</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_pad", "sel_pad")
    df_s = safe_read(st.session_state.sel_pad)
    if not df_s.empty:
        cor_h = TURMAS_CONFIG[st.session_state.sel_pad]["cor"]
        v_cols = ["ALUNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
        html = f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
        for _, r in df_s.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in v_cols]) + '</tr>'
        st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
