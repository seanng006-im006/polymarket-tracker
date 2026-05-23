import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict

st.set_page_config(
    page_title="Polymarket Tracker",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .market-card {
        background: #13131f;
        border: 1px solid #22223a;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.8rem;
    }
    .spike-card {
        background: #1a1010;
        border: 1px solid #ff4444;
        border-radius: 14px;
        padding: 1rem 1.4rem;
        margin-bottom: 0.6rem;
    }
    .question { font-size: 1rem; font-weight: 600; color: #e8e8f0; line-height: 1.4; }
    .meta     { font-size: 0.75rem; color: #666688; margin: 2px 0 8px; }
    .vol-big  { font-size: 1.4rem; font-weight: 700; color: #e8e8f0; }
    .vol-sub  { font-size: 0.75rem; color: #666688; }
    .yes-btn  { background:#1a3a1a; color:#34d399; border:1px solid #34d399;
                border-radius:8px; padding:6px 18px; font-weight:700; font-size:0.9rem; }
    .no-btn   { background:#3a1a1a; color:#f87171; border:1px solid #f87171;
                border-radius:8px; padding:6px 18px; font-weight:700; font-size:0.9rem; }
    .prob-yes { font-size:1.6rem; font-weight:800; color:#34d399; }
    .prob-no  { font-size:1.6rem; font-weight:800; color:#f87171; }
    .prob-mid { font-size:1.6rem; font-weight:800; color:#fbbf24; }
    .spike-badge {
        background:#ff2222; color:#fff; border-radius:6px;
        padding:2px 10px; font-size:0.72rem; font-weight:700; margin-left:8px;
    }
    .shift-up   { color:#34d399; font-weight:700; }
    .shift-down { color:#f87171; font-weight:700; }
    .rank { font-size:0.72rem; color:#44446a; font-weight:700; margin-bottom:4px; }
    .pill {
        display:inline-block; background:#1e1e30; border-radius:20px;
        padding:2px 10px; font-size:0.7rem; color:#7777aa; margin-right:4px;
    }
    .section-header {
        font-size:0.8rem; font-weight:700; color:#555577;
        letter-spacing:0.12em; text-transform:uppercase;
        margin: 1.2rem 0 0.6rem;
    }
    div[data-testid="stMetricValue"] { font-size: 1.3rem !important; }
</style>
""", unsafe_allow_html=True)

GAMMA_API  = "https://gamma-api.polymarket.com"
REFRESH_8H = 8 * 3600

# ── Session state init ───────────────────────────────────────
if "top10"         not in st.session_state: st.session_state.top10        = None
if "top10_ts"      not in st.session_state: st.session_state.top10_ts     = 0
if "vol_history"   not in st.session_state: st.session_state.vol_history  = defaultdict(list)
if "prob_history"  not in st.session_state: st.session_state.prob_history = defaultdict(list)
if "spikes"        not in st.session_state: st.session_state.spikes       = []
if "last_live"     not in st.session_state: st.session_state.last_live    = 0

# ── Helpers ──────────────────────────────────────────────────
def fmt_vol(n):
    n = float(n or 0)
    if n >= 1e6: return f"${n/1e6:.1f}M"
    if n >= 1e3: return f"${n/1e3:.0f}K"
    return f"${n:.0f}"

def parse_outcomes(m):
    try:
        outcomes = json.loads(m.get("outcomes", "[]"))
        prices   = json.loads(m.get("outcomePrices", "[]"))
        return list(zip(outcomes, [float(p) for p in prices]))
    except:
        return []

def yes_no(pairs):
    yes = next((p for o, p in pairs if o.lower() == "yes"), None)
    no  = next((p for o, p in pairs if o.lower() == "no"),  None)
    return yes, no

def fetch_top10():
    r = requests.get(f"{GAMMA_API}/markets", params={
        "active": "true", "closed": "false",
        "limit": 10, "order": "volume24hr", "ascending": "false"
    }, timeout=10)
    r.raise_for_status()
    return r.json()

def detect_spikes(market_id, current_vol, current_prob, question, spike_vol, window_hrs):
    now   = datetime.utcnow()
    hist  = st.session_state.vol_history[market_id]
    phist = st.session_state.prob_history[market_id]

    hist.append({"t": now, "vol": current_vol})
    phist.append({"t": now, "prob": current_prob})

    cutoff = now - timedelta(hours=24)
    st.session_state.vol_history[market_id]  = [h for h in hist  if h["t"] > cutoff]
    st.session_state.prob_history[market_id] = [h for h in phist if h["t"] > cutoff]

    window_cutoff = now - timedelta(hours=window_hrs)
    window  = [h for h in st.session_state.vol_history[market_id]  if h["t"] > window_cutoff]
    pwindow = [h for h in st.session_state.prob_history[market_id] if h["t"] > window_cutoff]

    if len(window) < 2:
        return None

    vol_gain   = window[-1]["vol"] - window[0]["vol"]
    prob_shift = (pwindow[-1]["prob"] - pwindow[0]["prob"]) if len(pwindow) >= 2 else None

    if vol_gain >= spike_vol:
        existing = [s for s in st.session_state.spikes
                    if s["id"] == market_id and (now - s["detected_at"]).seconds < 3600]
        if not existing:
            spike = {
                "id": market_id, "question": question,
                "vol_gain": vol_gain, "prob_shift": prob_shift,
                "current_prob": current_prob, "detected_at": now,
            }
            st.session_state.spikes.insert(0, spike)
            st.session_state.spikes = st.session_state.spikes[:20]
            return spike
    return None

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    spike_threshold = st.number_input(
        "Spike threshold ($)", min_value=50_000,
        max_value=5_000_000, value=250_000, step=50_000, format="%d"
    )
    window_hrs = st.slider("Spike window (hours)", 1, 12, 3)
    auto_refresh = st.toggle("Auto-refresh (60s)", value=False)
    st.markdown("---")
    st.caption("Top 10 list refreshes 3× per day (every 8h).")
    st.caption("Prices & volume refresh every 60s when auto-refresh is on.")
    st.caption("Data: [Polymarket Gamma API](https://gamma-api.polymarket.com)")
    if st.button("🔄 Force refresh everything"):
        st.session_state.top10_ts = 0

# ── Refresh top-10 every 8h ──────────────────────────────────
now_ts = time.time()
if (now_ts - st.session_state.top10_ts) > REFRESH_8H or st.session_state.top10 is None:
    try:
        with st.spinner("Refreshing top 10 markets…"):
            st.session_state.top10    = fetch_top10()
            st.session_state.top10_ts = now_ts
    except Exception as e:
        st.error(f"API error: {e}")
        st.stop()

markets = st.session_state.top10

# ── Live spike detection (every 60s) ────────────────────────
if (now_ts - st.session_state.last_live) > 60:
    for m in markets:
        mid   = m.get("id") or m.get("slug")
        vol   = float(m.get("volume", 0))
        pairs = parse_outcomes(m)
        yes, _ = yes_no(pairs)
        if yes is None and pairs:
            yes = pairs[0][1]
        if mid and yes is not None:
            detect_spikes(mid, vol, yes, m.get("question",""), spike_threshold, window_hrs)
    st.session_state.last_live = now_ts

# ── Header ───────────────────────────────────────────────────
st.markdown("# 📊 Polymarket Tracker")
next_refresh = datetime.utcfromtimestamp(st.session_state.top10_ts + REFRESH_8H)
st.caption(
    f"Top 10 updated: {datetime.utcfromtimestamp(st.session_state.top10_ts).strftime('%d %b %H:%M')} UTC  ·  "
    f"Next: {next_refresh.strftime('%H:%M')} UTC  ·  "
    f"Now: {datetime.utcnow().strftime('%H:%M:%S')} UTC"
)

# ── Summary metrics ──────────────────────────────────────────
total_24h = sum(float(m.get("volume24hr", 0)) for m in markets)
total_vol = sum(float(m.get("volume", 0)) for m in markets)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Markets tracked", len(markets))
c2.metric("Total 24h volume", fmt_vol(total_24h))
c3.metric("Total all-time vol", fmt_vol(total_vol))
c4.metric("🚨 Spikes detected", len(st.session_state.spikes))

# ── Spike alerts panel ───────────────────────────────────────
if st.session_state.spikes:
    st.markdown('<div class="section-header">🚨 Volume Spike Alerts</div>', unsafe_allow_html=True)
    st.caption(f">${fmt_vol(spike_threshold)} traded within {window_hrs}h · showing last {min(5, len(st.session_state.spikes))}")

    for sp in st.session_state.spikes[:5]:
        age     = datetime.utcnow() - sp["detected_at"]
        age_str = f"{int(age.seconds/60)}m ago" if age.seconds < 3600 else f"{int(age.seconds/3600)}h ago"

        shift_html = ""
        if sp["prob_shift"] is not None and abs(sp["prob_shift"]) >= 0.005:
            direction = "▲" if sp["prob_shift"] > 0 else "▼"
            cls = "shift-up" if sp["prob_shift"] > 0 else "shift-down"
            shift_html = f'<span class="{cls}">{direction} {abs(sp["prob_shift"]*100):.1f}pp</span>'

        st.markdown(f"""
        <div class="spike-card">
          <span class="spike-badge">SPIKE</span>
          <span style="font-size:0.75rem;color:#888;margin-left:8px;">{age_str}</span><br>
          <span class="question">{sp['question'][:80]}{'…' if len(sp['question'])>80 else ''}</span><br>
          <span style="color:#ff6666;font-weight:700;">+{fmt_vol(sp['vol_gain'])}</span>
          <span style="color:#666;font-size:0.8rem;"> in {window_hrs}h</span>
          {"&nbsp;&nbsp;" + shift_html if shift_html else ""}
          &nbsp;&nbsp;<span style="color:#aaa;font-size:0.8rem;">YES: {sp['current_prob']*100:.0f}%</span>
        </div>
        """, unsafe_allow_html=True)

# ── Market cards ─────────────────────────────────────────────
st.markdown('<div class="section-header">Top 10 Most Active Markets</div>', unsafe_allow_html=True)

for i, m in enumerate(markets, 1):
    question = m.get("question", "Unknown")
    cat      = m.get("groupItemTitle") or m.get("category") or ""
    v24      = float(m.get("volume24hr", 0))
    vtot     = float(m.get("volume", 0))
    slug     = m.get("slug", "")
    url      = m.get("url") or (f"https://polymarket.com/event/{slug}" if slug else None)
    pairs    = parse_outcomes(m)
    yes, no  = yes_no(pairs)

    is_binary = (
        len(pairs) == 2 and
        any(o.lower() == "yes" for o, _ in pairs) and
        any(o.lower() == "no"  for o, _ in pairs)
    )

    mid       = m.get("id") or m.get("slug")
    has_spike = any(
        s["id"] == mid for s in st.session_state.spikes
        if (datetime.utcnow() - s["detected_at"]).seconds < window_hrs * 3600
    )

    col_info, col_prob, col_vol = st.columns([3, 1.5, 1])

    with col_info:
        spike_tag = '<span class="spike-badge">SPIKE</span>' if has_spike else ''
        q_text = f'<a href="{url}" target="_blank" style="color:#e8e8f0;text-decoration:none;">{question}</a>' if url else question
        st.markdown(f"""
        <div class="rank">#{i}</div>
        <div class="question">{q_text} {spike_tag}</div>
        <div class="meta">{cat}</div>
        """, unsafe_allow_html=True)

        if is_binary and yes is not None:
            yes_c = int(yes * 100)
            no_c  = 100 - yes_c
            st.markdown(f"""
            <span class="yes-btn">Buy Yes {yes_c}¢</span>&nbsp;&nbsp;
            <span class="no-btn">Buy No {no_c}¢</span>
            """, unsafe_allow_html=True)
        elif pairs:
            pills = "".join(
                f'<span class="pill">{o} {int(p*100)}¢</span>'
                for o, p in pairs[:4]
            )
            st.markdown(pills, unsafe_allow_html=True)

    with col_prob:
        if is_binary and yes is not None:
            pct = yes * 100
            cls = "prob-yes" if pct >= 65 else ("prob-mid" if pct >= 35 else "prob-no")
            st.markdown(f'<div class="{cls}" style="text-align:center;margin-bottom:4px;">{pct:.0f}%</div>', unsafe_allow_html=True)
            st.progress(yes)
            st.caption("YES probability")
        elif pairs:
            for label, prob in pairs[:3]:
                st.caption(f"{label}: {prob*100:.0f}%")
                st.progress(prob)

    with col_vol:
        st.markdown(
            f'<div class="vol-big">{fmt_vol(v24)}</div>'
            f'<div class="vol-sub">24h volume</div>'
            f'<div style="margin-top:8px;">'
            f'<div class="vol-sub">All-time</div>'
            f'<div style="font-size:1rem;font-weight:600;color:#aaa;">{fmt_vol(vtot)}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.divider()

# ── Probability shift log ────────────────────────────────────
shifts = []
for m in markets:
    mid   = m.get("id") or m.get("slug")
    phist = st.session_state.prob_history.get(mid, [])
    if len(phist) >= 2:
        delta = phist[-1]["prob"] - phist[0]["prob"]
        if abs(delta) >= 0.01:
            shifts.append((delta, m.get("question",""), phist[0]["prob"], phist[-1]["prob"]))

if shifts:
    st.markdown('<div class="section-header">📈 Probability Shifts (this session)</div>', unsafe_allow_html=True)
    for delta, q, start, end in sorted(shifts, key=lambda x: abs(x[0]), reverse=True):
        direction = "▲" if delta > 0 else "▼"
        cls = "shift-up" if delta > 0 else "shift-down"
        st.markdown(
            f'<span class="{cls}">{direction} {abs(delta*100):.1f}pp</span>'
            f'&nbsp;&nbsp;<span style="color:#aaa;font-size:0.85rem;">{q[:65]}…</span>'
            f'&nbsp;&nbsp;<span style="color:#666;font-size:0.8rem;">{start*100:.0f}% → {end*100:.0f}%</span>',
            unsafe_allow_html=True
        )

# ── Auto-refresh ─────────────────────────────────────────────
if auto_refresh:
    time.sleep(60)
    st.rerun()
