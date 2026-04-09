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
    div.stButton > button {{
        width: 100%; border-radius: 8px !important; font-weight: 700 !important; 
        height: 42px; font-size: 11px !important; border: none !important;
        transition: all 0.3s;
    }}
    </style>
    """, unsafe_allow_html=True)

# 2. Definições
CATEGORIAS = [
    "1. Atividades em Grupo/Proatividade", "2. Interesse pelo Novo",
    "3. Compartilhamento de Materiais", "4. Clareza e Desenvoltura",
    "5. Respeito às Regras", "6. Vocabulário Adequado",
    "7. Leitura e Escrita", "8. Compreensão de Comandos",
    "9. Superação de Desafios", "10. Assiduidade"
]

MARE_LABELS = {4: "Muito bom (Maré Cheia)", 3: "Em evolução (Maré Enchente)", 2: "Requer atenção (Maré Vazante)", 1: "Início (Maré Baixa)"}
MARE_OPCOES = {"Maré Cheia": 4, "Maré Enchente": 3, "Maré Vazante": 2, "Maré Baixa": 1}

# Níveis Alfabetização
NIVEIS_ALF = [
    "1. Pré-Silábico", "2. Silábico s/ Valor", "3. Silábico c/ Valor", 
    "4. Silábico Alfabético", "5. Alfabético Inicial", "6. Alfabético Final", "7. Alfabético Ortográfico"
]

AVAL_FILE = "avaliacoes.csv"
ALF_FILE = "alfabetizacao.csv"

# Inicialização de arquivos (Garantindo a coluna 'Sala' para evitar KeyError do print)
if not os.path.exists(AVAL_FILE):
    pd.DataFrame(columns=["Aluno", "Periodo"] + CATEGORIAS + ["Observacoes"]).to_csv(AVAL_FILE, index=False)

if not os.path.exists(ALF_FILE):
    pd.DataFrame(columns=["Aluno", "Avaliacao", "Nivel", "Gatilho", "Evidencias", "Obs", "Sala"]).to_csv(ALF_FILE, index=False)
else:
    # Correção automática se o arquivo existir sem a coluna 'Sala'
    temp_alf = pd.read_csv(ALF_FILE)
    if "Sala" not in temp_alf.columns:
        temp_alf["Sala"] = "SALA ROSA"
        temp_alf.to_csv(ALF_FILE, index=False)

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

# 3. Estados de Sessão
if "logado" not in st.session_state: st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
for k in ['sel_mat', 'sel_pad', 'sel_aval', 'sel_int', 'sel_alf', 'sel_ind', 'temp_nivel']:
    if k not in st.session_state: st.session_state[k] = "SALA ROSA"
if st.session_state.temp_nivel not in NIVEIS_ALF: st.session_state.temp_nivel = NIVEIS_ALF[0]

# 4. Login (Conforme seu código base)
if not st.session_state.logado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        with st.form("login"):
            u = st.text_input("👤 Usuário").strip().upper()
            s = st.text_input("🔑 Chave", type="password")
            if st.form_submit_button("ENTRAR"):
                if u == "ADMIN" and s == "123":
                    st.session_state.update({"logado": True, "perfil": "admin", "nome_usuario": "Coordenação"})
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
                    else: st.error("Usuário não localizado.")
    st.stop()

# --- FUNÇÕES DE INTERFACE ---
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
        x=categorias, y=valores, fill='tozeroy', mode='lines',
        line=dict(color=C_AZUL_MARE, width=5, shape='spline'),
        text=[MARE_LABELS[int(v)] for v in valores], hoverinfo="text+x"
    ))
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', yaxis=dict(range=[0.5, 4.5], visible=False),
        xaxis=dict(showgrid=False, zeroline=False, showspikes=True, spikemode='toaxis', spikedash='dot', spikecolor="#d1d1d1", spikethickness=1),
        height=450, margin=dict(l=20, r=20, t=30, b=80), hovermode="x")
    return fig

# --- SIDEBAR ---
menu_options = ["👤 Cadastro", "📝 Matrículas", "🤝 Apadrinhamento", "📊 Lançar Avaliação", "📖 Programa Alfabetização", "📈 Indicadores Pedagógicos", "🌊 Evolução (Padrinhos)", "🌊 Tábua da Maré - Interno"] if st.session_state.perfil == "admin" else ["🌊 Evolução (Padrinhos)"]
menu = st.sidebar.radio("Navegação", menu_options)
if st.sidebar.button("🚪 Sair"):
    st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""}); st.rerun()

st.markdown(f"<div class='main-header'><h1><span style='color:{C_VERDE}'>Instituto</span> <span style='color:{C_AZUL}'>Mãe</span> <span style='color:{C_VERDE}'>Lalu</span></h1></div><hr>", unsafe_allow_html=True)

# --- LOGICA DAS ABAS ---

if menu == "📖 Programa Alfabetização":
    st.markdown(f"<h3 style='color:{C_ROXO}'>📖 Trilha de Alfabetização</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_alf", "sel_alf")
    df_s = safe_read(st.session_state.sel_alf)
    
    if not df_s.empty:
        # BOTÕES DE NÍVEL (Fora do form para evitar erro de StreamlitAPIException)
        st.write("**Selecione o Nível de Diagnóstico:**")
        cols_n = st.columns(len(NIVEIS_ALF))
        for i, n_text in enumerate(NIVEIS_ALF):
            label = n_text.split(". ")[1]
            # Estilo dinâmico para destacar o selecionado
            btn_opacity = "1.0" if st.session_state.temp_nivel == n_text else "0.4"
            st.markdown(f'<style>div[data-testid="column"]:nth-child({i+1}) button {{ background-color: {C_ROXO} !important; color: white !important; opacity: {btn_opacity}; font-size: 10px !important; }}</style>', unsafe_allow_html=True)
            if cols_n[i].button(label, key=f"btn_nv_{i}"):
                st.session_state.temp_nivel = n_text; st.rerun()

        st.info(f"Nível selecionado: **{st.session_state.temp_nivel}**")

        with st.form("form_alfabetizacao"):
            c1, c2 = st.columns([2, 1])
            al = c1.selectbox("Aluno", sorted(df_s["ALUNO"].unique()))
            num_aval = c2.selectbox("Avaliação", ["1ª Avaliação", "2ª Avaliação", "Avaliação Final"])
            
            c3, c4 = st.columns(2)
            gatilho = c3.checkbox("Atende o Gatilho de Passagem?")
            evidencias = c4.multiselect("Evidências de Avanço:", ["Leitura de sílabas", "Diferenciação letra/desenho", "Escrita fonética", "Uso de dígrafos", "Produção textual"])
            obs_alf = st.text_area("Observações do Cirandeiro:")
            
            if st.form_submit_button("Registrar na Trilha"):
                df_alf = pd.read_csv(ALF_FILE)
                # Remove duplicata (mesmo aluno na mesma avaliação)
                df_alf = df_alf[~((df_alf["Aluno"] == al) & (df_alf["Avaliacao"] == num_aval))]
                nova_l = pd.DataFrame([[al, num_aval, st.session_state.temp_nivel, gatilho, ", ".join(evidencias), obs_alf, st.session_state.sel_alf]], columns=df_alf.columns)
                pd.concat([df_alf, nova_l], ignore_index=True).to_csv(ALF_FILE, index=False)
                st.success("Progresso salvo com sucesso!")

elif menu == "📈 Indicadores Pedagógicos":
    st.markdown(f"<h3 style='color:{C_VERDE}'>📈 Indicadores de Alfabetização</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_ind", "sel_ind")
    df_alf = pd.read_csv(ALF_FILE)
    df_sala = df_alf[df_alf["Sala"] == st.session_state.sel_ind]
    
    if not df_sala.empty:
        # Comparação: 1ª Avaliação vs Última registrada de cada aluno
        df_1 = df_sala[df_sala["Avaliacao"] == "1ª Avaliação"]
        df_ult = df_sala.sort_values("Avaliacao").groupby("Aluno").last().reset_index()
        
        # Filtros de níveis
        n_iniciais = ["1. Pré-Silábico", "2. Silábico s/ Valor"]
        n_consolidados = ["6. Alfabético Final", "7. Alfabético Ortográfico"]
        
        # 1. Redução Iniciais
        red_iniciais = len(df_1[df_1["Nivel"].isin(n_iniciais)]) - len(df_ult[df_ult["Nivel"].isin(n_iniciais)])
        # 2. Aumento Consolidados
        aum_cons = len(df_ult[df_ult["Nivel"].isin(n_consolidados)])
        # 4. % Avanço (subir ao menos 1 degrau na lista NIVEIS_ALF)
        avancou = 0
        for _, r in df_ult.iterrows():
            v1 = df_1[df_1["Aluno"] == r["Aluno"]]
            if not v1.empty:
                if NIVEIS_ALF.index(r["Nivel"]) > NIVEIS_ALF.index(v1.iloc[0]["Nivel"]): avancou += 1
        perc_avanco = (avancou / len(df_ult) * 100) if len(df_ult) > 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Queda Níveis Iniciais", f"-{red_iniciais}" if red_iniciais > 0 else "0")
        m2.metric("Níveis Consolidados", aum_cons)
        m3.metric("Nível Ortográfico", len(df_ult[df_ult["Nivel"] == "7. Alfabético Ortográfico"]))
        m4.metric("% Avanço de Nível", f"{perc_avanco:.1f}%")
        
        st.write("#### Lista de Progresso da Sala")
        st.dataframe(df_ult[["Aluno", "Avaliacao", "Nivel", "Gatilho"]], use_container_width=True)
    else: st.info("Sem registros pedagógicos para esta sala.")

elif menu == "🌊 Evolução (Padrinhos)":
    # Mantendo sua lógica original, apenas chamando a função criar_grafico_mare atualizada
    st.markdown(f"<h3 style='color:{C_AZUL}'>🌊 Evolução dos Afilhados</h3>", unsafe_allow_html=True)
    dfs = [safe_read(s) for s in TURMAS_CONFIG.keys()]
    df_full = pd.concat(dfs, ignore_index=True)
    p_sel = st.selectbox("Padrinho:", sorted([p for p in df_full["PADRINHO/MADRINHA"].unique() if str(p).strip() not in ["", "0", "nan"]])) if st.session_state.perfil == "admin" else st.session_state.nome_usuario
    if p_sel:
        df_av = pd.read_csv(AVAL_FILE)
        afilhas = df_full[(df_full["PADRINHO/MADRINHA"].astype(str).str.upper() == p_sel.upper()) & (df_full["ALUNO"].isin(df_av["Aluno"].unique()))]
        if not afilhas.empty:
            al_s = st.selectbox("Selecione o Afilhado:", sorted(afilhas["ALUNO"].unique()))
            row = df_av[df_av["Aluno"] == al_s].iloc[-1]
            st.plotly_chart(criar_grafico_mare(CATEGORIAS, [float(row[c]) for c in CATEGORIAS]), use_container_width=True)
            if str(row["Observacoes"]).strip() not in ["", "nan"]: st.info(f"**Observações:** {row['Observacoes']}")
        else: st.warning("Ainda não há avaliações.")

elif menu == "🤝 Apadrinhamento":
    st.markdown(f"<h3 style='color:{C_AZUL}'>🤝 Gestão de Apadrinhamento</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_pad", "sel_pad")
    df_s = safe_read(st.session_state.sel_pad)
    if not df_s.empty:
        cor_h = TURMAS_CONFIG[st.session_state.sel_pad]["cor"]
        v_cols = ["ALUNO", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
        html = f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
        for _, r in df_s.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in v_cols]) + '</tr>'
        st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

# Outras abas (Cadastro, Matrículas, Lançar, Interno) seguem o padrão do seu código funcional base...
elif menu == "📝 Matrículas":
    st.markdown(f"<h3 style='color:{C_VERDE}'>📋 Quadro de Matrículas</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_mat", "sel_mat")
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_mat)
    tn, cm = render_filtros(df_g, "mat"); df_f = aplicar_filtros(df_s, df_g, tn, cm)
    cor_h = TURMAS_CONFIG[st.session_state.sel_mat]["cor"]
    v_cols = ["ALUNO", "IDADE", "COMUNIDADE"]
    html = f'<table class="custom-table"><thead style="background-color:{cor_h}"><tr>' + "".join([f'<th>{c}</th>' for c in v_cols]) + '</tr></thead><tbody>'
    for _, r in df_f.iterrows(): html += '<tr>' + "".join([f'<td>{r[c]}</td>' for c in v_cols]) + '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

elif menu == "👤 Cadastro":
    st.markdown(f"<h3 style='color:{C_ROSA}'>👤 Novo Cadastro</h3>", unsafe_allow_html=True)
    with st.form("cad_form"):
        c1, c2 = st.columns(2)
        n, i = c1.text_input("Nome").strip(), c2.text_input("Idade").strip()
        comu, t = c1.text_input("Comunidade").strip(), c2.selectbox("Sala", list(TURMAS_CONFIG.keys()))
        tn = c1.selectbox("Turno", ["A", "B"])
        if st.form_submit_button("Cadastrar Aluno"):
            if n and i:
                client = get_gspread_client()
                sh = client.open_by_key("1MBAvQB5xGhE7OAHGWdFPvGfwqzP9SpiaIW4OEl2Mgk4")
                nova_linha = [n.upper(), t, tn, i, comu.upper(), ""]
                sh.worksheet(t).append_row(nova_linha); sh.worksheet("GERAL").append_row(nova_linha)
                st.success("Cadastro realizado com sucesso!"); st.rerun()

elif menu == "📊 Lançar Avaliação":
    st.markdown(f"<h3 style='color:{C_AMARELO}'>📊 Lançar Tábua da Maré</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_aval", "sel_aval")
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_aval)
    df_f = df_s[df_s["ALUNO"] != ""]
    with st.form("aval"):
        c1, c2 = st.columns(2)
        al, tr = c1.selectbox("Aluno", sorted(df_f["ALUNO"].unique())), c2.selectbox("Semestre", ["1º Semestre", "2º Semestre"])
        col_esq, col_dir = st.columns(2); n_l = {}
        for idx, cat in enumerate(CATEGORIAS): n_l[cat] = (col_esq if idx < 5 else col_dir).selectbox(cat, list(MARE_OPCOES.keys()), key=f"sel_{idx}")
        obs = st.text_area("Observações:"); 
        if st.form_submit_button("Salvar Avaliação"):
            df_av = pd.read_csv(AVAL_FILE); df_av = df_av[~((df_av['Aluno'] == al) & (df_av['Periodo'] == tr))]
            pd.concat([df_av, pd.DataFrame([[al, tr] + [MARE_OPCOES[n_l[c]] for c in CATEGORIAS] + [obs]], columns=df_av.columns)], ignore_index=True).to_csv(AVAL_FILE, index=False)
            st.success("Salvo!")

elif menu == "🌊 Tábua da Maré - Interno":
    st.markdown(f"<h3 style='color:{C_VERDE}'>🌊 Tábua da Maré</h3>", unsafe_allow_html=True)
    render_botoes_salas("btn_int", "sel_int")
    df_g, df_s = safe_read("GERAL"), safe_read(st.session_state.sel_int)
    df_av = pd.read_csv(AVAL_FILE)
    alunos_lista = sorted(df_s[df_s["ALUNO"].isin(df_av["Aluno"].unique())]["ALUNO"].unique())
    if alunos_lista:
        al_s = st.selectbox("Selecione o Aluno:", alunos_lista)
        df_al = df_av[df_av["Aluno"] == al_s]
        tri = st.selectbox("Semestre ", df_al["Periodo"].unique())
        row = df_al[df_al["Periodo"] == tri].iloc[0]
        st.plotly_chart(criar_grafico_mare(CATEGORIAS, [float(row[c]) for c in CATEGORIAS]), use_container_width=True)
