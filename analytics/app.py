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

_PATH_ACCENTS = ['#6366f1', '#0284c7', '#059669', '#d97706']
_PATH_HINTS   = ['Starting point', 'Where next?', 'Then what?', 'Final step']
SECTION_OPTIONS = [
    {'label': 'Overview',   'value': 'overview'},
    {'label': 'Radiology',  'value': 'radiology'},
    {'label': 'System',     'value': 'system'},
    {'label': 'Reports',    'value': 'reports'},
]


def path_col(step_num, dropdown_id, chart_id, count_id, initially_disabled=True):
    """One step column in the Path Explorer tab."""
    accent = _PATH_ACCENTS[step_num - 1]
    hint   = _PATH_HINTS[step_num - 1]
    return dbc.Col([
        html.Div([
            html.Span(
                f'STEP {step_num}',
                style={
                    'fontSize': '10px', 'fontWeight': '700', 'letterSpacing': '0.1em',
                    'color': accent, 'background': f'{accent}18',
                    'padding': '3px 10px', 'borderRadius': '99px',
                },
            ),
            html.Span(hint, style={'fontSize': '11px', 'color': '#94a3b8', 'marginLeft': '8px'}),
        ], style={'marginBottom': '8px', 'display': 'flex', 'alignItems': 'center'}),

        html.Div('', id=count_id, style={
            'fontSize': '13px', 'fontWeight': '600', 'color': '#374151',
            'minHeight': '20px', 'marginBottom': '10px',
        }),

        dcc.Dropdown(
            id=dropdown_id,
            options=SECTION_OPTIONS if step_num == 1 else [],
            placeholder='Select…',
            clearable=True,
            disabled=initially_disabled,
            style=DROPDOWN_STYLE,
        ) if dropdown_id else html.Div(style={'height': '36px'}),

        html.Div(style={'height': '12px'}),

        dcc.Loading(
            dcc.Graph(id=chart_id, config={'displayModeBar': False}),
            color=accent,
        ),
    ], md=3, style={
        'paddingLeft': '16px', 'paddingRight': '16px',
        'borderRight': '1px solid rgba(15,23,42,0.07)' if step_num < 4 else 'none',
    })

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

            # ══════════════════════════════════════════════════════════════
            # TAB 4 — ALL USERS FLOW
            # ══════════════════════════════════════════════════════════════
            dbc.Tab(label='All Users Flow', tab_id='allflow', children=[
                html.Div(style={'height': '16px'}),

                # Filter row
                dbc.Row([
                    dbc.Col([
                        html.Label('Auth Method', style=LABEL_STYLE),
                        dcc.Dropdown(
                            id='allflow-auth-filter',
                            options=[
                                {'label': 'All',         'value': 'all'},
                                {'label': 'Google',      'value': 'google'},
                                {'label': 'Credentials', 'value': 'credentials'},
                            ],
                            value='all',
                            clearable=False,
                            style=DROPDOWN_STYLE,
                        ),
                    ], md=3),
                    dbc.Col(
                        html.Div(
                            'Each ribbon is one session. Width = number of sessions that took that path. '
                            'Color = user. Hover a ribbon to see counts.',
                            style={'marginTop': '22px', 'fontSize': '12px', 'color': '#94a3b8'}
                        ),
                        md=9,
                    ),
                ], className='mb-4'),

                dbc.Card([
                    dbc.CardHeader(
                        html.Span(
                            'User Navigation Paths  —  ribbon = session  ·  color = user  ·  columns = journey steps',
                            style={'fontWeight': '700', 'fontSize': '13px', 'color': '#374151'}
                        ),
                        style={'background': '#f8fafc', 'border': 'none', 'paddingBottom': '0'},
                    ),
                    dbc.CardBody(
                        dcc.Loading(
                            dcc.Graph(id='chart-allflow', config={'displayModeBar': False},
                                      style={'height': '620px'}),
                            color='#6366f1'
                        )
                    ),
                ], style={'borderRadius': '12px', 'border': '1px solid rgba(15,23,42,0.08)',
                           'boxShadow': '0 2px 12px rgba(15,23,42,0.06)'}),
            ]),
            # ══════════════════════════════════════════════════════════════
            # TAB 5 — PATH EXPLORER
            # ══════════════════════════════════════════════════════════════
            dbc.Tab(label='Path Explorer', tab_id='pathexplorer', children=[
                html.Div(style={'height': '16px'}),
                html.P(
                    'Pick a starting section in Step 1, then drill down step-by-step '
                    'to see exactly how many sessions followed each route.',
                    style={'fontSize': '12px', 'color': '#94a3b8', 'marginBottom': '20px'},
                ),
                dbc.Card([
                    dbc.CardBody(
                        dbc.Row([
                            path_col(1, 'path-s1', 'path-chart1', 'path-count1', False),
                            path_col(2, 'path-s2', 'path-chart2', 'path-count2', True),
                            path_col(3, 'path-s3', 'path-chart3', 'path-count3', True),
                            path_col(4, None,       'path-chart4', 'path-count4', True),
                        ], className='g-0', style={'paddingTop': '8px', 'paddingBottom': '8px'}),
                        style={'padding': '16px 4px'},
                    ),
                ], style={
                    'borderRadius': '12px',
                    'border': '1px solid rgba(15,23,42,0.08)',
                    'boxShadow': '0 2px 12px rgba(15,23,42,0.06)',
                }),
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


@app.callback(
    Output('chart-allflow', 'figure'),
    Input('tabs', 'active_tab'),
    Input('allflow-auth-filter', 'value'),
)
def load_allflow(tab, auth_filter):
    if tab != 'allflow':
        raise dash.exceptions.PreventUpdate
    try:
        df = data.get_all_user_flows()
        if auth_filter and auth_filter != 'all':
            df = df[df['auth_method'] == auth_filter]
        return charts.build_alluvial(df)
    except Exception as exc:
        return charts._empty(f'DB error: {exc}')


# ── Path Explorer callbacks ──────────────────────────────────────────────────

@app.callback(
    Output('path-chart1', 'figure'),
    Output('path-count1', 'children'),
    Input('tabs',    'active_tab'),
    Input('path-s1', 'value'),
)
def path_step1(tab, s1):
    if tab != 'pathexplorer':
        raise dash.exceptions.PreventUpdate
    try:
        df    = data.get_path_continuation([])
        total = int(df['sessions'].sum()) if not df.empty else 0
        return charts.build_path_bars(df, selected=s1), f'{total:,} sessions'
    except Exception as exc:
        return charts._empty(f'DB error: {exc}'), ''


@app.callback(
    Output('path-s2',     'options'),
    Output('path-s2',     'disabled'),
    Output('path-chart2', 'figure'),
    Output('path-count2', 'children'),
    Input('path-s1', 'value'),
    Input('path-s2', 'value'),
)
def path_step2(s1, s2):
    if not s1:
        return [], True, charts._empty('← Select a starting section in Step 1'), ''
    try:
        df    = data.get_path_continuation([s1])
        total = int(df['sessions'].sum()) if not df.empty else 0
        opts  = [
            {'label': r['next_section'].title(), 'value': r['next_section']}
            for _, r in df.iterrows() if r['next_section'] != '(session ended)'
        ]
        return opts, False, charts.build_path_bars(df, selected=s2), f'{total:,} sessions'
    except Exception as exc:
        return [], True, charts._empty(f'DB error: {exc}'), ''


@app.callback(
    Output('path-s3',     'options'),
    Output('path-s3',     'disabled'),
    Output('path-chart3', 'figure'),
    Output('path-count3', 'children'),
    Input('path-s1', 'value'),
    Input('path-s2', 'value'),
    Input('path-s3', 'value'),
)
def path_step3(s1, s2, s3):
    if not s1 or not s2:
        return [], True, charts._empty('← Complete Steps 1 & 2 first'), ''
    try:
        df    = data.get_path_continuation([s1, s2])
        total = int(df['sessions'].sum()) if not df.empty else 0
        opts  = [
            {'label': r['next_section'].title(), 'value': r['next_section']}
            for _, r in df.iterrows() if r['next_section'] != '(session ended)'
        ]
        return opts, False, charts.build_path_bars(df, selected=s3), f'{total:,} sessions'
    except Exception as exc:
        return [], True, charts._empty(f'DB error: {exc}'), ''


@app.callback(
    Output('path-chart4', 'figure'),
    Output('path-count4', 'children'),
    Input('path-s1', 'value'),
    Input('path-s2', 'value'),
    Input('path-s3', 'value'),
)
def path_step4(s1, s2, s3):
    if not s1 or not s2 or not s3:
        return charts._empty('← Complete Steps 1 – 3 first'), ''
    try:
        df    = data.get_path_continuation([s1, s2, s3])
        total = int(df['sessions'].sum()) if not df.empty else 0
        return charts.build_path_bars(df), f'{total:,} sessions'
    except Exception as exc:
        return charts._empty(f'DB error: {exc}'), ''


# Cascade resets — changing an earlier step clears all downstream selections
@app.callback(
    Output('path-s2', 'value'),
    Input('path-s1', 'value'),
    prevent_initial_call=True,
)
def reset_path_s2(_):
    return None


@app.callback(
    Output('path-s3', 'value'),
    Input('path-s2', 'value'),
    prevent_initial_call=True,
)
def reset_path_s3(_):
    return None


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True, port=8050, host='0.0.0.0')
