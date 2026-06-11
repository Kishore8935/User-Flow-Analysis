# Drilldown Charts — Implementation Plan

## Concept

Click a bar → a modal overlay slides up containing a new ECharts instance
showing granular detail for exactly that one bar. Close the modal → back to
the main dashboard. No page navigation, no chart replacement.

---

## The Three Charts Getting Drilldown

| Chart | Click target | Drilldown shows |
|-------|-------------|-----------------|
| **STAT vs Routine** (`statRoutineChart`) | A day's bar | Hourly breakdown of STAT vs Routine for that day |
| **TAT by Radiologist** (`tatRadChart`) | A radiologist's bar | Per-modality TAT split + study count for that radiologist |
| **Referral Sources** (`referralChart`) | A referrer's bar | Study-type distribution (CT / MRI / X-Ray / US / MG) for that referrer |

These three are chosen because they already have a natural "one level deeper"
story in their data.

---

## Phase A — Modal Shell (HTML)

Add one reusable modal to the bottom of `index.html`, before the `<script>` block:

```html
<div id="drilldown-overlay" class="drilldown-overlay">
  <div class="drilldown-panel">
    <div class="drilldown-header">
      <div>
        <p class="drilldown-breadcrumb" id="dd-breadcrumb">Overview</p>
        <h3 class="drilldown-title"   id="dd-title">Detail</h3>
      </div>
      <button class="drilldown-close" id="dd-close">✕</button>
    </div>
    <div id="drilldown-chart" class="drilldown-chart"></div>
  </div>
</div>
```

One modal, three chart targets — reused every time.

---

## Phase B — Modal CSS (style.css)

```css
.drilldown-overlay {
  display: none;              /* hidden by default */
  position: fixed;
  inset: 0;
  background: rgba(15,23,42,0.45);
  backdrop-filter: blur(4px);
  z-index: 1000;
  align-items: center;
  justify-content: center;
}

.drilldown-overlay.open { display: flex; }  /* JS toggles this class */

.drilldown-panel {
  background: #ffffff;
  border-radius: 20px;
  width: min(680px, 90vw);
  padding: 32px;
  box-shadow: 0 24px 64px rgba(15,23,42,0.2);
  animation: slideUp 0.22s ease;
}

@keyframes slideUp {
  from { opacity:0; transform:translateY(20px); }
  to   { opacity:1; transform:translateY(0); }
}

.drilldown-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.drilldown-breadcrumb {
  font-size: 11px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 4px;
}

.drilldown-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.drilldown-close {
  background: none;
  border: none;
  font-size: 18px;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.15s;
}
.drilldown-close:hover { background: #f1f5f9; color: #0f172a; }

.drilldown-chart { height: 300px; width: 100%; }
```

---

## Phase C — JavaScript (inside the existing `<script>` block)

### 1. Modal open/close helpers

```js
let ddChart = null; // holds the drilldown ECharts instance

function openDrilldown(breadcrumb, title, option) {
  document.getElementById('dd-breadcrumb').textContent = breadcrumb;
  document.getElementById('dd-title').textContent      = title;

  document.getElementById('drilldown-overlay').classList.add('open');

  // dispose previous instance before re-initialising
  if (ddChart) { ddChart.dispose(); ddChart = null; }
  ddChart = echarts.init(document.getElementById('drilldown-chart'));
  ddChart.setOption(option);
}

function closeDrilldown() {
  document.getElementById('drilldown-overlay').classList.remove('open');
  if (ddChart) { ddChart.dispose(); ddChart = null; }
}

document.getElementById('dd-close').addEventListener('click', closeDrilldown);
// click outside the panel also closes
document.getElementById('drilldown-overlay').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) closeDrilldown();
});
```

### 2. Drilldown data

```js
// STAT vs Routine — hourly data per day
const statRoutineHourly = {
  Mon: { stat:[3,2,1,0,0,1,2,4,5,3,4,3,2,3,2,1,2,1,0,1,0,0,0,0], routine:[8,5,4,3,2,4,8,12,14,13,12,11,10,9,8,7,6,5,4,3,2,1,1,0] },
  Tue: { stat:[2,1,1,0,1,2,3,5,6,4,5,4,3,4,3,2,2,1,1,0,0,0,0,0], routine:[7,4,3,2,3,5,9,13,15,14,13,12,11,10,9,8,7,6,5,4,2,1,1,0] },
  // ... same shape for Wed–Sun
  Wed: { stat:[4,2,2,1,1,2,3,5,7,5,6,5,4,4,3,2,2,2,1,1,0,0,0,0], routine:[9,6,4,3,3,5,10,14,16,15,14,13,11,10,9,8,7,6,5,4,3,1,1,0] },
  Thu: { stat:[3,1,1,0,0,1,2,4,5,3,4,3,2,3,2,1,2,1,0,1,0,0,0,0], routine:[8,5,3,2,2,4,8,11,14,13,12,11,10,9,8,7,6,5,4,3,2,1,1,0] },
  Fri: { stat:[4,3,2,1,1,2,4,6,7,5,6,5,4,5,4,3,3,2,1,1,0,0,0,0], routine:[10,7,5,4,3,6,11,16,17,16,15,14,12,11,10,9,8,7,5,4,3,2,1,0] },
  Sat: { stat:[2,1,1,0,0,1,2,3,4,3,3,2,2,2,2,1,1,1,0,0,0,0,0,0], routine:[6,3,2,2,1,3,6,9,11,11,10,9,8,7,6,5,4,3,3,2,1,1,0,0] },
  Sun: { stat:[1,1,0,0,0,1,1,2,3,2,3,2,1,2,1,1,1,1,0,0,0,0,0,0], routine:[5,3,2,1,1,2,5,8,10,9,8,8,7,6,5,4,3,2,2,1,1,0,0,0] },
};

// TAT by Radiologist — per-study-type detail + count
const tatRadDetail = {
  'Dr. Adams': { ct:{ tat:1.8, count:42 }, mri:{ tat:2.5, count:28 }, xray:{ tat:0.8, count:65 } },
  'Dr. Brown': { ct:{ tat:2.1, count:38 }, mri:{ tat:2.8, count:22 }, xray:{ tat:1.0, count:58 } },
  'Dr. Chen':  { ct:{ tat:1.9, count:45 }, mri:{ tat:2.4, count:31 }, xray:{ tat:0.9, count:70 } },
  'Dr. Davis': { ct:{ tat:2.3, count:36 }, mri:{ tat:3.1, count:19 }, xray:{ tat:1.1, count:52 } },
  'Dr. Evans': { ct:{ tat:2.0, count:40 }, mri:{ tat:2.7, count:25 }, xray:{ tat:0.9, count:61 } },
};

// Referral Sources — study type breakdown per referrer
const referralDetail = {
  'Dr. Lopez':    { CT:18, MRI:12, 'X-Ray':22, US:8,  MG:4  },
  'Dr. Robinson': { CT:22, MRI:15, 'X-Ray':26, US:9,  MG:4  },
  'Dr. Patel':    { CT:28, MRI:20, 'X-Ray':25, US:11, MG:4  },
  'Dr. Nguyen':   { CT:30, MRI:22, 'X-Ray':28, US:10, MG:5  },
  'Dr. Mitchell': { CT:36, MRI:28, 'X-Ray':35, US:13, MG:6  },
  'Dr. Harris':   { CT:44, MRI:34, 'X-Ray':42, US:16, MG:6  },
};
```

### 3. Wire up click events on each chart

**STAT vs Routine:**
```js
statRoutineChartRef.on('click', (params) => {
  const day  = params.name;   // 'Mon', 'Tue', etc.
  const data = statRoutineHourly[day];
  const hours = Array.from({length:24}, (_,i) => `${i}:00`);

  openDrilldown('STAT vs Routine', `${day} — Hourly Breakdown`, {
    tooltip: { ...TT, trigger:'axis', axisPointer:{ type:'shadow' } },
    legend: { bottom:0, itemWidth:8, itemHeight:8, textStyle:{ color:'#64748b', fontFamily:'Inter', fontSize:10 } },
    grid: { left:10, right:10, top:12, bottom:28, containLabel:true },
    xAxis: { type:'category', data:hours, ...AX, axisLabel:{ ...AX.axisLabel, rotate:45, interval:3 } },
    yAxis: { type:'value', ...AX },
    series: [
      { name:'STAT',    type:'bar', stack:'s', data:data.stat,    itemStyle:{ color:'#dc2626' } },
      { name:'Routine', type:'bar', stack:'s', data:data.routine, itemStyle:{ color:'#6366f1', borderRadius:[4,4,0,0] } }
    ]
  });
});
```

**TAT by Radiologist:**
```js
tatRadChartRef.on('click', (params) => {
  const name = params.name;
  const d    = tatRadDetail[name];
  openDrilldown('TAT by Radiologist', `${name} — Modality Detail`, {
    tooltip: { ...TT, trigger:'axis', axisPointer:{ type:'shadow' } },
    grid: { left:10, right:10, top:12, bottom:10, containLabel:true },
    xAxis: { type:'category', data:['CT Scan', 'MRI', 'X-Ray'], ...AX },
    yAxis: [
      { type:'value', name:'Avg TAT (hrs)', ...AX },
      { type:'value', name:'Studies', ...AX, splitLine:{ show:false } }
    ],
    series: [
      { name:'Avg TAT', type:'bar', data:[d.ct.tat, d.mri.tat, d.xray.tat], barMaxWidth:48,
        itemStyle:{ color: lg(0,0,0,1,[[0,'#6366f1'],[1,'rgba(99,102,241,0.4)']]), borderRadius:[6,6,0,0] } },
      { name:'Study Count', type:'line', yAxisIndex:1,
        data:[d.ct.count, d.mri.count, d.xray.count],
        lineStyle:{ color:'#0284c7', width:2.5 }, symbol:'circle', symbolSize:7,
        itemStyle:{ color:'#0284c7', borderColor:'#fff', borderWidth:2 } }
    ]
  });
});
```

**Referral Sources:**
```js
referralChartRef.on('click', (params) => {
  const name = params.name;
  const d    = referralDetail[name];
  const types = Object.keys(d);
  const vals  = Object.values(d);
  openDrilldown('Referral Sources', `${name} — Study Type Breakdown`, {
    tooltip: { ...TT, trigger:'item', formatter:'{b}: {c} studies ({d}%)' },
    series: [{
      type: 'pie',
      radius: ['38%', '65%'],
      center: ['50%', '48%'],
      itemStyle: { borderRadius:6, borderColor:'#fff', borderWidth:2 },
      label: { formatter:'{b}\n{c}', fontFamily:'Inter', fontSize:11, color:'#0f172a' },
      data: types.map((t, i) => ({
        name: t, value: vals[i],
        itemStyle: { color: ['#0284c7','#6366f1','#059669','#d97706','#dc2626'][i] }
      }))
    }]
  });
});
```

---

## Phase D — Store Chart References

`init()` currently returns the chart instance but it's not being captured for
every chart. Change the three target charts to capture their return value:

```js
// Before (current):
init('statRoutineChart', { ... });

// After (needed):
const statRoutineChartRef = init('statRoutineChart', { ... });
const tatRadChartRef      = init('tatRadChart', { ... });
const referralChartRef    = init('referralChart', { ... });
```

---

## Phase E — Cursor Hint (UX Polish)

Add to CSS so users know bars are clickable:

```css
/* Applied inside each chart's ECharts option */
/* emphasis.itemStyle already highlights on hover — also set cursor via JS: */
```

In the ECharts option for each drilldown-enabled chart, add:

```js
cursor: 'pointer'   // inside each series object
```

---

## Files Changed

| Action | File | What changes |
|--------|------|-------------|
| `[MODIFY]` | `public/index.html` | Add modal HTML shell above `<script>` |
| `[MODIFY]` | `public/style.css` | Add overlay + panel CSS |
| `[MODIFY]` | `public/index.html` | Store chart refs, add drilldown data, add click handlers, add modal JS |

---

## Order of Implementation

1. Add the modal HTML to `index.html`
2. Add the modal CSS to `style.css`
3. Capture the three chart refs in the script
4. Add `openDrilldown` / `closeDrilldown` helpers
5. Add the drilldown data objects
6. Wire click handlers to each of the three charts
7. Test each one — click a bar, verify modal opens with correct title and data, close works

---

## What This Does NOT Cover

- Real API data (all drilldown data is static mock, matching the existing pattern)
- Infinite nesting / level 3 drill (two levels is enough for this dashboard)
- Mobile touch (works but no swipe-to-close added)
