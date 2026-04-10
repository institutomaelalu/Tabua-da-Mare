import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import gspread
from google.oauth2.service_account import Credentials

# 1. Configuração e Estilo
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

# Definição de Cores
C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"
C_AZUL_MARE = "#8fd9fb" 

# Configurações para Alfabetização (Cores do Print 2 / PDF solicitado)
CORES_TRILHA = {
    "1. Pré-Silábico": {"ativo": "#FF0000", "inativo": "#f1f6fb"},       # Vermelho
    "2. Silábico s/ Valor": {"ativo": "#5cc6d0", "inativo": "#d2eff2"},  # Azul Claro
    "3. Silábico c/ Valor": {"ativo": "#FFFF00", "inativo": "#e5f0cc"},  # Amarelo
    "4. Silábico Alfabético": {"ativo": "#00B0F0", "inativo": "#fff1c2"}, # Azul Médio
    "5. Alfabético Inicial": {"ativo": "#00B050", "inativo": "#ffd9ea"},  # Verde
    "6. Alfabético Final": {"ativo": "#0070C0", "inativo": "#d2eff2"},    # Azul Escuro (Diferenciado)
    "7. Alfabético Ortográfico": {"ativo": "#B1A0C7", "inativo": "#ffd9ea"} # Lilás
}
NIVEIS_ALF = list(CORES_TRILHA.keys())
ALF_FILE = "alfabetizacao.csv"
AVAL_FILE = "avaliacoes.csv"

# Evidências Dinâmicas
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
    
    /* Tabelas customizadas */
    .custom-table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 20px; }}
    .custom-table th {{ background-color: #f2f2f2; border: 1px solid #ddd; padding: 8px; text-align: center; font-weight: bold; }}
    .custom-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    
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
                else: st.error("Acesso negado.")
    st.stop()

# --- MENU ---
menu_options = ["👤 Matrícula", "📝 Alunos matriculados", "Acompanhamento - Turno Estendido", "📖 Turno Estendido", "🤝 Gestão de apadrinhamento", "📊 Avaliação da Tábua da Maré", "📈 Indicadores pedagógicos", "🌊 Canal do Apadrinhamento", "🌊 Tábua da Maré"]
if st.session_state.perfil != "admin": menu_options = ["🌊 Canal do Apadrinhamento"]
menu = st.sidebar.radio("Navegação", menu_options)

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- ABAS ---

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
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_mat)
    cor_h = TURMAS_CONFIG[st.session_state.sel_mat]["cor"]
    
    selecionados = []
    for i, r in df_s.iterrows():
        c0, c1, c2, c3 = st.columns([0.5, 3, 1, 2])
        n_l = str(r['ALUNO']).replace("**", "").strip()
        if n_l in st.session_state["alunos_te_dict"]: c0.markdown("✍️📖")
        else:
            if c0.checkbox("", key=f"chk_{i}"): selecionados.append(n_l)
        c1.write(f"**{n_l}**"); c2.write(f"{r['IDADE']} anos"); c3.write(f"{r['COMUNIDADE']}")
    
    if selecionados:
        if st.button(f"Matricular {len(selecionados)} no Turno Estendido"):
            for al in selecionados: st.session_state["alunos_te_dict"][al] = st.session_state.sel_mat
            st.rerun()

elif menu == "Acompanhamento - Turno Estendido":
    st.markdown("### 📋 Acompanhamento - Turno Estendido")
    ano_sel = st.selectbox("Selecione o Ano:", ["2025", "2026"])
    
    # Legenda de Cores
    st.markdown("---")
    l_cols = st.columns(len(NIVEIS_ALF))
    for i, niv in enumerate(NIVEIS_ALF):
        l_cols[i].markdown(f"<div style='background-color:{CORES_TRILHA[niv]['ativo']}; color:white; padding:5px; text-align:center; border-radius:5px; font-size:10px; font-weight:bold;'>{niv.split('. ')[1]}</div>", unsafe_allow_html=True)
    st.markdown("---")

    df_h = pd.read_csv(ALF_FILE)
    df_h = df_h[df_h["Ano"].astype(str) == ano_sel]
    
    # Cabeçalho da Tabela
    cols = ["Nome", "Sala", "1ª Sondagem", "2ª Sondagem", "3ª Sondagem"]
    if ano_sel == "2026": cols.append("Evidências")
    cols.append("Observações")
    
    html = '<table class="custom-table"><thead><tr>' + "".join([f'<th>{c}</th>' for c in cols]) + '</tr></thead><tbody>'
    
    for al, sala in sorted(st.session_state["alunos_te_dict"].items()):
        al_data = df_h[df_h["Aluno"] == al]
        
        def get_nivel_color(tipo):
            row = al_data[al_data["Avaliacao"] == tipo]
            if not row.empty:
                nivel = row["Nivel"].iloc[0]
                return f'background-color:{CORES_TRILHA[nivel]["ativo"]}; color:transparent;'
            return ''

        html += f'<tr><td>{al}</td><td>{sala}</td>'
        html += f'<td style="{get_nivel_color("1ª Avaliação")}">-</td>'
        html += f'<td style="{get_nivel_color("2ª Avaliação")}">-</td>'
        html += f'<td style="{get_nivel_color("Avaliação Final")}">-</td>'
        
        if ano_sel == "2026":
            evid = al_data["Evidencias"].iloc[-1] if not al_data.empty else ""
            html += f'<td>{evid}</td>'
            
        obs = al_data["Obs"].iloc[-1] if not al_data.empty else ""
        html += f'<td>{obs}</td></tr>'
        
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

elif menu == "📖 Turno Estendido":
    st.markdown(f"### 📖 Lançamento Diagnóstico")
    ano_reg = st.radio("Ano do Registro:", ["2025", "2026"], horizontal=True)
    
    salas_te = sorted(list(set(st.session_state["alunos_te_dict"].values())))
    if salas_te:
        render_botoes_salas("btn_te", "sel_te", salas_permitidas=salas_te)
        al_te = [n for n, s in st.session_state["alunos_te_dict"].items() if s == st.session_state.sel_te]
        al = st.selectbox("Aluno:", sorted(al_te))
        
        df_h = pd.read_csv(ALF_FILE)
        diag_existente = df_h[(df_h["Aluno"] == al) & (df_h["Ano"].astype(str) == ano_reg)].iloc[-1] if not df_h[(df_h["Aluno"] == al) & (df_h["Ano"].astype(str) == ano_reg)].empty else None
        
        nV = st.selectbox("Nível Alfabetização:", NIVEIS_ALF, index=NIVEIS_ALF.index(diag_existente["Nivel"]) if diag_existente is not None else 0)
        
        with st.form("f_alf_din"):
            tipo = st.selectbox("Avaliação:", ["1ª Avaliação", "2ª Avaliação", "Avaliação Final"])
            s_ev = []
            if ano_reg == "2026":
                st.write(f"**Evidências para {nV}:**")
                evidencias_lista = EVIDENCIAS_POR_NIVEL.get(nV, [])
                e_cols = st.columns(2)
                for i, ev in enumerate(evidencias_lista):
                    if e_cols[i%2].checkbox(ev, key=f"ev_{i}"): s_ev.append(ev)
            
            obs = st.text_area("Observações:")
            if st.form_submit_button("Salvar"):
                # Remove registro anterior do mesmo aluno/av/ano para evitar duplicados
                df_h = df_h[~((df_h["Aluno"] == al) & (df_h["Avaliacao"] == tipo) & (df_h["Ano"].astype(str) == ano_reg))]
                novo_diag = pd.DataFrame([[al, tipo, nV, False, ", ".join(s_ev), obs, st.session_state.sel_te, ano_reg]], columns=df_h.columns)
                pd.concat([df_h, novo_diag], ignore_index=True).to_csv(ALF_FILE, index=False)
                st.success("Salvo com sucesso!"); st.rerun()

# (Restante das Abas de Gestão de Apadrinhamento, Tábua da Maré e Indicadores permanecem conforme original)
elif menu == "🤝 Gestão de apadrinhamento":
    st.markdown(f"### 🤝 Gestão de Apadrinhamento")
    render_botoes_salas("btn_pad", "sel_pad")
    df_s = safe_read(st.session_state.sel_pad)
    if not df_s.empty:
        st.dataframe(df_s[["ALUNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]], use_container_width=True)

elif menu == "📊 Avaliação da Tábua da Maré":
    st.markdown(f"### 📊 Avaliação da Maré")
    render_botoes_salas("btn_aval", "sel_aval")
    df_s = safe_read(st.session_state.sel_aval)
    if not df_s.empty:
        n_limpos = sorted([str(n).replace("**", "").strip() for n in df_s["ALUNO"].unique() if n != ""])
        al = st.selectbox("Aluno:", n_limpos)
        with st.form("f_av"):
            tr = st.selectbox("Período", ["1º Semestre", "2º Semestre"])
            res = {}
            for cat in CATEGORIAS: res[cat] = st.selectbox(cat, list(MARE_OPCOES.keys()))
            obs = st.text_area("Notas:")
            if st.form_submit_button("Salvar"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Periodo'] == tr))]
                nova_av = pd.DataFrame([[al, tr] + [MARE_OPCOES[res[c]] for c in CATEGORIAS] + [obs]], columns=df_av.columns)
                pd.concat([df_av, nova_av], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Salvo!"); st.rerun()
