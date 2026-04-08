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
    .row-ciranda {{ background-color: #1a237e !important; color: #ffffff !important; font-weight: 500; }}
    </style>
    
    <div style='text-align: center; padding: 5px;'>
        <h1 style='margin-bottom: 0; font-size: 26px;'>
            <span style='color: {COR_VERDE_INST};'>Instituto</span> <span style='color: {COR_AZUL_INST};'>Mãe</span> <span style='color: {COR_VERDE_INST};'>Lalu</span>
        </h1>
    </div>
    <hr style="border: 0.5px solid {COR_VERDE_INST}; margin: 10px 0;">
    """, unsafe_allow_html=True)

# 2. Configurações de Dados e CSVs Locais
CATEGORIAS = ["Frequência", "Leitura", "Escrita", "Materiais", "Participação", "Regras", "Clareza", "Interesse"]
ALUNOS_FILE = "alunos.csv"
AVAL_FILE = "avaliacoes.csv"
PADRINHOS_FILE = "padrinhos_local.csv"

def init_db():
    if not os.path.exists(ALUNOS_FILE):
        pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]).to_csv(ALUNOS_FILE, index=False)
    if not os.path.exists(AVAL_FILE):
        pd.DataFrame(columns=["Aluno", "Trimestre"] + CATEGORIAS).to_csv(AVAL_FILE, index=False)
    if not os.path.exists(PADRINHOS_FILE):
        pd.DataFrame(columns=["ALUNO", "PADRINHO_EDITADO"]).to_csv(PADRINHOS_FILE, index=False)

init_db()

# 3. Mapeamento e Funções de Dados
MAPA_LINKS = {
    "GERAL": "geral", "SALA ROSA": "sala_rosa", "SALA AMARELA": "sala_amarela",
    "SALA VERDE": "sala_verde", "SALA AZUL": "sala_azul", "CIRAND. MUNDO": "cirand_mundo"
}

TURMAS_CORES = {
    "SALA ROSA": {"bg_off": "#ffeef2", "txt_off": "#d63384", "bg_on": "#ff80ab", "txt_on": "#ffffff"},
    "SALA AMARELA": {"bg_off": "#fff9db", "txt_off": "#856404", "bg_on": "#ffd600", "txt_on": "#ffffff"},
    "SALA VERDE": {"bg_off": "#ebfbee", "txt_off": "#087f5b", "bg_on": "#00c853", "txt_on": "#ffffff"},
    "SALA AZUL": {"bg_off": "#e7f5ff", "txt_off": "#1971c2", "bg_on": "#2979ff", "txt_on": "#ffffff"},
    "CIRAND. MUNDO": {"bg_off": "#e8eaf6", "txt_off": "#1a237e", "bg_on": "#1a237e", "txt_on": "#ffffff"},
}

def safe_read(worksheet_name):
    try:
        secret_key = MAPA_LINKS.get(worksheet_name)
        url = st.secrets["connections"]["gsheets"][secret_key].split("/edit")[0] + "/export?format=csv"
        if "gid=" in st.secrets["connections"]["gsheets"][secret_key]:
            url += f"&gid={st.secrets['connections']['gsheets'][secret_key].split('gid=')[1]}"
        
        df = pd.read_csv(url)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        df_local = pd.read_csv(ALUNOS_FILE)
        df_pad = pd.read_csv(PADRINHOS_FILE)
        
        full_df = pd.concat([df, df_local], ignore_index=True) if worksheet_name == "GERAL" else \
                  pd.concat([df, df_local[df_local["TURMA"].str.contains(worksheet_name.replace("SALA ", ""), na=False, case=False)]], ignore_index=True)
        
        if "ALUNO" in full_df.columns:
            for _, row_p in df_pad.iterrows():
                full_df.loc[full_df["ALUNO"] == row_p["ALUNO"], "PADRINHO/MADRINHA"] = row_p["PADRINHO_EDITADO"]
        
        return full_df.fillna("")
    except:
        return pd.DataFrame(columns=["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"])

def render_styled_table(df, context_color=None):
    if df.empty: return st.info("Sem dados para os filtros selecionados.")
    def get_row_class(row_val, context):
        val = (context if context else str(row_val)).upper()
        if 'ROSA' in val: return 'row-rosa'
        if 'AMARELA' in val: return 'row-amarela'
        if 'VERDE' in v: return 'row-verde'
        if 'AZUL' in v: return 'row-azul'
        if 'CIRAND' in v: return 'row-ciranda'
        return ''
    html = '<table class="custom-table"><thead><tr>' + "".join([f'<th>{c}</th>' for c in df.columns]) + '</tr></thead><tbody>'
    for _, row in df.iterrows():
        row_class = get_row_class(row.get('TURMA', ''), context_color)
        html += f'<tr class="{row_class}">' + "".join([f'<td>{v}</td>' for v in row]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# 4. Navegação Lateral
menu = st.sidebar.radio("Navegação", ["👤 1. Novo Cadastro", "📝 2. Matrículas", "🤝 3. Apadrinhamento", "📊 4. Avaliação", "🌊 5. Evolução"])

# --- NOVO CADASTRO ---
if menu == "👤 1. Novo Cadastro":
    st.header("📝 Registro de Novo Aluno")
    with st.form("cad", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1: n, i, comu = st.text_input("Nome Completo"), st.text_input("Idade"), st.text_input("Comunidade")
        with c2: t, tn = st.selectbox("Turma", ["SALA ROSA", "SALA AMARELA", "SALA VERDE", "SALA AZUL", "CIRAND. MUNDO"]), st.selectbox("Turno", ["MATUTINO", "VESPERTINO"])
        if st.form_submit_button("Salvar Registro"):
            if n and t and tn:
                df_l = pd.read_csv(ALUNOS_FILE)
                pd.concat([df_l, pd.DataFrame([[n.upper(), t, tn, i, comu]], columns=df_l.columns)], ignore_index=True).to_csv(ALUNOS_FILE, index=False)
                st.success("Registrado!")

# --- MATRÍCULAS ---
elif menu == "📝 2. Matrículas":
    st.header("📋 Quadro de Matrículas")
    
    # Filtro de Turmas com Botões Coloridos
    st.write("Selecione a Turma:")
    cols_t = st.columns(6)
    if 'f_turma_mat' not in st.session_state: st.session_state.f_turma_mat = "Todas"
    
    if cols_t[0].button("Todas", type="primary" if st.session_state.f_turma_mat == "Todas" else "secondary"): st.session_state.f_turma_mat = "Todas"
    
    idx = 1
    for sala, cores in TURMAS_CORES.items():
        # CSS dinâmico para destacar o botão selecionado
        is_sel = st.session_state.f_turma_mat == sala
        bg = cores["bg_on"] if is_sel else cores["bg_off"]
        txt = cores["txt_on"] if is_sel else cores["txt_off"]
        
        if cols_t[idx].button(sala, key=f"mat_{sala}", help=f"Filtrar por {sala}"):
            st.session_state.f_turma_mat = sala
        
        # Injeção de CSS para estilizar o botão específico
        st.markdown(f"""
            <style>
            div[data-testid="stColumn"]:nth-child({idx+1}) button {{
                background-color: {bg} !important;
                color: {txt} !important;
                border: 1px solid #e0e0e0;
                border-radius: 8px; /* Bordas suavizadas */
                font-size: 11px; padding: 5px 10px;
            }}
            </style>
            """, unsafe_allow_html=True)
        idx += 1

    # Outros Filtros
    df = safe_read("GERAL")
    f1, f2 = st.columns(2)
    with f1: f_turno = st.selectbox("Turno", ["Todos"] + sorted(list(df["TURNO"].dropna().unique())))
    with f2: f_comu = st.selectbox("Comunidade", ["Todas"] + sorted(list(df["COMUNIDADE"].dropna().unique())))
    
    df_f = df.copy()
    if st.session_state.f_turma_mat != "Todas": df_f = df_f[df_f["TURMA"] == st.session_state.f_turma_mat]
    if f_turno != "Todos": df_f = df_f[df_f["TURNO"] == f_turno]
    if f_comu != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_comu]
    
    render_styled_table(df_f[["ALUNO", "TURMA", "TURNO", "IDADE", "COMUNIDADE"]])

# --- APADRINHAMENTO ---
elif menu == "🤝 3. Apadrinhamento":
    st.header("🤝 Gestão de Apadrinhamento")
    
    # Botões coloridos para Turmas
    st.write("Selecione a Sala:")
    c_rosa, c_ama, c_ver, c_azu, c_cir = st.columns(5)
    if 'sala_sel_pad' not in st.session_state: st.session_state.sala_sel_pad = "SALA ROSA"
    
    idx = 1
    for sala, cores in TURMAS_CORES.items():
        is_sel = st.session_state.sala_sel_pad == sala
        bg = cores["bg_on"] if is_sel else cores["bg_off"]
        txt = cores["txt_on"] if is_sel else cores["txt_off"]
        
        if st.columns(5)[idx-1].button(sala, key=f"pad_{sala}"):
            st.session_state.sala_sel_pad = sala
            
        st.markdown(f"""
            <style>
            div[data-testid="stColumn"]:nth-child({idx}) button {{
                background-color: {bg} !important;
                color: {txt} !important;
                border: 1px solid #e0e0e0;
                border-radius: 8px; /* Bordas suavizadas */
            }}
            </style>
            """, unsafe_allow_html=True)
        idx += 1

    df = safe_read(st.session_state.sala_sel_pad)
    f1, f2 = st.columns(2)
    with f1: f_comu_pad = st.selectbox("Comunidade", ["Todas"] + sorted([x for x in df["COMUNIDADE"].unique() if x]))
    with f2: check = st.checkbox("Somente sem Padrinho")
    
    df_f = df.copy()
    if f_comu_pad != "Todas": df_f = df_f[df_f["COMUNIDADE"] == f_comu_pad]
    if check: df_f = df_f[df_f["PADRINHO/MADRINHA"].astype(str).str.strip().isin(["", "nan", "None"])]
    
    render_styled_table(df_f[["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]], context_color=st.session_state.sala_sel_pad)
    
    st.divider()
    with st.expander("📝 Editar Padrinho/Madrinha"):
        with st.form("edit_p"):
            al_edit = st.selectbox("Selecionar Aluno", sorted(df["ALUNO"].unique()))
            novo_p = st.text_input("Nome do Padrinho/Madrinha")
            if st.form_submit_button("Salvar Alteração"):
                df_p = pd.read_csv(PADRINHOS_FILE)
                df_p = df_p[df_p["ALUNO"] != al_edit]
                pd.concat([df_p, pd.DataFrame([[al_edit, novo_p]], columns=df_p.columns)], ignore_index=True).to_csv(PADRINHOS_FILE, index=False)
                st.success("Atualizado!")
                st.rerun()

# --- AVALIAÇÃO ---
elif menu == "📊 4. Avaliação":
    st.header("📊 Registro de Notas")
    df_g = safe_read("GERAL")
    if not df_g.empty:
        with st.form("av"):
            al = st.selectbox("Aluno", sorted([x for x in df_g["ALUNO"].unique() if x]))
            tr = st.selectbox("Trimestre", ["1º Trimestre", "2º Trimestre", "3º Trimestre"])
            notas = {c: st.slider(c, 1, 5, 3) for c in CATEGORIAS}
            if st.form_submit_button("Gravar"):
                if al and tr:
                    df_av = pd.read_csv(AVAL_FILE)
                    df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Trimestre'] == tr))]
                    pd.concat([df_av, pd.DataFrame([[al, tr] + [float(n) for n in notas.values()]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
                    st.success("Gravado!")

# --- EVOLUÇÃO (BLINDADA) ---
elif menu == "🌊 5. Evolução":
    st.header("🌊 Evolução Individual")
    if os.path.exists(AVAL_FILE):
        df_av = pd.read_csv(AVAL_FILE)
        if not df_av.empty:
            al_s = st.selectbox("Aluno", sorted(df_av["Aluno"].unique()))
            df_al = df_av[df_av["Aluno"] == al_s]
            tri_s = st.selectbox("Trimestre", df_al["Trimestre"].unique())
            row = df_al[df_al["Trimestre"] == tri_s].iloc[0]
            
            # Converte valores para numérico para o gráfico
            y_vals = []
            for c in CATEGORIAS:
                try: y_vals.append(float(row[c]))
                except: y_vals.append(3.0) # Valor padrão caso falhe a conversão
            
            fig = go.Figure(go.Scatter(x=CATEGORIAS, y=y_vals, mode='lines+markers', fill='tozeroy', line=dict(color=COR_AZUL_INST, width=3)))
            fig.update_layout(yaxis=dict(range=[0, 5.5], tickvals=[1,2,3,4,5]), height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma avaliação registrada ainda. Vá em '4. Avaliação' para lançar notas.")
