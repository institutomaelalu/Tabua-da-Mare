import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuração e Estilo
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"
C_AZUL_MARE = "#8fd9fb" 

# Cores específicas da Trilha de Alfabetização
CORES_TRILHA = {
    "1. Pré-Silábico": "#d9e6f2",      
    "2. Silábico s/ Valor": "#5cc6d0", 
    "3. Silábico c/ Valor": "#a8cf45", 
    "4. Silábico Alfabético": "#ffc713", 
    "5. Alfabético Inicial": "#ff81ba", 
    "6. Alfabético Final": "#5cc6d0",   
    "7. Alfabético Ortográfico": "#ff81ba" 
}
NIVEIS_ALF = list(CORES_TRILHA.keys())
ALF_FILE = "alfabetizacao.csv"

if not os.path.exists(ALF_FILE):
    pd.DataFrame(columns=["Data", "Aluno", "Nivel", "Avaliacao", "Observacoes"]).to_csv(ALF_FILE, index=False)

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp {{ background-color: #ffffff; font-family: 'Inter', sans-serif; }}
    .main-header {{ text-align: center; padding: 20px 0; }}
    
    /* Estilo da Trilha Visual */
    .trilha-wrapper {{
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 40px 0;
        overflow-x: auto;
    }}
    .bloco-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 130px;
        position: relative;
        z-index: 2;
    }}
    .caixa-trilha {{
        width: 85px;
        height: 85px;
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        font-weight: bold;
        color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }}
    .label-trilha {{
        font-size: 11px;
        font-weight: 700;
        text-align: center;
        color: #555;
        height: 30px;
    }}
    .curva {{
        position: absolute;
        top: 35px;
        left: 90px;
        width: 100px;
        z-index: 1;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. Funções de Dados (Mantidas do seu código original)
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
        return df.fillna("")
    except: return pd.DataFrame()

# 3. Definições de Interface
TURMAS_CONFIG = {
    "SALA ROSA": {"cor": C_ROSA, "key": "sala_rosa"},
    "SALA AMARELA": {"cor": C_AMARELO, "key": "sala_amarela"},
    "SALA VERDE": {"cor": C_VERDE, "key": "sala_verde"},
    "SALA AZUL": {"cor": C_AZUL, "key": "sala_azul"},
    "CIRAND. MUNDO": {"cor": C_ROXO, "key": "cirand_mundo"},
}

CATEGORIAS = ["1. Atividades em Grupo/Proatividade", "2. Interesse pelo Novo", "3. Compartilhamento de Materiais", "4. Clareza e Desenvoltura", "5. Respeito às Regras", "6. Vocabulário Adequado", "7. Leitura e Escrita", "8. Compreensão de Comandos", "9. Superação de Desafios", "10. Assiduidade"]
MARE_OPCOES = {"Maré Cheia": 4, "Maré Enchente": 3, "Maré Vazante": 2, "Maré Baixa": 1}
AVAL_FILE = "avaliacoes.csv"

# --- LÓGICA DA TRILHA VISUAL ---
def desenhar_trilha(nivel_atual=None):
    # SVG da seta curva (simulando a imagem)
    seta_svg = """
    <svg class="curva" width="100" height="40" viewBox="0 0 100 40">
        <path d="M0,10 Q50,-10 100,10" fill="none" stroke="#ccc" stroke-width="3" stroke-dasharray="6,4" />
        <path d="M95,5 L100,10 L95,15" fill="none" stroke="#ccc" stroke-width="3" />
    </svg>
    """
    
    cols = st.columns(len(NIVEIS_ALF))
    for i, nivel in enumerate(NIVEIS_ALF):
        label = nivel.split(". ")[1]
        ativo = nivel == nivel_atual
        cor_fundo = CORES_TRILHA[nivel] if ativo else "#f0f0f0"
        cor_texto = "white" if ativo else "#ccc"
        marcador = "---" if ativo else ""
        
        with cols[i]:
            st.markdown(f"""
                <div class="bloco-container">
                    <div class="caixa-trilha" style="background-color: {cor_fundo}; color: {cor_texto};">
                        {marcador}
                    </div>
                    <div class="label-trilha">{label}</div>
                    {seta_svg if i < len(NIVEIS_ALF)-1 else ""}
                </div>
            """, unsafe_allow_html=True)

# --- LOGIN E ESTADOS ---
if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
for k in ['sel_mat', 'sel_pad', 'sel_aval', 'sel_int', 'sel_alf']:
    if k not in st.session_state: st.session_state[k] = "SALA ROSA"

if not st.session_state.logado:
    # ... (Seu código de login aqui igual ao original)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        with st.form("login"):
            u = st.text_input("👤 Usuário").strip().upper()
            s = st.text_input("🔑 Chave", type="password")
            if st.form_submit_button("ENTRAR"):
                if u == "ADMIN" and s == "123":
                    st.session_state.update({"logado": True, "perfil": "admin", "nome_usuario": "Coordenação"})
                    st.rerun()
                else: st.error("Acesso negado")
    st.stop()

# --- NAVEGAÇÃO ---
menu_options = ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "📖 Programa Alfabetização", "🌊 Evolução (Padrinhos)", "🌊 Tábua da Maré - Interno"]
menu = st.sidebar.radio("Navegação", menu_options)

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- ABA: PROGRAMA ALFABETIZAÇÃO ---
if menu == "📖 Programa Alfabetização":
    st.markdown(f"<h3 style='color:{C_AZUL}'>📖 Programa Alfabetização</h3>", unsafe_allow_html=True)
    
    # Seleção de Sala (Botões Coloridos)
    cols_s = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        if cols_s[i].button(sala, key=f"alf_{sala}"):
            st.session_state.sel_alf = sala
            st.rerun()

    df_geral = safe_read("GERAL")
    df_sala = safe_read(st.session_state.sel_alf)
    
    if not df_sala.empty:
        aluno_sel = st.selectbox("Selecione o Aluno:", sorted(df_sala["ALUNO"].unique()))
        
        # Buscar nível atual no CSV local
        df_historico = pd.read_csv(ALF_FILE)
        diag_aluno = df_historico[df_historico["Aluno"] == aluno_sel]
        nivel_atual = diag_aluno.iloc[-1]["Nivel"] if not diag_aluno.empty else None
        
        # Exibir Trilha Visual
        st.write(f"**Nível de Diagnóstico: {aluno_sel}**")
        desenhar_trilha(nivel_atual)
        
        # Formulário para novo diagnóstico
        with st.form("novo_diagnostico"):
            st.markdown("#### Atualizar Diagnóstico")
            c1, c2 = st.columns(2)
            novo_nivel = c1.selectbox("Novo Nível:", NIVEIS_ALF)
            tipo_aval = c2.selectbox("Tipo de Avaliação:", ["1ª Avaliação", "2ª Avaliação", "Final"])
            obs_alf = st.text_area("Evidências observadas:")
            
            if st.form_submit_button("Registrar Avanço"):
                nova_data = pd.to_datetime("today").strftime("%d/%m/%Y")
                novo_reg = pd.DataFrame([[nova_data, aluno_sel, novo_nivel, tipo_aval, obs_alf]], columns=df_historico.columns)
                pd.concat([df_historico, novo_reg], ignore_index=True).to_csv(ALF_FILE, index=False)
                st.success("Diagnóstico atualizado!")
                st.rerun()

# --- OUTRAS ABAS (Mantidas exatamente como o seu original) ---
elif menu == "📝 Matrículas":
    # ... (Seu código original de Matrículas)
    pass
elif menu == "📊 Lançar Avaliação":
    # ... (Seu código original de Lançar Avaliação)
    pass
# ... Adicione as outras opções (Cadastro, Apadrinhamento, Tábua da Maré) conforme seu app original
