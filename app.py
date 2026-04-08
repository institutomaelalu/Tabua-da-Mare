import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# 1. Configuração e Identidade Visual
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp {{ background-color: #ffffff; font-family: 'Inter', sans-serif; }}
    
    .main-title {{ text-align: center; padding: 10px 0; }}
    .main-title h1 {{ font-size: 30px; margin: 0; font-weight: 800; }}
    
    /* Botões de Sala com Cores Fixas */
    div[data-testid="stHorizontalBlock"] {{ align-items: center !important; gap: 0.3rem !important; }}
    .stButton > button {{
        width: 100%; border-radius: 8px !important; 
        font-weight: 700 !important; height: 35px; font-size: 10px !important;
        text-transform: uppercase; border: none !important; color: white !important;
    }}
    
    /* Tabelas */
    .custom-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        border: 1px solid #f2f2f2; border-radius: 10px; font-size: 13px; margin-top: 10px;
    }}
    .custom-table thead th {{ padding: 12px; text-align: left; border-bottom: 2px solid #eee; background-color: #fafafa; }}
    
    /* Cabeçalho Colorido */
    .th-aluno {{ color: {C_AZUL} !important; }}
    .th-turma {{ color: {C_VERDE} !important; }}
    .th-idade {{ color: {C_AMARELO} !important; }}
    .th-comunidade {{ color: {C_ROSA} !important; }}
    .th-padrinho {{ color: {C_AZUL} !important; }}

    /* Fonte Cinza Escuro no Corpo */
    .td-corpo {{ color: #444444 !important; font-weight: 500; }}

    hr {{ margin: 0.5rem 0 !important; border: 0; height: 2px; background: linear-gradient(to right, {C_ROSA}, {C_VERDE}, {C_AZUL}, {C_AMARELO}); }}
    </style>
    
    <div class="main-title">
        <h1>
            <span style='color: {C_VERDE};'>Instituto</span> 
            <span style='color: {C_AZUL};'>Mãe</span> 
            <span style='color: {C_VERDE};'>Lalu</span>
        </h1>
    </div>
    <hr>
    """, unsafe_allow_html=True)

# 2. Estrutura de Dados
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE, AVAL_FILE, PADRINHOS_FILE = "alunos.csv", "avaliacoes.csv", "padrinhos_local.csv"

def init_db():
    if not os.path.exists(ALUNOS_FILE): pd.DataFrame(columns=["ALUNO", "TURMA", "IDADE", "COMUNIDADE"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE): pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)
    if not os.path.exists(PADRINHOS_FILE): pd.DataFrame(columns=["ALUNO", "PADRINHO_EDITADO"]).to_csv(PADRINHOS_FILE, index=False)
init_db()

TURMAS_CONFIG = {
    "SALA ROSA": {"cor": C_ROSA}, "SALA AMARELA": {"cor": C_AMARELO},
    "SALA VERDE": {"cor": C_VERDE}, "SALA AZUL": {"cor": C_AZUL},
    "CIRAND. MUNDO": {"cor": C_ROXO},
}

def safe_read(worksheet_name):
    df = pd.DataFrame(columns=["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])
    try:
        df_l = pd.read_csv(ALUNOS_FILE)
        df_p = pd.read_csv(PADRINHOS_FILE)
        
        if worksheet_name == "GERAL": full = df_l
        else:
            sala_f = worksheet_name.replace("SALA ", "")
            full = df_l[df_l["TURMA"].str.contains(sala_f, na=False, case=False)]
        
        full["ALUNO"] = full["ALUNO"].astype(str).str.strip().upper()
        # Merge de padrinhos editados
        for _, r in df_p.iterrows():
            full.loc[full["ALUNO"] == str(r["ALUNO"]).strip().upper(), "PADRINHO/MADRINHA"] = r["PADRINHO_EDITADO"]
        return full.fillna("")
    except: return df

def render_styled_table(df):
    if df.empty: return st.info("Nenhum dado encontrado.")
    header_map = {"ALUNO": "th-aluno", "TURMA": "th-turma", "IDADE": "th-idade", "COMUNIDADE": "th-comunidade", "PADRINHO/MADRINHA": "th-padrinho"}
    cols = [c for c in df.columns if "UNNAMED" not in c.upper()]
    html = '<table class="custom-table"><thead><tr>'
    for c in cols: html += f'<th class="{header_map.get(c, "")}">{c}</th>'
    html += '</tr></thead><tbody>'
    for _, row in df.iterrows():
        html += f'<tr>' + "".join([f'<td class="td-corpo">{row[v]}</td>' for v in cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# 3. Navegação
menu = st.sidebar.radio("Navegação", ["👤 Novo Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução Individual"])

if menu == "👤 Novo Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA};'>👤 Matricular Aluno</h3>", unsafe_allow_html=True)
    with st.form("cad_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: 
            n = st.text_input("Nome Completo")
            i = st.text_input("Idade")
        with c2: 
            t = st.text_input("Turma (Ex: SALA ROSA A)")
            comu = st.text_input("Comunidade")
        if st.form_submit_button("Salvar"):
            df_l = pd.read_csv(ALUNOS_FILE)
            novo_aluno = pd.DataFrame([[n.upper(), t.upper(), i, comu.upper()]], columns=["ALUNO", "TURMA", "IDADE", "COMUNIDADE"])
            pd.concat([df_l, novo_aluno], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Salvo!")

elif menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE};'>📋 Quadro de Matrículas</h3>", unsafe_allow_html=True)
    if 'f_mat' not in st.session_state: st.session_state.f_mat = "Todas"
    cols = st.columns(6)
    if cols[0].button("Todas"): st.session_state.f_mat = "Todas"
    st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child(1) button {{ background-color: #333 !important; }}</style>", unsafe_allow_html=True)
    for idx, (sala, conf) in enumerate(TURMAS_CONFIG.items(), 2):
        if cols[idx-1].button(sala): st.session_state.f_mat = sala
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({idx}) button {{ background-color: {conf['cor']} !important; }}</style>", unsafe_allow_html=True)
    
    df = safe_read(st.session_state.f_mat if st.session_state.f_mat != "Todas" else "GERAL")
    t_f = st.selectbox("Filtrar Turma", ["Todas"] + sorted(list(df["TURMA"].unique())))
    df_res = df[df["TURMA"] == t_f] if t_f != "Todas" else df
    render_styled_table(df_res[["ALUNO", "TURMA", "IDADE", "COMUNIDADE"]])

elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL};'>🤝 Apadrinhamento</h3>", unsafe_allow_html=True)
    if 'f_pad' not in st.session_state: st.session_state.f_pad = "SALA ROSA"
    cols = st.columns(5)
    for idx, (sala, conf) in enumerate(TURMAS_CONFIG.items(), 1):
        if cols[idx-1].button(sala, key=f"p_{sala}"): st.session_state.f_pad = sala
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({idx}) button {{ background-color: {conf['cor']} !important; }}</style>", unsafe_allow_html=True)
    
    df = safe_read(st.session_state.f_pad)
    t_f = st.selectbox("Filtrar Turma", ["Todas"] + sorted(list(df["TURMA"].unique())), key="pad_f")
    df_res = df[df["TURMA"] == t_f] if t_f != "Todas" else df
    render_styled_table(df_res[["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]])

elif menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO};'>📊 Lançar Notas</h3>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    with st.form("aval"):
        c1, c2 = st.columns(2)
        with c1: al = st.selectbox("Aluno", sorted(list(df_g["ALUNO"].unique())))
        with c2: tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
        st.write("---")
        notas = {}
        sc1, sc2 = st.columns(2)
        for idx, cat in enumerate(CATEGORIAS):
            with sc1 if idx < 4 else sc2: notas[cat] = st.slider(cat, 1, 5, 3)
        if st.form_submit_button("Salvar Avaliação"):
            df_av = pd.read_csv(AVAL_FILE)
            df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
            pd.concat([df_av, pd.DataFrame([[al, tr] + [float(v) for v in notas.values()]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
            st.success("Nota salva!")

elif menu == "🌊 Evolução Individual":
    st.markdown(f"<h3 style='color:{C_AZUL};'>🌊 Evolução Individual</h3>", unsafe_allow_html=True)
    if os.path.exists(AVAL_FILE):
        df_av = pd.read_csv(AVAL_FILE)
        if not df_av.empty:
            al_s = st.selectbox("Selecione o Aluno", sorted(df_av["Aluno"].unique()))
            df_al = df_av[df_av["Aluno"] == al_s]
            if not df_al.empty:
                tri_s = st.selectbox("Selecione o Trimestre", df_al["Trimestre"].unique())
                row = df_al[df_al["Trimestre"] == tri_s].iloc[0]
                y_v = [float(row[c]) for c in CATEGORIAS]
                
                fig = go.Figure(go.Scatter(x=CATEGORIAS, y=y_v, mode='lines+markers+text', text=y_v, textposition="top center", fill='tozeroy', line=dict(color=C_AZUL, width=4, shape='spline')))
                fig.update_layout(yaxis=dict(range=[0, 5.5], tickvals=[1,2,3,4,5]), height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
    else: st.info("Nenhuma avaliação registrada ainda.")
