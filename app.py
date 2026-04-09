import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# --- CONFIGURAÇÕES E ESTILOS ---
st.set_page_config(page_title="Gestão Instituto Mãe Lalu", layout="wide")

# Cores da imagem da trilha
CORES_TRILHA = {
    "1. Pré-Silábico": "#d9e6f2",      # Azul clarinho
    "2. Silábico s/ Valor": "#5cc6d0", # Turquesa
    "3. Silábico c/ Valor": "#a8cf45", # Verde
    "4. Silábico Alfabético": "#ffc713", # Amarelo
    "5. Alfabético Inicial": "#ff81ba", # Rosa
    "6. Alfabético Final": "#5cc6d0",   # Azul/Turquesa
    "7. Alfabético Ortográfico": "#ff81ba" # Rosa Escuro
}

ALF_FILE = "alfabetizacao.csv"
NIVEIS_ALF = list(CORES_TRILHA.keys())

# --- FUNÇÃO DA TRILHA VISUAL ---
def renderizar_trilha_visual(nivel_atual=None):
    """Renderiza a trilha com setas e cores idênticas à imagem enviada."""
    
    # CSS para o caminho em zigue-zague e as setas
    st.markdown("""
        <style>
        .trilha-container {
            display: flex;
            align-items: center;
            justify-content: space-around;
            padding: 40px 10px;
            background-color: white;
            border-radius: 15px;
        }
        .bloco {
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            width: 120px;
        }
        .caixa {
            width: 80px;
            height: 80px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.3s;
        }
        .label-nivel {
            margin-top: 10px;
            font-size: 12px;
            font-weight: 600;
            color: #444;
            text-align: center;
            min-height: 30px;
        }
        .seta {
            font-size: 24px;
            color: #ccc;
            margin-top: -30px;
        }
        .inativo { background-color: #f0f0f0 !important; color: #ccc !important; box-shadow: none !important; }
        </style>
    """, unsafe_allow_html=True)

    cols = st.columns(len(NIVEIS_ALF))
    
    for i, nivel in enumerate(NIVEIS_ALF):
        # Lógica de destaque: Se o nível for o atual, usa a cor. Se não, fica cinza.
        esta_ativo = "ativo" if nivel == nivel_atual else "inativo"
        cor_fundo = CORES_TRILHA[nivel] if nivel == nivel_atual else "#f0f0f0"
        texto_cor = "white" if nivel == nivel_atual else "#ccc"
        
        # Simula o número ou as reticências da imagem
        conteudo = "---" if nivel == nivel_atual else "" # Ou puxe dados reais de contagem aqui
        
        with cols[i]:
            label_curto = nivel.split(". ")[1]
            st.markdown(f"""
                <div class="bloco">
                    <div class="caixa" style="background-color: {cor_fundo}; color: {texto_cor};">
                        {conteudo}
                    </div>
                    <div class="label-nivel">{label_curto}</div>
                </div>
            """, unsafe_allow_html=True)
            if i < len(NIVEIS_ALF) - 1:
                st.markdown("<div style='text-align:center; color:#ccc; font-size:20px;'>→</div>", unsafe_allow_html=True)

# --- MENU PROGRAMA ALFABETIZAÇÃO ---
# (Assumindo que este código entra no bloco do seu Menu principal)

if "menu" not in st.session_state: st.session_state.menu = "📖 Programa Alfabetização"

if st.session_state.menu == "📖 Programa Alfabetização":
    st.markdown("### 📖 Programa Alfabetização")
    
    # Carregamento de dados (Simulação baseada no seu safe_read)
    # df_s = safe_read(st.session_state.sel_alf)
    df_alf = pd.read_csv(ALF_FILE) if os.path.exists(ALF_FILE) else pd.DataFrame()

    # 1. Seleção do Aluno
    # al_sel = st.selectbox("Selecione o Aluno para Diagnóstico", sorted(df_s["ALUNO"].unique()))
    al_sel = "ALICE SANTOS" # Exemplo para teste
    
    # 2. Busca diagnóstico atual
    nivel_detectado = None
    if not df_alf.empty:
        ult_diag = df_alf[df_alf["Aluno"] == al_sel]
        if not ult_diag.empty:
            nivel_detectado = ult_diag.iloc[-1]["Nivel"]

    # 3. Exibição da Trilha Visual (conforme solicitado: após seleção do aluno)
    st.write("---")
    st.write(f"**Trilha de Aprendizagem: {al_sel}**")
    renderizar_trilha_visual(nivel_detectado)
    st.write("---")

    # 4. Formulário de Atualização (Abaixo da trilha)
    with st.form("form_novo_diag"):
        st.subheader("Atualizar Diagnóstico")
        c1, c2 = st.columns(2)
        novo_nv = c1.selectbox("Novo Nível:", NIVEIS_ALF, index=NIVEIS_ALF.index(nivel_detectado) if nivel_detectado else 0)
        aval_tipo = c2.selectbox("Avaliação:", ["1ª Avaliação", "2ª Avaliação", "Final"])
        
        obs = st.text_area("Evidências observadas:")
        
        if st.form_submit_button("Registrar Avanço"):
            # Lógica de salvar no CSV (idêntica ao seu código funcional anterior)
            st.success(f"Nível de {al_sel} atualizado para {novo_nv}!")
            st.rerun()
