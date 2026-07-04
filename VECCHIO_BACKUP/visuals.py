import plotly.graph_objects as go
import numpy as np

def genera_grafico_predittivo(percorsi_rischio, giorni_proiettati):
    fig = go.Figure()

    # 1. Tracciamo i percorsi individuali (Sfondo)
    for i in range(min(50, percorsi_rischio.shape[1])):
        fig.add_trace(go.Scatter(
            y=percorsi_rischio[:, i],
            mode='lines',
            line=dict(width=0.5, color='rgba(128, 128, 128, 0.3)'),
            showlegend=False
        ))

    # 2. AGGIUNTA: Linea Media (La tendenza centrale)
    media_percorso = np.mean(percorsi_rischio, axis=1)
    fig.add_trace(go.Scatter(
        y=media_percorso,
        mode='lines',
        name='Tendenza Media IA',
        line=dict(width=3, color='#3498db') # Un bel blu brillante
    ))

    # 3. Soglia critica
    fig.add_hline(y=9.0, line_dash="dash", line_color="#e74c3c", 
                  annotation_text="ZONA COLLASSO (9.0)", annotation_position="top left")

    fig.update_layout(
        title="<b>Proiezione Strategica RGD-Alpha (30gg)</b>",
        xaxis_title="Giorni di Proiezione",
        yaxis_title="Indice di Rischio Esposto",
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20)
    )
    return fig