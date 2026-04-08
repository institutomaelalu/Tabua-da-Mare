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
    .login-card {{
        background: linear-gradient(135deg, {C_AZUL}22, {C_ROSA}22);
        padding: 30px; border-radius: 20px; border: 2px solid #f0f0f0;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. Funções de Banco de Dados (Leitura e Escrita)
TURMAS_CONFIG = {
    "SALA ROSA": {"cor": C_ROSA, "key": "sala_rosa"},
    "SALA AMARELA": {"cor": C_AMARELO, "key": "sala_amarela"},
    "SALA VERDE": {"cor": C_VERDE, "key": "sala_verde"},
    "SALA AZUL": {"cor": C_AZUL, "key": "sala_azul"},
    "CIRAND. MUNDO": {"cor": C_ROXO, "key": "cirand_mundo"},
}

CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
AVAL_FILE = "avaliacoes.csv"

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

# 3. Autenticação
if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
if 'sel_mat' not in st.session_state: st.session_state.sel_mat = "SALA ROSA"
if 'sel_pad' not in st.session_state: st.session_state.sel_pad = "SALA ROSA"

if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown(f'<div class="login-card"><h2 style="text-align: center; color: {C_AZUL}; margin:0;">Bem-vindo!</h2></div>', unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("👤 Usuário").strip().upper()
            s = st.text_input("🔑 Chave", type="password")
            if st.form_submit_button("ENTRAR NO SISTEMA"):
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
    menu = st.sidebar.radio("Navegação", ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução", "🌊 Tábua da Maré"])
else:
    menu = "🌊 Evolução"

if st.sidebar.button("🚪 Sair"):
    st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
    st.rerun()

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- FUNCIONALIDADES ---

if menu == "👤 Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA}'>👤 Novo Cadastro no Google Sheets</h3>", unsafe_allow_html=True)
    with st.form("cad_form"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nome").upper()
        i = c2.text_input("Idade")
        comu = c1.text_input("Comunidade").upper()
        t = c2.selectbox("Sala", list(TURMAS_CONFIG.keys()))
        tn = c1.selectbox("Turno", ["A", "B"])
        
        if st.form_submit_button("Finalizar Matrícula"):
            if n and i:
                with st.spinner("Gravando dados..."):
                    client = get_gspread_client()
                    sh = client.open_by_key("1MBAvQB5xGhE7OAHGWdFPvGfwqzP9SpiaIW4OEl2Mgk4")
                    nova_linha = [n, t, tn, i, comu, ""] # Nome, Turma, Turno, Idade, Comu, Padrinho vazio
                    sh.worksheet(t).append_row(nova_linha)
                    sh.worksheet("GERAL").append_row(nova_linha)
                    st.success(f"Matrícula de {n} salva com sucesso!")
            else: st.warning("Preencha os campos obrigatórios.")

elif menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE}'>📋 Quadro de Matrículas</h3>", unsafe_allow_html=True)
    cols_btn = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
        if cols_btn[i].button(sala, key=f"btn_mat_{sala}"): 
            st.session_state.sel_mat = sala
            st.rerun()
    
    df = safe_read(st.session_state.sel_mat)
    if not df.empty:
        st.dataframe(df, use_container_width=True)

elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🤝 Gestão de Apadrinhamento</h3>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    
    sem_pad = df_g[df_g["PADRINHO/MADRINHA"].isin(["", "0", "nan", "NAN", None])]
    
    with st.expander("✨ Vincular Novo Padrinho", expanded=True):
        if not sem_pad.empty:
            c1, c2, c3 = st.columns([2, 2, 1])
            al_vinc = c1.selectbox("Aluno sem Padrinho", sorted(sem_pad["ALUNO"].unique()))
            pad_nome = c2.text_input("Nome do Padrinho/Madrinha").upper()
            if c3.button("Confirmar"):
                if pad_nome:
                    client = get_gspread_client()
                    sh = client.open_by_key("1MBAvQB5xGhE7OAHGWdFPvGfwqzP9SpiaIW4OEl2Mgk4")
                    
                    # Atualiza na aba GERAL (Coluna 6 = F)
                    aba_g = sh.worksheet("GERAL")
                    cell = aba_g.find(al_vinc)
                    aba_g.update_cell(cell.row, 6, pad_nome)
                    
                    # Atualiza na aba da Sala
                    turma_aluno = sem_pad[sem_pad["ALUNO"] == al_vinc]["TURMA"].values[0]
                    aba_s = sh.worksheet(turma_aluno)
                    cell_s = aba_s.find(al_vinc)
                    aba_s.update_cell(cell_s.row, 6, pad_nome)
                    
                    st.success("Vínculo atualizado!")
                    st.rerun()
        else: st.info("Todos os alunos têm padrinhos.")

elif menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO}'>📊 Lançar Notas</h3>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    with st.form("aval"):
        al = st.selectbox("Aluno", sorted(df_g["ALUNO"].unique()))
        tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
        cols_nt = st.columns(2)
        notas = {cat: cols_nt[idx % 2].slider(cat, 1, 5, 3) for idx, cat in enumerate(CATEGORIAS)}
        if st.form_submit_button("Salvar Avaliação"):
            df_av = pd.read_csv(AVAL_FILE) if os.path.exists(AVAL_FILE) else pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS)
            df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
            pd.concat([df_av, pd.DataFrame([[al, tr] + [float(v) for v in notas.values()]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
            st.success("Avaliação salva!")

elif menu == "🌊 Evolução":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🌊 Evolução dos Afilhados</h3>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    df_av = pd.read_csv(AVAL_FILE) if os.path.exists(AVAL_FILE) else pd.DataFrame()
    
    padrinho = st.session_state.nome_usuario if st.session_state.perfil == "padrinho" else st.selectbox("Padrinho:", sorted(df_g["PADRINHO/MADRINHA"].unique()))
    
    afilhas = df_g[df_g["PADRINHO/MADRINHA"].astype(str).str.upper() == padrinho.upper()]
    if not afilhas.empty:
        al_s = st.selectbox("Afilhado:", afilhas["ALUNO"].unique())
        df_al = df_av[df_av["Aluno"] == al_s]
        if not df_al.empty:
            tri = st.selectbox("Trimestre", df_al["Trimestre"].unique())
            row = df_al[df_al["Trimestre"] == tri].iloc[0]
            fig = go.Figure(go.Scatter(x=CATEGORIAS, y=[float(row[c]) for c in CATEGORIAS], fill='tozeroy', line=dict(color=C_AZUL, width=4, shape='spline')))
            fig.update_layout(yaxis=dict(range=[0, 5.5]), height=400)
            st.plotly_chart(fig, use_container_width=True)
    else: st.warning("Nenhum afilhado encontrado.")

elif menu == "🌊 Tábua da Maré":
    st.markdown(f"<h3 style='color:{C_VERDE}'>🌊 Tábua da Maré - Interno</h3>", unsafe_allow_html=True)
    if os.path.exists(AVAL_FILE):
        df_av = pd.read_csv(AVAL_FILE)
        al_s = st.selectbox("Pesquisar Aluno:", sorted(df_av["Aluno"].unique()))
        df_al = df_av[df_av["Aluno"] == al_s]
        if not df_al.empty:
            tri = st.selectbox("Trimestre", df_al["Trimestre"].unique())
            row = df_al[df_al["Trimestre"] == tri].iloc[0]
            fig = go.Figure(go.Scatter(x=CATEGORIAS, y=[float(row[c]) for c in CATEGORIAS], fill='tozeroy', line=dict(color=C_VERDE, width=4, shape='spline')))
            st.plotly_chart(fig, use_container_width=True)
