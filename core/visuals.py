# core/visuals.py
import plotly.graph_objects as go
import numpy as np

def genera_grafico_predittivo(percorsi_rischio, giorni_proiettati):
    """
    Modulo di visualizzazione per Stress Test Monte Carlo.
    Riceve l'array (giorni x iterazioni) e restituisce un oggetto Plotly.
    """
    fig = go.Figure()

    # Tracciamo una selezione di percorsi (es. primi 50)
    for i in range(min(50, percorsi_rischio.shape[1])):
        fig.add_trace(go.Scatter(
            y=percorsi_rischio[:, i],
            mode='lines',
            line=dict(width=0.5, color='gray'),
            opacity=0.3,
            showlegend=False
        ))

    # Linea soglia critica
    fig.add_hline(y=9.0, line_dash="dash", line_color="red", annotation_text="Soglia Crisi (9.0)")

    fig.update_layout(
        title="Proiezione Monte Carlo: Evoluzione Rischio a 30gg",
        xaxis_title="Giorni",
        yaxis_title="Livello Rischio",
        template="plotly_dark",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig