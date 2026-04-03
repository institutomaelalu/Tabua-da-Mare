import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os
from scipy.ndimage import gaussian_filter1d  # Adicione esta importação no topo

# ... (Mantenha o início do código igual até chegar na parte do gráfico) ...

elif menu == "Painel de Evolução":
    # ... (filtros de turno, aluno e trimestre) ...

    if trim_sel:
        # 1. Coleta das notas
        dados = df_av[(df_av["Aluno"] == aluno_sel) & (df_av["Trimestre"] == trim_sel)].iloc[0]
        notas = [dados[c] for c in CATEGORIAS]

        # 2. CRIAÇÃO DA ONDA SENOIDAL (A MÁGICA AQUI)
        x_indices = np.arange(len(CATEGORIAS))
        x_suave = np.linspace(0, len(CATEGORIAS) - 1, 500) # 500 pontos para ultra resolução
        
        # Interpolação inicial
        y_interp = np.interp(x_suave, x_indices, notas)
        
        # APLICAÇÃO DE FILTRO GAUSSIANO: Isso remove as "quinas" e transforma em onda
        # O sigma=7.0 é o que dá o aspecto de seno/cosseno (curva fluida)
        y_wave = gaussian_filter1d(y_interp, sigma=7.0)

        st.subheader(f"🌊 Tábua da Maré: {aluno_sel} - {trim_sel}")
        
        fig = go.Figure()
        
        # Desenho da Maré
        fig.add_trace(go.Scatter(
            x=x_suave, 
            y=y_wave,
            mode='lines',
            line=dict(width=6, color=COR_AZUL, shape='spline'),
            fill='tozeroy',
            fillcolor=f"rgba(92, 198, 208, 0.3)",
            hoverinfo='skip' # Esconde os pontos técnicos para manter o visual limpo
        ))

        # Adiciona apenas os pontos das notas reais como "boias" flutuando na onda
        fig.add_trace(go.Scatter(
            x=x_indices, 
            y=notas,
            mode='markers',
            marker=dict(size=12, color=COR_VERDE, symbol='circle'),
            name='Nível Real'
        ))

        fig.update_layout(
            xaxis=dict(
                tickmode='array', 
                tickvals=list(range(len(CATEGORIAS))), 
                ticktext=[c[:15]+"..." for c in CATEGORIAS],
                showgrid=False
            ),
            yaxis=dict(range=[0, 5.5], showgrid=True, gridcolor='#f0f0f0'),
            plot_bgcolor='white',
            height=450,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # ... (Resto do código com o Radar) ...
