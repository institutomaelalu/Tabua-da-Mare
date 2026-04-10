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

# --- EVIDÊNCIAS DINÂMICAS (Mantidas conforme seu código) ---
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
    pd.DataFrame(columns=["Aluno", "Avaliacao", "Nivel", "Gatilho", "Evidencias", "Obs", "Sala"]).to_csv(ALF_FILE, index=False)

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
    .custom-table td {{ padding: 10px; border-bottom: 1px solid #f9f9f9; }}
    
    div.stButton > button {{
        width: 100%; border-radius: 8px !important; font-weight: 700 !important; 
        height: 42px; font-size: 11px !important; border: none !important;
        transition: all 0.3s;
    }}
    .sala-badge {{
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        color: white; font-weight: 700; font-size: 10px; margin-top: 5px;
        text-transform: uppercase;
    }}
    .trilha-container {{ display: flex; align-items: center; justify-content: space-between; width: 100%; padding: 10px 0; }}
    .caixa-trilha {{
        flex: 1; height: 85px; border-radius: 15px; display: flex; align-items: center; justify-content: center;
        text-align: center; font-size: 10px; font-weight: 800; padding: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 2px solid transparent; line-height: 1.2;
    }}
    .seta-trilha {{ padding: 0 5px; color: #ccc; font-size: 18px; font-weight: bold; }}
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

# --- ABAS ---

if menu == "👤 Matrícula":
    # (Mantido original)
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
    # (Mantido original com a aplicação de cor dinâmica no botão)
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
    # (Mantido original)
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
    # (Mantido original)
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
    # (Mantido original com suas evidências dinâmicas)
    st.markdown(f"<h3 style='color:{C_ROXO}'>📖 Turno Estendido</h3>", unsafe_allow_html=True)
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
        cor_o = TURMAS_CONFIG[st.session_state.sel_te]["cor"]
        st.markdown(f'<div class="sala-badge" style="background-color:{cor_o}">{st.session_state.sel_te}</div>', unsafe_allow_html=True)
        
        df_h = pd.read_csv(ALF_FILE)
        diag = df_h[df_h["Aluno"] == al].iloc[-1] if not df_h[df_h["Aluno"] == al].empty else None
        
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
                if e_cols[i % 3].checkbox(ev, key=f"chk_{nV}_{i}"):
                    s_ev.append(ev)
            obs = st.text_area("Obs:")
            if st.form_submit_button("Salvar Diagnóstico"):
                new_row = pd.DataFrame([[al, tipo, nV, False, ", ".join(s_ev), obs, st.session_state.sel_te]], columns=df_h.columns)
                pd.concat([df_h, new_row], ignore_index=True).to_csv(ALF_FILE, index=False)
                st.success("Diagnóstico salvo!"); st.rerun()
    else: st.info("Sem alunos no Turno.")
# --- NOVA ABA: DADOS - TURNO ESTENDIDO (VERSÃO CORRIGIDA) ---
elif menu == "📊 Dados - Turno Estendido":
    st.markdown("### 📋 Acompanhamento Geral - Turno Estendido")
    df_h = pd.read_csv(ALF_FILE)
    
    # 7 Cores exclusivas, suaves e distintas (sem repetição)
    CORES_EXCLUSIVAS = {
        "1. Pré-Silábico": "#E8E8E8",          # Cinza suave
        "2. Silábico s/ Valor": "#D1F2EB",     # Verde água
        "3. Silábico c/ Valor": "#FCF3CF",     # Amarelo claro
        "4. Silábico Alfabético": "#D5F5E3",   # Verde menta
        "5. Alfabético Inicial": "#FADBD8",    # Rosa pastel
        "6. Alfabético Final": "#E8DAEF",      # Lavanda
        "7. Alfabético Ortográfico": "#D6EAF8" # Azul céu claro
    }

    # Legenda da Trilha no topo
    cols_leg = st.columns(len(NIVEIS_ALF))
    for idx, niv in enumerate(NIVEIS_ALF):
        cols_leg[idx].markdown(f"<div style='background-color:{CORES_EXCLUSIVAS[niv]}; padding:10px; border-radius:10px; text-align:center; font-size:9px; font-weight:bold; color:black; border: 1px solid #ccc;'>{niv.split('. ')[1]}</div>", unsafe_allow_html=True)

    # Tabela Principal (Sem Observações e com Fonte Preta)
    html = """
    <style>
        .cell-diag { text-align: center; font-weight: bold; font-size: 11px; color: black !important; }
        .card-detalhe { border: 1px solid #ddd; padding: 20px; border-radius: 15px; background-color: #f9f9f9; margin-top: 20px; color: black; }
    </style>
    <table class="custom-table">
        <thead style="background-color:#5cc6d0">
            <tr><th>Nome</th><th>Sala</th><th>1ª Sondagem</th><th>2ª Sondagem</th><th>3ª Sondagem</th></tr>
        </thead>
        <tbody>
    """
    
    for al in sorted(st.session_state["alunos_te_dict"].keys()):
        sala_v = st.session_state["alunos_te_dict"][al]
        dados_al = df_h[df_h["Aluno"] == al]
        
        html += f'<tr><td>{al}</td><td>{sala_v}</td>'
        for etapa in ["1ª Avaliação", "2ª Avaliação", "Avaliação Final"]:
            row = dados_al[dados_al["Avaliacao"] == etapa]
            if not row.empty:
                nv = row["Nivel"].iloc[0]
                cor = CORES_EXCLUSIVAS.get(nv, "#eee")
                html += f'<td style="background-color:{cor};"><div class="cell-diag">{nv.split(". ")[1]}</div></td>'
            else:
                html += '<td></td>'
        html += '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

    # --- SEÇÃO DE FILTRO INDIVIDUAL (EVIDÊNCIAS E OBSERVAÇÕES) ---
    st.markdown("---")
    st.markdown("### 🔍 Detalhes por Aluno")
    
    salas_ativas = sorted(list(set(st.session_state["alunos_te_dict"].values())))
    if salas_ativas:
        # Botões de Sala para filtrar alunos do Turno Estendido
        if "sel_te_dados" not in st.session_state: st.session_state.sel_te_dados = salas_ativas[0]
        render_botoes_salas("btn_te_dados", "sel_te_dados", salas_permitidas=salas_ativas)
        
        alunos_da_sala = [n for n, s in st.session_state["alunos_te_dict"].items() if s == st.session_state.sel_te_dados]
        al_sel = st.selectbox("Selecione o aluno para ficha pedagógica:", sorted(alunos_da_sala), key="detalhe_aluno")
        
        if al_sel:
            dados_h = df_h[df_h["Aluno"] == al_sel]
            if not dados_h.empty:
                ultimo = dados_h.iloc[-1]
                cor_nivel = CORES_EXCLUSIVAS.get(ultimo['Nivel'], "#eee")
                
                st.markdown(f"""
                <div class="card-detalhe">
                    <h4 style="margin-top:0; color:black;">Ficha de Evolução: {al_sel}</h4>
                    <p style="color:black;"><b>Nível Diagnosticado:</b> <span style="background-color:{cor_nivel}; padding:5px 12px; border-radius:12px; border: 1px solid #bbb;">{ultimo['Nivel']}</span></p>
                    <p style="color:black;"><b>Evidências Notadas:</b><br>{ultimo['Evidencias'] if ultimo['Evidencias'] else 'Nenhuma evidência registrada.'}</p>
                    <p style="color:black;"><b>Observações Pedagógicas:</b><br><i>{ultimo['Obs'] if ultimo['Obs'] else 'Sem observações.'}</i></p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Este aluno ainda não possui diagnósticos registrados.")

# --- PRÓXIMO MENU (Certifique-se que o elif abaixo está fora do bloco anterior) ---
elif menu == "📈 Indicadores pedagógicos":

    st.markdown(f"### 📈 Indicadores")
    render_botoes_salas("btn_ind", "sel_ind")
    df_h = pd.read_csv(ALF_FILE)
    if not df_h.empty:
        df_ult = df_h.sort_values("Avaliacao").groupby("Aluno").last().reset_index()
        df_ult["Aluno"] = df_ult["Aluno"].str.replace("**", "", regex=False)
        st.dataframe(df_ult, use_container_width=True)
    else: st.info("Sem dados.")

elif menu == "🌊 Canal do Apadrinhamento":
    # (Mantido original)
    st.markdown(f"### 🌊 Canal do Apadrinhamento")
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
    # (Mantido original)
    st.markdown(f"### 🌊 Tábua da Maré")
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
        else: st.info("Nenhuma avaliação lançada para esta sala.")
    else: st.error("Erro ao carregar dados da sala.")
