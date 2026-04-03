# --- GRÁFICO DE MARÉ (FORMATO SENOIDE/COSSENOIDE) ---
        st.subheader("🌊 Movimento da Maré Individual")
        st.caption("Evolução dos critérios com curvatura suavizada (Seno e Cosseno)")
        
        fig_mare = go.Figure()
        
        # Paleta de cores baseada na identidade do Instituto
        cores_ondas = ['#5cc6d0', '#a8cf45', '#0077b6', '#00b4d8', '#90e0ef', '#72efdd', '#48cae4', '#b5e48c']
        
        for i, crit in enumerate(CATEGORIAS):
            fig_mare.add_trace(go.Scatter(
                x=df_aluno["Trimestre"], 
                y=df_aluno[crit],
                mode='lines+markers',
                name=crit,
                # 'spline' com smoothing alto cria o efeito de onda senoidal
                line=dict(
                    shape='spline', 
                    smoothing=1.3, 
                    width=4, 
                    color=cores_ondas[i % len(cores_ondas)]
                ),
                # Preenchimento suave para dar profundidade à "água"
                fill='tozeroy',
                fillcolor=f"rgba{tuple(list(int(cores_ondas[i % len(cores_ondas)].lstrip('#')[j:j+2], 16) for j in (0, 2, 4)) + [0.2])}" 
            ))

        fig_mare.update_layout(
            yaxis=dict(
                range=[0, 5.5], 
                title="Nível de Aprendizado",
                gridcolor='rgba(0,0,0,0.1)'
            ),
            xaxis=dict(title="Trimestre"),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor='white',
            paper_bgcolor='rgba(0,0,0,0)',
            height=500
        )
        
        st.plotly_chart(fig_mare, use_container_width=True)
