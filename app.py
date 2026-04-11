import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import gspread
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
def get_gspread_client(connection):
    """Tenta encontrar o cliente gspread dentro da conexão GSheets do Streamlit"""
    if hasattr(connection, "_instance"):
        instance = connection._instance
        # Tenta .client (comum no st-gsheets) ou retorna a própria instância
        if hasattr(instance, "client"):
            return instance.client
        return instance
    return connection

nome_planilha = "APP_IMLA"
sheet_id = nome_planilha

# 1. CONFIGURAÇÃO E ESTILO (Sempre o primeiro comando Streamlit)
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")
# --- 1. ESTABELECER CONEXÃO (OBRIGATÓRIO SER AQUI) ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- VARIÁVEIS GLOBAIS IMPORTANTES ---
CATEGORIAS = [
    "Atividades em grupo/Proatividade", "Interesse pelo novo", "Compartilhamento de Materiais",
    "Clareza e desenvoltura", "Respeito às regras", "Vocabulário adequado",
    "Leitura e Escrita", "Compreensão de comandos", "Superação de desafios", "Assiduidade"
]

MARE_LABELS = {
    1: "Maré Baixa", 2: "Maré Vazante", 
    3: "Maré Enchente", 4: "Maré Alta", 5: "Maré Cheia"
}

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


def safe_read(worksheet_name):
    try:
        # Simplificando a leitura
        df = conn.read(worksheet=worksheet_name).fillna("")
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except: 
        return pd.DataFrame()

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
menu_options = ["📝 Controle de Matrícula e Apadrinhamento", "📊 Dados - Turno Estendido", "📊 Avaliação da Tábua da Maré", "📖 Turno Estendido", "📈 Indicadores pedagógicos", "🌊 Canal do Apadrinhamento", "🌊 Tábua da Maré"]
if st.session_state.perfil != "admin": menu_options = ["🌊 Canal do Apadrinhamento"]
menu = st.sidebar.radio("Navegação", menu_options)

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- ABAS ---
if menu == "📝 Controle de Matrícula e Apadrinhamento":
    st.markdown("### 📝 Controle de Matrícula e Apadrinhamento")
    st.markdown("*Esse é o nosso canal de controle e registro dos alunos matriculados e do Programa de Apadrinhamento!*")
    
    # Configuração de Cores (Identidade Visual)
    cor_rosa, cor_amarela, cor_verde, cor_azul, cor_lavanda = "#F783AC", "#FFE066", "#A9E34B", "#99E9F2", "#D0BFFF"

    # --- CSS PARA INVERSÃO DE CORES ---
    st.markdown(f"""
        <style>
        div[data-testid="stPopover"] > button {{
            background-color: white !important;
            background-image: none !important;
            border-radius: 8px;
            transition: 0.3s;
            height: 3.2rem;
            box-shadow: none !important;
        }}
        div[key="mat_popover"] > button {{ color: {cor_rosa} !important; border: 2px solid {cor_rosa} !important; }}
        div[key="pad_popover"] > button {{ color: {cor_amarela} !important; border: 2px solid {cor_amarela} !important; }}
        div[key="est_popover"] > button {{ color: {cor_verde} !important; border: 2px solid {cor_verde} !important; }}
        div[key="del_popover"] > button {{ color: {cor_azul} !important; border: 2px solid {cor_azul} !important; }}

        div[data-testid="stPopover"] button p {{ font-weight: 800 !important; color: inherit !important; }}

        div[key^="btn_pad"] > button {{ color: white !important; border: none !important; }}
        div[key^="btn_pad"] button div[data-testid="stMarkdownContainer"] p {{
            font-weight: 900 !important;
            color: white !important;
            -webkit-text-stroke: 0.5px white;
        }}

        div[key$="SALA ROSA"] > button {{ background-color: {cor_rosa} !important; }}
        div[key$="SALA AMARELA"] > button {{ background-color: {cor_amarela} !important; }}
        div[key$="SALA VERDE"] > button {{ background-color: {cor_verde} !important; }}
        div[key$="SALA AZUL"] > button {{ background-color: {cor_azul} !important; }}
        div[key$="CIRAND. MUNDO"] > button {{ background-color: {cor_lavanda} !important; }}
        </style>
    """, unsafe_allow_html=True)

    # --- BLOCO DE GESTÃO ---
    gestao_col1, gestao_col2, gestao_col3, gestao_col4 = st.columns([1, 2.2, 1.3, 0.9])

    with gestao_col1:
        with st.popover("➕ Matrícula", key="mat_popover", use_container_width=True):
            st.markdown("##### 📝 Nova Matrícula")
            n_nome = st.text_input("Nome do Aluno")
            n_nasc = st.date_input("Nascimento", format="DD/MM/YYYY")
            n_sala = st.selectbox("Sala Destino", list(TURMAS_CONFIG.keys()), key="reg_sala")
            n_turno = st.selectbox("Turno", ["A", "B"], key="reg_turno")
            n_comu = st.text_input("Comunidade")
            
            idade_calc = datetime.now().year - n_nasc.year - ((datetime.now().month, datetime.now().day) < (n_nasc.month, n_nasc.day))
            txt_idade = f"{idade_calc} ANOS"
            
            if st.button("Confirmar Matrícula", use_container_width=True):
                nova_linha = [n_nome.upper(), n_turno, txt_idade, n_nasc.strftime("%d/%m/%Y"), n_comu.upper(), ""]
                conn.append_row(worksheet=n_sala, data=nova_linha)
                st.success(f"{n_nome.upper()} matriculado!")
                st.cache_data.clear()
                st.rerun()

    with gestao_col2:
        with st.popover("🤝 Padrinho/Madrinha", key="pad_popover", use_container_width=True):
            st.markdown("##### 🤝 Novo Apadrinhamento")
            s_busca = st.selectbox("Selecione a Sala:", list(TURMAS_CONFIG.keys()), key="pad_sala")
            df_b = conn.read(worksheet=s_busca).fillna("")
            df_b.columns = [str(c).strip().upper() for c in df_b.columns]
            lista_lib = sorted(df_b[df_b["PADRINHO/MADRINHA"].isin(["", "-", "nan", "0"])]["ALUNO"].unique())
            
            nome_p = st.text_input("Nome do Padrinho/Madrinha")
            al_sel = st.selectbox("Escolha o Afilhado:", lista_lib)
            
            if st.button("Confirmar Apadrinhamento", use_container_width=True):
                idx = df_b[df_b["ALUNO"] == al_sel].index[0] + 2
                conn.update_cell(worksheet=s_busca, row=idx, col=7, value=nome_p.upper())
                st.success("Registro concluído!")
                st.cache_data.clear()
                st.rerun()

    with gestao_col3:
        with st.popover("⏳ Turno Estendido", key="est_popover", use_container_width=True):
            st.markdown("##### ⏳ Matrícula Estendida")
            s_est = st.selectbox("Origem dos Alunos:", list(TURMAS_CONFIG.keys()), key="sel_est_sala")
            df_est_leitura = conn.read(worksheet=s_est).fillna("")
            lista_est = sorted(df_est_leitura["ALUNO"].unique())
            selecionados = st.multiselect("Selecione os alunos:", lista_est)
            
            if st.button("Confirmar Matrícula no Turno Estendido"):
            if selecionados:
                try:
                    # 1. Conexão robusta usando gspread puro para garantir a escrita
                    import gspread
                    from google.oauth2.service_account import Credentials
                    
                    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                    creds = Credentials.from_service_account_info(st.secrets["connections"]["gsheets"], scopes=scope)
                    gc = gspread.authorize(creds)
                    
                    # 2. Abre a planilha e a aba correta
                    sh = gc.open(nome_planilha)
                    ws = sh.worksheet("TURNO_ESTENDIDO")
                    
                    ano_atual = datetime.now().strftime("%Y")
                    
                    # 3. Itera sobre os alunos selecionados no multiselect
                    for aluno in selecionados:
                        # Criamos a linha com as 9 colunas da sua planilha:
                        # [ALUNO, SALA, 1 AVAL, 2 AVAL, 3 AVAL, ANO, DIAGNÓSTICO, EVIDÊNCIAS, OBSERVAÇÕES]
                        # Deixamos as colunas de avaliação e pedagógicas vazias ("") para preenchimento posterior
                        nova_linha = [
                            aluno.upper(), # ALUNO
                            s_est,         # SALA
                            "",            # 1 AVALIAÇÃO
                            "",            # 2 AVALIAÇÃO
                            "",            # 3 AVALIAÇÃO
                            ano_atual,     # ANO
                            "",            # DIAGNÓSTICO
                            "",            # EVIDÊNCIAS
                            ""             # OBSERVAÇÕES PEDAGÓGICAS
                        ]
                        ws.append_row(nova_linha)
                    
                    st.success(f"✅ {len(selecionados)} aluno(s) registrados no Turno Estendido!")
                    st.cache_data.clear() # Força o app a ler os dados novos do Google Sheets
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Erro ao acessar o Google Sheets: {e}")
            else:
                st.warning("Selecione pelo menos um aluno.")

    with gestao_col4:
        with st.popover("🗑️ Remover", key="del_popover", use_container_width=True):
            st.markdown("##### ⚠️ Zona de Exclusão")
            tipo_del = st.radio("O que deseja remover?", ["Aluno (Matrícula)", "Padrinho"])
            
            # --- CORREÇÃO DE LÓGICA AQUI ---
            # Se for Padrinho, o Turno Estendido não entra na lista de opções.
            if tipo_del == "Padrinho":
                abas_disponiveis = list(TURMAS_CONFIG.keys())
            else:
                abas_disponiveis = list(TURMAS_CONFIG.keys()) + ["TURNO_ESTENDIDO"]
            
            s_del = st.selectbox("Localizar em:", abas_disponiveis)
            
            # Leitura dos dados para o selectbox
            df_del = conn.read(worksheet=s_del).fillna("")
            df_del.columns = [str(c).strip().upper() for c in df_del.columns]
            
            # Lista de alunos única e ordenada
            lista_alunos_del = sorted(df_del["ALUNO"].unique()) if "ALUNO" in df_del.columns and not df_del.empty else []
            al_del = st.selectbox("Selecionar Aluno:", lista_alunos_del)
            
            if st.button("🚨 EXCLUIR REGISTRO", use_container_width=True):
                if al_del:
                    try:
                        # USANDO A FUNÇÃO SEGURA
                        gc = get_gspread_client(conn)
                        sh = gc.open(nome_planilha)
                        ws = sh.worksheet(s_del)
                        
                        # LOCALIZAR A LINHA (Index do pandas + 2)
                        idx_del = df_del[df_del["ALUNO"] == al_del].index[0] + 2
                        
                        if tipo_del == "Padrinho":
                            # Coluna 7 (G) é PADRINHO nas abas das salas
                            ws.update_cell(idx_del, 7, "")
                            st.success(f"Padrinho removido da {s_del}!")
                        else:
                            # DELETAR LINHA INTEIRA (Matrícula)
                            ws.delete_rows(idx_del)
                            st.error(f"Matrícula de {al_del} excluída permanentemente!")
                            
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")
                else:
                    st.warning("Selecione um aluno para excluir.")

    st.divider()

    # --- VISUALIZAÇÃO ---
    render_botoes_salas("btn_pad", "sel_pad")
    
    if "sel_pad" not in st.session_state:
        st.session_state.sel_pad = "SALA ROSA"
    
    sala_v = st.session_state.sel_pad
    cor_h = TURMAS_CONFIG[sala_v]["cor"]

    try:
        df_g = conn.read(worksheet="GERAL").fillna("")
        df_s = conn.read(worksheet=sala_v).fillna("")
        df_s.columns = [str(c).strip().upper() for c in df_s.columns]

        if not df_s.empty:
            tn, cm = render_filtros(df_g, "pad")
            df_f = df_s.copy()
            if tn != "Todos": df_f = df_f[df_f["TURMA"] == tn]
            if cm != "Todas": df_f = df_f[df_f["COMUNIDADE"] == cm]

            st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 4px solid {cor_h}; margin: 20px 0;">
                    <span style="font-size: 14px; color: #555;">📍 Atualmente: <b>{len(df_f)}</b> alunos na <b>{sala_v}</b></span>
                </div>
            """, unsafe_allow_html=True)

            v_cols = ["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
            html = f'<table style="width:100%; border-collapse: collapse; font-size:13px;">'
            html += f'<tr style="background:{cor_h}; color:white;">' + "".join([f'<th style="padding:10px;">{c}</th>' for c in v_cols]) + '</tr>'
            for _, r in df_f.iterrows():
                p_txt = str(r.get('PADRINHO/MADRINHA','-')) if str(r.get('PADRINHO/MADRINHA','')) not in ['nan','', '0', '-'] else '-'
                html += f"<tr><td style='padding:8px; border-bottom:1px solid #eee;'>{r['ALUNO']}</td><td style='text-align:center'>{r['TURMA']}</td><td>{r['IDADE']}</td><td>{r['COMUNIDADE']}</td><td>{p_txt}</td></tr>"
            st.markdown(html + '</table>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
elif menu == "📊 Avaliação da Tábua da Maré":
    st.markdown(f"### 📊 Lançar Avaliação (Google Sheets)")

    CATEGORIAS = [
        "Atividades em grupo/Proatividade", "Interesse pelo novo", "Compartilhamento de Materiais",
        "Clareza e desenvoltura", "Respeito às regras", "Vocabulário adequado",
        "Leitura e Escrita", "Compreensão de comandos", "Superação de desafios", "Assiduidade"
    ]

    # 1. Leitura da Planilha de Avaliações (para puxar dados anteriores)
    try:
        df_av = conn.read(worksheet="TABUA_MARE").fillna("")
        # Padroniza colunas para evitar erros de busca
        df_av.columns = [str(c).strip().title() for c in df_av.columns]
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha: {e}")
        st.stop()

    render_botoes_salas("btn_aval", "sel_aval")
    sala_atual = st.session_state.sel_aval

    # 2. BUSCA DINÂMICA DE ALUNOS (Melhoria de Robustez)
    # Tentamos primeiro pelo dicionário do Turno Estendido, 
    # se estiver vazio, buscamos no st.session_state.df_total (se você tiver ele global)
    # ou direto da aba da sala selecionada.
    
    dict_te = st.session_state.get("alunos_te_dict", {})
    alunos_na_sala = [n for n, s in dict_te.items() if str(s).strip().upper() == str(sala_atual).strip().upper()]

    # Caso o dicionário TE falhe, tentamos ler a aba da sala diretamente
    if not alunos_na_sala:
        try:
            df_temp = conn.read(worksheet=sala_atual).fillna("")
            df_temp.columns = [str(c).strip().upper() for c in df_temp.columns]
            alunos_na_sala = sorted(df_temp["ALUNO"].unique().tolist())
        except:
            alunos_na_sala = []

    if alunos_na_sala:
        al = st.selectbox("Selecione o Aluno", sorted(alunos_na_sala))
        
        # 3. PUXAR DADOS ANTERIORES (Para facilitar o preenchimento)
        # Filtramos pelo nome do aluno na aba de avaliações
        col_busca_aluno = "Aluno" if "Aluno" in df_av.columns else df_av.columns[0]
        historico_aluno = df_av[df_av[col_busca_aluno].astype(str).str.upper() == al.upper()]
        dados_anteriores = historico_aluno.iloc[-1] if not historico_aluno.empty else None
        
        st.markdown("#### ⭐ 10 motivos para avaliar!")
        
        with st.form("f_av_nuvem"):
            tr = st.selectbox("Período", ["1º Semestre", "2º Semestre"])
            
            cE, cD = st.columns(2)
            n_l = {}
            
            opcoes = ["Maré Baixa", "Maré Vazante", "Maré Enchente", "Maré Alta", "Maré Cheia"]

            for i, cat in enumerate(CATEGORIAS):
                # Busca a nota anterior ou define o padrão "Maré Enchente" (3)
                val_anterior = "Maré Enchente"
                if dados_anteriores is not None:
                    # Tenta buscar pela coluna exata (case-insensitive)
                    for col_av in dados_anteriores.index:
                        if col_av.strip().lower() == cat.strip().lower():
                            val_anterior = dados_anteriores[col_av]
                            break
                
                # Garante que o valor anterior existe nas opções para não dar erro no index
                try:
                    # Se o valor for numérico (1-5), converte para o texto correspondente
                    if str(val_anterior).isdigit():
                        idx_default = int(val_anterior) - 1
                    else:
                        idx_default = opcoes.index(val_anterior)
                except:
                    idx_default = 2 # Default: Maré Enchente
                
                n_l[cat] = (cE if i < 5 else cD).selectbox(cat, opcoes, index=idx_default, key=f"mare_s_{i}")
            
            # Recupera observação anterior
            obs_col = "Observações Pedagógicas" 
            obs_anterior = ""
            if dados_anteriores is not None:
                for col_av in dados_anteriores.index:
                    if "OBSERV" in col_av.upper():
                        obs_anterior = dados_anteriores[col_av]
                        break

            obs = st.text_area("Observações pedagógicas:", value=obs_anterior)
            
            if st.form_submit_button("🚀 Enviar para Tábua da Maré"):
                if al:
                    sucesso = registrar_tabua_mare(aluno=al, sala=sala_atual, semestre=tr, notas_dict=n_l, obs=obs)
                    if sucesso:
                        st.balloons()
                        st.success(f"Avaliação de {al} sincronizada!")
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.error("Por favor, selecione um aluno.")
    else:
        st.warning(f"Nenhum aluno encontrado na {sala_atual}. Verifique se a aba da sala na planilha tem a coluna 'ALUNO'.")
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
    for nome_aba in TURMAS_CONFIG.keys():
        try:
            df_t = conn.read(worksheet=nome_aba).fillna("")
            df_t.columns = [str(c).strip().upper() for c in df_t.columns]
            df_t["SALA_NOME"] = nome_aba  
            lista_salas.append(df_t)
        except:
            continue
    
    if not lista_salas:
        st.error("⚠️ Erro ao carregar salas. Verifique a conexão.")
        st.stop()

    df_total = pd.concat(lista_salas, ignore_index=True)
    
    # --- 2. IDENTIFICAÇÃO E SELEÇÃO (ADMIN vs PADRINHO) ---
    col_padrinho = "PADRINHO/MADRINHA"
    padrinhos_lista = sorted([
        str(p).strip() for p in df_total[col_padrinho].unique() 
        if str(p).strip() not in ["", "0", "nan", "None", "NaN"]
    ]) if col_padrinho in df_total.columns else []

    if st.session_state.get("perfil") == "padrinho":
        p_sel = st.session_state.get("nome_usuario", "")
    else:
        p_sel = st.selectbox("👤 Selecionar Padrinho (Visualização Admin):", ["Selecione..."] + padrinhos_lista)
    
    if p_sel and p_sel not in ["Selecione...", "Nenhum Padrinho Encontrado"]:
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

            # --- VISUALIZAÇÃO 1: TÁBUA DA MARÉ ---
            if modo == "🌊 Tábua da Maré (Geral)":
                CATEGORIAS = [
                    "Atividades em grupo/Proatividade", "Interesse pelo novo", "Compartilhamento de Materiais",
                    "Clareza e desenvoltura", "Respeito às regras", "Vocabulário adequado",
                    "Leitura e Escrita", "Compreensão de comandos", "Superação de desafios", "Assiduidade"
                ]
                
                aluno_info = df_total[df_total["ALUNO"] == al_af]
                if not aluno_info.empty:
                    info = aluno_info.iloc[0]
                    aba_origem = info.get("SALA_NOME", "Não identificada")
                    turno_aluno = info.get("TURMA", "")
                    sala_oficial = f"{aba_origem.title()} - {turno_aluno}" if turno_aluno else aba_origem.title()

                    col_ficha, col_conteudo = st.columns([1, 2.3])
                    with col_ficha:
                        st.markdown(f"""
                            <div style="background-color: #f1f8ff; padding: 18px; border-radius: 12px; border: 1px solid #d1e9ff; color: black;">
                                <h4 style="margin: 0 0 12px 0; color: #1A5276;">📋 Ficha</h4>
                                <p style="font-size: 13px; margin: 8px 0;"><b>👤 Nome:</b><br>{al_af}</p>
                                <p style="font-size: 13px; margin: 8px 0;"><b>🏫 Sala:</b><br>{sala_oficial}</p>
                                <p style="font-size: 13px; margin: 8px 0;"><b>🎂 Idade:</b> {info.get('IDADE', '---')}</p>
                                <p style="font-size: 13px; margin: 8px 0;"><b>🏡 Comunidade:</b> {info.get('COMUNIDADE', '---')}</p>
                            </div>
                        """, unsafe_allow_html=True)

                    with col_conteudo:
                            df_av = df_aval.copy()
                            df_av.columns = [str(c).strip().upper() for c in df_av.columns]
                            
                            # Filtra e remove linhas totalmente vazias que o pandas possa ter lido
                            dados_mare = df_av[df_av["ALUNO"] == al_af].dropna(subset=["ALUNO"])
                            
                            # --- CHECK DE EXISTÊNCIA DE REGISTRO ---
                            if not dados_mare.empty:
                                r_m = dados_mare.iloc[-1]
                                
                                # Verifica se pelo menos uma categoria tem valor (evita processar linha vazia)
                                tem_nota = any([r_m.get(cat.upper()) for cat in CATEGORIAS])
                                
                                if tem_nota:
                                    valores = []
                                    mapa_notas = {"MARÉ BAIXA": 1, "MARÉ VAZANTE": 2, "MARÉ ENCHENTE": 3, "MARÉ ALTA": 4, "MARÉ CHEIA": 5}
                                    
                                    for cat in CATEGORIAS:
                                        v = r_m.get(cat.upper(), 3)
                                        # Conversão segura
                                        if isinstance(v, str):
                                            n = mapa_notas.get(v.strip().upper(), 3)
                                        else:
                                            n = v if v and not pd.isna(v) else 3
                                        
                                        try:
                                            valores.append(float(n))
                                        except:
                                            valores.append(3.0)
                
                                    # Renderização das Vasilhas
                                    c1 = st.columns(5); c2 = st.columns(5)
                                    for i in range(5):
                                        with c1[i]: st.markdown(render_vasilha_mare(valores[i], CATEGORIAS[i]), unsafe_allow_html=True)
                                    for i in range(5, 10):
                                        with c2[i-5]: st.markdown(render_vasilha_mare(valores[i], CATEGORIAS[i]), unsafe_allow_html=True)
                
                                    st.plotly_chart(criar_grafico_mare(CATEGORIAS, valores), use_container_width=True)
                                    st.info(f"**Observação Pedagógica:** {r_m.get('OBSERVAÇÕES PEDAGÓGICAS', 'Sem registro.')}")
                                else:
                                    st.warning(f"🟡 O aluno {al_af} possui um registro na planilha, mas as notas ainda não foram lançadas.")
                            else:
                                # MENSAGEM AMIGÁVEL QUANDO NÃO HÁ NADA LANÇADO
                                st.info(f"ℹ️ **Nenhuma avaliação registrada.**\nAinda não foram realizados lançamentos para a Tábua da Maré deste aluno.")

            # --- VISUALIZAÇÃO 2: TURNO ESTENDIDO (O CÓDIGO QUE VOCÊ ENVIOU) ---
            elif modo == "📚 Turno Estendido":
                df_h = (df_alf.copy()).fillna("")
                dados_al = df_h[df_h["Aluno"] == al_af].sort_values(["Ano", "Avaliacao"])
                dados_al = dados_al.drop_duplicates(subset=['Avaliacao', 'Ano'], keep='last')
                
                if not dados_al.empty:
                    u_nv = dados_al['Nivel'].iloc[-1]
                    c_inf, c_mare = st.columns([1.2, 1])
                    with c_inf:
                        cor_bg_nivel = CORES_EXCLUSIVAS.get(u_nv, "#ddd")
                        st.markdown(f"""
                        <div style="border:1px solid #ddd; padding:15px; border-radius:12px; background:#f9f9f9; color:black; height:220px; overflow-y: auto;">
                            <h4 style="margin:0;">{al_af}</h4>
                            <p style="margin: 10px 0;"><b>Nível Atual:</b> <span style="background:{cor_bg_nivel}; color:#2C3E50; padding:6px 12px; border-radius:20px; font-weight:bold; border: 1px solid rgba(0,0,0,0.1);">{u_nv}</span></p>
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
                                🔵 <b>Cheia:</b> Nível Ortográfico<br>🟢 <b>Enchente:</b> Evoluiu<br>🟡 <b>Vazante:</b> Oscilação<br>⚪ <b>Baixa:</b> Inicial
                            </div>""", unsafe_allow_html=True)

                    st.markdown("---")
                    st.markdown("##### 🚀 Jornada de Alfabetização")
                    
                    # Estilo Trilha
                    st.markdown("""<style>
                        .trilha-ap-container { display: flex; align-items: center; justify-content: center; gap: 4px; overflow-x: auto; padding: 10px 0; }
                        .caixa-trilha-ap { padding: 6px 4px; border-radius: 10px; text-align: center; font-size: 11px; font-weight: bold; min-width: 110px; height: 55px; display: flex; align-items: center; justify-content: center; line-height: 1.1; flex-shrink: 0; box-shadow: 1px 1px 3px rgba(0,0,0,0.05); }
                        .seta-ap { font-weight: bold; color: #D5DBDB; font-size: 16px; margin: 0 -2px; }
                    </style>""", unsafe_allow_html=True)

                    html_t = '<div class="trilha-ap-container">'
                    for i, nv_ref in enumerate(NIVEIS_ALF):
                        is_current = (u_nv == nv_ref)
                        cor_bg = CORES_EXCLUSIVAS.get(nv_ref, "#eee")
                        borda = "3px solid #2C3E50" if is_current else "1px solid rgba(0,0,0,0.15)"
                        opacidade = "1.0" if is_current else "0.65"
                        html_t += f'<div class="caixa-trilha-ap" style="background-color:{cor_bg}; border:{borda}; opacity:{opacidade}; color:#2C3E50;">{nv_ref.split(". ")[1]}</div>'
                        if i < len(NIVEIS_ALF)-1: html_t += '<div class="seta-ap">→</div>'
                    st.markdown(html_t + '</div>', unsafe_allow_html=True)

                    st.markdown("##### 📂 Histórico")
                    for _, r in dados_al.iterrows():
                        t_av = r["Avaliacao"].replace("Avaliação Final", "3ª Avaliação")
                        st.markdown(f"""<div style="display:flex; justify-content:space-between; align-items:center; padding:8px; border-bottom:1px solid #eee; font-size:13px; color:black;">
                            <span>📅 <b>{t_av}/{r['Ano']}</b></span>
                            <span style="background:{CORES_EXCLUSIVAS.get(r['Nivel'], '#ddd')}; padding:4px 10px; border-radius:12px; font-weight:bold; border:1px solid rgba(0,0,0,0.1);">{r['Nivel']}</span>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.info("Ainda não há dados de alfabetização para este aluno.")
        else:
            st.warning("Nenhum afilhado encontrado.")
elif menu == "🌊 Tábua da Maré":
    st.markdown(f"### 🌊 Tábua da Maré")
    
    CATEGORIAS = [
        "Atividades em grupo/Proatividade", "Interesse pelo novo", "Compartilhamento de Materiais",
        "Clareza e desenvoltura", "Respeito às regras", "Vocabulário adequado",
        "Leitura e Escrita", "Compreensão de comandos", "Superação de desafios", "Assiduidade"
    ]
    
    render_botoes_salas("btn_int", "sel_int")
    
    df_av = df_aval.copy()
    df_av.columns = [str(c).strip().upper() for c in df_av.columns]
    
    # df_total deve ser o DataFrame que une as abas SALA AZUL, SALA VERDE, etc.
    df_s = safe_read(st.session_state.sel_int)
    
    if not df_s.empty:
        df_s.columns = [str(c).strip().upper() for c in df_s.columns]
        alunos_sala = sorted([str(n).replace("**", "").strip() for n in df_s["ALUNO"].unique()])
        
        for al in alunos_sala:
            with st.expander(f"👤 {al}"):
                # --- FICHA CADASTRAL (O Espelho) ---
                aluno_row = df_s[df_s["ALUNO"] == al].iloc[0]
                turno = aluno_row.get("TURMA", "")
                sala_full = f"{st.session_state.sel_int.title()} - {turno}" if turno else st.session_state.sel_int.title()
                
                col_f1, col_f2 = st.columns([1, 2])
                with col_f1:
                    st.markdown(f"""
                        <div style="background-color: #f1f8ff; padding: 15px; border-radius: 10px; border: 1px solid #d1e9ff; color: black;">
                            <p style="margin: 0; font-size: 12px;"><b>SALA/TURMA:</b><br>{sala_full}</p>
                            <p style="margin: 8px 0 0 0; font-size: 12px;"><b>IDADE:</b> {aluno_row.get("IDADE", "---")}</p>
                            <p style="margin: 8px 0 0 0; font-size: 12px;"><b>COMUNIDADE:</b> {aluno_row.get("COMUNIDADE", "---")}</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                # --- AVALIAÇÕES ---
                dados_aluno = df_av[df_av["ALUNO"] == al]
                if not dados_aluno.empty:
                    for _, r in dados_aluno.iterrows():
                        periodo = r.get("PERIODO", "Avaliação")
                        st.write(f"---")
                        st.markdown(f"**🗓️ {periodo}**")
                        
                        valores = []
                        mapa_notas = {"MARÉ BAIXA": 1, "MARÉ VAZANTE": 2, "MARÉ ENCHENTE": 3, "MARÉ ALTA": 4, "MARÉ CHEIA": 5}
                        for cat in CATEGORIAS:
                            v = r.get(cat.upper(), 3)
                            n = mapa_notas.get(v.upper(), v) if isinstance(v, str) else v
                            valores.append(float(n))

                        # Vasilhas 5x5
                        c1 = st.columns(5)
                        for i in range(5):
                            with c1[i]: st.markdown(render_vasilha_mare(valores[i], CATEGORIAS[i]), unsafe_allow_html=True)
                        c2 = st.columns(5)
                        for i in range(5, 10):
                            with c2[i-5]: st.markdown(render_vasilha_mare(valores[i], CATEGORIAS[i]), unsafe_allow_html=True)

                        st.plotly_chart(criar_grafico_mare(CATEGORIAS, valores), use_container_width=True, key=f"gen_{al}_{periodo}")
                        st.info(f"**Observação:** {r.get('OBSERVAÇÕES PEDAGÓGICAS', 'Sem registro.')}")
                else:
                    st.info("Nenhuma avaliação registrada para este aluno.")
