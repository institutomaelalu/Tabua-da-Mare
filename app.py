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
    .row-rosa {{ background-color: #ffeef2 !important; color: #d63384 !important; font-weight: 500; }}
    .row-amarela {{ background-color: #fff9db !important; color: #856404 !important; font-weight: 500; }}
    .row-verde {{ background-color: #ebfbee !important; color: #087f5b !important; font-weight: 500; }}
    .row-azul {{ background-color: #e7f5ff !important; color: #1971c2 !important; font-weight: 500; }}
    .row-ciranda {{ background-color: #3f51b5 !important; color: #ffffff !important; font-weight: 500; }}
    </style>
    <div style='text-align: center;'>
        <h1 style='color: {COR_VERDE_INST}; font-size: 26px;'>Instituto Mãe Lalu</h1>
    </div>
    """, unsafe_allow_html=True)

# 2. Configurações Iniciais e Banco de Dados Local
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"
PADRINHOS_LOCAL = "padrinhos_extra.csv"

def init_db():
    if not os.path.exists(ALUNOS_FILE):
        pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE):
        pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)
    if not os.path.exists(PADRINHOS_LOCAL):
        pd.DataFrame(columns=["ALUNO", "PADRINHO_EDITADO"]).to_csv(PADRINHOS_LOCAL, index=False)

init_db()

# 3. Mapeamento e Funções de Dados
MAPA_LINKS = {
    "GERAL": "geral", "SALA ROSA": "sala_rosa", "SALA AMARELA": "sala_amarela",
    "SALA VERDE": "sala_verde", "SALA AZUL": "sala_azul", "CIRAND. MUNDO": "cirand_mundo"
}

def safe_read(worksheet_name):
    try:
        secret_key = MAPA_LINKS.get(worksheet_name)
        url_original = st.secrets["connections"]["gsheets"][secret_key]
        url_export = url_original.split("/edit")[0] + "/export?format=csv"
        if "gid=" in url_original: url_export += f"&gid={url_original.split('gid=')[1]}"
        df = pd.read_csv(url_export)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Integrar alunos locais
        df_local = pd.read_csv(ALUNOS_FILE)
        if worksheet_name == "GERAL":
            df = pd.concat([df, df_local], ignore_index=True)
        else:
            # Filtra alunos locais que pertencem à sala selecionada
            sala_key = worksheet_name.replace("SALA ", "")
            df_local_sala = df_local[df_local["TURMA"].str.contains(sala_key, na=False, case=False)]
            df = pd.concat([df, df_local_sala], ignore_index=True)
            
        # Aplicar edições locais de padrinhos
        df_pad = pd.read_csv(PADRINHOS_LOCAL)
        if 'PADRINHO/MADRINHA' not in df.columns: df['PADRINHO/MADRINHA'] = ""
        for _, row_p in df_pad.iterrows():
            df.loc[df['ALUNO'] == row_p['ALUNO'], 'PADRINHO/MADRINHA'] = row_p['PADRINHO_EDITADO']
            
        return df.fillna("")
    except:
        return pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])

def render_styled_table(df, context_color=None):
    def get_row_class(row_val, context):
        val = (context if context else str(row_val)).upper()
        if 'ROSA' in val: return 'row-rosa'
        if 'AMARELA' in val: return 'row-amarela'
        if 'VERDE' in val: return 'row-verde'
        if 'AZUL' in val: return 'row-azul'
        if 'CIRAND' in val: return 'row-ciranda'
        return ''

    if df.empty:
        st.info("Nenhum dado encontrado.")
        return

    html = '<table class="custom-table"><thead><tr>'
    for col in df.columns: html += f'<th>{col}</th>'
    html += '</tr></thead><tbody>'
    
    for _, row in df.iterrows():
        row_class = get_row_class(row.get('TURMA', ''), context_color)
        html += f'<tr class="{row_class}">'
        for val in row: html += f'<td>{val}</td>'
        html += '</tr>'
    
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# 4. Navegação
menu = st.sidebar.radio("Navegação", [
    "👤 1. Novo Cadastro",
    "📝 2. Controle de Matrículas", 
    "🤝 3. Controle de Apadrinhamento",
    "📊 4. Avaliação - Tábua da Maré",
    "🌊 5. Tábua da Maré"
])

# --- 1. NOVO CADASTRO ---
if menu == "👤 1. Novo Cadastro":
    st.header("📝 Registro de Novo Aluno")
    with st.form("cad_l", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            n = st.text_input("Nome Completo")
            i = st.text_input("Idade")
            comu = st.text_input("Comunidade")
        with c2:
            t = st.selectbox("Turma", ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"])
            tn = st.selectbox("Turno", ["MATUTINO", "VESPERTINO"])
            
        if st.form_submit_button("Salvar Registro"):
            if n:
                df_l = pd.read_csv(ALUNOS_FILE)
                novo = pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)
                pd.concat([df_l, novo], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
                st.success(f"Aluno {n} cadastrado com sucesso!")
                st.rerun()

# --- 2. CONTROLE DE MATRÍCULAS ---
elif menu == "📝 2. Controle de Matrículas":
    st.header("📋 Quadro de Matrículas")
    df = safe_read("GERAL")
    
    c1, c2 = st.columns(2)
    with c1: f_nome = st.text_input("Buscar Nome")
    with c2:
        lista_turnos = ["Todos"] + sorted([str(x) for x in df["TURNO"].unique() if x])
        f_turno = st.selectbox("Filtrar Turno", lista_turnos)

    df_f = df.copy()
    if f_nome: df_f = df_f[df_f["ALUNO"].str.contains(f_nome, case=False, na=False)]
    if f_turno != "Todos": df_f = df_f[df_f["TURNO"] == f_turno]
    
    render_styled_table(df_f[["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]])

# --- 3. CONTROLE DE APADRINHAMENTO ---
elif menu == "🤝 3. Controle de Apadrinhamento":
    st.header("🤝 Gestão de Apadrinhamento")
    sala = st.selectbox("Selecione a Sala", ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"])
    df = safe_read(sala)
    
    check = st.checkbox("Mostrar apenas sem Padrinho/Madrinha")
    df_f = df.copy()
    if check:
        df_f = df_f[df_f["PADRINHO/MADRINHA"].astype(str).str.strip().isin(["", "None", "nan"])]
    
    render_styled_table(df_f[["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]], context_color=sala)
    
    if not df_f.empty:
        st.divider()
        st.subheader("✍️ Atualizar Padrinho")
        with st.form("edit_p"):
            al_sel = st.selectbox("Selecione o Aluno", sorted(df["ALUNO"].unique()))
            novo_p = st.text_input("Nome do Padrinho/Madrinha")
            if st.form_submit_button("Atualizar"):
                df_p = pd.read_csv(PADRINHOS_LOCAL)
                df_p = df_p[df_p["ALUNO"] != al_sel]
                pd.concat([df_p, pd.DataFrame([[al_sel, novo_p]], columns=df_p.columns)], ignore_index=True).to_csv(PADRINHOS_LOCAL, index=False)
                st.success("Atualizado!")
                st.rerun()

# --- 4. AVALIAÇÃO - TÁBUA DA MARÉ ---
elif menu == "📊 4. Avaliação - Tábua da Maré":
    st.header("📊 Registro de Notas")
    df_g = safe_read("GERAL")
    lista_alunos = sorted([str(x) for x in df_g["ALUNO"].unique() if x])
    
    if lista_alunos:
        with st.form("notas_f"):
            al = st.selectbox("Aluno", lista_alunos)
            tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            sc = {c: st.slider(c, 1, 5, 3) for c in CATEGORIAS}
            if st.form_submit_button("Confirmar"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
                pd.concat([df_av, pd.DataFrame([[al, tr] + list(sc.values())], columns=["Aluno", "Trimestre"] + CATEGORIAS)], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Avaliação salva!")
    else:
        st.warning("Nenhum aluno encontrado.")

# --- 5. TÁBUA DA MARÉ (EVOLUÇÃO) ---
elif menu == "🌊 5. Tábua da Maré":
    st.header("🌊 Tábua da Maré - Evolução Individual")
    df_av = pd.read_csv(AVAL_FILE)
    if not df_av.empty:
        al_sel = st.selectbox("Escolha o Aluno", sorted(df_av["Aluno"].unique()))
        df_al = df_av[df_av["Aluno"] == al_sel]
        tri_sel = st.selectbox("Trimestre", df_al["Trimestre"].unique())
        
        row = df_al[df_al["Trimestre"] == tri_sel].iloc[0]
        val = [float(row[c]) for c in CATEGORIAS]
        
        fig = go.Figure(go.Scatter(x=CATEGORIAS, y=val, mode='lines+markers', fill='tozeroy', line=dict(color=COR_AZUL_INST, width=3)))
        fig.update_layout(yaxis=dict(range=[0, 5.5]), height=450)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma avaliação registrada ainda.")
