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

    /* Espaçamentos equilibrados e scannability */
    .block-container {{ padding-top: 1rem !important; padding-bottom: 1rem !important; }}
    [data-testid="stVerticalBlock"] > div {{ padding-bottom: 0.4rem !important; }}
    .stSelectbox, .stCheckbox, .stSlider {{ margin-bottom: 8px !important; }}
    [data-testid="stHorizontalBlock"] {{ gap: 0.8rem !important; margin-bottom: 5px !important; }}
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

# 2. Inicialização de Arquivos Locais
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

# 3. Funções de Leitura
def safe_read(worksheet_name):
    df = pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])
    try:
        sheet_key = "geral" if worksheet_name == "GERAL" else TURMAS_CONFIG.get(worksheet_name, {}).get("key")
        if sheet_key in st.secrets["connections"]["gsheets"]:
            url = st.secrets["connections"]["gsheets"][sheet_key]
            url_csv = url.split("/edit")[0] + "/export?format=csv"
            if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
            df_sheet = pd.read_csv(url_csv)
            df_sheet.columns = [str(c).strip().upper() for c in df_sheet.columns]
            # Mapeamento dinâmico para garantir que "Padrinho/Madrinha" seja encontrado
            if "PADRINHO/MADRINHA" in df_sheet.columns:
                df = df_sheet
            elif "PADRINHO" in df_sheet.columns:
                df_sheet = df_sheet.rename(columns={"PADRINHO": "PADRINHO/MADRINHA"})
                df = df_sheet
    except: pass
    
    try:
        df_l, df_p = pd.read_csv(ALUNOS_FILE), pd.read_csv(PADRINHOS_FILE)
        if worksheet_name == "GERAL": full = pd.concat([df, df_l], ignore_index=True)
        else:
            sala_f = worksheet_name.replace("SALA ", "")
            full = pd.concat([df, df_l[df_l["TURMA"].astype(str).str.contains(sala_f, na=False, case=False)]], ignore_index=True)
        
        full["ALUNO"] = full["ALUNO"].astype(str).str.strip().str.upper()
        # Sobrescreve com edições locais se existirem
        for _, r in df_p.iterrows():
            full.loc[full["ALUNO"] == str(r["ALUNO"]).strip().upper(), "PADRINHO/MADRINHA"] = r["PADRINHO_EDITADO"]
        return full.fillna("")
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
        
# 5. Navegação e Regras de Visibilidade
def set_mat(t): st.session_state.f_mat = t
def set_pad(t): st.session_state.f_pad = t

if 'f_mat' not in st.session_state: st.session_state.f_mat = "Todas"
if 'f_pad' not in st.session_state: st.session_state.f_pad = "SALA ROSA"

if st.session_state.perfil == "admin":
    menu = st.sidebar.radio("Navegação", ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução Individual"])
else:
    menu = "🌊 Evolução Individual" # Padrinho entra direto aqui

# --- ABAS ESPECÍFICAS (Somente Admin vê as primeiras 4) ---

if menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE}; margin-bottom:5px;'>📋 Quadro de Matrículas</h3>", unsafe_allow_html=True)
    cols_t = st.columns(6)
    cols_t[0].button("Todas", on_click=set_mat, args=("Todas",))
    st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child(1) button {{ background-color: {'#333' if st.session_state.f_mat == 'Todas' else '#eee'} !important; color: white !important; }}</style>", unsafe_allow_html=True)
    for i, (sala, conf) in enumerate(TURMAS_CONFIG.items(), 2):
        cols_t[i-1].button(sala, key=f"m_{sala}", on_click=set_mat, args=(sala,))
        is_sel = st.session_state.f_mat == sala
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({i}) button {{ background-color: {conf['cor'] if is_sel else '#eee'} !important; color: {conf['txt'] if is_sel else '#888'} !important; border:none; }}</style>", unsafe_allow_html=True)
    
    df = safe_read(st.session_state.f_mat if st.session_state.f_mat != "Todas" else "GERAL")
    f1, f2 = st.columns(2)
    with f1: f_tn = st.selectbox("Turno (A/B)", ["Todos", "A", "B"])
    with f2: f_cm = st.selectbox("Comunidade", ["Todas"] + sorted([str(x) for x in df["COMUNIDADE"].unique() if x]))
    
    df_f = df.copy()
    if f_tn != "Todos": df_f = df_f[df_f["TURNO"].astype(str).str.strip().str.upper() == f_tn]
    if f_cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm]
    
    # Render Table
    header_classes = ["th-rosa", "th-verde", "th-azul", "th-amarelo"]
    view_cols = ["ALUNO", "TURMA", "IDADE", "COMUNIDADE"]
    html = '<table class="custom-table"><thead><tr>' + "".join([f'<th class="{header_classes[idx%4]}">{c}</th>' for idx, c in enumerate(view_cols)]) + '</tr></thead><tbody>'
    for _, r in df_f.iterrows():
        html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in view_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL}; margin-bottom:5px;'>🤝 Apadrinhamento</h3>", unsafe_allow_html=True)
    cols_p = st.columns(5)
    for i, (sala, conf) in enumerate(TURMAS_CONFIG.items()):
        cols_p[i].button(sala, key=f"p_{sala}", on_click=set_pad, args=(sala,))
        is_sel = st.session_state.f_pad == sala
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({i+1}) button {{ background-color: {conf['cor'] if is_sel else '#eee'} !important; color: {conf['txt'] if is_sel else '#888'} !important; }}</style>", unsafe_allow_html=True)
    
    df = safe_read(st.session_state.f_pad)
    f1, f2, f3 = st.columns([1, 1, 1])
    with f1: f_tn_p = st.selectbox("Turma (A/B) ", ["Todos", "A", "B"])
    with f2: f_cm_p = st.selectbox("Comunidade ", ["Todas"] + sorted([str(x) for x in df["COMUNIDADE"].unique() if x]))
    with f3: check = st.checkbox("Sem padrinho/madrinha")
    
    df_f = df.copy()
    if f_tn_p != "Todos": df_f = df_f[df_f["TURMA"].astype(str).str.strip().str.upper() == f_tn_p]
    if f_cm_p != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm_p]
    if check: df_f = df_f[df_f["PADRINHO/MADRINHA"].astype(str).str.strip().isin(["", "nan", "None", "0"])]
    
    view_cols = ["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
    html = '<table class="custom-table"><thead><tr>' + "".join([f'<th class="th-azul">{c}</th>' for c in view_cols]) + '</tr></thead><tbody>'
    for _, r in df_f.iterrows():
        html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in view_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

    with st.expander("📝 Gerenciar Padrinhos"):
        with st.form("form_pad"):
            al_sel = st.selectbox("Aluno", sorted(df["ALUNO"].unique()))
            novo_p = st.text_input("Nome do Padrinho/Madrinha")
            if st.form_submit_button("Atualizar"):
                df_p = pd.read_csv(PADRINHOS_FILE)
                df_p = df_p[df_p["ALUNO"] != al_sel]
                pd.concat([df_p, pd.DataFrame([[al_sel, novo_p]], columns=["ALUNO", "PADRINHO_EDITADO"])], ignore_index=True).to_csv(PADRINHOS_FILE, index=False)
                st.success("Atualizado!")
                st.rerun()

elif menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO};'>📊 Lançar Notas</h3>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    with st.form("aval_form"):
        c1, c2 = st.columns(2)
        al = c1.selectbox("Aluno", sorted([str(x) for x in df_g["ALUNO"].unique() if x]))
        tr = c2.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
        notas = {cat: st.slider(cat, 1, 5, 3) for cat in CATEGORIAS}
        if st.form_submit_button("Salvar Avaliação"):
            df_av = pd.read_csv(AVAL_FILE)
            df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
            pd.concat([df_av, pd.DataFrame([[al, tr] + [float(v) for v in notas.values()]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
            st.success("Salvo!")

elif menu == "🌊 Evolução Individual":
    st.markdown(f"<h3 style='color:{C_AZUL};'>🌊 Tábua da Maré (Evolução)</h3>", unsafe_allow_html=True)
    if os.path.exists(AVAL_FILE):
        df_av = pd.read_csv(AVAL_FILE)
        df_geral = safe_read("GERAL")
        
        if st.session_state.perfil == "admin":
            alunos_visiveis = sorted(df_av["Aluno"].unique())
        else:
            # Filtra os afilhados comparando o nome do padrinho logado com a planilha
            nome_logado = st.session_state.nome_usuario
            afilhados = df_geral[df_geral["PADRINHO/MADRINHA"].astype(str).str.strip().str.upper() == nome_logado]["ALUNO"].unique()
            alunos_visiveis = [a for a in df_av["Aluno"].unique() if a in afilhados]

        if alunos_visiveis:
            al_s = st.selectbox("Escolha o Aluno", alunos_visiveis)
            df_al = df_av[df_av["Aluno"] == al_s]
            if not df_al.empty:
                tri_s = st.selectbox("Trimestre", df_al["Trimestre"].unique())
                row = df_al[df_al["Trimestre"] == tri_s].iloc[0]
                y_vals = [float(row[cat]) for cat in CATEGORIAS]
                fig = go.Figure(go.Scatter(x=CATEGORIAS, y=y_vals, mode='lines+markers+text', text=[str(int(v)) for v in y_vals], textposition="top center", fill='tozeroy', line=dict(color=C_AZUL, width=4, shape='spline')))
                fig.update_layout(yaxis=dict(range=[0, 5.5], tickvals=[1,2,3,4,5]), height=400, plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Ainda não há avaliações registradas para seus afilhados.")

elif menu == "👤 Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA};'>👤 Novo Cadastro</h3>", unsafe_allow_html=True)
    with st.form("cad"):
        n, i, comu = st.text_input("Nome"), st.text_input("Idade"), st.text_input("Comunidade")
        t, tn = st.selectbox("Sala", list(TURMAS_CONFIG.keys())), st.selectbox("Turma (A/B)", ["A", "B"])
        if st.form_submit_button("Cadastrar"):
            df_l = pd.read_csv(ALUNOS_FILE)
            pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Cadastrado!")
