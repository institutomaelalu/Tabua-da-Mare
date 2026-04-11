import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
# 1. CONFIGURAÇÃO E ESTILO (Sempre o primeiro comando Streamlit)
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")
# --- 1. ESTABELECER CONEXÃO (OBRIGATÓRIO SER AQUI) ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. CARREGAMENTO INICIAL ---
try:
    # 1. Base Geral de Alunos
    df_g = conn.read(worksheet="GERAL").fillna("")
    df_g.columns = [str(c).strip().upper() for c in df_g.columns]
    
    # 2. Base do Turno Estendido (Substitui o ALF_FILE)
    df_alf = conn.read(worksheet="TURNO_ESTENDIDO").fillna("")
    df_alf.columns = [str(c).strip().upper() for c in df_alf.columns]

    # 3. Base da Tábua da Maré (Substitui o AVAL_FILE)
    df_aval = conn.read(worksheet="TABUA_MARE").fillna("")
    df_aval.columns = [str(c).strip().upper() for c in df_aval.columns]
    
except Exception as e:
    st.error(f"Erro ao carregar dados da nuvem: {e}")
    df_g = pd.DataFrame(columns=["ALUNO", "TURNO", "COMUNIDADE", "SALA"])
    df_alf = pd.DataFrame(columns=["ALUNO", "SALA", "ANO", "AVALIAÇÃO", "DIAGNÓSTICO"])
    df_aval = pd.DataFrame(columns=["ALUNO", "SEMESTRE"] + CATEGORIAS)

# --- 3. FUNÇÕES DE FILTRO (Ajustadas para os novos nomes) ---
def render_filtros(df_geral, key_suffix):
    f1, f2 = st.columns(2)
    tn = f1.selectbox("Filtrar Turno", ["Todos", "A", "B"], key=f"tn_{key_suffix}")
    
    # Verificação de segurança para evitar o KeyError: 'COMUNIDADE'
    if "COMUNIDADE" in df_geral.columns:
        comu_list = ["Todas"] + sorted([c for c in df_geral["COMUNIDADE"].unique() if str(c).strip()])
    else:
        comu_list = ["Todas"]
        
    cm = f2.selectbox("Filtrar Comunidade", comu_list, key=f"cm_{key_suffix}")
    return tn, cm

# --- DEFINIÇÕES DE NÍVEIS E CORES (MATRIZES) ---
NIVEIS_ALF = [
    "1. Pré-Silábico", "2. Silábico s/ Valor", "3. Silábico c/ Valor", 
    "4. Silábico Alfabético", "5. Alfabético Inicial", "6. Alfabético Final", 
    "7. Alfabético Ortográfico"
]

MAPA_NIVEIS = {niv: i+1 for i, niv in enumerate(NIVEIS_ALF)}

CORES_EXCLUSIVAS = {
    "1. Pré-Silábico": "#FADBD8", "2. Silábico s/ Valor": "#FDEBD0", 
    "3. Silábico c/ Valor": "#FCF3CF", "4. Silábico Alfabético": "#D5F5E3", 
    "5. Alfabético Inicial": "#A9DFBF", "6. Alfabético Final": "#D6EAF8", 
    "7. Alfabético Ortográfico": "#EBDEF0"
}

# Cores de Identidade Visual
C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"
C_AZUL_MARE = "#8fd9fb" 

# --- FUNÇÕES DE REGISTRO (ESCRITA NA NUVEM) ---

def registrar_turno_estendido(aluno, sala, avaliacao_tipo, nivel, evidencias_list, obs, ano=2026):
    """Salva dados na aba TURNO_ESTENDIDO"""
    try:
        # Lê a aba atual
        df_atual = conn.read(worksheet="TURNO_ESTENDIDO").fillna("")
        evidencias_str = "; ".join(evidencias_list) if isinstance(evidencias_list, list) else evidencias_list
        
        novo_registro = {
            "DATA": datetime.now().strftime("%d/%m/%Y"),
            "ALUNO": aluno,
            "SALA": sala,
            "1 AVALIAÇÃO": nivel if avaliacao_tipo == "1ª Avaliação" else "",
            "2 AVALIAÇÃO": nivel if avaliacao_tipo == "2ª Avaliação" else "",
            "3 AVALIAÇÃO": nivel if avaliacao_tipo == "3ª Avaliação" else "",
            "ANO": ano,
            "DIAGNÓSTICO": nivel,
            "EVIDÊNCIAS": evidencias_str,
            "OBSERVAÇÕES PEDAGÓGICAS": obs
        }
        
        df_final = pd.concat([df_atual, pd.DataFrame([novo_registro])], ignore_index=True)
        conn.update(worksheet="TURNO_ESTENDIDO", data=df_final)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar Turno Estendido: {e}")
        return False

def registrar_tabua_mare(aluno, sala, semestre, notas_dict, obs):
    """Salva ou atualiza dados na aba TABUA_MARE"""
    try:
        df_atual = conn.read(worksheet="TABUA_MARE").fillna("")
        
        # Lógica de Update ou Insert
        mask = (df_atual["ALUNO"] == aluno) & (df_atual["SEMESTRE"] == semestre)
        
        if mask.any():
            idx = df_atual.index[mask][0]
            for col, valor in notas_dict.items():
                df_atual.at[idx, col] = valor
            df_atual.at[idx, "OBSERVAÇÕES PEDAGÓGICAS"] = obs
            df_atual.at[idx, "SALA"] = sala
        else:
            registro = {"ALUNO": aluno, "SALA": sala, "SEMESTRE": semestre, "OBSERVAÇÕES PEDAGÓGICAS": obs}
            registro.update(notas_dict)
            df_atual = pd.concat([df_atual, pd.DataFrame([registro])], ignore_index=True)
        
        conn.update(worksheet="TABUA_MARE", data=df_atual)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao sincronizar Tábua da Maré: {e}")
        return False

# --- COMPONENTES VISUAIS E SUPORTE ---

def get_text_color(nivel=None):
    return "#2C3E50"

def render_legenda_niveis():
    st.markdown("##### 📝 Legenda de Níveis")
    cols_leg = st.columns(len(NIVEIS_ALF))
    for i, nv in enumerate(NIVEIS_ALF):
        cor_fundo = CORES_EXCLUSIVAS.get(nv, "#eee")
        cor_txt = get_text_color(nv)
        cols_leg[i].markdown(f"""
            <div style="background-color:{cor_fundo}; color:{cor_txt}; padding:8px 2px; border-radius:10px; 
            text-align:center; font-size:10px; font-weight:bold; min-height:50px; display:flex; align-items:center; justify-content:center; line-height:1.1; border: 1px solid rgba(0,0,0,0.05);">
                {nv.split(". ")[1]}
            </div>
        """, unsafe_allow_html=True)

def render_vasilha_mare(nivel_num, titulo):
    config = {
        1: {"pct": 85, "txt": "Maré Baixa", "seta": ""},
        2: {"pct": 70, "txt": "Maré Vazante", "seta": "↓"},
        3: {"pct": 45, "txt": "Maré Enchente", "seta": "↑"},
        4: {"pct": 15, "txt": "Maré Cheia", "seta": "↑"}
    }
    try:
        n = int(float(nivel_num))
        n = max(1, min(4, n))
    except: n = 1
    c = config[n]
    return f'''
    <div style="text-align: center; margin-bottom: 20px; border: 1px solid #eee; padding: 10px; border-radius: 10px; background: #fff;">
        <div style="font-size: 11px; font-weight: bold; color: #333; min-height: 35px; display: flex; align-items: center; justify-content: center; line-height: 1.2;">{titulo}</div>
        <div style="width: 70px; height: 45px; margin: 5px auto; background: linear-gradient(to bottom, #f0f0f0 {c['pct']}%, #5DADE2 {c['pct']}%);
                    clip-path: path('M 0 10 Q 17.5 0 35 10 T 70 10 L 70 40 Q 70 45 65 45 L 5 45 Q 0 45 0 40 Z'); border: 1px solid #ddd; position: relative;">
            <span style="position: absolute; right: 2px; top: 5px; font-size: 12px; font-weight: bold; color: #2E86C1;">{c['seta']}</span>
        </div>
        <div style="font-size: 9px; color: #5DADE2; font-weight: bold; text-transform: uppercase; margin-top: 5px;">{c['txt']}</div>
    </div>'''

def render_grafico_alfabetizacao_individual(df_aluno):
    if df_aluno.empty: 
        st.info("Sem dados de evolução.")
        return
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_aluno["Avaliacao"].str.replace("Avaliação Final", "3ª Aval") + "/" + df_aluno["Ano"].astype(str),
        y=[MAPA_NIVEIS.get(n, 0) for n in df_aluno["Nivel"]],
        fill='tozeroy', mode='lines+markers',
        line=dict(color="#6741d9", width=3),
        marker=dict(size=10, color="#6741d9")
    ))
    fig.update_layout(height=280, margin=dict(l=0, r=10, t=20, b=0),
        yaxis=dict(range=[0.5, 7.5], tickmode='array', tickvals=list(range(1, 8)), ticktext=[n.split(". ")[1] for n in NIVEIS_ALF]),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=10))
    st.plotly_chart(fig, use_container_width=True)

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
        df = conn.read(worksheet=nome_da_aba_selecionada).fillna("")
        df.columns = [str(c).strip().upper() for c in df.columns]
        if "PADRINHO" in df.columns: df = df.rename(columns={"PADRINHO": "PADRINHO/MADRINHA"})
        return df.fillna("")
    except: return pd.DataFrame()

def render_filtros(df_geral, key_suffix):
    f1, f2 = st.columns(2)
    tn = f1.selectbox("Filtrar Turno", ["Todos", "A", "B"], key=f"tn_{key_suffix}")
    
    # Se a coluna não existir, ele não trava o app
    cols = [c.upper() for c in df_geral.columns]
    if "COMUNIDADE" in cols:
        comu_list = ["Todas"] + sorted([c for c in df_geral["COMUNIDADE"].unique() if str(c).strip()])
    else:
        comu_list = ["Todas"]
        
    cm = f2.selectbox("Filtrar Comunidade", comu_list, key=f"cm_{key_suffix}")
    return tn, cm

def aplicar_filtros(df_alvo, df_geral, tn, cm):
    # Fazemos uma cópia para não alterar o dataframe original (Boa prática de R&D)
    df_f = df_alvo.copy()
    
    # Padroniza as colunas do df_alvo também, caso ele venha de outra aba
    df_f.columns = [str(c).strip().upper() for c in df_f.columns]
    
    # 1. Filtro de Turno
    if tn != "Todos":
        # Filtra no df_geral quem é do turno selecionado e pega os nomes dos alunos
        alunos_no_turno = df_geral[df_geral["TURNO"].astype(str).str.contains(tn, na=False)]["ALUNO"].unique()
        # Filtra o dataframe alvo apenas com esses alunos
        df_f = df_f[df_f["ALUNO"].isin(alunos_no_turno)]
    
    # 2. Filtro de Comunidade
    if cm != "Todas":
        # Verifica se a coluna COMUNIDADE existe no df_f antes de filtrar
        if "COMUNIDADE" in df_f.columns:
            df_f = df_f[df_f["COMUNIDADE"] == cm]
        else:
            # Se não existir no alvo, buscamos os alunos daquela comunidade no geral
            alunos_na_comu = df_geral[df_geral["COMUNIDADE"] == cm]["ALUNO"].unique()
            df_f = df_f[df_f["ALUNO"].isin(alunos_na_comu)]
            
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
# --- FUNÇÕES DE SUPORTE VISUAL (ADICIONAR NO TOPO) ---

def render_vasilha_mare(nivel_num, titulo):
    # Mapeamento conforme sua regra: 1: Baixa, 2: Vazante, 3: Enchente, 4: Cheia
    config = {
        1: {"pct": 85, "txt": "Maré Baixa", "seta": ""},
        2: {"pct": 70, "txt": "Maré Vazante", "seta": "↓"},
        3: {"pct": 45, "txt": "Maré Enchente", "seta": "↑"},
        4: {"pct": 15, "txt": "Maré Cheia", "seta": "↑"}
    }
    # Garante que o nível seja um int e esteja entre 1 e 4
    try:
        n = int(float(nivel_num))
        if n < 1: n = 1
        if n > 4: n = 4
    except:
        n = 1
        
    c = config[n]
    
    return f'''
    <div style="text-align: center; margin-bottom: 20px; border: 1px solid #eee; padding: 10px; border-radius: 10px; background: #fff;">
        <div style="font-size: 11px; font-weight: bold; color: #333; min-height: 35px; display: flex; align-items: center; justify-content: center; line-height: 1.2;">{titulo}</div>
        <div style="width: 70px; height: 45px; margin: 5px auto; background: linear-gradient(to bottom, #f0f0f0 {c['pct']}%, #5DADE2 {c['pct']}%);
                    clip-path: path('M 0 10 Q 17.5 0 35 10 T 70 10 L 70 40 Q 70 45 65 45 L 5 45 Q 0 45 0 40 Z'); border: 1px solid #ddd; position: relative;">
            <span style="position: absolute; right: 2px; top: 5px; font-size: 12px; font-weight: bold; color: #2E86C1;">{c['seta']}</span>
        </div>
        <div style="font-size: 9px; color: #5DADE2; font-weight: bold; text-transform: uppercase; margin-top: 5px;">{c['txt']}</div>
    </div>
    '''

def render_grafico_alfabetizacao_individual(df_aluno):
    if df_aluno.empty: 
        st.warning("Sem dados históricos de alfabetização.")
        return
    
    # Ordenar por data ou ano/avaliação se necessário
    df_plot = df_aluno.copy()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_plot["Avaliacao"].str.replace("Avaliação Final", "3ª Aval") + "/" + df_plot["Ano"].astype(str),
        y=[MAPA_NIVEIS.get(n, 0) for n in df_plot["Nivel"]],
        fill='tozeroy', 
        mode='lines+markers',
        line=dict(color="#6741d9", width=3),
        marker=dict(size=10, color="#6741d9", symbol="circle")
    ))
    
    fig.update_layout(
        height=280, 
        margin=dict(l=0, r=10, t=20, b=0),
        yaxis=dict(
            range=[0.5, 7.5], 
            tickmode='array', 
            tickvals=list(range(1, 8)), 
            ticktext=[n.split(". ")[1] for n in NIVEIS_ALF],
            gridcolor="#eee"
        ),
        xaxis=dict(gridcolor="#eee"),
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=10)
    )
    st.plotly_chart(fig, use_container_width=True)
    
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
    st.markdown(f"### 📋 Quadro de Alunos Matriculados")
    render_botoes_salas("btn_mat", "sel_mat")
    st.info("✍️📖 = Aluno já matriculado no Turno Estendido")

    # --- CONEXÃO COM GOOGLE SHEETS (R&D) ---
    # Lemos a aba GERAL para os filtros e a aba da SALA selecionada para a lista
    df_g = conn.read(worksheet="GERAL").fillna("")
    df_g.columns = [str(c).strip().upper() for c in df_g.columns]
    
    # Lemos a aba específica da sala (ex: "SALA ROSA")
    df_s = conn.read(worksheet=st.session_state.sel_mat).fillna("")
    df_s.columns = [str(c).strip().upper() for c in df_s.columns]

    # Renderiza filtros baseados na aba GERAL
    tn, cm = render_filtros(df_g, "mat")
    
    # Filtragem dos dados da sala
    df_f = df_s.copy()
    if tn != "Todos":
        df_f = df_f[df_f["TURMA"] == tn] # No seu arquivo da sala, a coluna é TURMA (A ou B)
    if cm != "Todas":
        df_f = df_f[df_f["COMUNIDADE"] == cm]

    cor_h = TURMAS_CONFIG[st.session_state.sel_mat]["cor"]
    st.markdown(f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr><th style="width: 10%;">Sel.</th><th style="width: 45%;">ALUNO</th><th style="width: 15%;">IDADE</th><th style="width: 30%;">COMUNIDADE</th></tr></thead></table>', unsafe_allow_html=True)
    
    selecionados = []
    
    # Iteração sobre os dados filtrados
    for i, r in df_f.iterrows():
        c0, c1, c2, c3 = st.columns([0.5, 3, 1, 2])
        # Usamos o nome da coluna exatamente como no seu CSV: ALUNO
        n_l = str(r['ALUNO']).replace("**", "").strip()
        
        if n_l in st.session_state.get("alunos_te_dict", {}): 
            c0.markdown("✍️📖")
        else:
            # Usamos uma chave única combinando sala e nome para evitar conflitos
            if c0.checkbox("", key=f"chk_{st.session_state.sel_mat}_{i}"): 
                selecionados.append(n_l)
        
        c1.write(f"**{n_l}**")
        c2.write(f"{r['IDADE']}") # No seu CSV, IDADE já vem como "05 ANOS"
        c3.write(f"{r['COMUNIDADE']}")

    if selecionados:
        st.markdown(f"<style>div.stButton > button[key='btn_bulk_te'] {{ background-color: {cor_h} !important; color: white !important; opacity: 1.0 !important; }}</style>", unsafe_allow_html=True)
        if st.button(f"Matricular {len(selecionados)} aluno(s) no Turno Estendido", key="btn_bulk_te"):
            for al in selecionados: 
                st.session_state["alunos_te_dict"][al] = st.session_state.sel_mat
            st.success(f"{len(selecionados)} alunos adicionados à lista de matrícula!")
            st.rerun()

elif menu == "🤝 Gestão de apadrinhamento":
    st.markdown(f"### 🤝 Gestão de Apadrinhamento")
    render_botoes_salas("btn_pad", "sel_pad")

    # --- CONEXÃO COM GOOGLE SHEETS ---
    # 1. Busca a base geral para os filtros (Turno/Comunidade)
    df_g = conn.read(worksheet="GERAL").fillna("")
    df_g.columns = [str(c).strip().upper() for c in df_g.columns]

    # 2. Busca a aba específica da sala selecionada (ex: "SALA ROSA")
    # O st.session_state.sel_pad contém o nome da sala vindo do botão
    df_s = conn.read(worksheet=st.session_state.sel_pad).fillna("")
    df_s.columns = [str(c).strip().upper() for c in df_s.columns]

    if not df_s.empty:
        # Renderiza os filtros usando a base geral
        tn, cm = render_filtros(df_g, "pad")
        
        # Filtra os dados da sala selecionada
        # Note: No arquivo da sala a coluna de turno chama-se "TURMA"
        df_f = df_s.copy()
        if tn != "Todos":
            df_f = df_f[df_f["TURMA"] == tn]
        if cm != "Todas":
            df_f = df_f[df_f["COMUNIDADE"] == cm]

        cor_h = TURMAS_CONFIG[st.session_state.sel_pad]["cor"]
        
        # Colunas conforme a estrutura do seu arquivo CSV
        v_cols = ["ALUNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
        
        # Montagem da Tabela HTML
        html = f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
        
        for _, r in df_f.iterrows():
            # Limpeza do nome do aluno
            n_l = str(r.get("ALUNO", "")).replace("**", "").strip()
            idade = str(r.get("IDADE", ""))
            comunidade = str(r.get("COMUNIDADE", ""))
            padrinho = str(r.get("PADRINHO/MADRINHA", ""))
            
            # Se o padrinho estiver vazio ou for "nan", mostramos vazio para ficar limpo
            padrinho_texto = padrinho if padrinho.lower() not in ["nan", "", "none", "0"] else ""
            
            html += f'<tr><td>{n_l}</td><td>{idade}</td><td>{comunidade}</td><td>{padrinho_texto}</td></tr>'
        
        st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
        
        # Rodapé com contagem (estilo R&D)
        st.caption(f"Total exibido: {len(df_f)} alunos na {st.session_state.sel_pad}")
        
    else: 
        st.warning(f"A aba '{st.session_state.sel_pad}' parece estar vazia na Google Sheet.")

# --- ABA: AVALIAÇÃO TÁBUA DA MARÉ ---
elif menu == "📊 Avaliação da Tábua da Maré":
    st.markdown(f"### 📊 Lançar Avaliação (Google Sheets)")

    try:
        # Chamada simplificada usando a chave do secrets
        df_av = conn.read(worksheet="TABUA_MARE").fillna("")
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha: {e}")
        st.stop()

    # Renderiza os botões das salas
    render_botoes_salas("btn_aval", "sel_aval")
    
    # Busca a lista de alunos da sala selecionada
    alunos_na_sala = [n for n, s in st.session_state["alunos_te_dict"].items() if s == st.session_state.sel_aval]
    
    if alunos_na_sala:
        al = st.selectbox("Selecione o Aluno", sorted(alunos_na_sala))
        
        # Busca dados anteriores para facilitar o preenchimento (UX de Qualidade)
        dados_anteriores = df_av[df_av["Aluno"] == al].iloc[-1] if not df_av[df_av["Aluno"] == al].empty else None
        
        st.markdown("#### ⭐ 10 motivos para avaliar!")
        
        with st.form("f_av_nuvem"):
            tr = st.selectbox("Período", ["1º Semestre", "2º Semestre"])
            
            cE, cD = st.columns(2)
            n_l = {}
            
            # Itera sobre as 10 categorias criando os seletores
            for i, cat in enumerate(CATEGORIAS):
                # Define o index padrão: se já existir nota na planilha, tenta selecionar ela
                val_anterior = dados_anteriores[cat] if dados_anteriores is not None and cat in dados_anteriores else "Maré Enchente"
                opcoes = list(MARE_OPCOES.keys())
                
                try:
                    idx_default = opcoes.index(val_anterior)
                except ValueError:
                    idx_default = 2 # Maré Enchente (Padrão)
                
                n_l[cat] = (cE if i < 5 else cD).selectbox(
                    cat, 
                    opcoes, 
                    index=idx_default,
                    key=f"mare_s_{i}"
                )
            
            obs_anterior = dados_anteriores["Observações pedagógicas"] if dados_anteriores is not None else ""
            obs = st.text_area("Observações pedagógicas:", value=obs_anterior)
            
            if st.form_submit_button("🚀 Enviar para Tábua da Maré"):
                # Chamada da função de escrita para a nuvem
                sucesso = registrar_tabua_mare(
                    aluno=al,
                    sala=st.session_state.sel_aval,
                    semestre=tr,
                    notas_dict=n_l,
                    obs=obs
                )
                
                if sucesso:
                    st.balloons()
                    st.success(f"Avaliação de {al} sincronizada com sucesso!")
                    st.cache_data.clear() # Limpa o cache para atualizar gráficos imediatamente
                    st.rerun()
    else:
        st.warning("Nenhum aluno encontrado para esta sala.")
# --- ABA: TURNO ESTENDIDO ---
elif menu == "📖 Turno Estendido":
    st.markdown(f"<h3 style='color:{C_ROXO}'>📖 Turno Estendido</h3>", unsafe_allow_html=True)

    try:
        # Chamada simplificada usando a chave do secrets
        df_h = conn.read(worksheet="TURNO_ESTENDIDO").fillna("")
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha: {e}")
        st.stop()

    # --- LÓGICA DE ANOS DINÂMICOS ---
    if "Ano" not in df_h.columns:
        df_h["Ano"] = 2026

    # Converte para numérico para evitar erros de comparação
    df_h["Ano"] = pd.to_numeric(df_h["Ano"], errors='coerce').fillna(2026).astype(int)
    anos_na_planilha = sorted(df_h["Ano"].unique().tolist())
    
    if "lista_anos_te" not in st.session_state:
        st.session_state.lista_anos_te = anos_na_planilha if anos_na_planilha else [2025, 2026]
    
    if "ano_registro_te" not in st.session_state: 
        st.session_state.ano_registro_te = st.session_state.lista_anos_te[-1]

    st.write("**Ano da Avaliação:**")
    cols_anos_all = st.columns([0.15] * len(st.session_state.lista_anos_te) + [0.1, 0.6])
    
    cores_interface_anos = {2025: "#2E86C1", 2026: "#28B463", 2027: "#E67E22", 2028: "#8E44AD"}

    for i, ano in enumerate(st.session_state.lista_anos_te):
        is_active = st.session_state.ano_registro_te == ano
        cor_base = cores_interface_anos.get(ano, "#34495E")
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

    # --- SELEÇÃO DE ALUNO ---
    salas_te = sorted(list(set(st.session_state["alunos_te_dict"].values())))
    if salas_te:
        if st.session_state.sel_te not in salas_te: st.session_state.sel_te = salas_te[0]
        render_botoes_salas("btn_te", "sel_te", salas_permitidas=salas_te)
        
        al_te = [n for n, s in st.session_state["alunos_te_dict"].items() if s == st.session_state.sel_te]
        al = st.selectbox("Aluno:", sorted(al_te))
        
        # Puxa o histórico do aluno
        dados_aluno = df_h[df_h["Aluno"] == al]
        diag = dados_aluno.iloc[-1] if not dados_aluno.empty else None
        
        # --- TRILHA VISUAL ---
        st.markdown("""<style>
            .trilha-container { display: flex; align-items: center; justify-content: center; gap: 0px; margin: 10px 0; padding: 5px 0; overflow-x: auto; }
            .caixa-trilha-ajustada { padding: 6px 4px; border-radius: 10px; text-align: center; font-size: 11px; font-weight: bold; min-width: 110px; height: 55px; display: flex; align-items: center; justify-content: center; line-height: 1.1; box-shadow: 1px 1px 3px rgba(0,0,0,0.05); flex-shrink: 0; }
            .seta-trilha { font-weight: bold; color: #D5DBDB; font-size: 16px; margin: 0 -5px; z-index: 1; }
        </style>""", unsafe_allow_html=True)

        ht = '<div class="trilha-container">'
        for i, n_t in enumerate(NIVEIS_ALF):
            nivel_atual_planilha = diag["Diagnóstico"] if diag is not None else ""
            is_current = (nivel_atual_planilha == n_t)
            
            cor_bg = CORES_EXCLUSIVAS.get(n_t, "#eee")
            cor_txt = get_text_color(n_t)
            borda = "3px solid #2C3E50" if is_current else "1px solid rgba(0,0,0,0.1)"
            opacidade = "1.0" if is_current else "0.65"
            
            ht += f'<div class="caixa-trilha-ajustada" style="background-color:{cor_bg}; color:{cor_txt}; border:{borda}; opacity:{opacidade};">{n_t.split(". ")[1]}</div>'
            if i < len(NIVEIS_ALF)-1: ht += '<div class="seta-trilha">→</div>'
        st.markdown(ht + '</div>', unsafe_allow_html=True)

        # --- FORMULÁRIO DE SALVAMENTO ---
        try:
            idx_inicial = NIVEIS_ALF.index(diag["Diagnóstico"]) if (diag is not None and diag["Diagnóstico"] in NIVEIS_ALF) else 0
        except:
            idx_inicial = 0
            
        nV = st.selectbox("Novo Nível de Diagnóstico:", NIVEIS_ALF, index=idx_inicial)

        with st.form("f_alf_nuvem"):
            tipo = st.selectbox("Etapa da Avaliação:", ["1ª Avaliação", "2ª Avaliação", "Avaliação Final"])
            evidencias_atuais = EVIDENCIAS_POR_NIVEL.get(nV, [])
            
            st.write(f"**Evidências observadas para {nV}:**")
            e_cols = st.columns(3)
            s_ev = []
            for i, ev in enumerate(evidencias_atuais):
                if e_cols[i % 3].checkbox(ev, key=f"chk_{nV}_{i}"):
                    s_ev.append(ev)
            
            obs = st.text_area("Observações Adicionais:")
            
            if st.form_submit_button("🚀 Salvar na Planilha Google"):
                tipo_map = {
                    "1ª Avaliação": "1 Avaliação",
                    "2ª Avaliação": "2 Avaliação",
                    "Avaliação Final": "3 Avaliação"
                }
                
                sucesso = registrar_turno_estendido(
                    aluno=al,
                    sala=st.session_state.sel_te,
                    avaliacao_tipo=tipo_map.get(tipo),
                    nivel=nV,
                    evidencias_list=s_ev,
                    obs=obs,
                    ano=int(st.session_state.ano_registro_te)
                )
                
                if sucesso:
                    st.success("Dados sincronizados com sucesso!")
                    st.cache_data.clear() 
                    st.rerun()
# --- ABA: DADOS - TURNO ESTENDIDO (ATUALIZADO COM CORES E LEGENDA) ---
elif menu == "📊 Dados - Turno Estendido":
    st.markdown("""
        <style>
            thead tr th, th {
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
                font-weight: bold !important;
                background-color: #f8f9fa !important;
                text-align: center !important;
            }
            .mare-box {
                display: flex; flex-direction: column; align-items: center; 
                justify-content: center; gap: 2px; padding: 2px;
            }
            .mare-mini-tabela {
                width: 35px; height: 20px; border: 1px solid #999; border-radius: 3px;
            }
            .mare-texto-tabela {
                font-size: 10px; color: #555; font-weight: bold; line-height: 1;
                text-transform: lowercase;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### 📋 Panorama de Avaliações")
    
    df_h = df_alf.copy()

    # Garante que a coluna ANO existe e sincroniza com a nuvem
    if "ANO" not in df_h.columns:
        df_h["ANO"] = 2025
        df_save = df_h.copy()
        df_save.columns = [str(c).upper() for c in df_save.columns]
        df_save = df_save.astype(str)
        conn.update(worksheet="TURNO_ESTENDIDO", data=df_save)

    # 1. SELEÇÃO DE ANO
    st.write("Selecione o Ano:")
    if "ano_ativo_te" not in st.session_state: 
        st.session_state.ano_ativo_te = 2025
    
    col_anos = st.columns([0.15, 0.15, 0.7]) 
    anos = [2025, 2026]
    cores_ano = {2025: "#2E86C1", 2026: "#28B463"} 

    for i, ano in enumerate(anos):
        is_active = st.session_state.ano_ativo_te == ano
        cor_btn = cores_ano[ano] if is_active else "#D5DBDB"
        txt_cor = "white" if is_active else "#566573"
        
        if col_anos[i].button(f"📅 {ano}", key=f"btn_ano_{ano}", use_container_width=True):
            st.session_state.ano_ativo_te = ano
            st.rerun()
        
        st.markdown(f"<style>div[data-testid='stHorizontalBlock'] div:nth-child({i+1}) button {{ background-color: {cor_btn} !important; color: {txt_cor} !important; border: {'2px solid black' if is_active else '1px solid #ccc'} !important; }}</style>", unsafe_allow_html=True)

    ano_sel = st.session_state.ano_ativo_te
    st.markdown(f"**Exibindo dados de: {ano_sel}**")

    # --- 1. LEGENDA DE NÍVEIS ---
    st.markdown("##### 📝 Legenda de Níveis")
    cols_leg = st.columns(len(NIVEIS_ALF))
    for i, nv in enumerate(NIVEIS_ALF):
        cor_fundo = CORES_EXCLUSIVAS.get(nv, "#eee")
        cor_txt = get_text_color(nv) 
        
        cols_leg[i].markdown(f"""
            <div style="background-color:{cor_fundo}; color:{cor_txt}; padding:8px 2px; border-radius:10px; 
            text-align:center; font-size:10px; font-weight:bold; min-height:50px; display:flex; align-items:center; justify-content:center; line-height:1.1; border: 1px solid rgba(0,0,0,0.05);">
                {nv.split(". ")[1]}
            </div>
        """, unsafe_allow_html=True)

    # --- 2. FUNÇÃO AUXILIAR MARÉ ---
    def get_status_mare_html(nv_atual, hist):
        pct, txt = 85, "maré baixa"
        if nv_atual == "7. Alfabético Ortográfico": pct, txt = 15, "maré cheia"
        elif len(hist) >= 2:
            n_at, n_ant = MAPA_NIVEIS.get(nv_atual, 0), MAPA_NIVEIS.get(hist[-2], 0)
            if n_at > n_ant: pct, txt = 45, "maré enchente"
            elif n_at < n_ant: pct, txt = 70, "maré vazante"
        
        return f'''
        <div class="mare-box">
            <div class="mare-mini-tabela" style="background: linear-gradient(to bottom, #f0f0f0 {pct}%, #5DADE2 {pct}%); clip-path: path('M 0 4 Q 10 0 20 4 T 40 4 L 40 20 L 0 20 Z');"></div>
            <span class="mare-texto-tabela">{txt}</span>
        </div>'''

    cols_header = ["Nome do Aluno", "1ª Sondagem", "2ª Sondagem", "3ª Sondagem", "STATUS MARÉ"]
    if ano_sel == 2026: cols_header.insert(1, "Diagnóstico Atual")

    html_tab = f"""<table style="width: 100%; border-collapse: collapse; margin-top: 15px; background: white; border: 1px solid #eee; color: #2C3E50;">
        <thead><tr style="background-color: #F8F9FA;">{"".join([f'<th style="padding:12px; border:1px solid #eee; font-size:12px;">{c}</th>' for c in cols_header])}</tr></thead>
        <tbody>"""
    
    alunos_te = sorted(st.session_state.get("alunos_te_dict", {}).keys())
    
    for al in alunos_te:
        dados_ano = df_h[(df_h["ALUNO"] == al) & (df_h["ANO"] == ano_sel)]
        html_tab += f'<tr><td style="font-weight:bold; padding:10px; border:1px solid #eee; font-size:12px;">{al}</td>'
        
        if ano_sel == 2026:
            d_ant = df_h[(df_h["ALUNO"] == al) & (df_h["ANO"] == 2025) & (df_h["AVALIACAO"] == "Avaliação Final")]
            if not d_ant.empty:
                nv = d_ant["NIVEL"].iloc[0]
                html_tab += f'<td style="background:{CORES_EXCLUSIVAS.get(nv)}; color:{get_text_color(nv)}; text-align:center; font-weight:bold; font-size:10px; border:1px solid #eee; padding:8px;">{nv.split(". ")[1]}</td>'
            else: 
                html_tab += '<td style="text-align:center; border:1px solid #eee; color:#ccc;">-</td>'

        for etapa in ["1ª Avaliação", "2ª Avaliação", "Avaliação Final"]:
            r = dados_ano[dados_ano["AVALIACAO"] == etapa]
            if not r.empty:
                nv = r["NIVEL"].iloc[0]
                html_tab += f'<td style="background:{CORES_EXCLUSIVAS.get(nv)}; color:{get_text_color(nv)}; text-align:center; font-weight:bold; border:1px solid #eee; font-size:11px; padding:8px;">{nv.split(". ")[1]}</td>'
            else: 
                html_tab += '<td style="border:1px solid #eee;"></td>'

        status_html = '<td style="border:1px solid #eee; text-align:center;">-</td>'
        if not dados_ano.empty:
            status_html = f'<td style="border:1px solid #eee; background:#FDFDFD;">{get_status_mare_html(dados_ano["NIVEL"].iloc[-1], dados_ano["NIVEL"].tolist())}</td>'
        html_tab += status_html + '</tr>'
    
    st.markdown(html_tab + "</tbody></table>", unsafe_allow_html=True)
    st.markdown("---")
    
elif menu == "📈 Indicadores pedagógicos":

    st.markdown(f"### 📈 Indicadores")
    render_botoes_salas("btn_ind", "sel_ind")
    df_h = df_alf.copy()
    if not df_h.empty:
        df_ult = df_h.sort_values("Avaliacao").groupby("Aluno").last().reset_index()
        df_ult["Aluno"] = df_ult["Aluno"].str.replace("**", "", regex=False)
        st.dataframe(df_ult, use_container_width=True)
    else: st.info("Sem dados.")

elif menu == "🌊 Canal do Apadrinhamento":
    st.markdown(f"### 🤝 Canal do Apadrinhamento")
    
    # --- 1. UNIÃO DAS TURMAS (CONEXÃO GOOGLE SHEETS) ---
    lista_salas = []
    # Usando TURMAS_CONFIG para mapear as abas
    for nome_aba in TURMAS_CONFIG.keys():
        try:
            df_t = conn.read(worksheet=nome_aba).fillna("")
            df_t.columns = [str(c).strip().upper() for c in df_t.columns]
            df_t["SALA_NOME"] = nome_aba  # Metadado para saber de qual aba veio
            lista_salas.append(df_t)
        except:
            continue
    
    if not lista_salas:
        st.error("⚠️ Erro ao carregar salas. Verifique a conexão.")
        st.stop()

    df_total = pd.concat(lista_salas, ignore_index=True)
    
    # --- 2. IDENTIFICAÇÃO E SELEÇÃO (ADMIN vs PADRINHO) ---
    col_padrinho = "PADRINHO/MADRINHA"
    
    # Lista de padrinhos únicos para o Admin
    padrinhos_lista = sorted([
        str(p).strip() for p in df_total[col_padrinho].unique() 
        if str(p).strip() not in ["", "0", "nan", "None", "NaN"]
    ]) if col_padrinho in df_total.columns else []

    # Lógica de Perfil
    if st.session_state.get("perfil") == "padrinho":
        p_sel = st.session_state.get("nome_usuario", "")
    else:
        p_sel = st.selectbox("👤 Selecionar Padrinho (Visualização Admin):", ["Selecione..."] + padrinhos_lista)
    
    if p_sel and p_sel not in ["Selecione...", "Nenhum Padrinho Encontrado"]:
        # Filtra afilhados
        afils_df = df_total[df_total[col_padrinho].astype(str).str.upper() == p_sel.upper()]
        
        if not afils_df.empty:
            lista_nomes = sorted([str(n).strip() for n in afils_df["ALUNO"].unique()])
            al_af = st.selectbox("👶 Selecione o afilhado:", lista_nomes)
            
            # Verificação de Turno Estendido
            is_turno = al_af in st.session_state.get("alunos_te_dict", {})
            modo = "🌊 Tábua da Maré (Geral)"

            if is_turno:
                st.markdown(f"""
                <div style="background-color: #f3e5f5; padding: 20px; border-radius: 12px; border-left: 5px solid #6741d9; margin-bottom: 20px; color: black;">
                    <span style="font-size: 18px;">✨ <b>O seu afilhado, {al_af}, participa do nosso Turno Estendido!</b></span><br>
                    <p style="margin-top: 10px; line-height: 1.5; font-size: 14px;">
                        Essa é uma ação do nosso Projeto <b>"Vamos Dar a Meia Volta e Alfabetizar"</b>.
                    </p>
                </div>""", unsafe_allow_html=True)
                modo = st.radio("O que deseja visualizar?", ["🌊 Tábua da Maré (Geral)", "📚 Turno Estendido"], horizontal=True)

            st.markdown("---")

# --- VISUALIZAÇÃO 1: GERAL (TÁBUA DA MARÉ) ---
if modo == "🌊 Tábua da Maré (Geral)":
    # 0. DEFINIÇÕES GLOBAIS
    CATEGORIAS = [
        "Atividades em grupo/proatividade", 
        "Interesse pelo novo", 
        "Compartilhamento de materiais", 
        "Clareza e Desenvoltura", 
        "Respeito às regras"
    ]
    
    # 1. EXTRAÇÃO DE DADOS DA MEMÓRIA (df_total já consolidado acima)
    # Filtramos a linha do aluno selecionado no DataFrame que já contém todas as salas
    aluno_info = df_total[df_total["ALUNO"] == al_af]
    
    if not aluno_info.empty:
        # Pega a primeira ocorrência encontrada
        info = aluno_info.iloc[0]
        
        # SALA_NOME foi criado lá no início do loop (df_temp["SALA_NOME"] = nome_aba)
        aba_origem = info.get("SALA_NOME", "Não identificada")
        turno_aluno = info.get("TURMA", "")
        
        # Monta a string: Sala Azul - Turma A
        sala_oficial = f"{aba_origem.title()} - {turno_aluno}" if turno_aluno else aba_origem.title()
        
        # Demais campos das colunas D e F
        idade = info.get("IDADE", "---")
        comunidade = info.get("COMUNIDADE", "Não informada")
        padrinho_nome = info.get("PADRINHO/MADRINHA", "Sem padrinho/madrinha")
    else:
        # Caso de segurança se o aluno sumir do df_total
        sala_oficial, idade, comunidade, padrinho_nome = "Não encontrada", "---", "Não informada", "Sem registro"

    # Lógica de cor baseada na sala encontrada
    cor_sala_bg = "#ffffff"
    sala_check = sala_oficial.upper()
    if "AZUL" in sala_check: cor_sala_bg = "#E3F2FD"
    elif "ROSA" in sala_check: cor_sala_bg = "#FCE4EC"
    elif "VERDE" in sala_check: cor_sala_bg = "#E8F5E9"
    elif "AMARELA" in sala_check: cor_sala_bg = "#FFFDE7"
    elif "LARANJA" in sala_check: cor_sala_bg = "#FFF3E0"

    # 2. LAYOUT (Ficha + Gráfico)
    st.markdown("<style>.status-mare-final {font-size: 11px !important; font-weight: bold; text-align: center;}</style>", unsafe_allow_html=True)
    col_ficha, col_conteudo = st.columns([1, 2.3])
    
    with col_ficha:
        st.markdown(f"""
            <div style="background-color: {cor_sala_bg}; padding: 18px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.1); color: black;">
                <h4 style="margin: 0 0 12px 0; color: #1A5276; border-bottom: 2px solid rgba(0,0,0,0.1);">📋 Ficha do Aluno</h4>
                <p style="margin: 8px 0; font-size: 13px;"><b>👤 Nome:</b><br>{al_af}</p>
                <p style="margin: 8px 0; font-size: 13px;"><b>🏫 Sala/Turma:</b><br>{sala_oficial}</p>
                <p style="margin: 8px 0; font-size: 13px;"><b>🎂 Idade:</b><br>{idade}</p>
                <p style="margin: 8px 0; font-size: 13px;"><b>🏡 Comunidade:</b><br>{comunidade}</p>
                <p style="margin: 8px 0; font-size: 13px;"><b>🤝 Padrinho/Madrinha:</b><br>{padrinho_nome}</p>
            </div>
        """, unsafe_allow_html=True)

    with col_conteudo:
        # Busca avaliações na aba TABUA_MARE (Variável df_aval deve estar carregada no app)
        df_av = df_aval.copy()
        df_av.columns = [str(c).strip().upper() for c in df_av.columns]
        dados_mare = df_av[df_av["ALUNO"] == al_af]
        
        valores_grafico = []
        if not dados_mare.empty:
            r_m = dados_mare.iloc[-1]
            for cat in CATEGORIAS:
                try:
                    v = r_m.get(cat.upper(), 0)
                    valores_grafico.append(float(v) if v not in ["", None] else 0.0)
                except: valores_grafico.append(0.0)

        if sum(valores_grafico) > 0:
            v_cols = st.columns(5)
            for i, cat in enumerate(CATEGORIAS):
                val = valores_grafico[i]
                status_txt = "Maré Baixa" if val <= 1 else "Maré Cheia" if val >= 3 else "Maré Alta"
                html_v = render_vasilha_mare(val, cat)
                html_v_limpo = html_v.split('<span style="position: absolute;')[0]
                if not html_v_limpo.endswith('</div></div>'): html_v_limpo += '</div></div>'
                with v_cols[i % 5]:
                    st.markdown(f'<div style="text-align: center;">{html_v_limpo}<div class="status-mare-final">{status_txt}</div></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            fig = criar_grafico_mare(CATEGORIAS, valores_grafico)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info(f"Sem novas Avaliações da Tábua da Maré de **{al_af}**")
# --- VISUALIZAÇÃO 2: TURNO ESTENDIDO (ESTILO ATUALIZADO E ENQUADRADO) ---
elif modo == "📚 Turno Estendido":
                df_h = (df_alf.copy()).fillna("")
                dados_al = df_h[df_h["Aluno"] == al_af].sort_values(["Ano", "Avaliacao"])
                dados_al = dados_al.drop_duplicates(subset=['Avaliacao', 'Ano'], keep='last')
                
                if not dados_al.empty:
                    u_nv = dados_al['Nivel'].iloc[-1]
                    
                    c_inf, c_mare = st.columns([1.2, 1])
                    with c_inf:
                        cor_bg_nivel = CORES_EXCLUSIVAS.get(u_nv, "#ddd")
                        cor_txt_nivel = "#2C3E50" 
                        
                        st.markdown(f"""
                        <div style="border:1px solid #ddd; padding:15px; border-radius:12px; background:#f9f9f9; color:black; height:220px; overflow-y: auto;">
                            <h4 style="margin:0;">{al_af}</h4>
                            <p style="margin: 10px 0;"><b>Nível Atual:</b> <span style="background:{cor_bg_nivel}; color:{cor_txt_nivel}; padding:6px 12px; border-radius:20px; font-weight:bold; border: 1px solid rgba(0,0,0,0.1);">{u_nv}</span></p>
                            <p style="font-size: 13px;"><b>Evidências:</b><br>{dados_al.iloc[-1]['Evidencias']}</p>
                        </div>""", unsafe_allow_html=True)
                    
                    with c_mare:
                        vols = [MAPA_NIVEIS.get(n, 0) for n in dados_al['Nivel']]
                        pct_g, s_txt = 85, "Maré Baixa"
                        if u_nv == "7. Alfabético Ortográfico": pct_g, s_txt = 15, "Maré Cheia"
                        elif len(vols) >= 2:
                            if vols[-1] > vols[-2]: pct_g, s_txt = 45, "Maré Enchente"
                            elif vols[-1] < vols[-2]: pct_g, s_txt = 70, "Maré Vazante"
                        
                        cl_vas, cl_leg = st.columns([1, 1])
                        with cl_vas:
                            st.markdown(f"""<div style="width:140px; height:75px; background:linear-gradient(to bottom, #f0f0f0 {pct_g}%, #5DADE2 {pct_g}%); clip-path: path('M 0 20 Q 40 5 80 20 T 160 20 L 160 80 Q 160 100 140 100 L 20 100 Q 0 100 0 80 Z'); border:1px solid #ccc; margin-top:20px;"></div>
                            <center><b style="color:#1A5276; font-size:14px;">{s_txt}</b></center>""", unsafe_allow_html=True)
                        with cl_leg:
                            st.markdown("""<div style="font-size: 11px; color: #555; padding-top: 15px; line-height: 1.4;">
                                <b>Legenda da Maré:</b><br>
                                🔵 <b>Cheia:</b> Nível Ortográfico<br>
                                🟢 <b>Enchente:</b> Evoluiu de nível<br>
                                🟡 <b>Vazante:</b> Oscilação/Retorno<br>
                                ⚪ <b>Baixa:</b> Nível Inicial
                            </div>""", unsafe_allow_html=True)

                    st.markdown("---")
                    st.markdown("##### 🚀 Jornada de Alfabetização")
                    
                    # CSS AJUSTADO PARA ENQUADRAMENTO PERFEITO (MANTENDO TAMANHO E COR)
                    st.markdown("""<style>
                        .trilha-ap-container { 
                            display: flex; align-items: center; justify-content: center; 
                            gap: 4px; margin: 10px 0; padding: 5px 0; overflow-x: auto; 
                        }
                        .caixa-trilha-ap { 
                            padding: 6px 4px; border-radius: 10px; text-align: center; 
                            font-size: 11px; font-weight: bold; min-width: 110px; height: 55px; 
                            display: flex; align-items: center; justify-content: center;
                            line-height: 1.1; flex-shrink: 0; box-shadow: 1px 1px 3px rgba(0,0,0,0.05);
                            box-sizing: border-box;
                        }
                        .seta-ap { 
                            font-weight: bold; color: #D5DBDB; font-size: 16px; 
                            margin: 0 -2px; z-index: 1; 
                            display: flex; align-items: center; justify-content: center;
                        }
                    </style>""", unsafe_allow_html=True)

                    html_t = '<div class="trilha-ap-container">'
                    for i, nv_ref in enumerate(NIVEIS_ALF):
                        is_current = (u_nv == nv_ref)
                        cor_bg = CORES_EXCLUSIVAS.get(nv_ref, "#eee")
                        
                        # Borda reforçada no atual e nítida nos outros
                        borda = "3px solid #2C3E50" if is_current else "1px solid rgba(0,0,0,0.15)"
                        opacidade = "1.0" if is_current else "0.65"
                        
                        html_t += f'<div class="caixa-trilha-ap" style="background-color:{cor_bg}; border:{borda}; opacity:{opacidade}; color:#2C3E50;">{nv_ref.split(". ")[1]}</div>'
                        if i < len(NIVEIS_ALF)-1: 
                            html_t += '<div class="seta-ap">→</div>'
                    st.markdown(html_t + '</div>', unsafe_allow_html=True)

                    st.markdown("##### 📂 Histórico de Avaliações")
                    for _, r in dados_al.iterrows():
                        t_av = r["Avaliacao"].replace("Avaliação Final", "3ª Avaliação")
                        cor_hist = CORES_EXCLUSIVAS.get(r['Nivel'], "#ddd")
                        st.markdown(f"""
                        <div style="display:flex; justify-content:space-between; align-items:center; padding:10px; border-bottom:1px solid #eee; font-size:13px; color: black;">
                            <span>📅 <b>{t_av}/{r['Ano']}</b></span>
                            <span style="background:{cor_hist}; padding:4px 10px; border-radius:12px; font-weight:bold; border:1px solid rgba(0,0,0,0.1); color:#2C3E50;">
                                {r['Nivel']}
                            </span>
                        </div>""", unsafe_allow_html=True)
elif menu == "🌊 Tábua da Maré":
    st.markdown(f"### 🌊 Tábua da Maré")
    
    # 1. Definições Locais (Garante que o código saiba o que comparar)
    CATEGORIAS = [
        "Atividades em grupo/proatividade", 
        "Interesse pelo novo", 
        "Compartilhamento de materiais", 
        "Clareza e Desenvoltura", 
        "Respeito às regras"
    ]
    
    # Renderiza os botões das salas (Azul, Verde, etc.)
    render_botoes_salas("btn_int", "sel_int")
    
    # 2. Preparação dos Dados
    df_av = df_aval.copy()
    # Padroniza para MAIÚSCULO para evitar erros de digitação na planilha
    df_av.columns = [str(c).strip().upper() for c in df_av.columns]
    
    # Lê a aba da sala selecionada no botão
    df_s = safe_read(st.session_state.sel_int)
    
    if not df_s.empty:
        df_s.columns = [str(c).strip().upper() for c in df_s.columns]
        # Lista de alunos da sala selecionada
        alunos_sala = [str(n).replace("**", "").strip() for n in df_s["ALUNO"].unique()]
        
        # Filtra as avaliações da Tábua da Maré apenas para esses alunos
        df_f = df_av[df_av["ALUNO"].isin(alunos_sala)]
        
        if not df_f.empty:
            # Itera sobre cada aluno encontrado nas avaliações
            for al in sorted(df_f["ALUNO"].unique()):
                with st.expander(f"📊 {al}"):
                    # Filtra todas as avaliações históricas desse aluno específico
                    dados_aluno = df_f[df_f["ALUNO"] == al]
                    
                    for _, r in dados_aluno.iterrows():
                        # Identifica o período (usa 'PERIODO' ou 'DATA', o que existir)
                        periodo = r.get("PERIODO", "Avaliação")
                        st.write(f"**{periodo}**")
                        
                        # Coleta as notas das 5 categorias
                        valores = []
                        for cat in CATEGORIAS:
                            try:
                                v = r.get(cat.upper(), 0)
                                valores.append(float(v) if v not in ["", None] else 0.0)
                            except:
                                valores.append(0.0)
                        
                        # Gera o gráfico de radar para cada período avaliado
                        fig = criar_grafico_mare(CATEGORIAS, valores)
                        st.plotly_chart(fig, use_container_width=True, key=f"g_tabua_{al}_{periodo}")
        else:
            st.info("Nenhuma avaliação encontrada para os alunos desta sala.")
    else:
        st.error("Não foi possível carregar a lista de alunos desta sala.")
