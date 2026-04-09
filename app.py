import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuração e Estilo
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp {{ background-color: #ffffff; font-family: 'Inter', sans-serif; }}
    .main-header {{ text-align: center; padding: 20px 0; }}
    
    /* Estilização das caixas de seleção (Identidade Visual) */
    div[data-baseweb="select"] > div {{
        background-color: {C_AZUL}22 !important;
        border: 1px solid {C_AZUL}44 !important;
        border-radius: 8px !important;
    }}
    
    .login-card {{
        background: linear-gradient(135deg, {C_AZUL}22, {C_ROSA}22);
        padding: 30px; border-radius: 20px; border: 2px solid #f0f0f0;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. Novos Critérios e Lógica de Maré
CATEGORIAS = [
    "1. Atividades em Grupo/Proatividade",
    "2. Interesse pelo Novo",
    "3. Compartilhamento de Materiais",
    "4. Clareza e Desenvoltura",
    "5. Respeito às Regras",
    "6. Vocabulário Adequado",
    "7. Leitura e Escrita",
    "8. Compreensão de Comandos",
    "9. Superação de Desafios",
    "10. Assiduidade"
]

MARE_OPCOES = {
    "C: Maré Cheia (Muito Bem)": 4,
    "E: Enchente (Em Evolução)": 3,
    "V: Vazante (Teve Declínio)": 2,
    "B: Maré Baixa (Atenção)": 1
}

MARE_REVERSO = {v: k[0] for k, v in MARE_OPCOES.items()}

AVAL_FILE = "avaliacoes.csv"
if not os.path.exists(AVAL_FILE):
    pd.DataFrame(columns=["Aluno", "Periodo"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)

# Funções de Dados
def get_gspread_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

def safe_read(worksheet_name):
    try:
        # Tenta ler do GSheets configurado nos secrets
        conf_keys = {"SALA ROSA": "sala_rosa", "SALA AMARELA": "sala_amarela", "SALA VERDE": "sala_verde", "SALA AZUL": "sala_azul", "CIRAND. MUNDO": "cirand_mundo"}
        if worksheet_name == "GERAL":
            url = st.secrets["connections"]["gsheets"]["geral"]
        else:
            url = st.secrets["connections"]["gsheets"][conf_keys[worksheet_name]]
        
        url_csv = url.split("/edit")[0] + "/export?format=csv"
        if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
        df = pd.read_csv(url_csv)
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df.fillna("")
    except:
        return pd.DataFrame(columns=["ALUNO", "COMUNIDADE", "TURNO"])

# 3. Autenticação e Estados
if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
if "sel_aval" not in st.session_state: st.session_state.sel_aval = "SALA ROSA"

if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown('<div class="login-card"><h2 style="text-align: center; margin:0;">Acesso</h2></div>', unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("👤 Usuário").strip().upper()
            s = st.text_input("🔑 Chave", type="password")
            if st.form_submit_button("ENTRAR"):
                if u == "ADMIN" and s == "123":
                    st.session_state.update({"logado": True, "perfil": "admin", "nome_usuario": "Coordenação"})
                    st.rerun()
                else:
                    df_g = safe_read("GERAL")
                    validos = df_g["PADRINHO/MADRINHA"].astype(str).str.upper().unique() if "PADRINHO/MADRINHA" in df_g.columns else []
                    if u in validos and s == "lalu2026":
                        st.session_state.update({"logado": True, "perfil": "padrinho", "nome_usuario": u})
                        st.rerun()
                    else: st.error("Acesso negado.")
    st.stop()

# --- SIDEBAR ---
menu = st.sidebar.radio("Navegação", ["📊 Lançar Avaliação", "🌊 Evolução (Padrinhos)", "🌊 Tábua da Maré - Interno"])
if st.sidebar.button("🚪 Sair"):
    st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
    st.rerun()

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- ABA: LANÇAR AVALIAÇÃO ---
if menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO}'>📊 Lançar Avaliação (Legenda Tábua de Maré)</h3>", unsafe_allow_html=True)
    
    # Seleção de Sala
    salas = ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"]
    st.session_state.sel_aval = st.selectbox("Selecione a Sala:", salas)

    df_f = safe_read(st.session_state.sel_aval)

    if not df_f.empty:
        with st.form("aval_form"):
            c1, c2 = st.columns(2)
            al = c1.selectbox("Aluno", sorted(df_f["ALUNO"].unique()))
            tr = c2.selectbox("Período", ["1º Semestre", "2º Semestre"])
            
            st.markdown("---")
            st.info("C: Cheia | E: Enchente | V: Vazante | B: Baixa")
            
            # 5 de cada lado
            col_esq, col_dir = st.columns(2)
            notas_letras = {}
            
            for idx, cat in enumerate(CATEGORIAS):
                target_col = col_esq if idx < 5 else col_dir
                notas_letras[cat] = target_col.selectbox(cat, list(MARE_OPCOES.keys()), index=0)

            if st.form_submit_button("Salvar Avaliação"):
                df_av = pd.read_csv(AVAL_FILE)
                # Remove registro anterior do mesmo aluno/periodo se existir
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Periodo'] == tr))]
                
                # Converte letras em números para o banco de dados/gráfico
                valores_num = [MARE_OPCOES[notas_letras[c]] for c in CATEGORIAS]
                nova_linha = pd.DataFrame([[al, tr] + valores_num], columns=df_av.columns)
                
                pd.concat([df_av, nova_linha], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success(f"Avaliação de {al} salva com sucesso!")
    else:
        st.warning("Nenhum aluno encontrado nesta sala.")

# --- ABA: EVOLUÇÃO / TÁBUA DA MARÉ ---
elif menu in ["🌊 Evolução (Padrinhos)", "🌊 Tábua da Maré - Interno"]:
    st.markdown(f"<h3 style='color:{C_AZUL}'>🌊 Visualização da Tábua da Maré</h3>", unsafe_allow_html=True)
    
    df_av = pd.read_csv(AVAL_FILE)
    if not df_av.empty:
        al_s = st.selectbox("Selecione o Aluno:", sorted(df_av["Aluno"].unique()))
        df_al = df_av[df_av["Aluno"] == al_s]
        
        if not df_al.empty:
            tri = st.selectbox("Período", df_al["Periodo"].unique())
            row = df_al[df_al["Periodo"] == tri].iloc[0]
            
            # Preparar dados para o gráfico
            y_vals = [float(row[c]) for c in CATEGORIAS]
            text_labels = [MARE_REVERSO[v] for v in y_vals]
            
            fig = go.Figure()
            
            # Gráfico de área para simular o movimento da maré
            fig.add_trace(go.Scatter(
                x=CATEGORIAS, 
                y=y_vals, 
                mode='lines+markers+text',
                text=text_labels,
                textposition="top center",
                fill='tozeroy',
                line=dict(color=C_AZUL, width=4, shape='spline'),
                marker=dict(size=10, color=C_ROXO)
            ))
            
            fig.update_layout(
                yaxis=dict(
                    range=[0, 4.5],
                    tickvals=[1, 2, 3, 4],
                    ticktext=["B (Baixa)", "V (Vazante)", "E (Enchente)", "C (Cheia)"],
                    gridcolor="#f0f0f0"
                ),
                xaxis=dict(tickangle=-45),
                height=500,
                margin=dict(l=20, r=20, t=20, b=100)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma avaliação registrada ainda.")
