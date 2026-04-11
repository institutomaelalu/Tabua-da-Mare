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
