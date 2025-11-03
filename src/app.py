import dash
import pandas as pd
import numpy as np
from dash import dcc, html, dash_table, Input, Output, State
import plotly.graph_objects as go

# ======================================================================================
# MOTOR DE SIMULACIÓN
# ======================================================================================
def simular_curva_capital(stop_loss, take_profit, df_trades):
    if df_trades.empty:
        return {'x': [], 'y': []}
    pnl_history = []
    for _, row in df_trades.iterrows():
        recorrido_str = row.get('Recorrido', '')
        if not isinstance(recorrido_str, str) or pd.isna(recorrido_str) or recorrido_str == '':
            pnl_history.append(-stop_loss)
            continue
        resultado = -stop_loss
        eventos = recorrido_str.split(',')
        for evento in eventos:
            if not evento: continue
            try:
                tipo, valor = evento[0].upper(), int(evento[1:])
                if tipo == 'M' and valor >= take_profit:
                    resultado = take_profit
                    break
                elif tipo == 'D' and valor >= stop_loss:
                    resultado = -stop_loss
                    break
            except (ValueError, IndexError):
                continue
        pnl_history.append(resultado)
    capital_acumulado = np.cumsum([0] + pnl_history)
    return {'x': np.arange(len(capital_acumulado)), 'y': capital_acumulado}

# ======================================================================================
# APP DASH
# ======================================================================================
app = dash.Dash(__name__)

# --- Carga y preparación de datos ---
df_results = pd.DataFrame()
df_trades = pd.DataFrame()
try:
    df_results = pd.read_csv('data/analisis_final_automatizado.csv', sep=';')
    df_trades = pd.read_csv('data/operaciones_con_recorrido.csv')
    for col in df_results.columns:
        if df_results[col].dtype == 'object':
            try:
                df_results[col] = df_results[col].str.replace(',', '.').astype(float)
            except (ValueError, AttributeError): pass
except FileNotFoundError as e:
    print(f"Error loading data: {e}")

# --- Componentes de la UI ---
sliders = []
# CORRECCIÓN: Crear una lista de columnas que SÍ tienen sliders
numeric_cols_with_sliders = []
if not df_results.empty:
    numeric_cols = df_results.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        min_val, max_val = df_results[col].min(), df_results[col].max()
        if min_val == max_val: continue
        numeric_cols_with_sliders.append(col) # Guardar solo las columnas que tendrán slider
        marks = {int(i): str(int(i)) for i in np.linspace(min_val, max_val, 5, dtype=int)}
        sliders.append(html.Div([
            html.Label(f'{col}:', style={'paddingBottom': '5px', 'display': 'block'}),
            dcc.RangeSlider(id=f'slider-{col}', min=min_val, max=max_val, value=[min_val, max_val], marks=marks, tooltip={"placement": "bottom", "always_visible": True})
        ], style={'marginBottom': '20px'}))

# --- Layout de la App ---
app.layout = html.Div(style={'backgroundColor': '#1E1E1E', 'color': 'white', 'fontFamily': 'Arial'}, children=[
    html.H1('Dashboard de Análisis de Estrategias', style={'textAlign': 'center', 'padding': '20px'}),
    html.Div([
        html.H3('🎛️ Panel de Control', style={'marginTop': '0'}),
        *sliders
    ], style={'padding': '20px', 'margin': '20px', 'border': '1px solid #555', 'borderRadius': '5px'}),

    html.Div(id='visualizations', children=[
        html.H3('📋 Top 20 Estrategias Filtradas', style={'paddingLeft': '20px'}),
        html.Div(dash_table.DataTable(id='data-table', data=df_results.head(20).to_dict('records'), columns=[{'name': i, 'id': i} for i in df_results.columns], style_header={'backgroundColor': '#333'}, style_cell={'backgroundColor': '#222', 'border': '1px solid #555'}), style={'padding': '20px'}),
        html.H3('📈 Visualizaciones Interactivas', style={'paddingLeft': '20px'}),
        html.Div([
            dcc.Graph(id='scatter-plot-pf', style={'flex': 1}),
            dcc.Graph(id='scatter-plot-cs', style={'flex': 1})
        ], style={'display': 'flex'}),
        dcc.Graph(id='heatmap'),
    ]),
    html.H3('💹 Curva de Capital', style={'paddingLeft': '20px'}),
    dcc.Graph(id='pnl-curve', figure=go.Figure(layout={'template': 'plotly_dark', 'paper_bgcolor': '#1E1E1E', 'plot_bgcolor': '#1E1E1E'}).update_layout(title='Curva de Capital - Selecciona una estrategia'))
])

# ======================================================================================
# CALLBACKS
# ======================================================================================
@app.callback(
    Output('visualizations', 'children'),
    # CORRECCIÓN: Usar la lista filtrada de columnas para los Inputs
    [Input(f'slider-{col}', 'value') for col in numeric_cols_with_sliders],
    prevent_initial_call=True
)
def update_visuals(*slider_values):
    df_filtered = df_results.copy()
    # CORRECCIÓN: Iterar sobre la lista correcta
    for i, col in enumerate(numeric_cols_with_sliders):
        min_val, max_val = slider_values[i]
        df_filtered = df_filtered[(df_filtered[col] >= min_val) & (df_filtered[col] <= max_val)]

    if df_filtered.empty:
        empty_fig = go.Figure(layout={'template': 'plotly_dark', 'paper_bgcolor': '#1E1E1E', 'plot_bgcolor': '#1E1E1E'}).add_annotation(text="No data available", showarrow=False)
        return [
            html.H3('📋 Top 20 Estrategias Filtradas', style={'paddingLeft': '20px'}),
            html.Div(dash_table.DataTable(id='data-table', data=[], columns=[{'name': i, 'id': i} for i in df_results.columns]), style={'padding': '20px'}),
            html.H3('📈 Visualizaciones Interactivas', style={'paddingLeft': '20px'}),
            dcc.Graph(figure=empty_fig), dcc.Graph(figure=empty_fig), dcc.Graph(figure=empty_fig)
        ]

    table = dash_table.DataTable(id='data-table', data=df_filtered.head(20).to_dict('records'), columns=[{'name': i, 'id': i} for i in df_filtered.columns], style_header={'backgroundColor': '#333'}, style_cell={'backgroundColor': '#222', 'border': '1px solid #555'})
    plot_layout = {'template': 'plotly_dark', 'paper_bgcolor': '#1E1E1E', 'plot_bgcolor': '#1E1E1E'}
    scatter_pf = go.Figure(go.Scatter(x=df_filtered['Max Drawdown'], y=df_filtered['Net P/L'], mode='markers', marker={'color': df_filtered['Profit Factor'], 'colorscale': 'Plasma', 'showscale': True}, customdata=df_filtered[['Stop', 'Profit']].values), layout=plot_layout).update_layout(title='Profit Factor')
    scatter_cs = go.Figure(go.Scatter(x=df_filtered['Max Drawdown'], y=df_filtered['Net P/L'], mode='markers', marker={'color': df_filtered['Composite_Score'], 'colorscale': 'Viridis', 'showscale': True}, customdata=df_filtered[['Stop', 'Profit']].values), layout=plot_layout).update_layout(title='Composite Score')
    pivot_data = df_filtered.pivot_table(index='Stop', columns='Profit', values='Recovery Factor').fillna(0)
    heatmap_fig = go.Figure(go.Heatmap(z=pivot_data.values, x=pivot_data.columns, y=pivot_data.index, colorscale='Viridis'), layout=plot_layout).update_layout(title='Mapa de Calor (Recovery Factor)')

    return [
        html.H3('📋 Top 20 Estrategias Filtradas', style={'paddingLeft': '20px'}),
        html.Div(table, style={'padding': '20px'}),
        html.H3('📈 Visualizaciones Interactivas', style={'paddingLeft': '20px'}),
        html.Div([dcc.Graph(id='scatter-plot-pf', figure=scatter_pf, style={'flex': 1}), dcc.Graph(id='scatter-plot-cs', figure=scatter_cs, style={'flex': 1})], style={'display': 'flex'}),
        dcc.Graph(id='heatmap', figure=heatmap_fig),
    ]

@app.callback(
    Output('pnl-curve', 'figure'),
    [Input('scatter-plot-pf', 'clickData'), Input('scatter-plot-cs', 'clickData'), Input('heatmap', 'clickData')],
    prevent_initial_call=True
)
def update_pnl_curve(click_pf, click_cs, click_heat):
    ctx = dash.callback_context
    click_data = ctx.triggered[0]['value']
    if not click_data or 'points' not in click_data or not click_data['points']:
        raise dash.exceptions.PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    point = click_data['points'][0]

    if trigger_id in ['scatter-plot-pf', 'scatter-plot-cs']:
        stop, profit = point['customdata']
    else: # heatmap
        profit, stop = point['x'], point['y']

    curve = simular_curva_capital(int(stop), int(profit), df_trades)
    pnl_fig = go.Figure(go.Scatter(x=curve['x'], y=curve['y'], mode='lines', line={'color': '#00CF9B'}), layout={'template': 'plotly_dark', 'paper_bgcolor': '#1E1E1E', 'plot_bgcolor': '#1E1E1E'})
    pnl_fig.update_layout(title=f'Curva de Capital: Stop={stop}, Profit={profit}')
    return pnl_fig

if __name__ == '__main__':
    app.run(debug=True)
