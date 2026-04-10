import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuração e Estilo
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"
C_AZUL_MARE = "#8fd9fb" 

# Configurações para Alfabetização (Cores do Print 2 enviadas anteriormente)
CORES_TRILHA = {
    "1. Pré-Silábico": {"ativo": "#FF0000", "inativo": "#f1f6fb"},
    "2. Silábico s/ Valor": {"ativo": "#5cc6d0", "inativo": "#d2eff2"},
    "3. Silábico c/ Valor": {"ativo": "#FFFF00", "inativo": "#e5f0cc"},
    "4. Silábico Alfabético": {"ativo": "#00B0F0", "inativo": "#fff1c2"},
    "5. Alfabético Inicial": {"ativo": "#00B050", "inativo": "#ffd9ea"},
    "6. Alfabético Final": {"ativo": "#005a92", "inativo": "#d2eff2"}, # Azul Escuro
    "7. Alfabético Ortográfico": {"ativo": "#B1A0C7", "inativo": "#ffd9ea"}
}
NIVEIS_ALF = list(CORES_TRILHA.keys())
ALF_FILE = "alfabetizacao.csv"
AVAL_FILE = "avaliacoes.csv"

if not os.path.exists(ALF_FILE):
    pd.DataFrame(columns=["Aluno", "Avaliacao", "Nivel", "Gatilho", "Evidencias", "Obs", "Sala", "Ano"]).to_csv(ALF_FILE, index=False)

CATEGORIAS = ["1. Atividades em Grupo/Proatividade", "2. Interesse pelo Novo", "3. Compartilhamento de Materiais", "4. Clareza e Desenvoltura", "5. Respeito às Regras", "6. Vocabulário Adequado", "7. Leitura e Escrita", "8. Compreensão de Comandos", "9. Superação de Desafios", "10. Assiduidade"]
MARE_OPCOES = {"Maré Cheia": 4, "Maré Enchente": 3, "Maré Vazante": 2, "Maré Baixa": 1}
MARE_LABELS = {4: "Maré Cheia", 3: "Maré Enchente", 2: "Maré Vazante", 1: "Maré Baixa"}

if not os.path.exists(AVAL_FILE):
    pd.DataFrame(columns=["Aluno", "Periodo"] + CATEGORIAS + ["Observacoes"]).to_csv(AVAL_FILE, index=False)

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp {{ background-color: #ffffff; font-family: 'Inter', sans-serif; }}
    .main-header {{ text-align: center; padding: 20px 0; }}
    .main-header h1 {{ font-size: 42px !important; font-weight: 800; }}
    .custom-table {{ width: 100%; border-collapse: collapse; font-size: 14px; margin-bottom: 20px; }}
    .custom-table th {{ background-color: #f2f2f2; border: 1px solid #ddd; padding: 12px; text-align: center; font-weight: bold; }}
    .custom-table td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
    .trilha-box {{ padding: 10px; border-radius: 10px; color: white; text-align: center; font-weight: bold; font-size: 10px; min-height: 50px; display: flex; align-items: center; justify-content: center; }}
    </style>
    """, unsafe_allow_html=True)

# 2. Funções de Dados
TURMAS_CONFIG = {
    "SALA ROSA": {"cor": C_ROSA, "key": "sala_rosa"},
    "SALA AMARELA": {"cor": C_AMARELO, "key": "sala_amarela"},
    "SALA VERDE": {"cor": C_VERDE, "key": "sala_verde"},
    "SALA AZUL": {"cor": C_AZUL, "key": "sala_azul"},
    "CIRAND. MUNDO": {"cor": C_ROXO, "key": "cirand_mundo"},
}

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

def render_botoes_salas(key_prefix, session_key, salas_permitidas=None):
    salas = salas_permitidas if salas_permitidas else list(TURMAS_CONFIG.keys())
    cols = st.columns(len(salas))
    for i, sala in enumerate(salas):
        cfg = TURMAS_CONFIG[sala]
        op = "1.0" if st.session_state[session_key] == sala else "0.3"
        st.markdown(f'<style>div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{ background-color: {cfg["cor"]} !important; color: white !important; opacity: {op}; }}</style>', unsafe_allow_html=True)
        if cols[i].button(sala, key=f"{key_prefix}_{sala}"):
            st.session_state[session_key] = sala; st.rerun()

def criar_grafico_mare(categorias, valores):
    fig = go.Figure(go.Scatter(
        x=categorias, y=valores, fill='tozeroy', mode='markers+lines',
        line=dict(color=C_AZUL_MARE, width=4, shape='spline'),
        marker=dict(size=10, color=C_AZUL),
        text=[MARE_LABELS[int(v)] for v in valores], hoverinfo="text+x"
    ))
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', yaxis=dict(range=[0.5, 4.5], visible=False),
        xaxis=dict(showgrid=False, zeroline=False), height=400, margin=dict(l=20, r=20, t=30, b=80))
    return fig

# 3. Inicialização e Login
if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
if "alunos_te_dict" not in st.session_state: st.session_state["alunos_te_dict"] = {}

for k in ['sel_mat', 'sel_pad', 'sel_aval', 'sel_int', 'sel_alf', 'sel_ind', 'sel_te']:
    if k not in st.session_state: st.session_state[k] = "SALA ROSA"

if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        with st.form("login"):
            u = st.text_input("👤 Usuário").strip().upper()
            s = st.text_input("🔑 Chave", type="password")
            if st.form_submit_button("ENTRAR"):
                if u == "ADMIN" and s == "123":
                    st.session_state.update({"logado": True, "perfil": "admin", "nome_usuario": "COORDENAÇÃO"})
                    st.rerun()
                else: st.error("Acesso negado.")
    st.stop()

# 4. Menu e Título Principal
st.sidebar.markdown(f"### 👤 {st.session_state.nome_usuario}")
menu = st.sidebar.radio("Navegação", ["👤 Matrícula", "📝 Alunos matriculados", "Dados - Turno Estendido", "📖 Turno Estendido", "📊 Avaliação da Tábua da Maré", "📈 Indicadores pedagógicos", "🌊 Canal do Apadrinhamento", "🌊 Tábua da Maré"])

if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- ABA: MATRÍCULA ---
if menu == "👤 Matrícula":
    st.markdown(f"### 👤 Novo Cadastro")
    with st.form("form_cad"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome Completo").strip().upper()
        idade = c2.text_input("Idade").strip()
        comu = c1.text_input("Comunidade").strip().upper()
        sala = c2.selectbox("Sala Destino", list(TURMAS_CONFIG.keys()))
        turno = c1.selectbox("Turno", ["A", "B"])
        if st.form_submit_button("Finalizar Cadastro"):
            if nome and idade:
                client = get_gspread_client()
                sh = client.open_by_key("1MBAvQB5xGhE7OAHGWdFPvGfwqzP9SpiaIW4OEl2Mgk4")
                sh.worksheet(sala).append_row([nome, sala, turno, idade, comu, ""])
                sh.worksheet("GERAL").append_row([nome, sala, turno, idade, comu, ""])
                st.success("Cadastrado com sucesso!"); st.rerun()

# --- ABA: ALUNOS MATRICULADOS (COM BOTÃO COLORIDO) ---
elif menu == "📝 Alunos matriculados":
    st.markdown(f"### 📋 Quadro de Alunos Matriculados")
    render_botoes_salas("btn_mat", "sel_mat")
    df_s = safe_read(st.session_state.sel_mat)
    if not df_s.empty:
        selecionados = []
        for i, r in df_s.iterrows():
            c0, c1, c2, c3, c4 = st.columns([0.5, 3, 1, 1, 2])
            n_l = str(r['ALUNO']).strip()
            if n_l in st.session_state["alunos_te_dict"]: c0.markdown("✍️📖")
            else:
                if c0.checkbox("", key=f"chk_{i}"): selecionados.append(n_l)
            c1.write(f"**{n_l}**"); c2.write(f"{r['IDADE']} anos"); c3.write(f"Turno {r['TURNO']}"); c4.write(f"{r['COMUNIDADE']}")
        
        if selecionados:
            cor_btn = TURMAS_CONFIG[st.session_state.sel_mat]['cor']
            st.markdown(f'<style>div.stButton > button:first-child {{ background-color: {cor_btn} !important; color: white !important; }}</style>', unsafe_allow_html=True)
            if st.button(f"Matricular {len(selecionados)} no Turno Estendido"):
                for al in selecionados: st.session_state["alunos_te_dict"][al] = st.session_state.sel_mat
                st.rerun()

# --- NOVA ABA: DADOS - TURNO ESTENDIDO ---
elif menu == "Dados - Turno Estendido":
    st.markdown(f"### 📋 Acompanhamento - Turno Estendido")
    df_h = pd.read_csv(ALF_FILE)
    
    # Legenda
    cols_leg = st.columns(len(NIVEIS_ALF))
    for idx, niv in enumerate(NIVEIS_ALF):
        cols_leg[idx].markdown(f"<div class='trilha-box' style='background-color:{CORES_TRILHA[niv]['ativo']}'>{niv.split('. ')[1]}</div>", unsafe_allow_html=True)

    html = '<table class="custom-table"><thead><tr><th>Nome</th><th>Sala</th><th>1ª Sondagem</th><th>2ª Sondagem</th><th>3ª Sondagem</th><th>Observações</th></tr></thead><tbody>'
    
    alunos_turno = sorted(st.session_state["alunos_te_dict"].keys())
    for al in alunos_turno:
        sala = st.session_state["alunos_te_dict"][al]
        dados_al = df_h[df_h["Aluno"] == al]
        
        def get_nivel_style(tipo):
            row = dados_al[dados_al["Avaliacao"] == tipo]
            if not row.empty:
                nv = row["Nivel"].iloc[0]
                return f'background-color:{CORES_TRILHA[nv]["ativo"]}; color:transparent;'
            return ''

        obs = dados_al["Obs"].iloc[-1] if not dados_al.empty else ""
        
        html += f'<tr><td>{al}</td><td>{sala}</td>'
        html += f'<td style="{get_nivel_style("1ª Avaliação")}">-</td>'
        html += f'<td style="{get_nivel_style("2ª Avaliação")}">-</td>'
        html += f'<td style="{get_nivel_style("Avaliação Final")}">-</td>'
        html += f'<td>{obs}</td></tr>'
    
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# --- ABA: TURNO ESTENDIDO (LANÇAMENTO) ---
elif menu == "📖 Turno Estendido":
    st.markdown(f"### 📖 Registro do Turno Estendido")
    render_botoes_salas("btn_te", "sel_te", salas_permitidas=sorted(list(set(st.session_state["alunos_te_dict"].values()))))
    al_te = [n for n, s in st.session_state["alunos_te_dict"].items() if s == st.session_state.sel_te]
    if al_te:
        al = st.selectbox("Selecione o Aluno", sorted(al_te))
        with st.form("f_alf"):
            nV = st.selectbox("Nível de Escrita", NIVEIS_ALF)
            tipo = st.selectbox("Sondagem", ["1ª Avaliação", "2ª Avaliação", "Avaliação Final"])
            obs = st.text_area("Observações")
            if st.form_submit_button("Salvar Diagnóstico"):
                df_h = pd.read_csv(ALF_FILE)
                # Registro com Ano fixo para 2025 conforme solicitado anteriormente
                new_data = pd.DataFrame([[al, tipo, nV, False, "", obs, st.session_state.sel_te, "2025"]], columns=df_h.columns)
                pd.concat([df_h, new_data], ignore_index=True).to_csv(ALF_FILE, index=False)
                st.success("Salvo com sucesso!"); st.rerun()

# --- ABA: AVALIAÇÃO TÁBUA DA MARÉ ---
elif menu == "📊 Avaliação da Tábua da Maré":
    st.markdown(f"### 📊 Lançar Avaliação")
    render_botoes_salas("btn_aval", "sel_aval")
    df_s = safe_read(st.session_state.sel_aval)
    if not df_s.empty:
        n_limpos = sorted([str(n).replace("**", "").strip() for n in df_s["ALUNO"].unique() if n != ""])
        al = st.selectbox("Selecione o Aluno", n_limpos)
        with st.form("f_av"):
            tr = st.selectbox("Período", ["1º Semestre", "2º Semestre"])
            res = {}
            for cat in CATEGORIAS: res[cat] = st.selectbox(cat, list(MARE_OPCOES.keys()))
            obs = st.text_area("Observações")
            if st.form_submit_button("Salvar"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Periodo'] == tr))]
                pd.concat([df_av, pd.DataFrame([[al, tr] + [MARE_OPCOES[res[c]] for c in CATEGORIAS] + [obs]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Salvo!"); st.rerun()

# --- ABA: INDICADORES PEDAGÓGICOS ---
elif menu == "📈 Indicadores pedagógicos":
    st.markdown("### 📈 Painel de Indicadores")
    df_h = pd.read_csv(ALF_FILE)
    if not df_h.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total de Diagnósticos", len(df_h))
        m2.metric("Alunos no Turno Estendido", len(st.session_state["alunos_te_dict"]))
        st.plotly_chart(px.histogram(df_h, x="Nivel", color="Nivel", title="Distribuição de Níveis", color_discrete_map={k: v["ativo"] for k, v in CORES_TRILHA.items()}))

# --- ABA: CANAL DO APADRINHAMENTO (ORIGINAL E INTACTA) ---
elif menu == "🌊 Canal do Apadrinhamento":
    st.markdown("### 🌊 Canal do Apadrinhamento")
    df_total = safe_read("GERAL")
    if not df_total.empty:
        c1, c2, c3 = st.columns(3)
        comus = ["TODAS"] + sorted([str(x) for x in df_total["COMUNIDADE"].unique() if str(x) != "nan"])
        c_sel = c1.selectbox("Filtrar Comunidade:", comus)
        turnos = ["TODOS", "A", "B"]
        t_sel = c2.selectbox("Filtrar Turno:", turnos)
        
        df_f = df_total.copy()
        if c_sel != "TODAS": df_f = df_f[df_f["COMUNIDADE"] == c_sel]
        if t_sel != "TODOS": df_f = df_f[df_f["TURNO"] == t_sel]
        
        p_sel = c3.selectbox("Pesquisar Padrinho/Madunha:", [""] + sorted([str(x) for x in df_f["PADRINHO/MADRINHA"].unique() if str(x) != "nan"]))
        
        if p_sel:
            afils = df_total[df_total["PADRINHO/MADRINHA"].astype(str).str.upper() == p_sel.upper()]
            if not afils.empty:
                st.write(f"**Afilhados de {p_sel}:**")
                for _, r in afils.iterrows():
                    st.info(f"👤 {r['ALUNO']} - {r['SALA']}")

# --- ABA: TÁBUA DA MARÉ (VISUALIZAÇÃO) ---
elif menu == "🌊 Tábua da Maré":
    st.markdown(f"### 🌊 Tábua da Maré")
    render_botoes_salas("btn_int", "sel_int")
    df_av = pd.read_csv(AVAL_FILE)
    df_geral = safe_read("GERAL")
    alunos_sala = df_geral[df_geral["SALA"] == st.session_state.sel_int]["ALUNO"].unique()
    df_f = df_av[df_av["Aluno"].isin(alunos_sala)]
    if not df_f.empty:
        for al in sorted(df_f["Aluno"].unique()):
            with st.expander(f"📊 {al}"):
                for _, r in df_f[df_f["Aluno"] == al].iterrows():
                    st.write(f"**{r['Periodo']}**")
                    st.plotly_chart(criar_grafico_mare(CATEGORIAS, [float(r[c]) for c in CATEGORIAS]))
