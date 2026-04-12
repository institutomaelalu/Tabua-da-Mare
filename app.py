import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
import gspread
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

ID_PLANILHA = "1Zj8u67oAWKgYRd2uOkGssdaxXnwdsKsZBDxeLChnBr4"
ARQUIVO_BUFFER   = "buffer_estendido.csv"
ARQUIVO_DADOS_TE = "dados_turno_estendido.csv"

C_ROSA, C_VERDE, C_AZUL, C_AMARELO, C_ROXO = "#ff81ba", "#a8cf45", "#5cc6d0", "#ffc713", "#6741d9"
C_AZUL_MARE = "#8fd9fb"

NIVEIS_ALF = [
    "1. Pré-Silábico", "2. Silábico s/ Valor", "3. Silábico c/ Valor",
    "4. Silábico Alfabético", "5. Alfabético Inicial", "6. Alfabético Final",
    "7. Alfabético Ortográfico"
]
MAPA_NIVEIS = {niv: i + 1 for i, niv in enumerate(NIVEIS_ALF)}
CORES_EXCLUSIVAS = {
    "1. Pré-Silábico": "#FADBD8", "2. Silábico s/ Valor": "#FDEBD0",
    "3. Silábico c/ Valor": "#FCF3CF", "4. Silábico Alfabético": "#D5F5E3",
    "5. Alfabético Inicial": "#A9DFBF", "6. Alfabético Final": "#D6EAF8",
    "7. Alfabético Ortográfico": "#EBDEF0"
}
MARE_LABELS = {1: "Maré Baixa", 2: "Maré Vazante", 3: "Maré Enchente", 4: "Maré Alta", 5: "Maré Cheia"}
TURMAS_CONFIG = {
    "SALA ROSA":     {"cor": C_ROSA,    "icon": "🌸"},
    "SALA AMARELA":  {"cor": C_AMARELO, "icon": "⭐"},
    "SALA VERDE":    {"cor": C_VERDE,   "icon": "🌿"},
    "SALA AZUL":     {"cor": C_AZUL,    "icon": "💧"},
    "CIRAND. MUNDO": {"cor": C_ROXO,    "icon": "🌍"},
}
BADGE_LABEL = {
    "SALA ROSA":     "ROSA",
    "SALA AMARELA":  "AMARELA",
    "SALA VERDE":    "VERDE",
    "SALA AZUL":     "AZUL",
    "CIRAND. MUNDO": "MUNDO",
}
CATEGORIAS = [
    "Atividades em grupo/Proatividade", "Interesse pelo novo", "Compartilhamento de Materiais",
    "Clareza e desenvoltura", "Respeito às regras", "Vocabulário adequado",
    "Leitura e Escrita", "Compreensão de comandos", "Superação de desafios", "Assiduidade"
]
EVIDENCIAS_POR_NIVEL = {
    "1. Pré-Silábico":          ["Diferencia letras de desenhos", "Escreve o nome sem apoio", "Acredita que nomes grandes têm muitas letras", "Sabe que se escreve da esquerda para a direita"],
    "2. Silábico s/ Valor":     ["Uma letra para cada sílaba (sem som)", "Segmenta a fala em partes", "Respeita quantidade de emissões sonoras", "Faz leitura global da palavra"],
    "3. Silábico c/ Valor":     ["Usa vogais correspondentes ao som", "Identifica o som inicial das palavras", "Leitura apontada (acompanha com o dedo)", "Escreve uma letra por sílaba com som correto"],
    "4. Silábico Alfabético":   ["Oscila entre uma letra e a sílaba completa", "Começa a usar consoantes nas sílabas", "Consegue completar lacunas de letras", "Percebe a estrutura da sílaba simples"],
    "5. Alfabético Inicial":    ["Compreende o sistema de escrita", "Erros ortográficos comuns (ex: K por C)", "Lê textos curtos com fluidez", "Segmentação de palavras irregular"],
    "6. Alfabético Final":      ["Diferencia sons semelhantes (P/B, T/D)", "Usa corretamente dígrafos (LH, NH, CH)", "Domina regras básicas de pontuação", "Produz textos com coesão"],
    "7. Alfabético Ortográfico":["Escrita autônoma e correta", "Domina acentuação e regras complexas", "Lê com entonação e fluidez total", "Revisa o próprio texto"],
}

conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600, show_spinner=False)
def ler_planilha(worksheet_name: str) -> pd.DataFrame:
    try:
        df = conn.read(worksheet=worksheet_name).fillna("")
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception as e:
        st.warning(f"Não foi possível carregar a aba '{worksheet_name}': {e}")
        return pd.DataFrame()

df_g    = ler_planilha("GERAL")
df_alf  = ler_planilha("TURNO_ESTENDIDO")
df_aval = ler_planilha("TABUA_MARE")

def get_gspread_client():
    from google.oauth2.service_account import Credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds = Credentials.from_service_account_info(st.secrets["connections"]["gsheets"], scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro nas credenciais: {e}")
        return None

def _upsert_csv(caminho, chaves, novo_registro):
    if os.path.exists(caminho):
        df = pd.read_csv(caminho).fillna("")
    else:
        df = pd.DataFrame(columns=list(novo_registro.keys()))
    for col in novo_registro:
        if col not in df.columns:
            df[col] = ""
    mask = pd.Series([True] * len(df))
    for k in chaves:
        mask = mask & (df[k].astype(str) == str(novo_registro[k]))
    if mask.any():
        for k, v in novo_registro.items():
            df.loc[mask, k] = v
    else:
        df = pd.concat([df, pd.DataFrame([novo_registro])], ignore_index=True)
    df.to_csv(caminho, index=False)


def salvar_dados_locais_te(aluno, sala, avaliacao_tipo, nivel, evidencias_str, obs, ano):
    MAP_ETAPA_COL = {
        "1ª Avaliação":    "1ª AVALIAÇÃO",
        "2ª Avaliação":    "2ª AVALIAÇÃO",
        "Avaliação Final": "AVALIAÇÃO FINAL",
    }
    col_destino = MAP_ETAPA_COL.get(avaliacao_tipo)
    if not col_destino:
        return

    if os.path.exists(ARQUIVO_DADOS_TE):
        df = pd.read_csv(ARQUIVO_DADOS_TE).fillna("")
    else:
        df = pd.DataFrame(columns=["ALUNO", "SALA", "ANO",
                                    "1ª AVALIAÇÃO", "2ª AVALIAÇÃO", "AVALIAÇÃO FINAL",
                                    "DIAGNÓSTICO", "EVIDÊNCIAS", "OBSERVAÇÕES"])

    for col in ["ALUNO", "SALA", "ANO", "1ª AVALIAÇÃO", "2ª AVALIAÇÃO",
                "AVALIAÇÃO FINAL", "DIAGNÓSTICO", "EVIDÊNCIAS", "OBSERVAÇÕES"]:
        if col not in df.columns:
            df[col] = ""

    mask = (
        (df["ALUNO"].astype(str).str.strip() == str(aluno).strip()) &
        (df["ANO"].astype(str).str.strip() == str(ano).strip())
    )

    if mask.any():
        idx = df.index[mask][0]
        df.at[idx, col_destino] = nivel
        df.at[idx, "SALA"] = sala
        df.at[idx, "DIAGNÓSTICO"] = nivel
        if evidencias_str:
            df.at[idx, "EVIDÊNCIAS"] = evidencias_str
        if obs:
            df.at[idx, "OBSERVAÇÕES"] = obs
    else:
        nova = {
            "ALUNO": aluno, "SALA": sala, "ANO": str(ano),
            "1ª AVALIAÇÃO": "", "2ª AVALIAÇÃO": "", "AVALIAÇÃO FINAL": "",
            "DIAGNÓSTICO": nivel,
            "EVIDÊNCIAS": evidencias_str, "OBSERVAÇÕES": obs,
        }
        nova[col_destino] = nivel
        df = pd.concat([df, pd.DataFrame([nova])], ignore_index=True)

    df.to_csv(ARQUIVO_DADOS_TE, index=False)


def salvar_buffer_local(aluno, sala, avaliacao_tipo, nivel, evidencias_list, obs, ano):
    hoje = datetime.now().strftime("%d/%m/%Y")
    evid_str = ", ".join(evidencias_list) if evidencias_list else ""
    novo_buf = {
        "ALUNO": aluno, "SALA": sala, "ETAPA": avaliacao_tipo,
        "NIVEL": nivel, "EVIDENCIAS": evid_str, "OBS": obs,
        "ANO": str(ano), "DATA": hoje,
    }
    _upsert_csv(ARQUIVO_BUFFER, ["ALUNO", "ANO", "ETAPA"], novo_buf)
    salvar_dados_locais_te(aluno, sala, avaliacao_tipo, nivel, evid_str, obs, ano)
    return True


def enviar_buffer_para_sheets():
    if not os.path.exists(ARQUIVO_BUFFER):
        st.info("Não há registros pendentes para sincronizar.")
        return
    df_pendente = pd.read_csv(ARQUIVO_BUFFER)
    if df_pendente.empty:
        st.info("Fila de registros está vazia.")
        return
    client = get_gspread_client()
    if client is None:
        return
    sh  = client.open_by_key(ID_PLANILHA)
    wks = sh.worksheet("TURNO_ESTENDIDO")
    col_map = {"1ª Avaliação": "C", "2ª Avaliação": "D", "Avaliação Final": "E"}
    sucessos = 0
    for _, row in df_pendente.iterrows():
        try:
            dados = wks.get_all_records()
            df_temp = pd.DataFrame(dados)
            linha_encontrada = -1
            if not df_temp.empty:
                df_temp.columns = [str(c).strip().upper() for c in df_temp.columns]
                filtro_vazio = (
                    (df_temp["ALUNO"].astype(str).str.strip() == str(row["ALUNO"]).strip()) &
                    (df_temp["ANO"].astype(str).str.strip() == "")
                )
                indices_vazios = df_temp.index[filtro_vazio].tolist()
                if indices_vazios:
                    linha_encontrada = indices_vazios[0] + 2
                else:
                    filtro_ano = (
                        (df_temp["ALUNO"].astype(str).str.strip() == str(row["ALUNO"]).strip()) &
                        (df_temp["ANO"].astype(str).str.strip() == str(row["ANO"]).strip())
                    )
                    indices_ano = df_temp.index[filtro_ano].tolist()
                    if indices_ano:
                        linha_encontrada = indices_ano[0] + 2
            etapa = str(row["ETAPA"])
            nivel = str(row["NIVEL"])
            evid  = str(row.get("EVIDENCIAS", ""))
            obs   = str(row.get("OBS", ""))
            ano   = str(row["ANO"])
            if linha_encontrada != -1:
                letra_col = col_map.get(etapa, "C")
                wks.update(range_name=f"F{linha_encontrada}", values=[[ano]])
                wks.update(range_name=f"{letra_col}{linha_encontrada}", values=[[nivel]])
                wks.update(range_name=f"G{linha_encontrada}", values=[[nivel]])
                if obs:
                    wks.update(range_name=f"I{linha_encontrada}", values=[[obs]])
                if evid:
                    wks.update(range_name=f"H{linha_encontrada}", values=[[evid]])
            else:
                nova_linha = [row["ALUNO"], row["SALA"], "", "", "", ano, "", evid, obs, str(row.get("DATA", ""))]
                idx_etapa = {"1ª Avaliação": 2, "2ª Avaliação": 3, "Avaliação Final": 4}.get(etapa, 2)
                nova_linha[idx_etapa] = nivel
                nova_linha[6] = nivel
                wks.append_row(nova_linha)
            sucessos += 1
        except Exception as e:
            st.warning(f"Falha ao sincronizar {row['ALUNO']}: {e}")
    if sucessos == len(df_pendente):
        st.success(f"🎉 {sucessos} registro(s) enviado(s) com sucesso!")
        os.remove(ARQUIVO_BUFFER)
        st.cache_data.clear()
        st.rerun()
    else:
        st.warning(f"⚠️ {sucessos}/{len(df_pendente)} registros sincronizados. Verifique os avisos acima.")


def registrar_matricula_te(aluno, sala):
    salvar_buffer_local(aluno=aluno, sala=sala, avaliacao_tipo="MATRÍCULA",
                        nivel="", evidencias_list=[], obs="", ano="")
    try:
        client = get_gspread_client()
        if client:
            sh  = client.open_by_key(ID_PLANILHA)
            wks = sh.worksheet("TURNO_ESTENDIDO")
            hoje = datetime.now().strftime("%d/%m/%Y")
            wks.append_row([aluno, sala, "", "", "", "", "", "", "", hoje])
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao matricular: {e}")
        return False


def registrar_tabua_mare(aluno, sala, semestre, notas_dict, obs):
    try:
        df_atual = ler_planilha("TABUA_MARE").copy()
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


def atualizar_padrinho_sheets(sala, aluno, nome_padrinho):
    try:
        client = get_gspread_client()
        if client is None:
            return False
        sh  = client.open_by_key(ID_PLANILHA)
        wks = sh.worksheet(sala)
        dados = wks.get_all_records()
        df_temp = pd.DataFrame(dados)
        df_temp.columns = [str(c).strip().upper() for c in df_temp.columns]
        if "PADRINHO/MADRINHA" not in df_temp.columns or "ALUNO" not in df_temp.columns:
            st.error("Colunas necessárias não encontradas.")
            return False
        indices = df_temp.index[df_temp["ALUNO"].astype(str).str.strip() == str(aluno).strip()].tolist()
        if not indices:
            st.error("Aluno não encontrado na aba.")
            return False
        linha = indices[0] + 2
        col_idx = list(df_temp.columns).index("PADRINHO/MADRINHA") + 1
        wks.update_cell(linha, col_idx, nome_padrinho)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar padrinho: {e}")
        return False


def get_text_color(nivel=None):
    return "#2C3E50"


def obter_ultimo_diagnostico(aluno_sel, df_logica, col_aluno, col_diag):
    ultimo_nv = "Sem registro"
    if col_aluno:
        df_al = df_logica[df_logica[col_aluno].astype(str).str.strip() == aluno_sel]
        if not df_al.empty:
            for c_av in ["AVALIAÇÃO FINAL", "2ª AVALIAÇÃO", "1ª AVALIAÇÃO"]:
                if c_av in df_al.columns:
                    val = str(df_al[c_av].iloc[-1]).strip()
                    if val and val not in ["nan", "None", ""]:
                        ultimo_nv = val
                        break
            if ultimo_nv == "Sem registro" and col_diag and col_diag in df_al.columns:
                val = str(df_al[col_diag].iloc[-1]).strip()
                if val and val not in ["nan", "None", ""]:
                    ultimo_nv = val

    if os.path.exists(ARQUIVO_BUFFER):
        df_buf_local = pd.read_csv(ARQUIVO_BUFFER)
        buf_aluno = df_buf_local[df_buf_local["ALUNO"].astype(str).str.strip() == aluno_sel]
        if not buf_aluno.empty and "NIVEL" in buf_aluno.columns:
            ultimo_nv_buf = str(buf_aluno["NIVEL"].iloc[-1]).strip()
            if ultimo_nv_buf and ultimo_nv_buf not in ["nan", "None", ""]:
                ultimo_nv = ultimo_nv_buf

    if os.path.exists(ARQUIVO_DADOS_TE):
        df_dados = pd.read_csv(ARQUIVO_DADOS_TE).fillna("")
        mask = df_dados["ALUNO"].astype(str).str.strip() == aluno_sel
        if mask.any():
            row = df_dados[mask].iloc[-1]
            for c_av in ["AVALIAÇÃO FINAL", "2ª AVALIAÇÃO", "1ª AVALIAÇÃO", "DIAGNÓSTICO"]:
                if c_av in df_dados.columns:
                    val = str(row.get(c_av, "")).strip()
                    if val and val not in ["nan", "None", ""]:
                        ultimo_nv = val
                        break

    return ultimo_nv


def render_legenda_niveis_botoes(aluno_sel, key_prefix="te"):
    st.markdown("##### 📝 Selecione o Nível de Diagnóstico")

    session_key = f"nivel_diag_{key_prefix}_{aluno_sel}"

    cols_leg = st.columns(len(NIVEIS_ALF))
    for i, nv in enumerate(NIVEIS_ALF):
        cor_fundo = CORES_EXCLUSIVAS.get(nv, "#eee")
        cor_txt = get_text_color(nv)
        is_selected = st.session_state.get(session_key) == nv
        borda = "3px solid #000000" if is_selected else "2px solid transparent"
        cols_leg[i].markdown(
            f'<div style="background-color:{cor_fundo}; color:{cor_txt}; padding:8px 2px; border-radius:10px; '
            f'text-align:center; font-size:10px; font-weight:bold; min-height:50px; display:flex; '
            f'align-items:center; justify-content:center; line-height:1.1; border:{borda}; cursor:pointer;">'
            f'{nv.split(". ")[1]}</div>',
            unsafe_allow_html=True
        )
        if cols_leg[i].button("Selecionar", key=f"btn_nivel_{key_prefix}_{i}", use_container_width=True):
            st.session_state[session_key] = nv
            st.rerun()

    nivel_selecionado = st.session_state.get(session_key, None)
    if nivel_selecionado:
        cor_sel = CORES_EXCLUSIVAS.get(nivel_selecionado, "#eee")
        st.markdown(
            f'<div style="background:{cor_sel}; padding:10px 20px; border-radius:10px; margin:10px 0; '
            f'font-weight:bold; font-size:14px; color:#2C3E50; border:2px solid #000;">'
            f'Nível de Diagnóstico: {nivel_selecionado}</div>',
            unsafe_allow_html=True
        )

    return nivel_selecionado


def render_legenda_niveis():
    st.markdown("##### 📝 Legenda de Níveis")
    st.write("<small>Clique no nível para filtrar a visualização:</small>", unsafe_allow_html=True)
    
    cols_leg = st.columns(len(NIVEIS_ALF))
    
    for i, nv in enumerate(NIVEIS_ALF):
        cor_fundo = CORES_EXCLUSIVAS.get(nv, "#eee")
        cor_txt = get_text_color(nv)
        nome_nivel = nv.split(". ")[1]
        
        # O botão agora carrega o nome do nível e a funcionalidade
        # Usamos uma chave (key) única para evitar conflitos
        if cols_leg[i].button(nome_nivel, key=f"filter_nv_{i}", use_container_width=True):
            st.session_state.nivel_selecionado = nv
            # Se você tiver uma lógica de filtro global, ela será disparada aqui
            st.rerun()

        # Injetamos o CSS para que este botão específico tenha a cor da legenda
        st.markdown(f"""
            <style>
            /* Alvos específicos para os botões desta legenda */
            div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{
                background-color: {cor_fundo} !important;
                color: {cor_txt} !important;
                height: 60px !important;
                font-size: 10px !important;
                font-weight: bold !important;
                border-radius: 10px !important;
                border: 1px solid rgba(0,0,0,0.1) !important;
                line-height: 1.1 !important;
                padding: 2px !important;
            }}
            /* Efeito de hover para indicar que é clicável */
            div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button:hover {{
                border: 2px solid #555 !important;
                opacity: 0.9;
            }}
            </style>
        """, unsafe_allow_html=True)


def render_vasilha_mare(nivel_num, titulo):
    config = {
        1: {"pct": 85, "txt": "Maré Baixa",    "seta": ""},
        2: {"pct": 70, "txt": "Maré Vazante",   "seta": "↓"},
        3: {"pct": 45, "txt": "Maré Enchente",  "seta": "↑"},
        4: {"pct": 15, "txt": "Maré Cheia",     "seta": "↑"},
    }
    try:
        n = max(1, min(4, int(float(nivel_num))))
    except Exception:
        n = 1
    c = config[n]
    return f'''
    <div style="text-align:center;margin-bottom:20px;border:1px solid #eee;padding:10px;border-radius:10px;background:#fff;">
        <div style="font-size:11px;font-weight:bold;color:#333;min-height:35px;display:flex;align-items:center;justify-content:center;line-height:1.2;">{titulo}</div>
        <div style="width:70px;height:45px;margin:5px auto;background:linear-gradient(to bottom,#f0f0f0 {c["pct"]}%,#5DADE2 {c["pct"]}%);
                    clip-path:path('M 0 10 Q 17.5 0 35 10 T 70 10 L 70 40 Q 70 45 65 45 L 5 45 Q 0 45 0 40 Z');border:1px solid #ddd;position:relative;">
            <span style="position:absolute;right:2px;top:5px;font-size:12px;font-weight:bold;color:#2E86C1;">{c["seta"]}</span>
        </div>
        <div style="font-size:9px;color:#5DADE2;font-weight:bold;text-transform:uppercase;margin-top:5px;">{c["txt"]}</div>
    </div>'''


def render_grafico_alfabetizacao_individual(df_aluno):
    if df_aluno.empty:
        st.info("Sem dados de evolução.")
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_aluno["Avaliacao"].str.replace("Avaliação Final", "3ª Aval") + "/" + df_aluno["Ano"].astype(str),
        y=[MAPA_NIVEIS.get(n, 0) for n in df_aluno["Nivel"]],
        fill="tozeroy", mode="lines+markers",
        line=dict(color="#6741d9", width=3),
        marker=dict(size=10, color="#6741d9"),
    ))
    fig.update_layout(
        height=280, margin=dict(l=0, r=10, t=20, b=0),
        yaxis=dict(range=[0.5, 7.5], tickmode="array", tickvals=list(range(1, 8)),
                   ticktext=[n.split(". ")[1] for n in NIVEIS_ALF], gridcolor="#eee"),
        xaxis=dict(gridcolor="#eee"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(size=10),
    )
    st.plotly_chart(fig, use_container_width=True)


def criar_grafico_mare(categorias, valores):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=valores, theta=categorias, fill="toself",
        text=[MARE_LABELS.get(int(v), "Nível Indefinido") for v in valores],
        hoverinfo="text+theta", line=dict(color="#2E86C1"),
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=False, margin=dict(l=40, r=40, t=20, b=20), height=350,
    )
    return fig


def render_filtros(df_geral, key_suffix):
    f1, f2 = st.columns(2)
    tn = f1.selectbox("Filtrar Turno", ["Todos", "A", "B"], key=f"tn_{key_suffix}")
    if "COMUNIDADE" in df_geral.columns:
        comu_list = ["Todas"] + sorted([c for c in df_geral["COMUNIDADE"].unique() if str(c).strip()])
    else:
        comu_list = ["Todas"]
    cm = f2.selectbox("Filtrar Comunidade", comu_list, key=f"cm_{key_suffix}")
    return tn, cm


def aplicar_filtros(df_alvo, df_geral, tn, cm):
    df_f = df_alvo.copy()
    df_f.columns = [str(c).strip().upper() for c in df_f.columns]
    if tn != "Todos":
        alunos_no_turno = df_geral[df_geral["TURNO"].astype(str).str.contains(tn, na=False)]["ALUNO"].unique()
        df_f = df_f[df_f["ALUNO"].isin(alunos_no_turno)]
    if cm != "Todas":
        if "COMUNIDADE" in df_f.columns:
            df_f = df_f[df_f["COMUNIDADE"] == cm]
        else:
            alunos_na_comu = df_geral[df_geral["COMUNIDADE"] == cm]["ALUNO"].unique()
            df_f = df_f[df_f["ALUNO"].isin(alunos_na_comu)]
    return df_f


def render_botoes_salas(key_prefix, session_key, salas_permitidas=None):
    salas = salas_permitidas if salas_permitidas else list(TURMAS_CONFIG.keys())
    cols = st.columns(len(salas))
    
    for i, nome_aba in enumerate(salas):
        cfg = TURMAS_CONFIG.get(nome_aba, {"cor": "#566573", "icon": "🏫"})
        label_exibicao = BADGE_LABEL.get(nome_aba, nome_aba.replace("SALA ", ""))
        
        is_active = st.session_state.get(session_key) == nome_aba
        
        # Estilização baseada no estado ativo
        cor_fundo = cfg["cor"]
        borda = "3px solid #000" if is_active else "1px solid rgba(0,0,0,0.2)"
        opacidade = "1.0" if is_active else "0.7"

        # 1. CRIAMOS APENAS O BOTÃO (sem o markdown de div antes)
        if cols[i].button(label_exibicao, key=f"{key_prefix}_{i}", use_container_width=True):
            st.session_state[session_key] = nome_aba
            st.rerun()

        # 2. INJETAMOS O CSS PARA COLORIR O BOTÃO
        st.markdown(f"""
            <style>
            div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button {{
                background-color: {cor_fundo} !important;
                color: white !important;
                height: 55px !important;
                font-weight: bold !important;
                border-radius: 10px !important;
                border: {borda} !important;
                opacity: {opacidade} !important;
                transition: 0.3s;
            }}
            div[data-testid="stHorizontalBlock"] > div:nth-child({i+1}) button:hover {{
                opacity: 1.0 !important;
                border: 3px solid #000 !important;
            }}
            </style>
        """, unsafe_allow_html=True)


st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
.stApp {{ background-color: #ffffff; font-family: 'Inter', sans-serif; }}
.main-header {{ text-align: center; padding: 20px 0; }}
.main-header h1 {{ font-size: 42px !important; font-weight: 800; }}
.custom-table {{ width: 100%; border-collapse: separate; border-spacing: 0;
    border: 1px solid #f0f0f0; border-radius: 10px; overflow: hidden;
    font-size: 13px; margin-top: 5px; margin-bottom: 15px; }}
.custom-table thead th {{ padding: 12px 10px; text-align: left; color: white !important; font-weight: 700; border: none; }}
.custom-table td {{ padding: 10px; border-bottom: 1px solid #f9f9f9; }}
div.stButton > button {{ width: 100%; border-radius: 8px !important; font-weight: 700 !important;
    height: 42px; font-size: 11px !important; border: none !important; transition: all 0.3s; }}
.sala-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px;
    color: white; font-weight: 700; font-size: 10px; margin-top: 5px; text-transform: uppercase; }}
.trilha-container {{ display: flex; align-items: center; justify-content: space-between; width: 100%; padding: 10px 0; }}
.caixa-trilha {{ flex: 1; height: 85px; border-radius: 15px; display: flex; align-items: center;
    justify-content: center; text-align: center; font-size: 10px; font-weight: 800; padding: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 2px solid transparent; line-height: 1.2; }}
.seta-trilha {{ padding: 0 5px; color: #ccc; font-size: 18px; font-weight: bold; }}
.mare-box {{ display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; padding: 2px; }}
.mare-mini-tabela {{ width: 35px; height: 20px; border: 1px solid #999; border-radius: 3px; }}
.mare-texto-tabela {{ font-size: 10px; color: #555; font-weight: bold; line-height: 1; text-transform: lowercase; }}
thead tr th, th {{ color: #000000 !important; -webkit-text-fill-color: #000000 !important;
    font-weight: bold !important; background-color: #f8f9fa !important; text-align: center !important; }}
</style>""", unsafe_allow_html=True)

if "logado" not in st.session_state:
    st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
if "alunos_te_dict" not in st.session_state:
    st.session_state["alunos_te_dict"] = {}

for k in ["sel_mat", "sel_pad", "sel_aval", "sel_int", "sel_alf", "sel_ind", "sel_te"]:
    if k not in st.session_state:
        st.session_state[k] = "SALA ROSA"

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
                        df_s = ler_planilha(sala)
                        if not df_s.empty and "PADRINHO/MADRINHA" in df_s.columns:
                            if u in df_s["PADRINHO/MADRINHA"].astype(str).str.strip().str.upper().unique():
                                encontrado = True
                                break
                    if encontrado:
                        st.session_state.update({"logado": True, "perfil": "padrinho", "nome_usuario": u})
                        st.rerun()
                    else:
                        st.error("Acesso negado.")
    st.stop()

if st.sidebar.button("🚪 Sair"):
    st.session_state.update({"logado": False, "perfil": None, "nome_usuario": ""})
    st.rerun()

menu_options = [
    "📝 Controle de Matrícula e Apadrinhamento",
    "📊 Dados - Turno Estendido",
    "📊 Avaliação da Tábua da Maré",
    "📖 Turno Estendido",
    "📈 Indicadores pedagógicos",
    "🌊 Canal do Apadrinhamento",
    "🌊 Tábua da Maré",
]
if st.session_state.perfil != "admin":
    menu_options = ["🌊 Canal do Apadrinhamento"]
menu = st.sidebar.radio("Navegação", menu_options)

st.markdown(
    f"<div class='main-header'><h1>"
    f"<span style='color:{C_VERDE}'>Instituto</span> "
    f"<span style='color:{C_AZUL}'>Mãe</span> "
    f"<span style='color:{C_VERDE}'>Lalu</span>"
    f"</h1></div><hr>",
    unsafe_allow_html=True,
)

if menu == "📝 Controle de Matrícula e Apadrinhamento":
    st.markdown("### 📝 Controle de Matrícula e Apadrinhamento")
    st.markdown("*Canal de controle e registro dos alunos matriculados e do Programa de Apadrinhamento.*")

    cor_rosa, cor_amarela, cor_verde, cor_azul = "#F783AC", "#FFE066", "#A9E34B", "#99E9F2"

    df_geral = df_g.copy()
    lista_alunos_geral = sorted(df_geral["ALUNO"].unique().tolist()) if not df_geral.empty else []

    df_te_check = df_alf.copy()
    set_matriculados_te = set(df_te_check["ALUNO"].unique().tolist()) if not df_te_check.empty else set()

    st.markdown(f"""
        <style>
        div[data-testid="stPopover"] > button {{
            background-color: white !important; border-radius: 8px; height: 3.2rem; transition: 0.3s;
        }}
        div[key="mat_popover"] > button {{ color: {cor_rosa} !important; border: 2px solid {cor_rosa} !important; }}
        div[key="pad_popover"] > button {{ color: {cor_amarela} !important; border: 2px solid {cor_amarela} !important; }}
        div[key="est_popover"] > button {{ color: {cor_verde} !important; border: 2px solid {cor_verde} !important; }}
        div[key="del_popover"] > button {{ color: {cor_azul} !important; border: 2px solid {cor_azul} !important; }}
        div[data-testid="stPopover"] button p {{ font-weight: 800 !important; }}
        </style>""", unsafe_allow_html=True)

    gestao_col1, gestao_col2, gestao_col3, gestao_col4 = st.columns([1, 2.2, 1.3, 0.9])

    with gestao_col1:
        with st.popover("➕ Matrícula", key="mat_popover", use_container_width=True):
            st.markdown("##### 📝 Nova Matrícula")
            n_nome = st.text_input("Nome do Aluno", key="reg_nome")
            n_sala = st.selectbox("Sala Destino", list(TURMAS_CONFIG.keys()), key="reg_sala")
            if st.button("Salvar Novo Aluno"):
                st.success("Aluno registrado!")

    with gestao_col2:
        with st.popover("🤝 Padrinho/Madrinha", key="pad_popover", use_container_width=True):
            st.markdown("##### 🤝 Novo Apadrinhamento")
            s_busca_p = st.selectbox("Selecione a Sala:", list(TURMAS_CONFIG.keys()), key="pad_sala_select")
            df_b = ler_planilha(s_busca_p)
            if "PADRINHO/MADRINHA" in df_b.columns:
                lista_lib = sorted(df_b[df_b["PADRINHO/MADRINHA"].astype(str).isin(["", "-", "nan", "0"])]["ALUNO"].unique())
                al_sel = st.selectbox("Escolha o Afilhado:", lista_lib)
                nome_p = st.text_input("Nome do Padrinho")
                if st.button("Confirmar Apadrinhamento"):
                    if nome_p.strip():
                        ok = atualizar_padrinho_sheets(s_busca_p, al_sel, nome_p.strip())
                        if ok:
                            st.success("Apadrinhamento registrado!")
                            st.rerun()
                    else:
                        st.warning("Informe o nome do padrinho/madrinha.")

    with gestao_col3:
        with st.popover("⏳ Turno Estendido", key="est_popover", use_container_width=True):
            st.markdown("##### ⏳ Matricular no Turno Estendido")
            lista_disponivel_te = [a for a in lista_alunos_geral if a not in set_matriculados_te]
            if lista_disponivel_te:
                al_mat = st.selectbox("Selecione o Aluno:", lista_disponivel_te, key="sel_aluno_matricula_te")
                if st.button("✅ Confirmar Matrícula", key="btn_confirmar_te"):
                    info_aluno = df_geral[df_geral["ALUNO"] == al_mat]
                    if not info_aluno.empty:
                        col_sala = "SALA" if "SALA" in df_geral.columns else "TURMA"
                        sala_origem = info_aluno[col_sala].values[0] if col_sala in info_aluno.columns else "NÃO DEFINIDA"
                        sucesso = registrar_matricula_te(aluno=al_mat, sala=sala_origem)
                        if sucesso:
                            st.success(f"✅ {al_mat} matriculado!")
                            st.rerun()
            else:
                st.info("Todos os alunos já estão matriculados no Turno Estendido.")

    with gestao_col4:
        with st.popover("🗑️ Remover", key="del_popover", use_container_width=True):
            st.radio("Remover:", ["Aluno", "Padrinho"])
            st.button("🚨 EXCLUIR")

    st.divider()

    render_botoes_salas("btn_pad", "sel_pad")
    sala_v = st.session_state.get("sel_pad", "SALA ROSA")
    cfg_sala = TURMAS_CONFIG.get(sala_v, {"cor": "#333", "icon": "🏫"})
    cor_h = cfg_sala["cor"]

    df_s = ler_planilha(sala_v)
    if not df_s.empty:
        tn, cm = render_filtros(df_geral, "pad")
        df_f = df_s.copy()
        if tn != "Todos" and "TURMA" in df_f.columns:
            df_f = df_f[df_f["TURMA"] == tn]
        if cm != "Todas" and "COMUNIDADE" in df_f.columns:
            df_f = df_f[df_f["COMUNIDADE"] == cm]

        st.markdown(f"""
            <div style="background-color:{cor_h}22;padding:10px;border-radius:5px;border-left:5px solid {cor_h};
                        margin:20px 0;display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:13px;color:#333;">{cfg_sala["icon"]} Atualmente: <b>{len(df_f)}</b> alunos na <b>{sala_v}</b></span>
                <span style="font-size:11px;background-color:{C_VERDE}44;padding:2px 8px;border-radius:10px;
                             border:1px solid {C_VERDE};color:#2b5e2b;"><b>📖</b> = Turno Estendido</span>
            </div>""", unsafe_allow_html=True)

        v_cols = ["ALUNO", "TURMA", "IDADE", "COMUNIDADE", "PADRINHO/MADRINHA"]
        table_html = f'<table style="width:100%;border-collapse:collapse;font-family:sans-serif;font-size:11px;border:1px solid #ddd;">'
        table_html += f'<thead style="background-color:{cor_h};color:white;text-align:left;"><tr>'
        for col in v_cols:
            table_html += f'<th style="padding:6px;border:1px solid #ddd;">{col}</th>'
        table_html += "</tr></thead><tbody>"

        for i, (_, r) in enumerate(df_f.iterrows()):
            bg = "#ffffff" if i % 2 == 0 else "#f9f9f9"
            p_nome = str(r.get("PADRINHO/MADRINHA", "-")).strip()
            if p_nome in ["", "0", "nan", "None", "-"]:
                p_nome = "-"
            nome_aluno = r.get("ALUNO", "-")
            marcador_te = " <span title='Turno Estendido' style='color:#2b5e2b;'>📖</span>" if nome_aluno in set_matriculados_te else ""
            table_html += f'<tr style="background-color:{bg};color:#333;">'
            table_html += f'<td style="padding:6px;border:1px solid #eee;font-weight:bold;">{nome_aluno}{marcador_te}</td>'
            table_html += f'<td style="padding:6px;border:1px solid #eee;text-align:center;">{r.get("TURMA","-")}</td>'
            table_html += f'<td style="padding:6px;border:1px solid #eee;text-align:center;">{r.get("IDADE","-")}</td>'
            table_html += f'<td style="padding:6px;border:1px solid #eee;">{r.get("COMUNIDADE","-")}</td>'
            table_html += f'<td style="padding:6px;border:1px solid #eee;font-weight:600;">{p_nome}</td>'
            table_html += "</tr>"

        st.markdown(table_html + "</tbody></table>", unsafe_allow_html=True)
    else:
        st.info(f"A {sala_v} ainda não possui alunos matriculados.")

elif menu == "📊 Avaliação da Tábua da Maré":
    st.markdown(f"### 📊 Lançar Avaliação (Google Sheets)")

    df_av = df_aval.copy()
    df_av.columns = [str(c).strip().title() for c in df_av.columns]

    render_botoes_salas("btn_aval", "sel_aval")
    sala_atual = st.session_state.sel_aval

    dict_te = st.session_state.get("alunos_te_dict", {})
    alunos_na_sala = [n for n, s in dict_te.items() if str(s).strip().upper() == str(sala_atual).strip().upper()]

    if not alunos_na_sala:
        df_sala = ler_planilha(sala_atual)
        if not df_sala.empty and "ALUNO" in df_sala.columns:
            alunos_na_sala = sorted(df_sala["ALUNO"].unique().tolist())

    if alunos_na_sala:
        al = st.selectbox("Selecione o Aluno", sorted(alunos_na_sala))
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
                val_anterior = "Maré Enchente"
                if dados_anteriores is not None:
                    for col_av in dados_anteriores.index:
                        if col_av.strip().lower() == cat.strip().lower():
                            val_anterior = dados_anteriores[col_av]
                            break
                try:
                    idx_default = int(val_anterior) - 1 if str(val_anterior).isdigit() else opcoes.index(val_anterior)
                except Exception:
                    idx_default = 2
                n_l[cat] = (cE if i < 5 else cD).selectbox(cat, opcoes, index=idx_default, key=f"mare_s_{i}")

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
                        st.rerun()
                else:
                    st.error("Por favor, selecione um aluno.")
    else:
        st.warning(f"Nenhum aluno encontrado na {sala_atual}.")

elif menu == "📖 Turno Estendido":
    st.markdown(f"<h3 style='color:{C_ROXO}'>📖 Turno Estendido</h3>", unsafe_allow_html=True)
    st.info("ℹ️ As avaliações registradas aqui são salvas localmente. Acesse **Dados - Turno Estendido** para enviar ao Google Sheets.")

    df_logica = df_alf.copy()

    col_diag  = next((c for c in ["NIVEL", "DIAGNÓSTICO", "NÍVEL", "DIAGNOSTICO"] if c in df_logica.columns), None)
    col_aluno = "ALUNO" if "ALUNO" in df_logica.columns else None
    col_sala  = "SALA" if "SALA" in df_logica.columns else None

    if not df_logica.empty and col_aluno and col_sala:
        dict_alunos_geral = {
            str(row[col_aluno]).strip(): str(row[col_sala]).strip().upper()
            for _, row in df_logica.iterrows() if str(row[col_aluno]).strip()
        }
        st.session_state["alunos_te_dict"] = dict_alunos_geral
    else:
        dict_alunos_geral = {}

    if os.path.exists(ARQUIVO_BUFFER):
        df_buf = pd.read_csv(ARQUIVO_BUFFER)
        for _, row in df_buf.iterrows():
            nome = str(row.get("ALUNO", "")).strip()
            sala = str(row.get("SALA", "")).strip().upper()
            if nome and nome not in dict_alunos_geral:
                dict_alunos_geral[nome] = sala

    st.write("### 🔍 Localizar Aluno")

    salas_disponiveis = sorted(set(dict_alunos_geral.values()))
    salas_com_todas = ["TODAS"] + salas_disponiveis

    if "filtro_sala_te" not in st.session_state:
        st.session_state["filtro_sala_te"] = "TODAS"

    st.markdown("**Filtrar por Sala:**")
    cols_filtro = st.columns(len(salas_com_todas))
    for i, sala_f in enumerate(salas_com_todas):
        if sala_f == "TODAS":
            cor_badge_f = "#888"
            txt_badge_f = "TODAS"
        else:
            cfg_f = TURMAS_CONFIG.get(sala_f, {"cor": "#888"})
            cor_badge_f = cfg_f.get("cor", "#888")
            txt_badge_f = BADGE_LABEL.get(sala_f, sala_f.replace("SALA ", ""))

        is_active_f = st.session_state.get("filtro_sala_te") == sala_f
        borda_f = "3px solid #000" if is_active_f else "2px solid transparent"
        op_f = "1.0" if is_active_f else "0.5"

        cols_filtro[i].markdown(
            f'<div style="background-color:{cor_badge_f}; color:white; padding:6px 10px; border-radius:20px; '
            f'text-align:center; font-size:11px; font-weight:bold; opacity:{op_f}; border:{borda_f}; '
            f'margin-bottom:2px; white-space:nowrap;">'
            f'{txt_badge_f}</div>',
            unsafe_allow_html=True
        )
        if cols_filtro[i].button(txt_badge_f, key=f"filtro_sala_te_{i}", use_container_width=True):
            st.session_state["filtro_sala_te"] = sala_f
            st.rerun()

    sala_filtro_sel = st.session_state.get("filtro_sala_te", "TODAS")

    if sala_filtro_sel != "TODAS":
        dict_alunos_filtrado = {n: s for n, s in dict_alunos_geral.items() if s == sala_filtro_sel}
    else:
        dict_alunos_filtrado = dict_alunos_geral

    lista_nomes_completa = sorted(list(dict_alunos_filtrado.keys()))
    busca_nome = st.text_input("Digite o nome para buscar:", placeholder="Ex: João Silva...").strip().upper()
    lista_filtrada = [n for n in lista_nomes_completa if busca_nome in n.upper()] if busca_nome else lista_nomes_completa

    if lista_filtrada:
        aluno_sel = st.selectbox("Selecione o Aluno:", lista_filtrada)
        sala_raw = dict_alunos_geral.get(aluno_sel, "NÃO DEFINIDA")

        cor_pilula = C_ROXO
        if "AZUL" in sala_raw:       cor_pilula = C_AZUL
        elif "VERDE" in sala_raw:    cor_pilula = C_VERDE
        elif "ROSA" in sala_raw:     cor_pilula = C_ROSA
        elif "AMARELA" in sala_raw or "AMARELO" in sala_raw: cor_pilula = C_AMARELO

        st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:25px;background:#f8f9fa;
                        padding:10px;border-radius:12px;border-left:5px solid {cor_pilula};">
                <span style="font-weight:bold;font-size:15px;color:#444;">Sala de Origem:</span>
                <span style="background-color:{cor_pilula};color:white;padding:6px 18px;border-radius:50px;
                             font-weight:800;font-size:13px;">{sala_raw}</span>
            </div>""", unsafe_allow_html=True)

        st.divider()

        ultimo_nv = obter_ultimo_diagnostico(aluno_sel, df_logica, col_aluno, col_diag)

        st.markdown(f"Diagnóstico atual: <span class='sala-badge' style='background:{C_ROXO}'>{ultimo_nv}</span>", unsafe_allow_html=True)

        if f"nivel_diag_te_{aluno_sel}" not in st.session_state:
            if ultimo_nv in NIVEIS_ALF:
                st.session_state[f"nivel_diag_te_{aluno_sel}"] = ultimo_nv

        novo_nv = render_legenda_niveis_botoes(aluno_sel, key_prefix="te")

        if not novo_nv:
            novo_nv = ultimo_nv if ultimo_nv in NIVEIS_ALF else NIVEIS_ALF[0]

        st.write("### 📝 Critérios de Avaliação")

        with st.form("form_te_unificado_v3"):
            ano_form = st.selectbox("Ano Letivo da Avaliação:", [2026, 2025])
            etapa_av = st.selectbox("Etapa da Avaliação:", ["1ª Avaliação", "2ª Avaliação", "Avaliação Final"])
            st.divider()
            evs = EVIDENCIAS_POR_NIVEL.get(novo_nv, [])
            st.write(f"**Evidências observadas para {novo_nv}:**")
            cols_ev = st.columns(3)
            selecionadas = [ev for i, ev in enumerate(evs) if cols_ev[i % 3].checkbox(ev, key=f"ev_final_te_{i}")]
            obs_txt = st.text_area("Observações Adicionais:")

            if st.form_submit_button("💾 Salvar Avaliação Localmente"):
                ok = salvar_buffer_local(
                    aluno=aluno_sel, sala=sala_raw, avaliacao_tipo=etapa_av,
                    nivel=novo_nv, evidencias_list=selecionadas, obs=obs_txt, ano=int(ano_form)
                )
                if ok:
                    st.success(f"✅ Avaliação de {aluno_sel} salva! Vá em **Dados - Turno Estendido** para enviar ao Google Sheets.")
                    st.rerun()
    else:
        st.warning("Nenhum aluno encontrado.")

elif menu == "📊 Dados - Turno Estendido":
    st.markdown("### 📋 Panorama de Avaliações")

    tem_pendentes = os.path.exists(ARQUIVO_BUFFER) and not pd.read_csv(ARQUIVO_BUFFER).empty if os.path.exists(ARQUIVO_BUFFER) else False

    if tem_pendentes:
        df_pendente = pd.read_csv(ARQUIVO_BUFFER)
        qtd = len(df_pendente)
        col_sync1, col_sync2, col_sync3 = st.columns([1.5, 1, 3])
        col_sync1.warning(f"⏳ **{qtd} registro(s) local(is) não sincronizado(s)**")
        if col_sync2.button("📤 Enviar para Google Sheets", type="primary", use_container_width=True):
            with st.spinner("Enviando registros para a planilha oficial (incluindo evidências e observações)..."):
                enviar_buffer_para_sheets()
        if col_sync3.button("🗑️ Descartar registros locais", use_container_width=True):
            os.remove(ARQUIVO_BUFFER)
            st.rerun()
    else:
        st.success("✅ Tudo sincronizado com o Google Sheets.")

    st.divider()

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
        st.markdown(
            f"<style>div[data-testid='stHorizontalBlock'] div:nth-child({i+1}) button {{"
            f"background-color:{cor_btn} !important;color:{txt_cor} !important;"
            f"border:{'2px solid black' if is_active else '1px solid #ccc'} !important;}}</style>",
            unsafe_allow_html=True,
        )

    ano_sel = st.session_state.ano_ativo_te
    st.markdown(f"**Exibindo dados de: {ano_sel}**")

    render_legenda_niveis()

    COLUNAS_TE = ["ALUNO", "SALA", "ANO", "1ª AVALIAÇÃO", "2ª AVALIAÇÃO",
                  "AVALIAÇÃO FINAL", "DIAGNÓSTICO", "EVIDÊNCIAS", "OBSERVAÇÕES"]

    df_sheets = df_alf.copy()
    if "ANO" not in df_sheets.columns:
        df_sheets["ANO"] = "2025"
    for col in COLUNAS_TE:
        if col not in df_sheets.columns:
            df_sheets[col] = ""
    df_sheets["ANO"] = (
        pd.to_numeric(df_sheets["ANO"], errors="coerce")
        .fillna(0).astype(int).astype(str)
        .replace("0", "")
    )

    if os.path.exists(ARQUIVO_DADOS_TE):
        df_local = pd.read_csv(ARQUIVO_DADOS_TE).fillna("")
        df_local.columns = [str(c).strip().upper() for c in df_local.columns]
        for col in COLUNAS_TE:
            if col not in df_local.columns:
                df_local[col] = ""
        df_local["ANO"] = (
            pd.to_numeric(df_local["ANO"], errors="coerce")
            .fillna(0).astype(int).astype(str)
            .replace("0", "")
        )
    else:
        df_local = pd.DataFrame(columns=COLUNAS_TE)

    for _, row_loc in df_local.iterrows():
        aluno_loc = str(row_loc.get("ALUNO", "")).strip()
        ano_loc   = str(row_loc.get("ANO",   "")).strip()
        if not aluno_loc:
            continue
        mask = (
            (df_sheets["ALUNO"].astype(str).str.strip() == aluno_loc) &
            (df_sheets["ANO"].astype(str).str.strip()   == ano_loc)
        )
        if mask.any():
            idx = df_sheets.index[mask][0]
            for col in ["1ª AVALIAÇÃO", "2ª AVALIAÇÃO", "AVALIAÇÃO FINAL",
                        "DIAGNÓSTICO", "EVIDÊNCIAS", "OBSERVAÇÕES", "SALA"]:
                val_loc = str(row_loc.get(col, "")).strip()
                if val_loc:
                    df_sheets.at[idx, col] = val_loc
        else:
            df_sheets = pd.concat([df_sheets, pd.DataFrame([row_loc])], ignore_index=True)

    df_h = df_sheets.copy()

    if "ANO" in df_h.columns:
        df_h["ANO"] = (
            pd.to_numeric(df_h["ANO"], errors="coerce")
            .fillna(0).astype(int).astype(str)
            .replace("0", "")
        )

    def get_status_mare_html(nv_atual, hist):
        pct, txt = 85, "maré baixa"
        if nv_atual == "7. Alfabético Ortográfico":
            pct, txt = 15, "maré cheia"
        elif len(hist) >= 2:
            n_at, n_ant = MAPA_NIVEIS.get(nv_atual, 0), MAPA_NIVEIS.get(hist[-2], 0)
            if n_at > n_ant:   pct, txt = 45, "maré enchente"
            elif n_at < n_ant: pct, txt = 70, "maré vazante"
        return (f'<div class="mare-box">'
                f'<div class="mare-mini-tabela" style="background:linear-gradient(to bottom,#f0f0f0 {pct}%,#5DADE2 {pct}%);"></div>'
                f'<span class="mare-texto-tabela">{txt}</span></div>')

    cols_header = ["Nome do Aluno", "1ª Sondagem", "2ª Sondagem", "3ª Sondagem", "STATUS MARÉ"]
    if ano_sel == 2026:
        cols_header.insert(1, "Diagnóstico Atual")

    html_tab = (
        f'<table style="width:100%;border-collapse:collapse;margin-top:15px;background:white;border:1px solid #eee;color:#2C3E50;">'
        f'<thead><tr style="background-color:#F8F9FA;">'
        + "".join([f'<th style="padding:12px;border:1px solid #eee;font-size:12px;">{c}</th>' for c in cols_header])
        + "</tr></thead><tbody>"
    )

    alunos_nesta_aba = sorted([
        a for a in df_h["ALUNO"].astype(str).str.strip().unique()
        if a and a not in ["nan", "None", ""]
    ]) if not df_h.empty else []

    for al in alunos_nesta_aba:
        dados_aluno_ano = df_h[
            (df_h["ALUNO"].astype(str).str.strip() == al) &
            (df_h["ANO"].astype(str).str.strip() == str(ano_sel))
        ]
        if dados_aluno_ano.empty:
            continue

        sala_al   = str(dados_aluno_ano["SALA"].iloc[0]).strip().upper() if "SALA" in dados_aluno_ano.columns else ""
        cfg_sala  = TURMAS_CONFIG.get(sala_al, {})
        cor_badge = cfg_sala.get("cor", "#aaa")
        txt_badge = BADGE_LABEL.get(sala_al, sala_al if sala_al else "—")
        badge_sala = (
            f' <span style="background:{cor_badge};color:#fff;border-radius:50px;'
            f'padding:3px 10px;font-size:9px;font-weight:bold;letter-spacing:0.5px;white-space:nowrap;">'
            f'{txt_badge}</span>'
        )

        html_tab += (
            f'<tr><td style="font-weight:bold;padding:10px;border:1px solid #eee;font-size:12px;">'
            f'{al}{badge_sala}</td>'
        )

        if ano_sel == 2026:
            dados_2025 = df_h[
                (df_h["ALUNO"].astype(str).str.strip() == al) &
                (df_h["ANO"].astype(str).str.strip() == "2025")
            ]
            diag_2025 = ""
            if not dados_2025.empty:
                for c_av in ["AVALIAÇÃO FINAL", "2ª AVALIAÇÃO", "1ª AVALIAÇÃO", "DIAGNÓSTICO"]:
                    if c_av in dados_2025.columns:
                        val = str(dados_2025[c_av].iloc[0]).strip()
                        if val and val not in ["nan", "None", ""]:
                            diag_2025 = val
                            break
            if not diag_2025 or diag_2025 in ["nan", "None", ""]:
                diag_2025 = "-"
            if diag_2025 != "-":
                cor_d  = CORES_EXCLUSIVAS.get(diag_2025, "#eee")
                txt_d  = diag_2025.split(". ")[1] if ". " in diag_2025 else diag_2025
                html_tab += (
                    f'<td style="background:{cor_d};color:{get_text_color(diag_2025)};'
                    f'text-align:center;font-weight:bold;border:1px solid #eee;font-size:11px;">{txt_d}</td>'
                )
            else:
                html_tab += '<td style="border:1px solid #eee;text-align:center;color:#aaa;">—</td>'

        for col_av in ["1ª AVALIAÇÃO", "2ª AVALIAÇÃO", "AVALIAÇÃO FINAL"]:
            nv = dados_aluno_ano[col_av].iloc[0] if col_av in dados_aluno_ano.columns else ""
            nv = str(nv).strip() if nv else ""
            if nv:
                cor    = CORES_EXCLUSIVAS.get(nv, "#eee")
                txt_nv = nv.split(". ")[1] if ". " in nv else nv
                html_tab += (
                    f'<td style="background:{cor};color:{get_text_color(nv)};text-align:center;'
                    f'font-weight:bold;border:1px solid #eee;font-size:11px;">{txt_nv}</td>'
                )
            else:
                html_tab += '<td style="border:1px solid #eee;"></td>'

        niveis_preenchidos = [
            str(dados_aluno_ano[c].iloc[0]).strip()
            for c in ["1ª AVALIAÇÃO", "2ª AVALIAÇÃO", "AVALIAÇÃO FINAL"]
            if c in dados_aluno_ano.columns and str(dados_aluno_ano[c].iloc[0]).strip()
        ]
        status_html = '<td style="border:1px solid #eee;text-align:center;">-</td>'
        if niveis_preenchidos:
            status_html = f'<td style="border:1px solid #eee;">{get_status_mare_html(niveis_preenchidos[-1], niveis_preenchidos)}</td>'

        html_tab += status_html + "</tr>"

    st.markdown(html_tab + "</tbody></table>", unsafe_allow_html=True)

elif menu == "📈 Indicadores pedagógicos":
    st.markdown(f"### 📈 Indicadores")
    render_botoes_salas("btn_ind", "sel_ind")
    df_h = df_alf.copy()
    if not df_h.empty:
        df_ult = df_h.sort_values("AVALIAÇÃO").groupby("ALUNO").last().reset_index() if "AVALIAÇÃO" in df_h.columns else df_h
        st.dataframe(df_ult, use_container_width=True)
    else:
        st.info("Sem dados.")

elif menu == "🌊 Canal do Apadrinhamento":
    st.markdown(f"### 🤝 Canal do Apadrinhamento")

    lista_salas = []
    for nome_aba in TURMAS_CONFIG.keys():
        df_t = ler_planilha(nome_aba)
        if not df_t.empty:
            df_t = df_t.copy()
            df_t["SALA_NOME"] = nome_aba
            lista_salas.append(df_t)

    if not lista_salas:
        st.error("⚠️ Erro ao carregar salas. Verifique a conexão.")
        st.stop()

    df_total = pd.concat(lista_salas, ignore_index=True)

    col_padrinho = "PADRINHO/MADRINHA"
    padrinhos_lista = (
        sorted([str(p).strip() for p in df_total[col_padrinho].unique()
                if str(p).strip() not in ["", "0", "nan", "None", "NaN"]])
        if col_padrinho in df_total.columns else []
    )

    if st.session_state.get("perfil") == "padrinho":
        p_sel = st.session_state.get("nome_usuario", "")
    else:
        p_sel = st.selectbox("👤 Selecionar Padrinho (Visualização Admin):", ["Selecione..."] + padrinhos_lista)

    if p_sel and p_sel not in ["Selecione...", "Nenhum Padrinho Encontrado"]:
        afils_df = df_total[df_total[col_padrinho].astype(str).str.upper() == p_sel.upper()]

        if not afils_df.empty:
            lista_nomes = sorted([str(n).strip() for n in afils_df["ALUNO"].unique()])
            al_af = st.selectbox("👶 Selecione o afilhado:", lista_nomes)

            is_turno = al_af in st.session_state.get("alunos_te_dict", {})
            modo = "🌊 Tábua da Maré (Geral)"

            if is_turno:
                st.markdown(f"""
                <div style="background-color:#f3e5f5;padding:20px;border-radius:12px;border-left:5px solid #6741d9;margin-bottom:20px;color:black;">
                    <span style="font-size:18px;">✨ <b>O seu afilhado, {al_af}, participa do nosso Turno Estendido!</b></span><br>
                    <p style="margin-top:10px;line-height:1.5;font-size:14px;">
                        Essa é uma ação do nosso Projeto <b>"Vamos Dar a Meia Volta e Alfabetizar"</b>.
                    </p>
                </div>""", unsafe_allow_html=True)
                modo = st.radio("O que deseja visualizar?", ["🌊 Tábua da Maré (Geral)", "📚 Turno Estendido"], horizontal=True)

            st.markdown("---")

            if modo == "🌊 Tábua da Maré (Geral)":
                df_av_canal = df_aval.copy()
                df_av_canal.columns = [str(c).strip().upper() for c in df_av_canal.columns]
                dados_aluno_mare = df_av_canal[df_av_canal["ALUNO"].astype(str).str.strip() == al_af.strip()]

                if not dados_aluno_mare.empty:
                    for _, r in dados_aluno_mare.iterrows():
                        periodo = r.get("SEMESTRE", r.get("PERIODO", "Avaliação"))
                        st.markdown(f"**🗓️ {periodo}**")
                        valores = []
                        mapa_notas = {
                            "MARÉ BAIXA": 1, "MARÉ VAZANTE": 2,
                            "MARÉ ENCHENTE": 3, "MARÉ ALTA": 4, "MARÉ CHEIA": 5,
                        }
                        for cat in CATEGORIAS:
                            v = r.get(cat.upper(), r.get(cat, 1))
                            if isinstance(v, str):
                                n = mapa_notas.get(v.strip().upper(), 1)
                            else:
                                n = v if v else 1
                            valores.append(float(n))

                        c1 = st.columns(5)
                        for i in range(5):
                            with c1[i]:
                                st.markdown(render_vasilha_mare(valores[i], CATEGORIAS[i]), unsafe_allow_html=True)
                        c2 = st.columns(5)
                        for i in range(5, 10):
                            with c2[i - 5]:
                                st.markdown(render_vasilha_mare(valores[i], CATEGORIAS[i]), unsafe_allow_html=True)

                        st.plotly_chart(criar_grafico_mare(CATEGORIAS, valores), use_container_width=True, key=f"canal_mare_{al_af}_{periodo}")
                        obs_pedag = r.get("OBSERVAÇÕES PEDAGÓGICAS", r.get("OBSERVACOES", "Sem registro."))
                        st.info(f"**Observação:** {obs_pedag}")
                        st.write("---")
                else:
                    st.info("Nenhuma avaliação da Tábua da Maré encontrada para este afilhado.")

            elif modo == "📚 Turno Estendido":
                df_h = df_alf.copy()
                df_h.columns = [str(c).strip().upper() for c in df_h.columns]
                dados_al = df_h[df_h["ALUNO"] == al_af]

                if not dados_al.empty:
                    info_al = dados_al.iloc[-1]
                    niveis_seq = []
                    for c_av in ["1ª AVALIAÇÃO", "2ª AVALIAÇÃO", "AVALIAÇÃO FINAL"]:
                        val = info_al.get(c_av, "")
                        if val and str(val).strip():
                            niveis_seq.append(str(val))
                    u_nv = niveis_seq[-1] if niveis_seq else str(info_al.get("DIAGNÓSTICO", "1. Pré-Silábico"))

                    col_info, col_graf = st.columns([1.2, 1])
                    with col_info:
                        cor_bg = CORES_EXCLUSIVAS.get(u_nv, "#ddd")
                        st.markdown(f"""
                        <div style="border:1px solid #ddd;padding:15px;border-radius:12px;background:#f9f9f9;color:black;">
                            <h4 style="margin:0;">{al_af}</h4>
                            <p style="margin:10px 0;"><b>Nível:</b> <span style="background:{cor_bg};padding:5px 10px;border-radius:15px;">{u_nv}</span></p>
                            <p style="font-size:13px;"><b>Evidências:</b> {info_al.get("EVIDÊNCIAS", "---")}</p>
                        </div>""", unsafe_allow_html=True)

                    with col_graf:
                        vols = [MAPA_NIVEIS.get(n, 0) for n in niveis_seq]
                        pct = 85
                        if "7." in u_nv: pct = 15
                        elif len(vols) >= 2 and vols[-1] > vols[-2]: pct = 45
                        st.markdown(
                            f'<div style="width:100px;height:50px;background:linear-gradient(to bottom,#f0f0f0 {pct}%,#5DADE2 {pct}%);'
                            f'clip-path:path(\'M 0 10 Q 25 0 50 10 T 100 10 L 100 40 Q 100 50 90 50 L 10 50 Q 0 50 0 40 Z\');border:1px solid #ccc;"></div>',
                            unsafe_allow_html=True,
                        )

                    st.markdown("##### 🚀 Jornada")
                    html_trilha = '<div style="display:flex;gap:5px;overflow-x:auto;">'
                    for nv_ref in NIVEIS_ALF:
                        opac = "1.0" if u_nv == nv_ref else "0.3"
                        cor = CORES_EXCLUSIVAS.get(nv_ref, "#eee")
                        html_trilha += f'<div style="background:{cor};opacity:{opac};padding:5px;border-radius:5px;font-size:10px;min-width:80px;text-align:center;">{nv_ref.split(". ")[1]}</div>'
                    st.markdown(html_trilha + "</div>", unsafe_allow_html=True)
                else:
                    st.warning("Dados não localizados para este aluno no Turno Estendido.")

elif menu == "🌊 Tábua da Maré":
    st.markdown(f"### 🌊 Tábua da Maré")

    render_botoes_salas("btn_int", "sel_int")

    if "sel_int" not in st.session_state:
        st.info("Selecione uma sala para visualizar os dados.")
        st.stop()

    df_av = df_aval.copy()
    df_av.columns = [str(c).strip().upper() for c in df_av.columns]

    df_s = ler_planilha(st.session_state.sel_int)

    if not df_s.empty:
        alunos_sala = sorted([str(n).replace("**", "").strip() for n in df_s["ALUNO"].dropna().unique()])

        for al in alunos_sala:
            with st.expander(f"👤 {al}"):
                filtro_aluno = df_s[df_s["ALUNO"].str.strip() == al.strip()]
                if filtro_aluno.empty:
                    st.warning("Dados cadastrais não encontrados.")
                    continue

                aluno_row = filtro_aluno.iloc[0]
                turno = aluno_row.get("TURMA", "")
                sala_nome = st.session_state.sel_int.replace("SALA ", "").title()
                sala_full = f"{sala_nome} - {turno}" if turno else sala_nome

                col_f1, col_f2 = st.columns([1, 2])
                with col_f1:
                    st.markdown(f"""
                        <div style="background-color:#f1f8ff;padding:15px;border-radius:10px;border:1px solid #d1e9ff;color:black;">
                            <p style="margin:0;font-size:12px;"><b>SALA/TURMA:</b><br>{sala_full}</p>
                            <p style="margin:8px 0 0;font-size:12px;"><b>IDADE:</b> {aluno_row.get("IDADE","---")}</p>
                            <p style="margin:8px 0 0;font-size:12px;"><b>COMUNIDADE:</b> {aluno_row.get("COMUNIDADE","---")}</p>
                        </div>""", unsafe_allow_html=True)

                dados_aluno = df_av[df_av["ALUNO"].str.strip() == al.strip()]

                if not dados_aluno.empty:
                    for _, r in dados_aluno.iterrows():
                        periodo = r.get("SEMESTRE", r.get("PERIODO", "Avaliação"))
                        st.write("---")
                        st.markdown(f"**🗓️ {periodo}**")
                        valores = []
                        mapa_notas = {
                            "MARÉ BAIXA": 1, "MARÉ VAZANTE": 2,
                            "MARÉ ENCHENTE": 3, "MARÉ ALTA": 4, "MARÉ CHEIA": 5,
                        }
                        for cat in CATEGORIAS:
                            v = r.get(cat.upper(), r.get(cat, 1))
                            if isinstance(v, str):
                                n = mapa_notas.get(v.strip().upper(), 1)
                            else:
                                n = v if v else 1
                            valores.append(float(n))

                        c1 = st.columns(5)
                        for i in range(5):
                            with c1[i]:
                                st.markdown(render_vasilha_mare(valores[i], CATEGORIAS[i]), unsafe_allow_html=True)
                        c2 = st.columns(5)
                        for i in range(5, 10):
                            with c2[i - 5]:
                                st.markdown(render_vasilha_mare(valores[i], CATEGORIAS[i]), unsafe_allow_html=True)

                        st.plotly_chart(criar_grafico_mare(CATEGORIAS, valores), use_container_width=True, key=f"gen_{al}_{periodo}")
                        obs_pedag = r.get("OBSERVAÇÕES PEDAGÓGICAS", r.get("OBSERVACOES", "Sem registro."))
                        st.info(f"**Observação:** {obs_pedag}")
                else:
                    st.info("Nenhuma avaliação registrada na Tábua da Maré.")
    else:
        st.warning(f"A aba '{st.session_state.sel_int}' está vazia ou não foi encontrada.")
