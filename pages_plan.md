# Multi-Page Dashboard — Implementation Plan

## Navigation Mechanism

Right now all nav items are dead `<a href="#">` links and one `<main>` block
holds everything. The approach is pure show/hide — no routing, no page loads,
no frameworks.

### How it works

1. Wrap existing content in `<div id="section-overview" class="page-section">`
2. Add three new `<div id="section-radiology" ...>`, `<div id="section-system" ...>`, `<div id="section-reports" ...>` — initially `display:none`
3. A tiny JS `switchSection(name)` function shows one section, hides the others,
   and updates the `active` class on the nav
4. ECharts in hidden sections are **lazily initialised** — the first time you
   click a tab the charts render; subsequent visits just call `.resize()`.
   This is required because ECharts renders with zero size inside `display:none` divs.

```js
const sectionChartInits = {}; // tracks which sections have been initialised

function switchSection(name) {
  document.querySelectorAll('.page-section').forEach(s => s.style.display = 'none');
  document.getElementById(`section-${name}`).style.display = 'block';
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(`nav-${name}`).classList.add('active');

  if (!sectionChartInits[name]) {
    sectionChartInits[name] = true;
    initSection_[name]();   // calls the section-specific init function
  }
}
```

---

## Section A — Radiology

**Theme:** deep-dive into radiology workflow — TAT, body parts, exam types, radiologist performance.

### KPI Cards (4)
| Label | Value | Delta |
|---|---|---|
| Avg TAT Today | 2.1 hrs | ↓ 12 min vs yesterday |
| STAT Compliance | 91% | ↑ 3% vs last week |
| Studies Read Today | 477 | ↑ 8% vs yesterday |
| Critical Findings | 18 | ↓ 2 vs yesterday |

### Charts & Components (6)

**1. TAT by Priority — 30-day trend** (line chart, 2-series)
- X: last 30 days (sampled as 30 data points)
- Y: avg TAT in hours
- Series: STAT (red line), Routine (indigo line)
- Mark line: target TAT (dashed)

**2. Studies by Body Part** (horizontal bar)
- Y: Chest · Abdomen · Brain · Spine · Pelvis · MSK · Extremities
- X: study count
- Gradient fill bars

**3. Radiologist Scorecard** (table)
- Columns: Radiologist, Studies Today, Avg TAT, STAT Compliance, Critical Found, Status
- 6 rows of mock data
- Status badges: On Duty / Off Duty

**4. Pending Worklist by Hour** (stacked bar, 24 bars)
- X: 0:00 → 23:00
- Stacks: STAT (red) / Urgent (amber) / Routine (indigo)
- Shows how pending load distributes across the day

**5. Exam Type Distribution** (donut chart)
- Slices: CT Chest, CT Abdomen, MRI Brain, MRI Spine, Chest X-Ray, Ultrasound Abd, Mammography
- Shows study count + % on hover

**6. TAT Heatmap** (ECharts heatmap)
- X: 7 days of the week
- Y: 6 time slots (Night / Early AM / Morning / Afternoon / Evening / Late)
- Color: avg TAT in minutes — green (fast) → red (slow)

---

## Section B — System

**Theme:** infrastructure health, DICOM connectivity, storage, network.

### KPI Cards (4)
| Label | Value | Delta |
|---|---|---|
| System Uptime | 99.97% | Last 30 days |
| Active Nodes | 12 / 13 | 1 in maintenance |
| Storage Used | 68% | 355 / 520 TB |
| Network Errors | 3 | Last 24 hours |

### Charts & Components (6)

**1. Server Resource Gauges** (3 gauges)
- CPU Load: 47%
- Memory: 68%
- Disk I/O: 34%
- Same gauge style as the existing CPU core gauges

**2. Network Throughput — 24h** (dual-line chart)
- X: 24 hourly slots
- Series: Inbound (GB/s), Outbound (GB/s)
- Area fill

**3. DICOM Node Status** (table)
- Columns: Node Name, IP Address, Status (Online/Offline badge), Last Ping, Studies Today
- 7 rows (mix of online/offline/maintenance)

**4. Error Rate Trend** (area chart, 7 days)
- Series: DICOM errors, Network timeouts, Auth failures
- Stacked area

**5. Storage by Category** (horizontal stacked bar — 1 bar)
- Segments: Active Archive (cyan) / Cold Storage (indigo) / Backup (mint) / Temp (amber)
- Shows TB used per category with labels

**6. System Event Log** (styled list)
- 6 timestamped events with severity icons
- e.g. "Node DC-03 came online", "Nightly sync completed", "Alert: disk threshold 70%"

---

## Section C — Reports

**Theme:** monthly analytics, compliance summaries, quality metrics, export tools.

### KPI Cards (4)
| Label | Value | Delta |
|---|---|---|
| Studies This Month | 5,842 | ↑ 7.3% vs last month |
| Avg TAT (Month) | 2.2 hrs | ↓ 8 min vs last month |
| STAT Compliance | 93% | Target: 95% |
| Report Quality Score | 97.4% | ↑ 0.6% vs last month |

### Charts & Components (6)

**1. Monthly Volume — This vs Last Month** (grouped bar by modality)
- X: CT · MRI · X-Ray · Ultrasound · Mammography
- 2 bars per modality: This Month (solid) / Last Month (lighter)

**2. 30-Day TAT Trend** (line chart)
- Actual daily avg TAT line
- Dashed target line at 2.0 hrs
- Shaded area above target = red tint, below = green tint

**3. Compliance by Week** (grouped bar, 4 weeks)
- X: Week 1 · Week 2 · Week 3 · Week 4
- 3 bars: STAT compliance / Urgent compliance / Routine compliance
- Reference line at 95% target

**4. Top Procedures by Volume** (horizontal bar)
- Top 8 exam types this month
- CT Chest, CXR, CT Abdomen, MRI Brain, US Abdomen, MRI Spine, CT Head, MG Bilateral

**5. Quality Metrics Panel** (4 stat cards in a 2×2 grid)
- Critical Concordance Rate: 98.2%
- Addendum Rate: 1.8%
- Preliminary Report Rate: 4.1%
- Peer Review Score: 96.7%

**6. Export Panel** (3 styled action cards)
- Export CSV — study volume data
- Generate PDF Report — full monthly summary
- DICOM Audit Log — download compliance log

---

## Files Changed

| Action | File | What changes |
|---|---|---|
| `[MODIFY]` | `public/index.html` | Wrap existing content in section div; add 3 new section divs with all HTML |
| `[MODIFY]` | `public/index.html` | Add `switchSection()` nav wiring + 3 lazy `initSection_X()` functions in `<script>` |
| `[MODIFY]` | `public/style.css` | Add `.page-section` utility + any section-specific component styles |

Only `index.html` and `style.css` are touched. No new files, no new dependencies.

---

## Order of Implementation

1. Add `switchSection()` nav wiring + wrap existing content in `#section-overview`
2. Build Section A (Radiology) HTML + charts
3. Build Section B (System) HTML + charts
4. Build Section C (Reports) HTML + charts
5. Test each tab: charts render on first visit, resize on subsequent visits

---

## Total chart count added
- Radiology: 6 charts
- System: 5 charts + 1 table
- Reports: 4 charts + 2 panel components

**12 new ECharts instances** (all lazily initialised, no performance impact on initial load).
