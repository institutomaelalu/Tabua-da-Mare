import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# 1. Configuração e Estilo
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"
C_AZUL_MARE = "#8fd9fb" 

# Configurações para Alfabetização
CORES_TRILHA = {
    "1. Pré-Silábico": {"ativo": "#d9e6f2", "inativo": "#f1f6fb"},
    "2. Silábico s/ Valor": {"ativo": "#5cc6d0", "inativo": "#d2eff2"},
    "3. Silábico c/ Valor": {"ativo": "#a8cf45", "inativo": "#e5f0cc"},
    "4. Silábico Alfabético": {"ativo": "#ffc713", "inativo": "#fff1c2"},
    "5. Alfabético Inicial": {"ativo": "#ff81ba", "inativo": "#ffd9ea"},
    "6. Alfabético Final": {"ativo": "#5cc6d0", "inativo": "#d2eff2"},
    "7. Alfabético Ortográfico": {"ativo": "#ff81ba", "inativo": "#ffd9ea"}
}
NIVEIS_ALF = list(CORES_TRILHA.keys())
ALF_FILE = "alfabetizacao.csv"
AVAL_FILE = "avaliacoes.csv"

EVIDENCIAS_POR_NIVEL = {
    "1. Pré-Silábico": ["Diferencia letras de desenhos", "Escreve o nome sem apoio", "Acredita que nomes grandes têm muitas letras", "Sabe que se escreve da esquerda para a direita"],
    "2. Silábico s/ Valor": ["Uma letra para cada sílaba (sem som)", "Segmenta a fala em partes", "Respeita quantidade de emissões sonoras", "Faz leitura global da palavra"],
    "3. Silábico c/ Valor": ["Usa vogais correspondentes ao som", "Identifica o som inicial das palavras", "Leitura apontada (acompanha com o dedo)", "Escreve uma letra por sílaba com som correto"],
    "4. Silábico Alfabético": ["Oscila entre uma letra e a sílaba completa", "Começa a usar consoantes nas sílabas", "Consegue completar lacunas de letras", "Percebe a estrutura da sílaba simples"],
    "5. Alfabético Inicial": ["Compreende o sistema de escrita", "Erros ortográficos comuns (ex: K por C)", "Lê textos curtos com fluidez", "Segmentação de palavras irregular"],
    "6. Alfabético Final": ["Diferencia sons semelhantes (P/B, T/D)", "Usa corretamente dígrafos (LH, NH, CH)", "Domina regras básicas de pontuação", "Produz textos com coesão"],
    "7. Alfabético Ortográfico": ["Escrita autônoma e correta", "Domina acentuação e regras complexas", "Lê com entonação e fluidez total", "Revisa o próprio texto"]
}

# Inicialização de arquivos locais
if not os.path.exists(ALF_FILE):
    pd.DataFrame(columns=["Aluno", "Avaliacao", "Nivel", "Flag", "Evidencias", "Obs", "Sala", "Ano"]).to_csv(ALF_FILE, index=False)

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
    .custom-table {{
        width: 100%; border-collapse: separate; border-spacing: 0;
        border: 1px solid #f0f0f0; border-radius: 10px;
        overflow: hidden; font-size: 13px; margin-top: 5px;
        margin-bottom: 15px;
    }}
    .custom-table thead th {{ padding: 12px 10px; text-align: left; color: white !important; font-weight: 700; border: none; }}
    .custom-table td {{ padding: 10px; border-bottom: 1px solid #f9f9f9; color: black; }}
    div.stButton > button {{
        width: 100%; border-radius: 8px !important; font-weight: 700 !important; 
        height: 42px; font-size: 11px !important; border: none !important;
        transition: all 0.3s;
    }}
    .trilha-container {{ display: flex; align-items: center; justify-content: space-between; width: 100%; padding: 10px 0; }}
    .caixa-trilha {{
        flex: 1; height: 85px; border-radius: 15px; display: flex; align-items: center; justify-content: center;
        text-align: center; font-size: 10px; font-weight: 800; padding: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 2px solid transparent; line-height: 1.2;
    }}
    .seta-trilha {{ padding: 0 5px; color: #ccc; font-size: 18px; font-weight: bold; }}
    /* Estilos para a miniatura da maré na tabela */
    .mare-box {{ display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; padding: 2px; }}
    .mare-mini-tabela {{ width: 35px; height: 20px; border: 1px solid #999; border-radius: 3px; }}
    .mare-texto-tabela {{ font-size: 10px; color: #555; font-weight: bold; line-height: 1; text-transform: lowercase; }}
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
        if "PADRINHO" in df.columns: df = df.rename(columns={"PADRINHO": "PADRINHO/MADRINHA"})
        return df.fillna("")
    except: return pd.DataFrame()

def render_filtros(df_geral, key_suffix):
    f1, f2 = st.columns(2)
    tn = f1.selectbox("Filtrar Turno", ["Todos", "A", "B"], key=f"tn_{key_suffix}")
    comu_list = ["Todas"] + sorted([c for c in df_geral["COMUNIDADE"].unique() if str(c).strip()])
    cm = f2.selectbox("Filtrar Comunidade", comu_list, key=f"cm_{key_suffix}")
    return tn, cm

def aplicar_filtros(df_alvo, df_geral, tn, cm):
    df_f = df_alvo.copy()
    if tn != "Todos":
        alunos_turno = df_geral[df_geral["TURNO"].astype(str).str.contains(tn)]["ALUNO"].unique()
        df_f = df_f[df_f["ALUNO"].isin(alunos_turno)]
    if cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == cm]
    return df_f

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

# --- INICIALIZAÇÃO DE SESSÃO ---
if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
if "alunos_te_dict" not in st.session_state: st.session_state["alunos_te_dict"] = {}

for k in ['sel_mat', 'sel_pad', 'sel_aval', 'sel_int', 'sel_alf', 'sel_ind', 'sel_te', 'sel_te_dados']:
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
                else:
                    encontrado = False
                    for sala in TURMAS_CONFIG.keys():
                        df_s = safe_read(sala)
                        if not df_s.empty and "PADRINHO/MADRINHA" in df_s.columns:
                            if u in df_s["PADRINHO/MADRINHA"].astype(str).str.strip().str.upper().unique():
                                encontrado = True; break
                    if encontrado:
                        st.session_state.update({"logado": True, "perfil": "padrinho", "nome_usuario": u})
                        st.rerun()
                    else: st.error("Acesso negado.")
    st.stop()

if st.sidebar.button("🚪 Sair"):
    st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
    st.rerun()

# --- MENU ---
menu_options = ["👤 Matrícula", "📝 Alunos matriculados", "📊 Dados - Turno Estendido", "🤝 Gestão de apadrinhamento", "📊 Avaliação da Tábua da Maré", "📖 Turno Estendido", "📈 Indicadores pedagógicos", "🌊 Canal do Apadrinhamento", "🌊 Tábua da Maré"]
if st.session_state.perfil != "admin": menu_options = ["🌊 Canal do Apadrinhamento"]
menu = st.sidebar.radio("Navegação", menu_options)

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- LOGICA DAS ABAS ---

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

elif menu == "📝 Alunos matriculados":
    st.markdown(f"### 📋 Quadro de Alunos Matriculados")
    render_botoes_salas("btn_mat", "sel_mat")
    st.info("✍️📖 = Aluno já matriculado no Turno Estendido")
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_mat)
    tn, cm = render_filtros(df_g, "mat"); df_f = aplicar_filtros(df_s, df_g, tn, cm)
    cor_h = TURMAS_CONFIG[st.session_state.sel_mat]["cor"]
    st.markdown(f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr><th style="width: 10%;">Sel.</th><th style="width: 45%;">ALUNO</th><th style="width: 15%;">IDADE</th><th style="width: 30%;">COMUNIDADE</th></tr></thead></table>', unsafe_allow_html=True)
    selecionados = []
    for i, r in df_f.iterrows():
        c0, c1, c2, c3 = st.columns([0.5, 3, 1, 2])
        n_l = str(r['ALUNO']).replace("**", "").strip()
        if n_l in st.session_state["alunos_te_dict"]: c0.markdown("✍️📖")
        else:
            if c0.checkbox("", key=f"chk_{i}"): selecionados.append(n_l)
        c1.write(f"**{n_l}**"); c2.write(f"{r['IDADE']} anos"); c3.write(f"{r['COMUNIDADE']}")
    if selecionados:
        st.markdown(f"<style>div.stButton > button[key='btn_bulk_te'] {{ background-color: {cor_h} !important; color: white !important; opacity: 1.0 !important; }}</style>", unsafe_allow_html=True)
        if st.button(f"Matricular {len(selecionados)} aluno(s) no Turno Estendido", key="btn_bulk_te"):
            for al in selecionados: st.session_state["alunos_te_dict"][al] = st.session_state.sel_mat
            st.rerun()

elif menu == "🤝 Gestão de apadrinhamento":
    st.markdown(f"### 🤝 Gestão de Apadrinhamento")
    render_botoes_salas("btn_pad", "sel_pad")
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_pad)
    if not df_s.empty:
        tn, cm = render_filtros(df_g, "pad"); df_f = aplicar_filtros(df_s, df_g, tn, cm)
        cor_h = TURMAS_CONFIG[st.session_state.sel_pad]["cor"]
        v_cols = ["ALUNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
        html = f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
        for _, r in df_f.iterrows():
            n_l = str(r["ALUNO"]).replace("**", "").strip()
            html += f'<tr><td>{n_l}</td><td>{r["IDADE"]}</td><td>{r["COMUNIDADE"]}</td><td>{r["PADRINHO/MADRINHA"]}</td></tr>'
        st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
    else: st.warning("Nenhum dado encontrado para esta sala.")

elif menu == "📊 Avaliação da Tábua da Maré":
    st.markdown(f"### 📊 Lançar Avaliação")
    render_botoes_salas("btn_aval", "sel_aval")
    df_s = safe_read(st.session_state.sel_aval)
    if not df_s.empty:
        n_limpos = sorted([str(n).replace("**", "").strip() for n in df_s[df_s["ALUNO"] != ""]["ALUNO"].unique()])
        al = st.selectbox("Selecione o Aluno", n_limpos)
        st.markdown("#### ⭐ 10 motivos para avaliar!")
        with st.form("f_av"):
            tr = st.selectbox("Período", ["1º Semestre", "2º Semestre"])
            cE, cD = st.columns(2); n_l = {}
            for i, cat in enumerate(CATEGORIAS): n_l[cat] = (cE if i < 5 else cD).selectbox(cat, list(MARE_OPCOES.keys()), key=f"s_{i}")
            obs = st.text_area("Observações:")
            if st.form_submit_button("Salvar"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Periodo'] == tr))]
                pd.concat([df_av, pd.DataFrame([[al, tr] + [MARE_OPCOES[n_l[c]] for c in CATEGORIAS] + [obs]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Salvo!"); st.rerun()

elif menu == "📖 Turno Estendido":
    st.markdown(f"<h3 style='color:{C_ROXO}'>📖 Turno Estendido</h3>", unsafe_allow_html=True)
    df_h = pd.read_csv(ALF_FILE).fillna("")
    if "Ano" not in df_h.columns:
        df_h["Ano"] = 2025
        df_h.to_csv(ALF_FILE, index=False)

    anos_no_csv = sorted(df_h["Ano"].unique().tolist())
    if "lista_anos_te" not in st.session_state:
        st.session_state.lista_anos_te = anos_no_csv if anos_no_csv else [2025, 2026]
    if "ano_registro_te" not in st.session_state: 
        st.session_state.ano_registro_te = st.session_state.lista_anos_te[-1]

    st.write("**Ano da Avaliação:**")
    cols_anos_all = st.columns([0.15] * len(st.session_state.lista_anos_te) + [0.1, 0.6])
    cores_anos = {2025: "#2E86C1", 2026: "#28B463", 2027: "#E67E22", 2028: "#8E44AD"}

    for i, ano in enumerate(st.session_state.lista_anos_te):
        is_active = st.session_state.ano_registro_te == ano
        cor_base = cores_anos.get(ano, "#34495E")
        cor_btn = cor_base if is_active else "#D5DBDB"
        txt_cor = "white" if is_active else "#566573"
        if cols_anos_all[i].button(f"📅 {ano}", key=f"btn_reg_ano_{ano}", use_container_width=True):
            st.session_state.ano_registro_te = ano
            st.rerun()
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] div:nth-child({i+1}) button {{ background-color: {cor_btn} !important; color: {txt_cor} !important; border: {'2px solid black' if is_active else '1px solid #ccc'} !important; }}</style>", unsafe_allow_html=True)

    with cols_anos_all[len(st.session_state.lista_anos_te)].popover("➕"):
        novo_ano_input = st.number_input("Digite o novo ano:", min_value=2024, max_value=2100, value=st.session_state.lista_anos_te[-1] + 1)
        if st.button("Confirmar Novo Ano"):
            if novo_ano_input not in st.session_state.lista_anos_te:
                st.session_state.lista_anos_te.append(novo_ano_input)
                st.session_state.lista_anos_te.sort()
                st.session_state.ano_registro_te = novo_ano_input
                st.rerun()

    st.write(f"Registrando para o ano letivo: **{st.session_state.ano_registro_te}**")
    st.markdown("---")

    with st.expander("➕ Cadastrar Aluno Manualmente no Turno"):
        with st.form("f_te_m"):
            c1, c2 = st.columns(2)
            nM, sM = c1.text_input("Nome").strip().upper(), c2.selectbox("Sala", list(TURMAS_CONFIG.keys()))
            if st.form_submit_button("Adicionar"):
                if nM: st.session_state["alunos_te_dict"][nM] = sM; st.rerun()
    
    salas_te = sorted(list(set(st.session_state["alunos_te_dict"].values())))
    if salas_te:
        if st.session_state.sel_te not in salas_te: st.session_state.sel_te = salas_te[0]
        render_botoes_salas("btn_te", "sel_te", salas_permitidas=salas_te)
        al_te = [n for n, s in st.session_state["alunos_te_dict"].items() if s == st.session_state.sel_te]
        al = st.selectbox("Aluno:", sorted(al_te))
        
        diag = df_h[(df_h["Aluno"] == al) & (df_h["Ano"] == st.session_state.ano_registro_te)].iloc[-1] if not df_h[(df_h["Aluno"] == al) & (df_h["Ano"] == st.session_state.ano_registro_te)].empty else None
        ht = '<div class="trilha-container">'
        for i, n_t in enumerate(NIVEIS_ALF):
            atv = (diag is not None and diag["Nivel"] == n_t)
            ht += f'<div class="caixa-trilha" style="background-color:{CORES_TRILHA[n_t]["ativo" if atv else "inativo"]}; color:{"white" if atv else "#444"}">{n_t.split(". ")[1]}</div>'
            if i < len(NIVEIS_ALF)-1: ht += '<div class="seta-trilha">→</div>'
        st.markdown(ht + '</div>', unsafe_allow_html=True)

        nV = st.selectbox("Novo Nível:", NIVEIS_ALF, index=NIVEIS_ALF.index(diag["Nivel"]) if diag is not None else 0)
        with st.form("f_alf_dinamico"):
            tipo = st.selectbox("Avaliação:", ["1ª Avaliação", "2ª Avaliação", "Avaliação Final"])
            evidencias_atuais = EVIDENCIAS_POR_NIVEL.get(nV, [])
            st.write(f"**Evidências para {nV}:**")
            e_cols = st.columns(3)
            s_ev = []
            for i, ev in enumerate(evidencias_atuais):
                if e_cols[i % 3].checkbox(ev, key=f"chk_{nV}_{i}"): s_ev.append(ev)
            obs = st.text_area("Obs:")
            if st.form_submit_button("Salvar Diagnóstico"):
                new_data = {"Aluno": al, "Avaliacao": tipo, "Nivel": nV, "Flag": datetime.now().strftime("%d/%m/%Y"), "Evidencias": ", ".join(s_ev), "Obs": obs, "Sala": st.session_state.sel_te, "Ano": int(st.session_state.ano_registro_te)}
                df_h = pd.concat([df_h, pd.DataFrame([new_data])], ignore_index=True)
                df_h.to_csv(ALF_FILE, index=False)
                st.success("Salvo!"); st.rerun()

elif menu == "📊 Dados - Turno Estendido":
    st.markdown("### 📋 Panorama de Avaliações")
    df_h = pd.read_csv(ALF_FILE).fillna("")
    if "Ano" not in df_h.columns: df_h["Ano"] = 2025
    
    st.write("Selecione o Ano:")
    if "ano_ativo_te" not in st.session_state: st.session_state.ano_ativo_te = 2025
    col_anos = st.columns([0.15, 0.15, 0.7]) 
    anos = [2025, 2026]
    cores = {2025: "#2E86C1", 2026: "#28B463"} 

    for i, ano in enumerate(anos):
        is_active = st.session_state.ano_ativo_te == ano
        cor_btn = cores[ano] if is_active else "#D5DBDB"
        txt_cor = "white" if is_active else "#566573"
        if col_anos[i].button(f"📅 {ano}", key=f"btn_ano_{ano}", use_container_width=True):
            st.session_state.ano_ativo_te = ano
            st.rerun()
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] div:nth-child({i+1}) button {{ background-color: {cor_btn} !important; color: {txt_cor} !important; border: {'2px solid black' if is_active else '1px solid #ccc'} !important; }}</style>", unsafe_allow_html=True)

    ano_sel = st.session_state.ano_ativo_te
    MAPA_NIVEIS = {niv: i+1 for i, niv in enumerate(NIVEIS_ALF)}
    CORES_EXCLUSIVAS = {"1. Pré-Silábico": "#FF0000", "2. Silábico s/ Valor": "#FFCC00", "3. Silábico c/ Valor": "#FFFF00", "4. Silábico Alfabético": "#00B0F0", "5. Alfabético Inicial": "#00B050", "6. Alfabético Final": "#FF66CC", "7. Alfabético Ortográfico": "#B1A0C7"}

    def get_status_mare_html(nv_atual, hist):
        pct, txt = 85, "maré baixa"
        if nv_atual == "7. Alfabético Ortográfico": pct, txt = 15, "maré cheia"
        elif len(hist) >= 2:
            n_at, n_ant = MAPA_NIVEIS.get(nv_atual, 0), MAPA_NIVEIS.get(hist[-2], 0)
            if n_at > n_ant: pct, txt = 45, "maré enchente"
            elif n_at < n_ant: pct, txt = 70, "maré vazante"
        return f'<div class="mare-box"><div class="mare-mini-tabela" style="background: linear-gradient(to bottom, #f0f0f0 {pct}%, #5DADE2 {pct}%); clip-path: path(\'M 0 4 Q 10 0 20 4 T 40 4 L 40 20 L 0 20 Z\');"></div><span class="mare-texto-tabela">{txt}</span></div>'

    cols_header = ["Nome do Aluno", "1ª Sondagem", "2ª Sondagem", "3ª Sondagem", "STATUS MARÉ"]
    if ano_sel == 2026: cols_header.insert(1, "Diagnóstico Atual")

    html_tab = f'<table class="custom-table"><thead><tr>' + "".join([f'<th style="color:black !important; text-align:center;">{c}</th>' for c in cols_header]) + '</tr></thead><tbody>'
    alunos_te = sorted(st.session_state["alunos_te_dict"].keys())
    for al in alunos_te:
        dados_ano = df_h[(df_h["Aluno"] == al) & (df_h["Ano"] == ano_sel)]
        html_tab += f'<tr><td><b>{al}</b></td>'
        if ano_sel == 2026:
            d_ant = df_h[(df_h["Aluno"] == al) & (df_h["Ano"] == 2025) & (df_h["Avaliacao"] == "Avaliação Final")]
            if not d_ant.empty:
                nv = d_ant["Nivel"].iloc[0]
                html_tab += f'<td style="background:{CORES_EXCLUSIVAS.get(nv)}; text-align:center; font-weight:bold;">{nv.split(". ")[1]}</td>'
            else: html_tab += '<td style="text-align:center;">-</td>'
        for etapa in ["1ª Avaliação", "2ª Avaliação", "Avaliação Final"]:
            r = dados_ano[dados_ano["Avaliacao"] == etapa]
            if not r.empty:
                nv = r["Nivel"].iloc[0]
                html_tab += f'<td style="background:{CORES_EXCLUSIVAS.get(nv)}; text-align:center; font-weight:bold;">{nv.split(". ")[1]}</td>'
            else: html_tab += '<td style="text-align:center;">-</td>'
        status_html = "<td>-</td>"
        if not dados_ano.empty: status_html = f'<td>{get_status_mare_html(dados_ano["Nivel"].iloc[-1], dados_ano["Nivel"].tolist())}</td>'
        html_tab += status_html + '</tr>'
    st.markdown(html_tab + "</tbody></table>", unsafe_allow_html=True)

    st.markdown("---")
    # Ficha Individual
    salas_ativas = sorted(list(set(st.session_state["alunos_te_dict"].values())))
    if salas_ativas:
        render_botoes_salas("btn_te_dados", "sel_te_dados", salas_permitidas=salas_ativas)
        alunos_sala = [n for n, s in st.session_state["alunos_te_dict"].items() if s == st.session_state.sel_te_dados]
        al_sel = st.selectbox("Selecione o Aluno:", sorted(alunos_sala))
        if al_sel:
            dados_al = df_h[(df_h["Aluno"] == al_sel) & (df_h["Ano"] == ano_sel)].copy()
            if not dados_al.empty:
                u_nv = dados_al['Nivel'].iloc[-1]
                vols = [MAPA_NIVEIS.get(n, 0) for n in dados_al['Nivel']]
                s_txt, pct_g = "Maré Baixa", 85
                if u_nv == "7. Alfabético Ortográfico": s_txt, pct_g = "Maré Cheia", 15
                elif len(vols) >= 2:
                    if vols[-1] > vols[-2]: s_txt, pct_g = "Maré Enchente", 45
                    elif vols[-1] < vols[-2]: s_txt, pct_g = "Maré Vazante", 70
                cI, cG = st.columns([1, 1])
                with cI:
                    st.markdown(f'<div style="border:1px solid #ddd; padding:15px; border-radius:12px; background:#f9f9f9; color:black;"><h3 style="margin:0;">{al_sel}</h3><p><b>Nível Atual:</b> <span style="background:{CORES_EXCLUSIVAS.get(u_nv)}; padding:3px 8px; border-radius:8px; font-weight:bold;">{u_nv}</span></p><p><b>Evidências:</b><br><small>{dados_al.iloc[-1]["Evidencias"]}</small></p><p><b>Obs:</b><br><small>{dados_al.iloc[-1]["Obs"]}</small></p></div>', unsafe_allow_html=True)
                with cG:
                    st.markdown(f"#### 🌊 Nível da Maré: {s_txt}")
                    st.markdown(f'<div style="width: 240px; height: 120px; margin: auto; background: linear-gradient(to bottom, #f0f0f0 {pct_g}%, #5DADE2 {pct_g}%); clip-path: path(\'M 0 30 Q 65 10 130 30 T 260 30 L 260 110 Q 260 140 230 140 L 30 140 Q 0 140 0 110 Z\');"></div>', unsafe_allow_html=True)

elif menu == "📈 Indicadores pedagógicos":
    st.markdown("### 📈 Indicadores")
    render_botoes_salas("btn_ind", "sel_ind")
    df_h = pd.read_csv(ALF_FILE)
    if not df_h.empty:
        df_ult = df_h.sort_values("Avaliacao").groupby("Aluno").last().reset_index()
        st.dataframe(df_ult, use_container_width=True)
    else: st.info("Sem dados.")

elif menu == "🌊 Canal do Apadrinhamento":
    st.markdown("### 🌊 Canal do Apadrinhamento")
    df_av = pd.read_csv(AVAL_FILE)
    df_total = pd.concat([safe_read(s) for s in TURMAS_CONFIG.keys()], ignore_index=True)
    p_sel = st.session_state.nome_usuario if st.session_state.perfil == "padrinho" else st.selectbox("Simular Padrinho:", sorted([p for p in df_total["PADRINHO/MADRINHA"].unique() if str(p).strip() not in ["", "0", "nan"]]))
    if p_sel:
        afils = df_total[df_total["PADRINHO/MADRINHA"].astype(str).str.upper() == p_sel.upper()]
        if not afils.empty:
            al_af = st.selectbox("Afilhado:", sorted([str(n).replace("**", "").strip() for n in afils["ALUNO"].unique()]))
            if al_af in df_av["Aluno"].unique():
                for _, r in df_av[df_av["Aluno"] == al_af].iterrows():
                    st.write(f"**{r['Periodo']}**")
                    st.plotly_chart(criar_grafico_mare(CATEGORIAS, [float(r[c]) for c in CATEGORIAS]), use_container_width=True)
            else: st.warning("Sem avaliações.")

elif menu == "🌊 Tábua da Maré":
    st.markdown("### 🌊 Tábua da Maré")
    render_botoes_salas("btn_int", "sel_int")
    df_av = pd.read_csv(AVAL_FILE)
    df_s = safe_read(st.session_state.sel_int)
    if not df_s.empty:
        alunos_sala = [str(n).replace("**", "").strip() for n in df_s["ALUNO"].unique()]
        df_f = df_av[df_av["Aluno"].isin(alunos_sala)]
        if not df_f.empty:
            for al in sorted(df_f["Aluno"].unique()):
                with st.expander(f"📊 {al}"):
                    for _, r in df_f[df_f["Aluno"] == al].iterrows():
                        st.write(f"**{r['Periodo']}**")
                        st.plotly_chart(criar_grafico_mare(CATEGORIAS, [float(r[c]) for c in CATEGORIAS]), key=f"g_{al}_{r['Periodo']}")
        else: st.info("Sem dados.")
