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
C_ROXO_PASTEL = "#e0d7f7" # Tom pastel para alunos não selecionados

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

EVIDENCIAS_PADRAO = [
    "Reconhece letras do nome", "Diferencia desenhos de letras", 
    "Identifica rimas", "Relaciona som à letra", 
    "Lê palavras simples", "Escreve frases curtas"
]

if not os.path.exists(ALF_FILE):
    pd.DataFrame(columns=["Aluno", "Avaliacao", "Nivel", "Gatilho", "Evidencias", "Obs", "Sala"]).to_csv(ALF_FILE, index=False)

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
    }}
    .custom-table thead th {{ padding: 12px 10px; text-align: left; color: white !important; font-weight: 700; border: none; }}
    .custom-table tbody td {{ padding: 8px 10px; border-bottom: 1px solid #fafafa; color: #444 !important; font-weight: 500; }}
    
    /* Botão Padrão */
    div.stButton > button {{
        width: 100%; border-radius: 8px !important; font-weight: 700 !important; 
        height: 42px; font-size: 11px !important; border: none !important;
        transition: all 0.3s;
    }}

    /* Estilo específico para o botão Turno Estendido na listagem (Menor) */
    .btn-estendido-col div.stButton > button {{
        height: 32px !important;
        font-size: 10px !important;
        padding: 0 5px !important;
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

# 2. Definições e Funções
CATEGORIAS = ["1. Atividades em Grupo/Proatividade", "2. Interesse pelo Novo", "3. Compartilhamento de Materiais", "4. Clareza e Desenvoltura", "5. Respeito às Regras", "6. Vocabulário Adequado", "7. Leitura e Escrita", "8. Compreensão de Comandos", "9. Superação de Desafios", "10. Assiduidade"]
MARE_OPCOES = {"Maré Cheia": 4, "Maré Enchente": 3, "Maré Vazante": 2, "Maré Baixa": 1}
MARE_LABELS = {4: "Maré Cheia", 3: "Maré Enchente", 2: "Maré Vazante", 1: "Maré Baixa"}
AVAL_FILE = "avaliacoes.csv"

if not os.path.exists(AVAL_FILE):
    pd.DataFrame(columns=["Aluno", "Periodo"] + CATEGORIAS + ["Observacoes"]).to_csv(AVAL_FILE, index=False)

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

def render_botoes_salas(key_prefix, session_key):
    cols = st.columns(5)
    for i, (sala, cfg) in enumerate(TURMAS_CONFIG.items()):
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
if "alunos_turno_estendido" not in st.session_state: st.session_state["alunos_turno_estendido"] = []

for k in ['sel_mat', 'sel_pad', 'sel_aval', 'sel_int', 'sel_alf', 'sel_ind']:
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

# --- MENU LATERAL ---
menu_options = [
    "👤 Matrícula", "📝 Alunos matriculados", "🤝 Gestão de apadrinhamento", 
    "📊 Avaliação da Tábua da Maré", "📖 Turno Estendido", 
    "📈 Indicadores pedagógicos", "🌊 Canal do Apadrinhamento", "🌊 Tábua da Maré"
] if st.session_state.perfil == "admin" else ["🌊 Canal do Apadrinhamento"]
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
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_mat)
    tn, cm = render_filtros(df_g, "mat"); df_f = aplicar_filtros(df_s, df_g, tn, cm)
    
    for i, r in df_f.iterrows():
        c1, c2, c3, c4 = st.columns([3, 1, 2, 1.3])
        c1.write(f"**{r['ALUNO']}**")
        c2.write(f"{r['IDADE']} anos")
        c3.write(f"{r['COMUNIDADE']}")
        
        # Lógica de Cor e Tamanho do Botão
        está_no_turno = r['ALUNO'] in st.session_state["alunos_turno_estendido"]
        cor_btn = C_ROXO if está_no_turno else C_ROXO_PASTEL
        
        with c4:
            st.markdown(f'<div class="btn-estendido-col">', unsafe_allow_html=True)
            st.markdown(f"""<style>button[key="btn_te_{i}"] {{ background-color: {cor_btn} !important; color: white !important; }}</style>""", unsafe_allow_html=True)
            if st.button("Turno Estendido", key=f"btn_te_{i}"):
                if not está_no_turno:
                    st.session_state["alunos_turno_estendido"].append(r['ALUNO'])
                    st.success(f"Adicionado!")
                    st.rerun()
                else:
                    st.info(f"Já na lista.")
            st.markdown('</div>', unsafe_allow_html=True)

elif menu == "🤝 Gestão de apadrinhamento":
    st.markdown(f"### 🤝 Gestão de Apadrinhamento")
    render_botoes_salas("btn_pad", "sel_pad")
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_pad)
    tn, cm = render_filtros(df_g, "pad"); df_f = aplicar_filtros(df_s, df_g, tn, cm)
    cor_h = TURMAS_CONFIG[st.session_state.sel_pad]["cor"]
    v_cols = ["ALUNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
    html = f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
    for _, r in df_f.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in v_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

elif menu == "📊 Avaliação da Tábua da Maré":
    st.markdown(f"### 📊 Lançar Avaliação")
    render_botoes_salas("btn_aval", "sel_aval")
    df_s = safe_read(st.session_state.sel_aval)
    if not df_s.empty:
        al = st.selectbox("Selecione o Aluno", sorted(df_s[df_s["ALUNO"] != ""]["ALUNO"].unique()))
        with st.form("form_aval"):
            tr = st.selectbox("Período", ["1º Semestre", "2º Semestre"])
            col_e, col_d = st.columns(2); notas_letras = {}
            for idx, cat in enumerate(CATEGORIAS):
                notas_letras[cat] = (col_e if idx < 5 else col_d).selectbox(cat, list(MARE_OPCOES.keys()), key=f"sel_{idx}")
            obs = st.text_area("Observações:")
            if st.form_submit_button("Salvar Avaliação"):
                df_av = pd.read_csv(AVAL_FILE)
                df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Periodo'] == tr))]
                pd.concat([df_av, pd.DataFrame([[al, tr] + [MARE_OPCOES[notas_letras[c]] for c in CATEGORIAS] + [obs]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
                st.success("Avaliação salva!"); st.rerun()

elif menu == "📖 Turno Estendido":
    st.markdown(f"<h3 style='color:{C_ROXO}'>📖 Turno Estendido</h3>", unsafe_allow_html=True)
    with st.expander("➕ Cadastrar novo aluno"):
        with st.form("cad_extra"):
            nome_ex = st.text_input("Nome do Aluno").strip().upper()
            if st.form_submit_button("Confirmar Cadastro"):
                if nome_ex and nome_ex not in st.session_state["alunos_turno_estendido"]:
                    st.session_state["alunos_turno_estendido"].append(nome_ex)
                    st.success(f"Cadastrado!")
                    st.rerun()

    lista_final = sorted(st.session_state["alunos_turno_estendido"])
    if lista_final:
        al = st.selectbox("Aluno para Diagnóstico:", lista_final)
        df_h = pd.read_csv(ALF_FILE)
        diag = df_h[df_h["Aluno"] == al].iloc[-1] if not df_h[df_h["Aluno"] == al].empty else None
        
        html_trilha = '<div class="trilha-container">'
        for i, n_text in enumerate(NIVEIS_ALF):
            ativo = (diag is not None and diag["Nivel"] == n_text)
            cor_bg = CORES_TRILHA[n_text]["ativo"] if ativo else CORES_TRILHA[n_text]["inativo"]
            label = n_text.split(". ")[1]
            html_trilha += f'<div class="caixa-trilha" style="background-color:{cor_bg}; color:{"white" if ativo else "#444"}; border-color:{"#aaa" if ativo else "transparent"}">{label}</div>'
            if i < len(NIVEIS_ALF) - 1: html_trilha += '<div class="seta-trilha">→</div>'
        html_trilha += '</div>'
        st.markdown(html_trilha, unsafe_allow_html=True)
        
        with st.form("form_alf"):
            c1, c2 = st.columns(2)
            novo_nv = c1.selectbox("Novo Nível:", NIVEIS_ALF, index=NIVEIS_ALF.index(diag["Nivel"]) if diag is not None else 0)
            tipo = c2.selectbox("Avaliação:", ["1ª Avaliação", "2ª Avaliação", "Avaliação Final"])
            ev_cols = st.columns(3); sel_ev = []
            for idx, ev in enumerate(EVIDENCIAS_PADRAO):
                if ev_cols[idx % 3].checkbox(ev): sel_ev.append(ev)
            obs = st.text_area("Observações Pedagógicas:")
            if st.form_submit_button("Registrar Diagnóstico"):
                df_h = df_h[~((df_h["Aluno"] == al) & (df_h["Avaliacao"] == tipo))]
                pd.concat([df_h, pd.DataFrame([[al, tipo, novo_nv, False, ", ".join(sel_ev), obs, "TURNO ESTENDIDO"]], columns=df_h.columns)], ignore_index=True).to_csv(ALF_FILE, index=False)
                st.success("Diagnóstico Salvo!"); st.rerun()
    else: st.info("Nenhum aluno na lista.")

elif menu == "📈 Indicadores pedagógicos":
    st.markdown(f"### 📈 Indicadores Pedagógicos")
    render_botoes_salas("btn_ind", "sel_ind")
    df_h = pd.read_csv(ALF_FILE)
    df_ult = df_h.sort_values("Avaliacao").groupby("Aluno").last().reset_index()
    st.dataframe(df_ult, use_container_width=True)

elif menu == "🌊 Canal do Apadrinhamento":
    st.markdown(f"### 🌊 Canal do Apadrinhamento")
    df_av = pd.read_csv(AVAL_FILE)
    df_total = pd.concat([safe_read(s) for s in TURMAS_CONFIG.keys()], ignore_index=True)
    
    # Restauração da Simulação para Admin
    pad_sel = st.session_state.nome_usuario if st.session_state.perfil == "padrinho" else st.selectbox("Simular Padrinho/Madrinha:", sorted([p for p in df_total["PADRINHO/MADRINHA"].unique() if str(p).strip() not in ["", "0", "nan"]]))
    
    if pad_sel:
        afilhados = df_total[df_total["PADRINHO/MADRINHA"].astype(str).str.upper() == pad_sel.upper()]
        al_afil = st.selectbox("Selecione o Afilhado:", sorted(afilhados["ALUNO"].unique()))
        if al_afil in df_av["Aluno"].unique():
            df_hist = df_av[df_av["Aluno"] == al_afil]
            for _, r in df_hist.iterrows():
                st.markdown(f"**Período:** {r['Periodo']}")
                st.plotly_chart(criar_grafico_mare(CATEGORIAS, [float(r[c]) for c in CATEGORIAS]), use_container_width=True)
        else: st.warning("Sem avaliações.")

elif menu == "🌊 Tábua da Maré":
    st.markdown(f"### 🌊 Tábua da Maré (Interno)")
    render_botoes_salas("btn_int", "sel_int")
    st.write("Análise detalhada por turma.")
