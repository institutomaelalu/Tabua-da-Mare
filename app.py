import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Configuração de Estilo e Cabeçalho
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

# Paleta de Identidade Visual
C_ROSA = "#ff81ba"
C_VERDE = "#a8cf45"
C_AZUL = "#5cc6d0"
C_AMARELO = "#ffc713"

st.markdown(f"""
    <style>
    /* Fundo Geral */
    .stApp {{ background-color: #ffffff; }}
    
    /* Barra Lateral */
    section[data-testid="stSidebar"] {{
        background-color: #f8f9fa;
        border-right: 1px solid {C_AZUL};
    }}

    /* Tabela Identidade Visual */
    .custom-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        font-family: 'Segoe UI', sans-serif;
        border: 1px solid #eee; border-radius: 12px;
        overflow: hidden; font-size: 13px; margin-top: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }}
    .custom-table thead th {{
        background-color: #ffffff; color: #888; padding: 15px;
        text-align: left; font-weight: 700; border-bottom: 2px solid #f1f1f1;
        text-transform: uppercase; letter-spacing: 1px;
    }}
    .custom-table tbody td {{ padding: 12px 15px; border-bottom: 1px solid #fafafa; background-color: #ffffff; }}
    
    /* Cores das Fontes */
    .txt-rosa {{ color: {C_ROSA} !important; font-weight: 600; }}
    .txt-verde {{ color: {C_VERDE} !important; font-weight: 600; }}
    .txt-azul {{ color: {C_AZUL} !important; font-weight: 600; }}
    .txt-amarelo {{ color: {C_AMARELO} !important; font-weight: 600; }}

    /* Botões Estilizados */
    div.stButton > button {{
        width: 100%; border-radius: 10px !important;
        border: 2px solid #f1f1f1 !important; font-weight: 700 !important;
        height: 48px; transition: all 0.3s ease;
        background-color: white;
    }}
    div.stButton > button:hover {{
        border-color: {C_AZUL} !important;
        transform: translateY(-2px);
    }}
    
    /* Inputs */
    .stTextInput>div>div>input, .stSelectbox>div>div>div {{
        border-radius: 8px !important;
    }}
    </style>
    
    <div style='text-align: center; padding: 10px;'>
        <h1 style='margin-bottom: 0; font-size: 32px;'>
            <span style='color: {C_VERDE};'>Instituto</span> 
            <span style='color: {C_AZUL};'>Mãe</span> 
            <span style='color: {C_VERDE};'>Lalu</span>
        </h1>
        <p style='color: #666; font-style: italic; margin-top: -5px;'>Educação e Afeto</p>
    </div>
    <hr style="border: 0; height: 2px; background-image: linear-gradient(to right, {C_ROSA}, {C_VERDE}, {C_AZUL}, {C_AMARELO}); margin-bottom: 25px;">
    """, unsafe_allow_html=True)

# 2. Configurações de Dados e Banco Local
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE, AVAL_FILE, PADRINHOS_FILE = "alunos.csv", "avaliacoes.csv", "padrinhos_local.csv"

def init_db():
    if not os.path.exists(ALUNOS_FILE): pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE): pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)
    if not os.path.exists(PADRINHOS_FILE): pd.DataFrame(columns=["ALUNO", "PADRINHO_EDITADO"]).to_csv(PADRINHOS_FILE, index=False)
init_db()

# Mapeamento para Identidade Visual nas Abas
TURMAS_CONFIG = {
    "SALA ROSA": {"cor": C_ROSA, "key": "sala_rosa", "txt": "#ffffff"},
    "SALA AMARELA": {"cor": C_AMARELO, "key": "sala_amarela", "txt": "#000000"},
    "SALA VERDE": {"cor": C_VERDE, "key": "sala_verde", "txt": "#ffffff"},
    "SALA AZUL": {"cor": C_AZUL, "key": "sala_azul", "txt": "#ffffff"},
    "CIRAND. MUNDO": {"cor": "#6741d9", "key": "cirand_mundo", "txt": "#ffffff"},
}

def safe_read(worksheet_name):
    df = pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])
    try:
        sheet_key = "geral" if worksheet_name == "GERAL" else TURMAS_CONFIG.get(worksheet_name, {}).get("key")
        if sheet_key and sheet_key in st.secrets["connections"]["gsheets"]:
            url = st.secrets["connections"]["gsheets"][sheet_key]
            url_csv = url.split("/edit")[0] + "/export?format=csv"
            if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
            df_sheet = pd.read_csv(url_csv)
            df_sheet.columns = [str(c).strip().upper() for c in df_sheet.columns]
            df = df_sheet
    except: pass
    
    try:
        df_local = pd.read_csv(ALUNOS_FILE)
        df_pad = pd.read_csv(PADRINHOS_FILE)
        if worksheet_name == "GERAL":
            full = pd.concat([df, df_local], ignore_index=True)
        else:
            sala_filtro = worksheet_name.replace("SALA ", "")
            df_local_sala = df_local[df_local["TURMA"].str.contains(sala_filtro, na=False, case=False)]
            full = pd.concat([df, df_local_sala], ignore_index=True)
        
        if "ALUNO" in full.columns:
            full["ALUNO"] = full["ALUNO"].astype(str).str.strip().str.upper()
            for _, r in df_pad.iterrows():
                full.loc[full["ALUNO"] == str(r["ALUNO"]).strip().upper(), "PADRINHO/MADRINHA"] = r["PADRINHO_EDITADO"]
        return full.fillna("")
    except: return df.fillna("")

def render_styled_table(df):
    if df.empty: return st.warning("Nenhum dado encontrado.")
    font_colors = ["txt-rosa", "txt-verde", "txt-azul", "txt-amarelo"]
    cols_to_show = [c for c in df.columns if "UNNAMED" not in c.upper()]
    html = '<table class="custom-table"><thead><tr>' + "".join([f'<th>{c}</th>' for c in cols_to_show]) + '</tr></thead><tbody>'
    for i, row in df.iterrows():
        color_class = font_colors[i % len(font_colors)]
        html += f'<tr>' + "".join([f'<td class="{color_class}">{row[v]}</td>' for v in cols_to_show]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# 3. Navegação Lateral
st.sidebar.markdown(f"<h3 style='color:{C_AZUL}; text-align:center;'>MENU GESTÃO</h3>", unsafe_allow_html=True)
menu = st.sidebar.radio("", ["👤 Novo Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "🌊 Evolução Individual"])

# --- LÓGICA DAS ABAS ---

if menu == "👤 Novo Cadastro":
    st.markdown(f"<h2 style='color:{C_ROSA};'>📝 Novo Aluno</h2>", unsafe_allow_html=True)
    with st.form("cad_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: n, i, comu = st.text_input("Nome Completo"), st.text_input("Idade"), st.text_input("Comunidade")
        with c2: t, tn = st.selectbox("Turma de Destino", list(TURMAS_CONFIG.keys())), st.selectbox("Turno", ["MATUTINO", "VESPERTINO"])
        if st.form_submit_button("Finalizar Cadastro"):
            df_l = pd.read_csv(ALUNOS_FILE)
            pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.balloons()
            st.success(f"Aluno {n} cadastrado com sucesso!")

elif menu == "📝 Matrículas":
    st.markdown(f"<h2 style='color:{C_VERDE};'>📋 Quadro de Matrículas</h2>", unsafe_allow_html=True)
    if 'f_mat' not in st.session_state: st.session_state.f_mat = "Todas"
    
    cols_t = st.columns(6)
    if cols_t[0].button("Todas", key="btn_todas"): st.session_state.f_mat = "Todas"
    st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child(1) button {{ background-color: {'#333' if st.session_state.f_mat == 'Todas' else '#eee'} !important; color: white !important; }}</style>", unsafe_allow_html=True)

    for i, (sala, conf) in enumerate(TURMAS_CONFIG.items(), 2):
        is_sel = st.session_state.f_mat == sala
        if cols_t[i-1].button(sala, key=f"mat_{sala}"): st.session_state.f_mat = sala
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({i}) button {{ background-color: {conf['cor'] if is_sel else '#eee'} !important; color: {conf['txt'] if is_sel else '#888'} !important; border: none !important; }}</style>", unsafe_allow_html=True)

    df = safe_read(st.session_state.f_mat if st.session_state.f_mat != "Todas" else "GERAL")
    f1, f2 = st.columns(2)
    with f1: f_tn = st.selectbox("Filtrar Turno", ["Todos"] + sorted([str(x) for x in df["TURNO"].unique() if x]))
    with f2: f_cm = st.selectbox("Filtrar Comunidade", ["Todas"] + sorted([str(x) for x in df["COMUNIDADE"].unique() if x]))
    
    df_f = df.copy()
    if f_tn != "Todos": df_f = df_f[df_f["TURNO"] == f_tn]
    if f_cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm]
    render_styled_table(df_f[["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]])

elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h2 style='color:{C_AZUL};'>🤝 Apadrinhamento</h2>", unsafe_allow_html=True)
    if 'f_pad' not in st.session_state: st.session_state.f_pad = "SALA ROSA"
    
    cols_p = st.columns(5)
    for i, (sala, conf) in enumerate(TURMAS_CONFIG.items()):
        is_sel = st.session_state.f_pad == sala
        if cols_p[i].button(sala, key=f"pad_btn_{sala}"): st.session_state.f_pad = sala
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({i+1}) button {{ background-color: {conf['cor'] if is_sel else '#eee'} !important; color: {conf['txt'] if is_sel else '#888'} !important; }}</style>", unsafe_allow_html=True)

    df = safe_read(st.session_state.f_pad)
    df_f = df.copy()
    check = st.checkbox("🔍 Mostrar apenas alunos sem padrinho/madrinha")
    if check and "PADRINHO/MADRINHA" in df_f.columns:
        df_f = df_f[df_f["PADRINHO/MADRINHA"].astype(str).str.strip().isin(["", "nan", "None", "0"])]
    
    render_styled_table(df_f[["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]])
    
    with st.expander("📝 Vincular Novo Padrinho/Madrinha"):
        with st.form("edit_pad_form"):
            al_edit = st.selectbox("Selecione o Aluno", sorted([str(x) for x in df["ALUNO"].unique() if x]))
            novo_p = st.text_input("Nome do Padrinho/Madrinha")
            if st.form_submit_button("Confirmar Vínculo"):
                df_p = pd.read_csv(PADRINHOS_FILE)
                df_p = pd.concat([df_p[df_p["ALUNO"] != al_edit], pd.DataFrame([[al_edit, novo_p]], columns=["ALUNO", "PADRINHO_EDITADO"])], ignore_index=True)
                df_p.to_csv(PADRINHOS_FILE, index=False)
                st.success("Vínculo atualizado!")
                st.rerun()

elif menu == "📊 Lançar Avaliação":
    st.markdown(f"<h2 style='color:{C_AMARELO};'>📊 Avaliação Trimestral</h2>", unsafe_allow_html=True)
    df_g = safe_read("GERAL")
    if not df_g.empty:
        with st.form("aval_form"):
            c1, c2 = st.columns(2)
            with c1: al = st.selectbox("Aluno", sorted([str(x) for x in df_g["ALUNO"].unique() if x]))
            with c2: tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            
            st.write("---")
            notas = {}
            col1, col2 = st.columns(2)
            for i, cat in enumerate(CATEGORIAS):
                with col1 if i < 4 else col2:
                    notas[cat] = st.select_slider(f"{cat}", options=[1, 2, 3, 4, 5], value=3)
            
            if st.form_submit_button("Salvar Avaliação"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
                pd.concat([df_av, pd.DataFrame([[al, tr] + [float(v) for v in notas.values()]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success(f"Notas de {al} gravadas!")

elif menu == "🌊 Evolução Individual":
    st.markdown(f"<h2 style='color:{C_AZUL};'>🌊 Evolução Individual</h2>", unsafe_allow_html=True)
    if os.path.exists(AVAL_FILE):
        df_av = pd.read_csv(AVAL_FILE)
        if not df_av.empty:
            al_s = st.selectbox("Escolha o Aluno", sorted(df_av["Aluno"].unique()))
            df_al = df_av[df_av["Aluno"] == al_s]
            tri_s = st.selectbox("Escolha o Trimestre", df_al["Trimestre"].unique())
            row = df_al[df_al["Trimestre"] == tri_s].iloc[0]
            
            y_vals = [float(row[cat]) for cat in CATEGORIAS]
            
            fig = go.Figure(go.Scatter(
                x=CATEGORIAS, y=y_vals, 
                mode='lines+markers+text',
                text=[str(v) for v in y_vals],
                textposition="top center",
                fill='tozeroy',
                fillcolor=f"rgba(92, 198, 208, 0.2)", # Azul translúcido
                line=dict(color=C_AZUL, width=4, shape='spline'),
                marker=dict(size=10, color=C_ROSA, line=dict(color='white', width=2))
            ))
            
            fig.update_layout(
                yaxis=dict(range=[0, 5.5], tickvals=[1,2,3,4,5], gridcolor="#f0f0f0"),
                xaxis=dict(gridcolor="#f0f0f0"),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=500,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Ainda não há dados para gerar o gráfico.")
