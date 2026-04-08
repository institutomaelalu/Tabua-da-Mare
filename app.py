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
    
    /* Espaçamentos e Redução de Rolagem */
    .block-container {{ padding-top: 1rem !important; padding-bottom: 1rem !important; }}
    [data-testid="stVerticalBlock"] > div {{ padding-bottom: 0.4rem !important; }}
    .stSelectbox, .stCheckbox, .stSlider {{ margin-bottom: 8px !important; }}
    hr {{ margin: 0.5rem 0 !important; }}

    .custom-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        border: 1px solid #f0f0f0; border-radius: 10px;
        overflow: hidden; font-size: 13px; margin-top: 5px;
    }}
    .custom-table thead th {{ background-color: #ffffff; padding: 10px; text-align: left; border-bottom: 2px solid #f8f8f8; }}
    .th-rosa {{ color: {C_ROSA} !important; font-weight: 700; }}
    .th-verde {{ color: {C_VERDE} !important; font-weight: 700; }}
    .th-azul {{ color: {C_AZUL} !important; font-weight: 700; }}
    .th-amarelo {{ color: {C_AMARELO} !important; font-weight: 700; }}
    .custom-table tbody td {{ padding: 8px 10px; border-bottom: 1px solid #fafafa; color: #666 !important; font-weight: 500; }}
    
    div.stButton > button {{
        width: 100%; border-radius: 8px !important; border: 1px solid #eee !important;
        font-weight: 600 !important; height: 38px; font-size: 12px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. Inicialização e Bancos Locais
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

# 3. Função de Leitura Robusta
def safe_read(worksheet_name):
    df = pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])
    try:
        if worksheet_name == "GERAL":
            lista_dfs = []
            for sala, conf in TURMAS_CONFIG.items():
                if conf['key'] in st.secrets["connections"]["gsheets"]:
                    url = st.secrets["connections"]["gsheets"][conf['key']]
                    url_csv = url.split("/edit")[0] + "/export?format=csv"
                    if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
                    temp_df = pd.read_csv(url_csv)
                    temp_df.columns = [str(c).strip().upper() for c in temp_df.columns]
                    # Tenta achar a coluna de padrinho por aproximação
                    for col in temp_df.columns:
                        if "PADRINHO" in col:
                            temp_df = temp_df.rename(columns={col: "PADRINHO/MADRINHA"})
                    lista_dfs.append(temp_df)
            df = pd.concat(lista_dfs, ignore_index=True) if lista_dfs else df
        else:
            sheet_key = TURMAS_CONFIG.get(worksheet_name, {}).get("key")
            if sheet_key in st.secrets["connections"]["gsheets"]:
                url = st.secrets["connections"]["gsheets"][sheet_key]
                url_csv = url.split("/edit")[0] + "/export?format=csv"
                if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
                df = pd.read_csv(url_csv)
                df.columns = [str(c).strip().upper() for c in df.columns]
                for col in df.columns:
                    if "PADRINHO" in col: df = df.rename(columns={col: "PADRINHO/MADRINHA"})
    except Exception as e:
        print(f"Erro ao ler {worksheet_name}: {e}")

    # Merge com dados locais
    try:
        df_l, df_p = pd.read_csv(ALUNOS_FILE), pd.read_csv(PADRINHOS_FILE)
        if worksheet_name == "GERAL": 
            df = pd.concat([df, df_l], ignore_index=True)
        
        df["ALUNO"] = df["ALUNO"].astype(str).str.strip().str.upper()
        for _, r in df_p.iterrows():
            df.loc[df["ALUNO"] == str(r["ALUNO"]).strip().upper(), "PADRINHO/MADRINHA"] = r["PADRINHO_EDITADO"]
        return df.fillna("")
    except: return df.fillna("")

# 4. SISTEMA DE LOGIN COM DIAGNÓSTICO
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.perfil = None
    st.session_state.nome_usuario = ""

if not st.session_state.logado:
    st.markdown("<div class='main-header'><h1>Acesso ao Sistema</h1></div><hr>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        with st.form("login_form"):
            user_input = st.text_input("Seu nome (conforme planilha)").strip().upper()
            senha_input = st.text_input("Chave de Acesso", type="password")
            btn_login = st.form_submit_button("Entrar")
            
            if btn_login:
                if user_input == "ADMIN" and senha_input == "123":
                    st.session_state.logado = True
                    st.session_state.perfil = "admin"
                    st.session_state.nome_usuario = "Coordenação"
                    st.rerun()
                else:
                    df_check = safe_read("GERAL")
                    if "PADRINHO/MADRINHA" in df_check.columns:
                        padrinhos_validos = df_check["PADRINHO/MADRINHA"].astype(str).str.strip().str.upper().unique()
                        padrinhos_validos = [p for p in padrinhos_validos if p not in ["", "NAN", "0", "NONE"]]
                        
                        if user_input in padrinhos_validos and senha_input == "lalu2026":
                            st.session_state.logado = True
                            st.session_state.perfil = "padrinho"
                            st.session_state.nome_usuario = user_input
                            st.rerun()
                        else:
                            st.error("Nome ou chave incorretos.")
                    else:
                        st.error("Erro técnico: Coluna de padrinhos não encontrada nas planilhas.")

        # FERRAMENTA DE DIAGNÓSTICO
        with st.expander("🔍 Não consegue acessar? Verifique os nomes cadastrados"):
            if st.button("Carregar lista de nomes da planilha"):
                df_diag = safe_read("GERAL")
                if "PADRINHO/MADRINHA" in df_diag.columns:
                    nomes = df_diag["PADRINHO/MADRINHA"].astype(str).str.strip().str.upper().unique()
                    nomes = [n for n in nomes if n not in ["", "NAN", "0", "NONE"]]
                    if nomes:
                        st.write("O sistema encontrou estes nomes de padrinhos nas planilhas:")
                        st.info(", ".join(nomes))
                        st.warning("O nome digitado no login deve ser EXATAMENTE igual a um destes acima.")
                    else:
                        st.error("A coluna 'Padrinho' foi encontrada, mas parece estar vazia em todas as abas.")
                else:
                    st.error("O sistema não conseguiu encontrar nenhuma coluna com o nome 'Padrinho' ou 'Madrinha' nas suas planilhas.")
    st.stop()

# --- CÓDIGO DO SISTEMA (APÓS LOGIN) ---
st.markdown(f"""
    <div class="main-header">
        <h1><span style='color: {C_VERDE};'>Instituto</span> <span style='color: {C_AZUL};'>Mãe</span> <span style='color: {C_VERDE};'>Lalu</span></h1>
    </div>
    <hr style="border: 0; height: 2px; background-image: linear-gradient(to right, {C_ROSA}, {C_VERDE}, {C_AZUL}, {C_AMARELO});">
    """, unsafe_allow_html=True)

st.sidebar.write(f"👤 **{st.session_state.nome_usuario}**")
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

# (Restante do código de Matrículas, Cadastro e Evolução permanece igual, 
# garantindo que a aba 'Evolução Individual' esteja funcionando perfeitamente)

if st.session_state.perfil == "admin":
    menu = st.sidebar.radio("Navegação", ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução Individual"])
else:
    menu = "🌊 Evolução Individual"

# --- Exemplo da aba de Evolução protegida ---
if menu == "🌊 Evolução Individual":
    st.markdown(f"<h3 style='color:{C_AZUL};'>🌊 Tábua da Maré (Evolução)</h3>", unsafe_allow_html=True)
    df_av = pd.read_csv(AVAL_FILE) if os.path.exists(AVAL_FILE) else pd.DataFrame()
    df_geral = safe_read("GERAL")
    
    if st.session_state.perfil == "admin":
        alunos_visiveis = sorted(df_av["Aluno"].unique()) if not df_av.empty else []
    else:
        afilhados = df_geral[df_geral["PADRINHO/MADRINHA"].astype(str).str.strip().str.upper() == st.session_state.nome_usuario]["ALUNO"].unique()
        alunos_visiveis = [a for a in df_av["Aluno"].unique() if a in afilhados] if not df_av.empty else []

    if alunos_visiveis:
        al_s = st.selectbox("Escolha o Aluno", alunos_visiveis)
        # ... (restante do código do gráfico Plotly)
    else:
        st.info("Ainda não há avaliações para seus afilhados.")

elif menu == "👤 Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA};'>👤 Novo Cadastro</h3>", unsafe_allow_html=True)
    with st.form("cad"):
        n, i, comu = st.text_input("Nome"), st.text_input("Idade"), st.text_input("Comunidade")
        t, tn = st.selectbox("Sala", list(TURMAS_CONFIG.keys())), st.selectbox("Turma (A/B)", ["A", "B"])
        if st.form_submit_button("Cadastrar"):
            df_l = pd.read_csv(ALUNOS_FILE)
            pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Cadastrado!")
