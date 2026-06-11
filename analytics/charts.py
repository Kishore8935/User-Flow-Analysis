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


def build_session_heatmap(df, max_steps=10, sort_by='date'):
    """
    2D heatmap: rows = sessions (variable length), columns = step positions.
    Color = section at that step. Gray = session ended before reaching that step.
    Handles any path depth — no fixed column cap on the data side.
    """
    if df.empty:
        return _empty('No session data yet')

    df = df.copy()

    # Sort
    if sort_by == 'depth':
        df = df.sort_values('depth', ascending=False).reset_index(drop=True)
    elif sort_by == 'user':
        df = df.sort_values(['user_label', 'started_at']).reset_index(drop=True)
    else:
        df = df.sort_values('started_at', ascending=False).reset_index(drop=True)

    actual_max = int(df['depth'].max()) if not df.empty else 1
    n_cols     = min(max_steps, actual_max)
    n_rows     = len(df)

    # section → integer (0 = ended/gray)
    S_INT = {'overview': 1, 'radiology': 2, 'system': 3, 'reports': 4}

    z_matrix, hover_matrix, y_labels = [], [], []

    for _, row in df.iterrows():
        seq = row['seq']
        if not isinstance(seq, list):
            seq = list(seq) if seq else []

        z_row, h_row = [], []
        for i in range(n_cols):
            if i < len(seq):
                s = seq[i]
                z_row.append(S_INT.get(s, 0))
                h_row.append(f'<b>Step {i + 1}</b>: {s.title()}')
            else:
                z_row.append(0)
                h_row.append(f'<b>Step {i + 1}</b>: session ended')

        z_matrix.append(z_row)
        hover_matrix.append(h_row)

        user  = str(row['user_label'])[:16]
        label = f"{user}  ·  {row['started_fmt']}"
        y_labels.append(label)

    # Discrete colorscale: 5 bands for values 0-4 (zmin=0, zmax=4)
    # Normalised positions: 0→0.0, 1→0.25, 2→0.5, 3→0.75, 4→1.0
    CSCALE = [
        [0.00, '#e8edf2'], [0.20, '#e8edf2'],   # 0: ended
        [0.20, '#0284c7'], [0.40, '#0284c7'],   # 1: overview
        [0.40, '#6366f1'], [0.60, '#6366f1'],   # 2: radiology
        [0.60, '#059669'], [0.80, '#059669'],   # 3: system
        [0.80, '#d97706'], [1.00, '#d97706'],   # 4: reports
    ]

    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        z=z_matrix,
        text=hover_matrix,
        hovertemplate='%{text}<extra></extra>',
        colorscale=CSCALE,
        zmin=0, zmax=4,
        showscale=False,
        xgap=3, ygap=2,
        name='',
    ))

    # Legend as invisible scatter markers
    for name, color, edge in [
        ('Overview',          '#0284c7', False),
        ('Radiology',         '#6366f1', False),
        ('System',            '#059669', False),
        ('Reports',           '#d97706', False),
        ('Ended / not reached', '#e8edf2', True),
    ]:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(
                symbol='square', size=12, color=color,
                line=dict(color='#94a3b8', width=1) if edge else dict(width=0),
            ),
            name=name, showlegend=True,
        ))

    fig.update_xaxes(
        tickvals=list(range(n_cols)),
        ticktext=[f'Step {i + 1}' for i in range(n_cols)],
        side='top',
        tickfont=dict(size=11, color='#64748b', family='Inter, sans-serif'),
        showgrid=False,
    )
    fig.update_yaxes(
        tickvals=list(range(n_rows)),
        ticktext=y_labels,
        tickfont=dict(size=10, color='#374151', family='Inter, sans-serif'),
        autorange='reversed',
        showgrid=False,
        automargin=True,
    )
    fig.update_layout(
        height=max(320, 60 + n_rows * 30),
        margin=dict(l=8, r=20, t=60, b=20),
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(family='Inter, sans-serif', size=11),
        legend=dict(
            orientation='h', y=-0.06,
            font=dict(size=11), itemsizing='constant',
        ),
    )
    return fig


def build_step_distribution(df, max_steps=10):
    """
    Stacked bar: at each step position, how many sessions visited which section.
    The 'Ended' slice shows how many sessions had already stopped by that step.
    """
    if df.empty:
        return _empty()

    SECTIONS   = ['overview', 'radiology', 'system', 'reports']
    actual_max = int(df['depth'].max()) if not df.empty else 1
    n_cols     = min(max_steps, actual_max)

    step_counts = {s: [0] * n_cols for s in SECTIONS}
    step_ended  = [0] * n_cols

    for _, row in df.iterrows():
        seq = row['seq']
        if not isinstance(seq, list):
            seq = list(seq) if seq else []
        for i in range(n_cols):
            if i < len(seq):
                s = seq[i]
                if s in step_counts:
                    step_counts[s][i] += 1
            else:
                step_ended[i] += 1

    x_labels = [f'Step {i + 1}' for i in range(n_cols)]

    fig = go.Figure()
    for section in SECTIONS:
        fig.add_trace(go.Bar(
            name=section.title(), x=x_labels, y=step_counts[section],
            marker_color=COLORS[section], marker_line_width=0,
            hovertemplate=f'<b>%{{x}}</b><br>{section.title()}: %{{y}}<extra></extra>',
        ))
    fig.add_trace(go.Bar(
        name='Ended / not reached', x=x_labels, y=step_ended,
        marker_color='#e2e8f0', marker_line_width=0,
        hovertemplate='<b>%{x}</b><br>Ended: %{y}<extra></extra>',
    ))

    fig.update_layout(
        barmode='stack',
        title=dict(text='Step Distribution  (aggregate across all sessions)',
                   font=dict(size=13, color='#374151')),
        height=300,
        xaxis=dict(tickfont=dict(size=11), showgrid=False),
        yaxis=dict(title='Sessions', gridcolor='rgba(15,23,42,0.06)'),
        legend=dict(orientation='h', y=-0.35, font=dict(size=11)),
        paper_bgcolor='white', plot_bgcolor='#f8fafc',
        font=dict(family='Inter, sans-serif', size=12),
        margin=dict(l=12, r=12, t=48, b=60),
    )
    return fig


def build_dropoff_chart(df):
    """Horizontal bar — which section users were in when they last exited."""
    if df.empty:
        return _empty()

    bar_colors  = [COLORS.get(s, '#94a3b8') for s in df['exit_section']]
    text_labels = [
        f"  {int(r['sessions'])}  ({r['pct']}%)   avg {r['avg_min']} min/session"
        for _, r in df.iterrows()
    ]

    fig = go.Figure(go.Bar(
        x=df['sessions'].tolist(),
        y=df['exit_section'].str.title().tolist(),
        orientation='h',
        marker_color=bar_colors,
        marker_line_width=0,
        text=text_labels,
        textposition='outside',
        cliponaxis=False,
        hovertemplate='%{y}: %{x} sessions<extra></extra>',
    ))

    fig.update_layout(
        title=dict(
            text='Drop-off Section  (last page before user left)',
            font=dict(size=13, color='#374151'),
        ),
        height=max(160, 48 + len(df) * 58),
        xaxis=dict(
            showgrid=False, showticklabels=False, showline=False, zeroline=False,
            range=[0, df['sessions'].max() * 1.75],
        ),
        yaxis=dict(showgrid=False, showline=False, zeroline=False,
                   tickfont=dict(size=13, color='#374151'), automargin=True),
        paper_bgcolor='white',
        plot_bgcolor='white',
        margin=dict(l=4, r=8, t=48, b=8),
        font=dict(family='Inter, sans-serif', size=12),
        showlegend=False,
        bargap=0.42,
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
