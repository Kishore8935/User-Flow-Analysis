import plotly.graph_objects as go
import plotly.express as px


def _hex_to_rgba(hex_color, alpha):
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'


COLORS = {
    'overview':  '#0284c7',
    'radiology': '#6366f1',
    'system':    '#059669',
    'reports':   '#d97706',
}

_BASE = dict(
    font=dict(family='Inter, system-ui, sans-serif', size=12),
    paper_bgcolor='white',
    plot_bgcolor='#f8fafc',
    margin=dict(l=12, r=12, t=40, b=12),
)


def _empty(msg='No data yet'):
    fig = go.Figure()
    fig.add_annotation(
        text=msg, xref='paper', yref='paper', x=0.5, y=0.5,
        showarrow=False, font=dict(size=13, color='#94a3b8', family='Inter, sans-serif')
    )
    fig.update_layout(
        paper_bgcolor='white', plot_bgcolor='#f8fafc',
        margin=dict(l=12, r=12, t=12, b=12), height=300
    )
    return fig


def build_sankey(df):
    if df.empty:
        return _empty('No events for this session')

    enters = df[df['event'] == 'section_enter'].sort_values('flow_position').reset_index(drop=True)
    exits  = df[df['event'] == 'section_exit'].sort_values('flow_position')

    time_map = dict(zip(exits['flow_position'], exits['time_spent_ms']))
    sections = enters['section'].tolist()

    if len(sections) < 2:
        return _empty('Visit at least 2 sections to see a flow diagram')

    node_labels = [s.title() for s in sections]
    node_colors = [COLORS.get(s, '#94a3b8') for s in sections]

    sources, targets, values, link_labels = [], [], [], []
    for i in range(len(sections) - 1):
        sources.append(i)
        targets.append(i + 1)
        ms  = time_map.get(enters.iloc[i]['flow_position']) or 1000
        val = max(round(ms / 1000, 1), 0.5)
        values.append(val)
        link_labels.append(f'{val}s in {sections[i].title()}')

    fig = go.Figure(go.Sankey(
        arrangement='snap',
        node=dict(
            pad=24, thickness=22,
            label=node_labels,
            color=node_colors,
            line=dict(color='white', width=1),
            hovertemplate='%{label}<extra></extra>',
        ),
        link=dict(
            source=sources, target=targets, value=values, label=link_labels,
            color='rgba(99,102,241,0.15)',
            hovertemplate='%{label}<extra></extra>',
        ),
    ))
    fig.update_layout(
        height=320, margin=dict(l=12, r=12, t=12, b=12),
        paper_bgcolor='white',
        font=dict(family='Inter, sans-serif', size=13),
    )
    return fig


def build_gantt(df):
    if df.empty:
        return _empty()

    enters = df[df['event'] == 'section_enter'].copy().reset_index(drop=True)
    exits  = df[df['event'] == 'section_exit'].copy().reset_index(drop=True)

    exits = exits.rename(columns={'ts_ist': 'ts_end', 'time_spent_ms': 'ms_end'})
    merged = enters.merge(
        exits[['flow_position', 'ts_end', 'ms_end']],
        on='flow_position', how='inner'
    )

    if merged.empty:
        return _empty('No completed section visits yet')

    merged['label'] = merged.apply(
        lambda r: f"{r['section'].title()}  ({round((r['ms_end'] or 0) / 1000, 1)}s)", axis=1
    )
    merged = merged.rename(columns={'ts_ist': 'Start', 'ts_end': 'Finish', 'section': 'Section'})

    fig = px.timeline(
        merged,
        x_start='Start', x_end='Finish',
        y='Section', color='Section',
        color_discrete_map=COLORS,
        text='label',
    )
    fig.update_traces(textposition='inside', insidetextanchor='middle')
    fig.update_yaxes(
        autorange='reversed', title='',
        categoryorder='array',
        categoryarray=list(COLORS.keys()),
    )
    fig.update_xaxes(title='Time (IST)')
    fig.update_layout(
        showlegend=False, height=240,
        font=dict(family='Inter, sans-serif', size=12),
        paper_bgcolor='white', plot_bgcolor='#f8fafc',
        margin=dict(l=12, r=12, t=12, b=12),
    )
    return fig


def build_section_bars(df):
    if df.empty:
        return _empty()
    colors = [COLORS.get(s, '#94a3b8') for s in df['section']]
    fig = go.Figure(go.Bar(
        x=df['section'].str.title(), y=df['visit_count'],
        marker_color=colors,
        text=df['visit_count'], textposition='outside',
        hovertemplate='%{x}: %{y} visits<extra></extra>',
    ))
    fig.update_layout(
        title=dict(text='Section Visit Counts', font=dict(size=13, color='#374151')),
        height=300, yaxis=dict(gridcolor='rgba(15,23,42,0.06)'), **_BASE
    )
    return fig


def build_avg_time(df):
    if df.empty:
        return _empty()
    df = df.dropna(subset=['avg_sec'])
    if df.empty:
        return _empty('No time data yet — exit events needed')
    colors = [COLORS.get(s, '#94a3b8') for s in df['section']]
    fig = go.Figure(go.Bar(
        x=df['section'].str.title(), y=df['avg_sec'],
        marker_color=colors,
        text=df['avg_sec'].apply(lambda x: f'{x}s'), textposition='outside',
        hovertemplate='%{x}: %{y}s avg<extra></extra>',
    ))
    fig.update_layout(
        title=dict(text='Avg Time per Section (seconds)', font=dict(size=13, color='#374151')),
        height=300, yaxis=dict(gridcolor='rgba(15,23,42,0.06)', title='seconds'), **_BASE
    )
    return fig


def build_daily_line(df):
    if df.empty:
        return _empty()
    fig = px.line(df, x='day', y='sessions', markers=True, line_shape='spline')
    fig.update_traces(
        line=dict(color='#6366f1', width=2.5),
        marker=dict(color='#6366f1', size=8),
        fill='tozeroy', fillcolor='rgba(99,102,241,0.08)',
        hovertemplate='%{x}: %{y} sessions<extra></extra>',
    )
    fig.update_layout(
        title=dict(text='Daily Sessions', font=dict(size=13, color='#374151')),
        height=300, xaxis_title='', yaxis_title='Sessions',
        yaxis=dict(gridcolor='rgba(15,23,42,0.06)'), **_BASE
    )
    return fig


def build_heatmap(df):
    if df.empty:
        return _empty()
    sections = ['overview', 'radiology', 'system', 'reports']
    pivot = (
        df.pivot(index='from_section', columns='to_section', values='count')
          .fillna(0)
          .reindex(index=sections, columns=sections, fill_value=0)
    )
    fig = px.imshow(
        pivot,
        color_continuous_scale='Blues', text_auto=True,
        labels=dict(x='To Section', y='From Section', color='Transitions'),
        title='Navigation Transitions',
    )
    fig.update_xaxes(ticktext=[s.title() for s in sections], tickvals=sections)
    fig.update_yaxes(ticktext=[s.title() for s in sections], tickvals=sections)
    fig.update_layout(
        height=360,
        font=dict(family='Inter, sans-serif', size=12),
        paper_bgcolor='white',
        margin=dict(l=12, r=12, t=60, b=12),
        title=dict(font=dict(size=13, color='#374151')),
    )
    return fig


def build_funnel(df):
    if df.empty:
        return _empty()
    labels_map = {1: '1 section', 2: '2 sections', 3: '3 sections', 4: 'All 4 sections'}
    df = df.copy()
    df['label'] = df['depth'].map(labels_map).fillna(df['depth'].astype(str) + ' sections')
    palette = ['#0284c7', '#6366f1', '#059669', '#d97706']
    fig = go.Figure(go.Funnel(
        y=df['label'], x=df['sessions'],
        textinfo='value+percent initial',
        marker=dict(color=palette[:len(df)]),
        connector=dict(line=dict(color='rgba(15,23,42,0.1)', width=1)),
    ))
    fig.update_layout(
        title=dict(text='Session Depth Funnel', font=dict(size=13, color='#374151')),
        height=320,
        font=dict(family='Inter, sans-serif', size=12),
        paper_bgcolor='white',
        margin=dict(l=12, r=12, t=60, b=12),
    )
    return fig


def build_path_bars(df, selected=None):
    """
    Horizontal bar chart showing next-step distribution for the path explorer.
    `selected` = the section currently chosen at this step (dims that bar to full,
    others to 30% opacity).
    """
    if df.empty:
        return _empty()

    df = df.copy()
    display, bar_colors, text_labels = [], [], []

    for _, row in df.iterrows():
        s = row['next_section']
        is_ended = s == '(session ended)'
        label    = '↩  Ended here' if is_ended else s.title()
        base     = '#94a3b8' if is_ended else COLORS.get(s.lower(), '#94a3b8')

        if selected is None:
            color = base
        elif s.lower() == selected.lower():
            color = base
        else:
            color = _hex_to_rgba(base, 0.25)

        display.append(label)
        bar_colors.append(color)
        text_labels.append(f"  {int(row['sessions'])}  ({row['pct']}%)")

    fig = go.Figure(go.Bar(
        x=df['sessions'].tolist(),
        y=display,
        orientation='h',
        marker_color=bar_colors,
        text=text_labels,
        textposition='outside',
        cliponaxis=False,
        hovertemplate='%{y}: %{x} sessions<extra></extra>',
        marker_line_width=0,
    ))

    fig.update_layout(
        height=max(160, 48 + len(df) * 56),
        xaxis=dict(
            showgrid=False, showticklabels=False, showline=False, zeroline=False,
            range=[0, df['sessions'].max() * 1.55],
        ),
        yaxis=dict(
            showgrid=False, showline=False, zeroline=False,
            tickfont=dict(size=13, color='#374151'),
            automargin=True,
        ),
        paper_bgcolor='white',
        plot_bgcolor='white',
        margin=dict(l=4, r=8, t=8, b=8),
        font=dict(family='Inter, sans-serif', size=12),
        showlegend=False,
        bargap=0.38,
    )
    return fig


def build_alluvial(df):
    """Parallel categories chart — one ribbon per session, colored by user."""
    if df.empty:
        return _empty('No session data yet')

    STEP_COLS   = ['step_1', 'step_2', 'step_3', 'step_4']
    STEP_LABELS = ['1st Section', '2nd Section', '3rd Section', '4th Section']
    PALETTE     = ['#6366f1', '#0284c7', '#059669', '#d97706',
                   '#dc2626', '#8b5cf6', '#ec4899', '#14b8a6']

    # Keep only steps that at least one session reached
    active = [(c, l) for c, l in zip(STEP_COLS, STEP_LABELS)
              if c in df.columns and df[c].notna().any()]

    if len(active) < 2:
        return _empty('Need sessions that visit at least 2 different sections')

    df = df.copy()
    for col, _ in active:
        df[col] = df[col].fillna('—').str.title()

    # Assign a normalised float per unique user for the continuous colorscale
    users = df['user_label'].fillna('Unknown').unique().tolist()
    n     = len(users)
    norm  = {u: (i / max(n - 1, 1)) for i, u in enumerate(users)}

    if n == 1:
        colorscale = [[0, PALETTE[0]], [1, PALETTE[0]]]
    else:
        colorscale = [[i / (n - 1), PALETTE[i % len(PALETTE)]] for i in range(n)]

    color_vals = df['user_label'].fillna('Unknown').map(norm).tolist()

    dims = [
        go.parcats.Dimension(
            values=df[col].tolist(),
            label=label,
            categoryorder='category ascending',
        )
        for col, label in active
    ]

    fig = go.Figure(go.Parcats(
        dimensions=dims,
        line=dict(
            color=color_vals,
            colorscale=colorscale,
            shape='hspline',
            colorbar=dict(
                title=dict(text='User', side='right'),
                tickvals=[norm[u] for u in users],
                ticktext=[u[:20] for u in users],  # truncate long emails
                thickness=14,
                len=0.85,
                outlinewidth=0,
            ),
        ),
        hoveron='color',
        hoverinfo='count+probability',
        arrangement='freeform',
        bundlecolors=False,
        labelfont=dict(family='Inter, sans-serif', size=12, color='#374151'),
        tickfont=dict(family='Inter, sans-serif', size=11, color='#6b7280'),
    ))

    fig.update_layout(
        height=600,
        font=dict(family='Inter, sans-serif', size=12),
        paper_bgcolor='white',
        margin=dict(l=20, r=140, t=40, b=30),
    )
    return fig


def build_auth_compare(df):
    if df.empty:
        return _empty()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Sessions', x=df['auth_method'], y=df['sessions'],
        marker_color='#6366f1', text=df['sessions'], textposition='outside',
        hovertemplate='%{x}: %{y} sessions<extra></extra>',
    ))
    fig.add_trace(go.Bar(
        name='Avg sec/section', x=df['auth_method'], y=df['avg_sec'],
        marker_color='#0284c7', text=df['avg_sec'], textposition='outside',
        yaxis='y2', hovertemplate='%{x}: %{y}s avg<extra></extra>',
    ))
    fig.update_layout(
        title=dict(text='Google vs Credentials', font=dict(size=13, color='#374151')),
        barmode='group', height=320,
        yaxis=dict(title='Sessions', gridcolor='rgba(15,23,42,0.06)'),
        yaxis2=dict(title='Avg sec/section', overlaying='y', side='right', showgrid=False),
        legend=dict(orientation='h', y=-0.2),
        font=dict(family='Inter, sans-serif', size=12),
        paper_bgcolor='white', plot_bgcolor='#f8fafc',
        margin=dict(l=12, r=12, t=60, b=40),
    )
    return fig
