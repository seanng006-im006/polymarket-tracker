import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta
from supabase import create_client

st.set_page_config(page_title="Polymarket Tracker", page_icon="📊", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

* { font-family: 'Rajdhani', sans-serif; box-sizing: border-box; }
.mono { font-family: 'Share Tech Mono', monospace; }

.block-container { padding: 1rem 1.5rem; max-width: 100%; }

/* Header */
.hdr { border-bottom: 1px solid #1a1a3a; padding-bottom: 0.8rem; margin-bottom: 1rem; }
.hdr h1 {
    font-size: 1.6rem; font-weight: 700; letter-spacing: 0.15em;
    background: linear-gradient(90deg, #00f5c4, #7b61ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;
}
.hdr-sub { font-size: 0.72rem; color: #444466; letter-spacing: 0.1em; margin-top: 2px; }

/* Metric boxes */
.metric-box { background:#0d0d1f; border:1px solid #1a1a3a; border-radius:8px; padding:0.6rem 1rem; }
.metric-box .lbl { font-size:0.65rem; color:#444466; letter-spacing:0.12em; text-transform:uppercase; }
.metric-box .val { font-size:1.3rem; font-weight:700; color:#e0e0ff; font-family:'Share Tech Mono',monospace; }

/* Spike panel */
.spike-panel { background:#120a0a; border:1px solid #ff3333; border-radius:10px; padding:0.8rem 1rem; margin-bottom:0.8rem; }
.spike-title { font-size:0.65rem; color:#ff3333; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:0.5rem; }
.spike-item { border-bottom:1px solid #1a0808; padding:0.4rem 0; font-size:0.82rem; }
.spike-item:last-child { border-bottom:none; }

/* Hero card */
.hero-card {
    background:#0a0a1a; border:1px solid #1a1a3a; border-radius:14px;
    padding:1.4rem 1.6rem; margin-bottom:1rem;
}
.hero-card.has-spike { border-color:#ff3333; }
.hero-card.has-outlier { border-color:#ffaa00; }

/* Grid cards */
.grid-card {
    background:#0a0a1a; border:1px solid #1a1a3a; border-radius:12px;
    padding:0.9rem 1rem; height:100%;
}
.grid-card.has-spike { border-color:#ff3333; }
.grid-card.has-outlier { border-color:#ffaa00; }

/* Card elements */
.card-rank { font-size:0.62rem; color:#333355; font-family:'Share Tech Mono'; letter-spacing:0.1em; }
.card-q { font-size:0.9rem; font-weight:600; color:#c0c0e0; line-height:1.35; margin:3px 0 6px; }
.card-q-hero { font-size:1.15rem; font-weight:700; color:#d0d0f0; line-height:1.4; margin:4px 0 8px; }

/* Banners */
.banner-spike { background:#2a0000; border:1px solid #ff3333; border-radius:6px; padding:4px 10px; font-size:0.68rem; color:#ff4444; font-weight:700; letter-spacing:0.1em; margin-bottom:8px; }
.banner-outlier { background:#1a1000; border:1px solid #ffaa00; border-radius:6px; padding:4px 10px; font-size:0.68rem; color:#ffaa00; font-weight:700; letter-spacing:0.1em; margin-bottom:8px; }
.banner-lambda { background:#001a2a; border:1px solid #00aaff; border-radius:6px; padding:4px 10px; font-size:0.68rem; color:#00aaff; font-weight:700; letter-spacing:0.1em; margin-bottom:8px; }

/* Yes/No rows */
.yn-row { display:flex; align-items:center; gap:8px; margin:3px 0; }
.yn-label { font-size:0.75rem; color:#666688; width:24px; }
.yn-bar-wrap { flex:1; height:5px; background:#111122; border-radius:3px; overflow:hidden; }
.yn-bar-yes { height:100%; background:#00f5a0; border-radius:3px; }
.yn-bar-no  { height:100%; background:#7b61ff; border-radius:3px; }
.yn-pct { font-size:0.82rem; font-weight:700; color:#e0e0ff; font-family:'Share Tech Mono'; width:42px; text-align:right; }

/* Badges */
.badge-row { display:flex; flex-wrap:wrap; gap:4px; margin:6px 0; }
.badge { border-radius:5px; padding:2px 7px; font-size:0.68rem; font-weight:700; font-family:'Share Tech Mono'; white-space:nowrap; }
.badge-vol-pos { background:#0a2010; color:#00cc80; border:1px solid #00cc80; }
.badge-vol-neu { background:#0d0d1f; color:#444466; border:1px solid #222244; }
.badge-pp-up   { background:#0a2010; color:#00f5a0; border:1px solid #00f5a0; }
.badge-pp-dn   { background:#200a0a; color:#ff5555; border:1px solid #ff5555; }
.badge-pp-neu  { background:#0d0d1f; color:#444466; border:1px solid #222244; }
.badge-spike   { background:#200000; color:#ff3333; border:1px solid #ff3333; }
.badge-outlier { background:#201000; color:#ffaa00; border:1px solid #ffaa00; }

/* Stats */
.stat-row { display:grid; grid-template-columns:1fr 1fr; gap:6px; margin:8px 0; }
.stat-box { background:#070712; border-radius:6px; padding:5px 8px; }
.stat-lbl { font-size:0.6rem; color:#444466; letter-spacing:0.08em; text-transform:uppercase; }
.stat-val { font-size:0.88rem; font-weight:700; color:#c0c0e0; font-family:'Share Tech Mono'; }

.ends-liq { display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-top:4px; }
.el-lbl { font-size:0.6rem; color:#444466; letter-spacing:0.08em; text-transform:uppercase; }
.el-val { font-size:0.8rem; color:#888899; font-family:'Share Tech Mono'; }

.sec-hdr { font-size:0.65rem; color:#333355; letter-spacing:0.15em; text-transform:uppercase; margin:0.8rem 0 0.5rem; border-top:1px solid #0d0d1f; padding-top:0.6rem; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────
GAMMA_API    = "https://gamma-api.polymarket.com"
CLOB_API     = "https://clob.polymarket.com"
SUPABASE_URL = "https://llwpjeokrxfuingxiksk.supabase.co"
SUPABASE_KEY = "sb_publishable_ovPph4WdVncPNq6AHztH_A_Ng8SlHlv"
TG_TOKEN     = "8973431939:AAF0HEC13sfGTO_d8-K5UU_DNlWPwyFL8wI"
TG_CHAT_ID   = "8928074857"
REFRESH_8H   = 8 * 3600
CLEANUP_DAYS = 7

VOL_THRESHOLDS = {"1h": 100_000, "3h": 250_000, "6h": 500_000, "24h": 2_000_000}

# ── Supabase ──────────────────────────────────────────────────
@st.cache_resource
def get_sb():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Helpers ───────────────────────────────────────────────────
def fmt_vol(n):
    n = float(n or 0)
    if n >= 1e6: return f"${n/1e6:.1f}M"
    if n >= 1e3: return f"${n/1e3:.0f}K"
    return f"${n:.0f}"

def fmt_pp(v):
    if v is None: return None
    return f"{'+' if v>0 else ''}{v*100:.1f}pp"

def parse_outcomes(m):
    try:
        outcomes = json.loads(m.get("outcomes","[]"))
        prices   = json.loads(m.get("outcomePrices","[]"))
        return list(zip(outcomes,[float(p) for p in prices]))
    except: return []

def yes_no(pairs):
    y = next((p for o,p in pairs if o.lower()=="yes"),None)
    n = next((p for o,p in pairs if o.lower()=="no"), None)
    return y,n

def get_token_id(m):
    try:
        ids = json.loads(m.get("clobTokenIds","[]"))
        return ids[0] if ids else None
    except: return None

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=5
        )
    except: pass

# ── CLOB price history ────────────────────────────────────────
@st.cache_data(ttl=300)
def clob_history(token_id, interval):
    try:
        r = requests.get(f"{CLOB_API}/prices-history",
            params={"market": token_id, "interval": interval, "fidelity": 60},
            timeout=8)
        if r.ok: return r.json().get("history",[])
    except: pass
    return []

def prob_shift_clob(token_id, interval):
    h = clob_history(token_id, interval)
    if len(h)<2: return None
    return h[-1]["p"] - h[0]["p"]

# ── Supabase ops ──────────────────────────────────────────────
def save_snapshot(market_id, volume, prob, question, end_date, liquidity):
    try:
        get_sb().table("volume_snapshots").insert({
            "market_id": market_id, "volume": volume, "prob": prob,
            "question": question[:200], "end_date": end_date,
            "liquidity": liquidity,
            "ts": datetime.utcnow().isoformat()
        }).execute()
    except: pass

def get_window_snaps(market_id, hours):
    try:
        since = (datetime.utcnow()-timedelta(hours=hours)).isoformat()
        r = get_sb().table("volume_snapshots")\
            .select("volume,prob,ts")\
            .eq("market_id",market_id)\
            .gte("ts",since).order("ts").execute()
        return r.data or []
    except: return []

def get_24h_lambdas(market_id):
    try:
        since = (datetime.utcnow()-timedelta(hours=24)).isoformat()
        r = get_sb().table("lambda_log")\
            .select("lambda_val")\
            .eq("market_id",market_id)\
            .gte("ts",since).execute()
        return [x["lambda_val"] for x in (r.data or [])]
    except: return []

def save_lambda(market_id, window, lambda_val):
    try:
        get_sb().table("lambda_log").insert({
            "market_id": market_id, "win": window,
            "lambda_val": lambda_val,
            "ts": datetime.utcnow().isoformat()
        }).execute()
    except: pass

def get_recent_spikes(limit=10):
    try:
        since = (datetime.utcnow()-timedelta(hours=24)).isoformat()
        r = get_sb().table("spike_log")\
            .select("*").gte("ts",since)\
            .order("ts",desc=True).limit(limit).execute()
        return r.data or []
    except: return []

def log_spike(market_id, question, vol_gain, prob_shift, current_prob, window, lambda_val):
    try:
        since = (datetime.utcnow()-timedelta(hours=1)).isoformat()
        ex = get_sb().table("spike_log")\
            .select("id").eq("market_id",market_id)\
            .eq("win",window).gte("ts",since).execute()
        if not ex.data:
            get_sb().table("spike_log").insert({
                "market_id": market_id, "question": question[:200],
                "vol_gain": vol_gain, "prob_shift": prob_shift,
                "current_prob": current_prob, "win": window,
                "lambda_val": lambda_val,
                "ts": datetime.utcnow().isoformat()
            }).execute()
    except: pass

def cleanup():
    try:
        cutoff = (datetime.utcnow()-timedelta(days=CLEANUP_DAYS)).isoformat()
        get_sb().table("volume_snapshots").delete().lt("ts",cutoff).execute()
        get_sb().table("lambda_log").delete().lt("ts",cutoff).execute()
    except: pass

# ── Kyle's Lambda detection ───────────────────────────────────
def compute_kyle(market_id, current_vol, current_prob, question, window_label, hours):
    snaps = get_window_snaps(market_id, hours)
    if len(snaps) < 2: return None, None, None

    vol_gain   = current_vol - snaps[0]["volume"]
    prob_shift = current_prob - snaps[0]["prob"]

    if vol_gain <= 0 or abs(prob_shift) < 0.001: return vol_gain, prob_shift, None

    lam = abs(prob_shift) / vol_gain

    # Compare against 24h rolling lambda
    hist_lambdas = get_24h_lambdas(market_id)
    save_lambda(market_id, window_label, lam)

    above_baseline = False
    if len(hist_lambdas) >= 5:
        avg_lam = sum(hist_lambdas) / len(hist_lambdas)
        above_baseline = lam > avg_lam * 1.5

    threshold = VOL_THRESHOLDS.get(window_label, 250_000)
    is_spike  = vol_gain >= threshold and abs(prob_shift) > 0.005

    if is_spike:
        log_spike(market_id, question, vol_gain, prob_shift, current_prob, window_label, lam)
        if window_label == "3h" and vol_gain >= 250_000:
            direction = "📈 YES" if prob_shift > 0 else "📉 NO"
            msg = (
                f"⚡ <b>POLYMARKET SPIKE ALERT</b>\n\n"
                f"<b>{question[:80]}</b>\n\n"
                f"💰 Volume: <b>+{fmt_vol(vol_gain)}</b> in 3h\n"
                f"📊 Prob shift: <b>{fmt_pp(prob_shift)}</b> {direction}\n"
                f"Current YES: <b>{current_prob*100:.1f}%</b>\n"
                f"Kyle λ: <b>{lam:.6f}</b>"
            )
            send_telegram(msg)

    return vol_gain, prob_shift, lam if above_baseline else None

# ── Fetch top 10 ──────────────────────────────────────────────
@st.cache_data(ttl=REFRESH_8H)
def fetch_top10():
    r = requests.get(f"{GAMMA_API}/markets", params={
        "active":"true","closed":"false",
        "limit":10,"order":"volume24hr","ascending":"false"
    }, timeout=10)
    r.raise_for_status()
    return r.json()

# ── Card renderer ─────────────────────────────────────────────
def render_card(m, rank, spikes, is_hero=False):
    question  = m.get("question","Unknown")
    cat       = m.get("groupItemTitle") or m.get("category") or ""
    v24       = float(m.get("volume24hr",0))
    vtot      = float(m.get("volume",0))
    liq       = float(m.get("liquidity") or m.get("liquidityClob") or 0)
    end_date  = m.get("endDate") or m.get("endDateIso","")
    slug      = m.get("slug","")
    mid       = m.get("conditionId") or m.get("id") or slug
    pairs     = parse_outcomes(m)
    yes, no   = yes_no(pairs)
    token_id  = get_token_id(m)

    is_binary = (
        len(pairs)==2 and
        any(o.lower()=="yes" for o,_ in pairs) and
        any(o.lower()=="no"  for o,_ in pairs)
    )

    # Format end date
    end_str = ""
    if end_date:
        try:
            dt = datetime.fromisoformat(end_date.replace("Z",""))
            end_str = dt.strftime("%b %d, %Y")
        except: end_str = end_date[:10]

    # Kyle's Lambda per window
    current_vol  = float(m.get("volume",0))
    current_prob = yes if yes is not None else (pairs[0][1] if pairs else 0.5)

    vol_gains, prob_shifts, lambdas = {}, {}, {}
    windows = [("1h",1),("3h",3),("6h",6),("24h",24)]
    for wl, wh in windows:
        vg, ps, lam = compute_kyle(mid, current_vol, current_prob, question, wl, wh)
        vol_gains[wl]   = vg
        prob_shifts[wl] = ps
        lambdas[wl]     = lam

    # CLOB prob shifts for longer windows
    ps_3h  = prob_shifts.get("3h")
    ps_7d  = prob_shift_clob(token_id, "1w") if token_id else None

    # Spike/outlier flags
    has_spike   = any(s["market_id"]==mid for s in spikes
                      if (datetime.utcnow()-datetime.fromisoformat(s["ts"])).seconds < 10800)
    has_lambda  = any(v is not None for v in lambdas.values())

    # Outlier: one timeframe moving against others
    pp_vals = [v for v in [prob_shifts.get("1h"), prob_shifts.get("6h"), prob_shifts.get("24h")] if v is not None]
    has_outlier = False
    if len(pp_vals) >= 3:
        avg = sum(pp_vals)/len(pp_vals)
        has_outlier = any(abs(v-avg) > abs(avg)*2 and abs(v) > 0.01 for v in pp_vals)

    card_class = "hero-card" if is_hero else "grid-card"
    if has_spike:   card_class += " has-spike"
    elif has_outlier: card_class += " has-outlier"

    # Build HTML
    # Banners
    banners = ""
    if has_spike:
        banners += f'<div class="banner-spike">⚡ VOLUME SPIKE DETECTED</div>'
    elif has_outlier:
        banners += f'<div class="banner-outlier">◈ OUTLIER — timeframe divergence detected</div>'
    if has_lambda:
        banners += f'<div class="banner-lambda">λ KYLE\'S LAMBDA ABOVE BASELINE</div>'

    # Yes/No bars
    if is_binary and yes is not None:
        yes_pct = yes*100
        no_pct  = (1-yes)*100
        yn_html = f"""
        <div class="yn-row">
          <span class="yn-label">Yes</span>
          <div class="yn-bar-wrap"><div class="yn-bar-yes" style="width:{yes_pct:.1f}%"></div></div>
          <span class="yn-pct">{yes_pct:.1f}%</span>
        </div>
        <div class="yn-row">
          <span class="yn-label">No</span>
          <div class="yn-bar-wrap"><div class="yn-bar-no" style="width:{no_pct:.1f}%"></div></div>
          <span class="yn-pct">{no_pct:.1f}%</span>
        </div>"""
    elif pairs:
        yn_html = "".join(
            f'<div class="yn-row"><span class="yn-label" style="width:60px;font-size:0.7rem;">{o[:8]}</span>'
            f'<div class="yn-bar-wrap"><div class="yn-bar-yes" style="width:{p*100:.0f}%"></div></div>'
            f'<span class="yn-pct">{p*100:.0f}%</span></div>'
            for o,p in pairs[:4]
        )
    else:
        yn_html = '<span style="color:#444466;font-size:0.75rem;">No price data</span>'

    # Vol delta badges
    vol_badges = '<div class="badge-row"><span style="font-size:0.65rem;color:#444466;margin-right:2px;">VOL Δ</span>'
    for wl,_ in windows:
        vg = vol_gains.get(wl)
        if vg and vg > 0:
            vol_badges += f'<span class="badge badge-vol-pos">+{fmt_vol(vg)} {wl}</span>'
        else:
            vol_badges += f'<span class="badge badge-vol-neu">+$0 {wl}</span>'
    vol_badges += '</div>'

    # Prob shift badges
    pp_windows = [
        ("1h",  prob_shifts.get("1h")),
        ("3h",  prob_shifts.get("3h")),
        ("6h",  prob_shifts.get("6h")),
        ("24h", prob_shifts.get("24h")),
        ("7d",  ps_7d),
    ]
    pp_badges = '<div class="badge-row">'
    for wl, ps in pp_windows:
        if ps is None:
            pp_badges += f'<span class="badge badge-pp-neu">— {wl}</span>'
        elif ps > 0.001:
            pp_badges += f'<span class="badge badge-pp-up">▲{abs(ps*100):.2f}pp {wl}</span>'
        elif ps < -0.001:
            pp_badges += f'<span class="badge badge-pp-dn">▼{abs(ps*100):.2f}pp {wl}</span>'
        else:
            pp_badges += f'<span class="badge badge-pp-neu">0pp {wl}</span>'
    pp_badges += '</div>'

    q_class = "card-q-hero" if is_hero else "card-q"

    html = f"""
    <div class="{card_class}">
      {banners}
      <div class="card-rank">#{rank:02d} · {cat.upper()}</div>
      <div class="{q_class}">{question}</div>
      {yn_html}
      {vol_badges}
      {pp_badges}
      <div class="stat-row">
        <div class="stat-box">
          <div class="stat-lbl">24H VOL</div>
          <div class="stat-val">{fmt_vol(v24)}</div>
        </div>
        <div class="stat-box">
          <div class="stat-lbl">TOTAL VOL</div>
          <div class="stat-val">{fmt_vol(vtot)}</div>
        </div>
      </div>
      <div class="ends-liq">
        <div>
          <div class="el-lbl">LIQUIDITY</div>
          <div class="el-val">{fmt_vol(liq) if liq else '—'}</div>
        </div>
        <div>
          <div class="el-lbl">ENDS</div>
          <div class="el-val">{end_str if end_str else '—'}</div>
        </div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────
if "last_poll" not in st.session_state: st.session_state.last_poll = 0

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙ CONFIG")
    auto_refresh = st.toggle("Auto-refresh (60s)", value=False)
    st.markdown("---")
    st.caption("Top 10 refreshes 3× daily.")
    st.caption("Snapshots stored in Supabase.")
    st.caption("Telegram alerts on 3h $250K spike.")
    if st.button("🔄 Force refresh"):
        st.cache_data.clear()
        st.rerun()

# ── Fetch markets ─────────────────────────────────────────────
try:
    markets = fetch_top10()
except Exception as e:
    st.error(f"Cannot reach Polymarket API: {e}")
    st.stop()

# ── Poll snapshots every 60s ──────────────────────────────────
now_ts = time.time()
if (now_ts - st.session_state.last_poll) > 60:
    for m in markets:
        mid  = m.get("conditionId") or m.get("id") or m.get("slug","")
        vol  = float(m.get("volume",0))
        liq  = float(m.get("liquidity") or m.get("liquidityClob") or 0)
        end  = m.get("endDate") or m.get("endDateIso","")
        pairs = parse_outcomes(m)
        yes,_ = yes_no(pairs)
        prob = yes if yes is not None else (pairs[0][1] if pairs else 0.5)
        if mid:
            save_snapshot(mid, vol, prob, m.get("question",""), end, liq)
    cleanup()
    st.session_state.last_poll = now_ts

spikes = get_recent_spikes()

# ── Header ────────────────────────────────────────────────────
total_24h = sum(float(m.get("volume24hr",0)) for m in markets)
now_str   = datetime.utcnow().strftime("%d %b %Y · %H:%M UTC")

st.markdown(f"""
<div class="hdr">
  <h1>◈ POLYMARKET TRACKER</h1>
  <div class="hdr-sub">LIVE PREDICTION MARKET INTELLIGENCE · TOP 10 BY 24H VOLUME · {now_str}</div>
</div>
""", unsafe_allow_html=True)

# ── Summary metrics ───────────────────────────────────────────
c1,c2,c3,c4 = st.columns(4)
with c1: st.markdown(f'<div class="metric-box"><div class="lbl">markets</div><div class="val">10</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="metric-box"><div class="lbl">24h volume</div><div class="val">{fmt_vol(total_24h)}</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="metric-box"><div class="lbl">spikes (24h)</div><div class="val">{len(spikes)}</div></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="metric-box"><div class="lbl">alerts sent</div><div class="val">{len([s for s in spikes if s.get("win")=="3h"])}</div></div>', unsafe_allow_html=True)

# ── Spike log ─────────────────────────────────────────────────
if spikes:
    items_html = ""
    for sp in spikes[:5]:
        age = datetime.utcnow() - datetime.fromisoformat(sp["ts"])
        age_str = f"{int(age.seconds/60)}m ago" if age.seconds < 3600 else f"{int(age.seconds/3600)}h ago"
        ps  = sp.get("prob_shift") or 0
        d   = "▲" if ps > 0 else "▼"
        col = "#00f5a0" if ps > 0 else "#ff5555"
        items_html += f"""
        <div class="spike-item">
          <span style="color:#ff3333;font-weight:700;font-family:'Share Tech Mono'">⚡ +{fmt_vol(sp['vol_gain'])}</span>
          <span style="color:#666;font-size:0.72rem"> {sp.get('window','?')} window · {age_str}</span>
          <span style="color:{col};font-weight:700"> {d}{abs(ps*100):.1f}pp</span><br>
          <span style="color:#aaaacc;font-size:0.8rem">{sp['question'][:75]}{'…' if len(sp['question'])>75 else ''}</span>
        </div>"""
    st.markdown(f'<div class="spike-panel"><div class="spike-title">⚡ spike log — last 24h</div>{items_html}</div>', unsafe_allow_html=True)

# ── Hero card (#1) ────────────────────────────────────────────
st.markdown('<div class="sec-hdr">▸ #1 most active market</div>', unsafe_allow_html=True)
render_card(markets[0], 1, spikes, is_hero=True)

# ── 3x3 grid (#2–#10) ────────────────────────────────────────
st.markdown('<div class="sec-hdr">▸ top markets</div>', unsafe_allow_html=True)

rest = markets[1:10]
rows = [rest[i:i+3] for i in range(0,len(rest),3)]
for row in rows:
    cols = st.columns(3)
    for j, m in enumerate(row):
        with cols[j]:
            render_card(m, markets.index(m)+1, spikes, is_hero=False)

# ── Auto refresh ──────────────────────────────────────────────
if auto_refresh:
    time.sleep(60)
    st.rerun()
