import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# 1. Configuração de Estilo e Cabeçalho
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

COR_VERDE_INST = "#a8cf45"
COR_AZUL_INST = "#5cc6d0"

st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    .custom-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        font-family: 'Segoe UI', sans-serif; color: #31333F;
        border: 1px solid #e6e9ef; border-radius: 8px;
        overflow: hidden; font-size: 12px; margin-top: 15px;
    }}
    .custom-table thead th {{
        background-color: #f0f2f6; color: #555; padding: 8px 12px;
        text-align: left; font-weight: 600; border-bottom: 2px solid #e6e9ef;
    }}
    .custom-table tbody td {{ padding: 6px 12px; border-bottom: 1px solid #f0f2f6; }}
    .row-rosa {{ background-color: #ffeef2 !important; color: #d63384 !important; }}
    .row-amarela {{ background-color: #fff9db !important; color: #856404 !important; }}
    .row-verde {{ background-color: #ebfbee !important; color: #087f5b !important; }}
    .row-azul {{ background-color: #e7f5ff !important; color: #1971c2 !important; }}
    .row-ciranda {{ background-color: #1a237e !important; color: #ffffff !important; }}
    
    div.stButton > button {{
        width: 100%; border-radius: 8px !important;
        border: 1px solid #ddd !important; font-weight: 600 !important; height: 45px;
    }}
    </style>
    
    <div style='text-align: center; padding: 5px;'>
        <h1 style='margin-bottom: 0; font-size: 26px;'>
            <span style='color: {COR_VERDE_INST};'>Instituto</span> <span style='color: {COR_AZUL_INST};'>Mãe</span> <span style='color: {COR_VERDE_INST};'>Lalu</span>
        </h1>
    </div>
    <hr style="border: 0.5px solid {COR_VERDE_INST}; margin: 10px 0;">
    """, unsafe_allow_html=True)

# 2. Configurações de Dados
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE, AVAL_FILE, PADRINHOS_FILE = "alunos.csv", "avaliacoes.csv", "padrinhos_local.csv"

def init_db():
    if not os.path.exists(ALUNOS_FILE): pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE): pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)
    if not os.path.exists(PADRINHOS_FILE): pd.DataFrame(columns=["ALUNO", "PADRINHO_EDITADO"]).to_csv(PADRINHOS_FILE, index=False)
init_db()

TURMAS_CORES = {
    "SALA ROSA": {"bg_off": "#ffeef2", "txt_off": "#d63384", "bg_on": "#d63384", "txt_on": "#ffffff"},
    "SALA AMARELA": {"bg_off": "#fff9db", "txt_off": "#856404", "bg_on": "#ffd600", "txt_on": "#000000"},
    "SALA VERDE": {"bg_off": "#ebfbee", "txt_off": "#087f5b", "bg_on": "#087f5b", "txt_on": "#ffffff"},
    "SALA AZUL": {"bg_off": "#e7f5ff", "txt_off": "#1971c2", "bg_on": "#1971c2", "txt_on": "#ffffff"},
    "CIRAND. MUNDO": {"bg_off": "#e8eaf6", "txt_off": "#1a237e", "bg_on": "#1a237e", "txt_on": "#ffffff"},
}

def safe_read(worksheet_name):
    # Tenta ler do Google Sheets
    try:
        sheet_key = worksheet_name.lower().replace(" ", "_").replace(".", "")
        if worksheet_name == "GERAL": sheet_key = "geral"
        
        url = st.secrets["connections"]["gsheets"][sheet_key]
        url_csv = url.split("/edit")[0] + "/export?format=csv"
        if "gid=" in url: url_csv += f"&gid={url.split('gid=')[1]}"
        
        df = pd.read_csv(url_csv)
        df.columns = [str(c).strip().upper() for c in df.columns]
    except Exception as e:
        # Se falhar o Google, cria um DF vazio com colunas padrão para não travar os filtros
        df = pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])
    
    # Sempre tenta unir com os dados locais salvos no Streamlit Cloud
    try:
        df_local = pd.read_csv(ALUNOS_FILE)
        df_pad = pd.read_csv(PADRINHOS_FILE)
        
        if worksheet_name == "GERAL":
            full = pd.concat([df, df_local], ignore_index=True)
        else:
            sala_filtro = worksheet_name.replace("SALA ", "")
            df_local_sala = df_local[df_local["TURMA"].str.contains(sala_filtro, na=False, case=False)]
            full = pd.concat([df, df_local_sala], ignore_index=True)
            
        # Aplica edições de padrinhos
        if "ALUNO" in full.columns:
            full["ALUNO"] = full["ALUNO"].astype(str).str.strip().str.upper()
            for _, r in df_pad.iterrows():
                al_nome = str(r["ALUNO"]).strip().upper()
                full.loc[full["ALUNO"] == al_nome, "PADRINHO/MADRINHA"] = r["PADRINHO_EDITADO"]
        return full.fillna("")
    except:
        return df.fillna("")

def render_styled_table(df, context_color=None):
    if df.empty: return st.warning("Nenhum dado encontrado.")
    def get_row_class(row_val, context):
        val = (context if context else str(row_val)).upper()
        if 'ROSA' in val: return 'row-rosa'
        if 'AMARELA' in val: return 'row-amarela'
        if 'VERDE' in val: return 'row-verde'
        if 'AZUL' in val: return 'row-azul'
        if 'CIRAND' in val: return 'row-ciranda'
        return ''
    
    cols_to_show = [c for c in df.columns if "UNNAMED" not in c.upper()]
    html = '<table class="custom-table"><thead><tr>' + "".join([f'<th>{c}</th>' for c in cols_to_show]) + '</tr></thead><tbody>'
    for _, row in df.iterrows():
        r_c = get_row_class(row.get('TURMA', ''), context_color)
        html += f'<tr class="{r_c}">' + "".join([f'<td>{row[v]}</td>' for v in cols_to_show]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# 4. Interface Principal
menu = st.sidebar.radio("Navegação", ["👤 1. Novo Cadastro", "📝 2. Matrículas", "🤝 3. Apadrinhamento", "📊 4. Avaliação", "🌊 5. Evolução"])

if menu == "👤 1. Novo Cadastro":
    st.header("📝 Registro de Novo Aluno")
    with st.form("cad_form"):
        c1, c2 = st.columns(2)
        with c1: n, i, comu = st.text_input("Nome"), st.text_input("Idade"), st.text_input("Comunidade")
        with c2: t, tn = st.selectbox("Turma", list(TURMAS_CORES.keys())), st.selectbox("Turno", ["MATUTINO", "VESPERTINO"])
        if st.form_submit_button("Salvar"):
            df_l = pd.read_csv(ALUNOS_FILE)
            pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
            st.success("Salvo com sucesso!")

elif menu == "📝 2. Matrículas":
    st.header("📋 Quadro de Matrículas")
    if 'f_mat' not in st.session_state: st.session_state.f_mat = "Todas"
    
    # Botões de Turma Lado a Lado
    cols_t = st.columns(6)
    if cols_t[0].button("Todas", key="btn_todas", type="primary" if st.session_state.f_mat == "Todas" else "secondary"):
        st.session_state.f_mat = "Todas"
    
    for i, (sala, cores) in enumerate(TURMAS_CORES.items(), 1):
        is_sel = st.session_state.f_mat == sala
        if cols_t[i].button(sala, key=f"mat_{sala}"): st.session_state.f_mat = sala
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({i+1}) button {{ background-color: {cores['bg_on'] if is_sel else cores['bg_off']} !important; color: {cores['txt_on'] if is_sel else cores['txt_off']} !important; }}</style>", unsafe_allow_html=True)

    df = safe_read("GERAL")
    f1, f2 = st.columns(2)
    with f1: f_tn = st.selectbox("Turno", ["Todos"] + sorted([str(x) for x in df["TURNO"].unique() if x]))
    with f2: f_cm = st.selectbox("Comunidade", ["Todas"] + sorted([str(x) for x in df["COMUNIDADE"].unique() if x]))
    
    df_f = df.copy()
    if st.session_state.f_mat != "Todas": df_f = df_f[df_f["TURMA"] == st.session_state.f_mat]
    if f_tn != "Todos": df_f = df_f[df_f["TURNO"] == f_tn]
    if f_cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm]
    render_styled_table(df_f[["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]])

elif menu == "🤝 3. Apadrinhamento":
    st.header("🤝 Gestão de Apadrinhamento")
    if 'f_pad' not in st.session_state: st.session_state.f_pad = "SALA ROSA"
    
    cols_p = st.columns(5)
    for i, (sala, cores) in enumerate(TURMAS_CORES.items()):
        is_sel = st.session_state.f_pad == sala
        if cols_p[i].button(sala, key=f"pad_btn_{sala}"): st.session_state.f_pad = sala
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] > div:nth-child({i+1}) button {{ background-color: {cores['bg_on'] if is_sel else cores['bg_off']} !important; color: {cores['txt_on'] if is_sel else cores['txt_off']} !important; }}</style>", unsafe_allow_html=True)

    df = safe_read(st.session_state.f_pad)
    f1, f2 = st.columns(2)
    with f1: f_cm = st.selectbox("Comunidade ", ["Todas"] + sorted([str(x) for x in df["COMUNIDADE"].unique() if x]))
    with f2: check = st.checkbox("Sem Padrinho")
    
    df_f = df.copy()
    if f_cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_cm]
    if check: 
        if "PADRINHO/MADRINHA" in df_f.columns:
            df_f = df_f[df_f["PADRINHO/MADRINHA"].astype(str).str.strip().isin(["", "nan", "None", "0"])]
    
    render_styled_table(df_f[["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]], context_color=st.session_state.f_pad)
    
    with st.expander("📝 Editar Padrinho/Madrinha"):
        with st.form("edit_pad_form"):
            al_edit = st.selectbox("Aluno", sorted([str(x) for x in df["ALUNO"].unique() if x]))
            novo_p = st.text_input("Nome do Padrinho")
            if st.form_submit_button("Salvar"):
                df_p = pd.read_csv(PADRINHOS_FILE)
                df_p = pd.concat([df_p[df_p["ALUNO"] != al_edit], pd.DataFrame([[al_edit, novo_p]], columns=["ALUNO", "PADRINHO_EDITADO"])], ignore_index=True)
                df_p.to_csv(PADRINHOS_FILE, index=False)
                st.success("Atualizado!"); st.rerun()

elif menu == "📊 4. Avaliação":
    st.header("📊 Lançar Notas")
    df_g = safe_read("GERAL")
    if not df_g.empty:
        with st.form("aval_form"):
            al = st.selectbox("Aluno", sorted([str(x) for x in df_g["ALUNO"].unique() if x]))
            tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            notas = {c: st.slider(c, 1, 5, 3) for c in CATEGORIAS}
            if st.form_submit_button("Gravar Avaliação"):
                df_av = pd.read_csv(AVAL_FILE)
                # Remove duplicata antes de salvar
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
                nova_linha = pd.DataFrame([[al, tr] + [float(v) for v in notas.values()]], columns=df_av.columns)
                pd.concat([df_av, nova_linha], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Avaliação salva!")

elif menu == "🌊 5. Evolução":
    st.header("🌊 Evolução Individual")
    if os.path.exists(AVAL_FILE):
        df_av = pd.read_csv(AVAL_FILE)
        if not df_av.empty:
            al_s = st.selectbox("Selecione o Aluno", sorted(df_av["Aluno"].unique()))
            df_al = df_av[df_av["Aluno"] == al_s]
            tri_s = st.selectbox("Selecione o Trimestre", df_al["Trimestre"].unique())
            row = df_al[df_al["Trimestre"] == tri_s].iloc[0]
            
            y_vals = [float(row[c]) for c in CATEGORIAS]
            fig = go.Figure(go.Scatter(x=CATEGORIAS, y=y_vals, mode='lines+markers', fill='tozeroy', line=dict(color=COR_AZUL_INST, width=3)))
            fig.update_layout(yaxis=dict(range=[0, 5.5], tickvals=[1,2,3,4,5]), height=450)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma avaliação registrada no sistema.")
