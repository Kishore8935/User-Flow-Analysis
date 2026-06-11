import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import data
import charts

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.FLATLY,
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap',
    ],
    title='RadOps Analytics',
    suppress_callback_exceptions=True,
)

# ── Helpers ──────────────────────────────────────────────────────────────────

def kpi_card(label, value_id, accent):
    return dbc.Card(
        dbc.CardBody(
            html.Div([
                html.Div(
                    '—',
                    id=value_id,
                    style={
                        'fontSize': '30px', 'fontWeight': '800',
                        'color': '#0f172a', 'lineHeight': '1',
                    },
                ),
                html.Div(
                    label,
                    style={
                        'fontSize': '11px', 'fontWeight': '600',
                        'color': '#64748b', 'textTransform': 'uppercase',
                        'letterSpacing': '0.08em', 'marginTop': '6px',
                    },
                ),
            ])
        ),
        style={
            'borderRadius': '12px',
            'borderLeft': f'4px solid {accent}',
            'boxShadow': '0 2px 12px rgba(15,23,42,0.07)',
        },
    )


def section_card(header_text, graph_id):
    return dbc.Card([
        dbc.CardHeader(
            html.Span(header_text, style={'fontWeight': '700', 'fontSize': '13px', 'color': '#374151'}),
            style={'background': '#f8fafc', 'border': 'none', 'paddingBottom': '0'},
        ),
        dbc.CardBody(
            dcc.Loading(dcc.Graph(id=graph_id, config={'displayModeBar': False}), color='#6366f1')
        ),
    ], style={'borderRadius': '12px', 'border': '1px solid rgba(15,23,42,0.08)',
               'boxShadow': '0 2px 12px rgba(15,23,42,0.06)'})


DROPDOWN_STYLE = {'borderRadius': '8px', 'fontSize': '13px'}

LABEL_STYLE = {
    'fontWeight': '600', 'fontSize': '11px', 'color': '#64748b',
    'textTransform': 'uppercase', 'letterSpacing': '0.07em',
    'marginBottom': '6px', 'display': 'block',
}

# ── Layout ───────────────────────────────────────────────────────────────────

app.layout = dbc.Container([

    # Header
    dbc.Row(dbc.Col(html.Div([
        html.Span('⬡ ', style={'fontSize': '22px', 'color': '#6366f1'}),
        html.Span('RadOps', style={'fontSize': '22px', 'fontWeight': '800',
                                    'color': '#0f172a', 'letterSpacing': '-0.03em'}),
        html.Span(' Analytics', style={'fontSize': '22px', 'fontWeight': '400',
                                        'color': '#64748b', 'letterSpacing': '-0.02em'}),
    ], style={'padding': '24px 0 16px', 'display': 'flex', 'alignItems': 'center'}))),

    dbc.Tabs(
        id='tabs',
        active_tab='overview',
        children=[

            # ══════════════════════════════════════════════════════════════
            # TAB 1 — OVERVIEW
            # ══════════════════════════════════════════════════════════════
            dbc.Tab(label='Overview', tab_id='overview', children=[
                html.Div(style={'height': '16px'}),

                # KPI row
                dbc.Row([
                    dbc.Col(kpi_card('Total Sessions',     'kpi-sessions', '#6366f1'), md=3),
                    dbc.Col(kpi_card('Unique Users',        'kpi-users',    '#0284c7'), md=3),
                    dbc.Col(kpi_card('Most Visited',        'kpi-top',      '#059669'), md=3),
                    dbc.Col(kpi_card('Avg Duration (min)',  'kpi-duration', '#d97706'), md=3),
                ], className='g-3 mb-3'),

                # Charts row 1
                dbc.Row([
                    dbc.Col(section_card('Section Visit Counts',        'chart-visits'),  md=6),
                    dbc.Col(section_card('Avg Time per Section (sec)',   'chart-avgtime'), md=6),
                ], className='g-3 mb-3'),

                # Charts row 2
                dbc.Row([
                    dbc.Col(section_card('Daily Sessions', 'chart-daily'), md=12),
                ], className='g-3'),
            ]),

            # ══════════════════════════════════════════════════════════════
            # TAB 2 — USER JOURNEY
            # ══════════════════════════════════════════════════════════════
            dbc.Tab(label='User Journey', tab_id='journey', children=[
                html.Div(style={'height': '16px'}),

                # Selectors row
                dbc.Row([
                    dbc.Col([
                        html.Label('User', style=LABEL_STYLE),
                        dcc.Dropdown(
                            id='user-dropdown',
                            placeholder='Select a user…',
                            clearable=False,
                            style=DROPDOWN_STYLE,
                        ),
                    ], md=4),
                    dbc.Col([
                        html.Label('Session', style=LABEL_STYLE),
                        dcc.Dropdown(
                            id='session-dropdown',
                            placeholder='Select a session…',
                            clearable=False,
                            style=DROPDOWN_STYLE,
                        ),
                    ], md=5),
                    dbc.Col([
                        html.Div(id='session-badges', style={'marginTop': '24px'}),
                    ], md=3),
                ], className='mb-4'),

                # Sankey
                section_card('Navigation Flow  (node = section, width = time spent)', 'chart-sankey'),
                html.Div(style={'height': '16px'}),

                # Gantt
                section_card('Section Timeline  (IST)', 'chart-gantt'),
            ]),

            # ══════════════════════════════════════════════════════════════
            # TAB 3 — PATTERNS
            # ══════════════════════════════════════════════════════════════
            dbc.Tab(label='Patterns', tab_id='patterns', children=[
                html.Div(style={'height': '16px'}),
                dbc.Row([
                    dbc.Col(section_card('Navigation Transitions Heatmap', 'chart-heatmap'), md=6),
                    dbc.Col(section_card('Session Depth Funnel',           'chart-funnel'),  md=6),
                ], className='g-3 mb-3'),
                dbc.Row([
                    dbc.Col(section_card('Google vs Credentials',          'chart-auth'), md=12),
                ], className='g-3'),
            ]),
        ],
    ),

    html.Div(style={'height': '48px'}),

], fluid=True, style={'maxWidth': '1380px', 'padding': '0 24px', 'fontFamily': 'Inter, sans-serif'})


# ── Callbacks ────────────────────────────────────────────────────────────────

@app.callback(
    Output('chart-visits',  'figure'),
    Output('chart-avgtime', 'figure'),
    Output('chart-daily',   'figure'),
    Output('kpi-sessions',  'children'),
    Output('kpi-users',     'children'),
    Output('kpi-top',       'children'),
    Output('kpi-duration',  'children'),
    Input('tabs', 'active_tab'),
)
def load_overview(_tab):
    try:
        stats = data.get_section_stats()
        daily = data.get_daily_sessions()
        kpis  = data.get_kpis()
        return (
            charts.build_section_bars(stats),
            charts.build_avg_time(stats),
            charts.build_daily_line(daily),
            str(kpis.get('total_sessions', '—')),
            str(kpis.get('unique_users',   '—')),
            str(kpis.get('top_section',    '') or '—').title(),
            f"{kpis.get('avg_min', '—')} min",
        )
    except Exception as exc:
        empty = charts._empty(f'DB error: {exc}')
        return empty, empty, empty, '—', '—', '—', '—'


@app.callback(
    Output('user-dropdown', 'options'),
    Input('tabs', 'active_tab'),
)
def load_users(_tab):
    try:
        df = data.get_users()
        return [{'label': row['label'], 'value': int(row['id'])} for _, row in df.iterrows()]
    except Exception:
        return []


@app.callback(
    Output('session-dropdown', 'options'),
    Output('session-dropdown', 'value'),
    Input('user-dropdown', 'value'),
)
def load_sessions(user_id):
    if user_id is None:
        return [], None
    try:
        df = data.get_sessions(user_id)
        options = []
        for _, row in df.iterrows():
            flow  = ' → '.join(row['section_flow']) if row['section_flow'] else 'no sections'
            label = f"{row['started_fmt']}  ·  {row['duration_min']} min  ·  {flow}"
            options.append({'label': label, 'value': row['session_id']})
        default = options[0]['value'] if options else None
        return options, default
    except Exception:
        return [], None


@app.callback(
    Output('chart-sankey',    'figure'),
    Output('chart-gantt',     'figure'),
    Output('session-badges',  'children'),
    Input('session-dropdown', 'value'),
)
def load_journey(session_id):
    placeholder = charts._empty('Select a user and session above')
    if not session_id:
        return placeholder, placeholder, ''
    try:
        df     = data.get_session_events(session_id)
        sankey = charts.build_sankey(df)
        gantt  = charts.build_gantt(df)

        enters   = df[df['event'] == 'section_enter']
        exits    = df[df['event'] == 'section_exit']
        total_ms = exits['time_spent_ms'].sum()
        methods  = df['auth_method'].dropna()
        method   = methods.iloc[0] if not methods.empty else 'unknown'

        badges = html.Div([
            dbc.Badge(f"{len(enters)} sections", color='primary',   className='me-2'),
            dbc.Badge(f"{round(total_ms / 1000)}s total", color='secondary', className='me-2'),
            dbc.Badge(method, color='success'),
        ])
        return sankey, gantt, badges
    except Exception as exc:
        err = charts._empty(f'Error: {exc}')
        return err, err, ''


@app.callback(
    Output('chart-heatmap', 'figure'),
    Output('chart-funnel',  'figure'),
    Output('chart-auth',    'figure'),
    Input('tabs', 'active_tab'),
)
def load_patterns(tab):
    if tab != 'patterns':
        raise dash.exceptions.PreventUpdate
    try:
        return (
            charts.build_heatmap(data.get_transition_matrix()),
            charts.build_funnel(data.get_funnel_data()),
            charts.build_auth_compare(data.get_auth_comparison()),
        )
    except Exception as exc:
        empty = charts._empty(f'DB error: {exc}')
        return empty, empty, empty


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=8050, host='0.0.0.0')
