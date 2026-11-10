import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit.components.v1 as components
import io

st.set_page_config(page_title="GradeGlow", page_icon="✨", layout="centered")

# --- PALETAS E IMAGENS DE MÁSCARA ---
PALETTES = {
    "🎨 Bauhaus Modern": ["#E63946", "#457B9D", "#E9C46A", "#2A9D8F"],
    "🍬 Candy Pop": ["#FACC15", "#F43F5E", "#FB923C", "#A855F7"],
    "🌊 Ocean Breeze": ["#0EA5E9", "#2563EB", "#14B8A6", "#6366F1"],
    "🌲 Nordic Forest": ["#10B981", "#F59E0B", "#047857", "#84CC16"],
}

PHOTO_MASKS = {
    "🌤️ Sky & Birds": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1000&q=85",
    "🌻 Golden Seeds": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1000&q=85",
    "📚 Library Books": "https://images.unsplash.com/photo-1507842229356-51c61504d3ab?auto=format&fit=crop&w=1000&q=85",
    "🎨 Acrylic Texture": "https://images.unsplash.com/photo-1541701494587-cb58502866ab?auto=format&fit=crop&w=1000&q=85",
}

DEMO_DATA = """Class A, Exam 1, 4.5
Class A, Exam 2, 6.2
Class A, Exam 3, 7.4
Class A, Exam 4, 5.8
Class A, Exam 5, 6.1
Class A, Exam 6, 7.3
Class A, Exam 7, 9.0
Class A, Exam 7, 8.4
Class B, Exam 1, 2.8
Class B, Exam 2, 4.5
Class B, Exam 3, 6.0
Class B, Exam 4, 7.6
Class B, Exam 5, 8.1
Class B, Exam 6, 9.3
Class B, Exam 7, 9.8
Class B, Exam 7, 8.9
Class C, Exam 1, 2.1
Class C, Exam 2, 2.7
Class C, Exam 3, 4.3
Class C, Exam 4, 3.1
Class C, Exam 5, 3.4
Class C, Exam 6, 5.0
Class C, Exam 7, 6.2
Class C, Exam 7, 5.5
Class D, Exam 1, 5.0
Class D, Exam 2, 5.8
Class D, Exam 3, 6.5
Class D, Exam 4, 6.9
Class D, Exam 5, 7.2
Class D, Exam 6, 7.8
Class D, Exam 7, 8.1"""

if "raw_text" not in st.session_state:
    st.session_state.raw_text = DEMO_DATA

# --- SIDEBAR: ENTRADA DE DADOS E ESTILO ---
with st.sidebar:
    st.markdown("### 📥 Classroom Data")
    st.caption("Paste `Class, Exam, Grade` or `Class, Grade` below, or upload a CSV.")
    
    if st.button("⚡ Load Demo Data", use_container_width=True):
        st.session_state.raw_text = DEMO_DATA
        st.rerun()

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
    if uploaded_file is not None:
        content = uploaded_file.getvalue().decode("utf-8")
        st.session_state.raw_text = content

    raw_input = st.text_area(
        "Raw Grades",
        value=st.session_state.raw_text,
        height=210,
        label_visibility="collapsed"
    )
    st.session_state.raw_text = raw_input

    st.divider()
    st.markdown("### 🎨 Visual Identity")
    fill_mode = st.radio("Bar Fill Mode", ["🎨 Solid 3D Colors", "🖼️ Photo Mask"], horizontal=False)
    
    if fill_mode == "🎨 Solid 3D Colors":
        palette_name = st.selectbox("Color Palette", list(PALETTES.keys()))
        colors = PALETTES[palette_name]
        photo_url = None
    else:
        photo_name = st.selectbox("Mask Photograph", list(PHOTO_MASKS.keys()))
        photo_url = PHOTO_MASKS[photo_name]
        colors = PALETTES["🎨 Bauhaus Modern"]

# --- PARSER DE DADOS ---
def parse_grades(text: str) -> pd.DataFrame:
    rows = []
    for idx, line in enumerate(text.strip().splitlines()):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        try:
            if len(parts) >= 3:
                rows.append({"Class": parts[0], "Exam": parts[1], "Grade": float(parts[2])})
            elif len(parts) == 2:
                rows.append({"Class": parts[0], "Exam": f"Eval {(idx % 5) + 1}", "Grade": float(parts[1])})
        except ValueError:
            continue
    if not rows:
        return pd.DataFrame(columns=["Class", "Exam", "Grade"])
    return pd.DataFrame(rows)

df = parse_grades(st.session_state.raw_text)

# --- ESTILO CSS GLOBAL ---
bg_gradient = "linear-gradient(135deg, #F5F7FA 0%, #D6DEE8 100%)"
axis_color = "#283548"
stick_color = "#FFFFFF"
shadow_rgba = "rgba(15, 23, 42, 0.36)"

st.markdown(f"""
<style>
.stApp {{
    background: {bg_gradient};
}}
div[data-testid="stPlotlyChart"] {{
    background: transparent;
    box-shadow: none !important;
    border: none !important;
}}
.js-plotly-plot .plotly .main-svg {{
    overflow: visible !important;
}}
.js-plotly-plot .plotly .cartesianlayer .trace.scatter:nth-child(3n+1),
.js-plotly-plot .plotly .cartesianlayer .trace.bars path {{
    filter: drop-shadow(-8px 14px 10px {shadow_rgba});
}}
div[data-testid="stMetric"] {{
    background: rgba(255, 255, 255, 0.45);
    border: 1px solid rgba(255, 255, 255, 0.7);
    border-radius: 14px;
    padding: 10px 16px;
}}
</style>
""", unsafe_allow_html=True)

st.title("✨ GradeGlow")
st.caption("Your classroom data, beautifully visualized — in seconds.")

if df.empty:
    st.warning("Please enter valid grade lines in the sidebar (e.g., `Class A, Exam 1, 8.5`).")
    st.stop()

class_means = df.groupby("Class", as_index=False)["Grade"].mean()
top_class_row = class_means.loc[class_means["Grade"].idxmax()]

m1, m2, m3 = st.columns(3)
m1.metric("Total Entries", f"{len(df)} grades")
m2.metric("Overall Average", f"{df['Grade'].mean():.1f} / 10")
m3.metric("Top Class", f"{top_class_row['Class']} ({top_class_row['Grade']:.1f})")

# --- FUNÇÕES DE EIXO E EXPORTAÇÃO SVG/PNG ---
def apply_ruler_axes(fig, x_range, y_range, x_vals=None, x_labels=None, y_dtick=2):
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="sans-serif", size=13, color=axis_color, weight="bold"),
        margin=dict(l=55, r=35, t=40, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(
            range=x_range, showgrid=False, zeroline=False,
            linecolor=axis_color, linewidth=3.5,
            ticks="outside", tickvals=x_vals, ticktext=x_labels,
            tickwidth=3, ticklen=10, tickcolor=axis_color,
        ),
        yaxis=dict(
            range=y_range, showgrid=False, zeroline=False,
            linecolor=axis_color, linewidth=3.5,
            ticks="outside", dtick=y_dtick, tick0=0,
            tickwidth=3, ticklen=10, tickcolor=axis_color,
            minor=dict(ticks="outside", ticklen=6, tickwidth=2, tickcolor=axis_color, dtick=y_dtick / 5.0)
        )
    )
    return fig

def build_bar_svg(title, labels, values, max_y, bar_colors=None, img_url=None, is_histogram=False):
    """Gera SVG autônomo. Se is_histogram=True, desenha os ticks nas bordas (0, 1, 2... 10) e as barras exatamente entre dois traços."""
    svg_w, svg_h = 740, 430
    pad_l, pad_r, pad_t, pad_b = 65, 35, 55, 60
    plot_w = svg_w - pad_l - pad_r
    plot_h = svg_h - pad_t - pad_b
    n = max(len(values), 1)
    slot_w = plot_w / n
    bar_w = slot_w * (0.98 if is_histogram else 0.48)
    rx = 5 if is_histogram else 12

    rects_clip = ""
    colored_bars = ""
    labels_svg = ""
    ticks_x = ""

    for i, val in enumerate(values):
        bh = max((val / max_y) * plot_h, 0)
        bx = pad_l + i * slot_w + (slot_w - bar_w) / 2
        by = pad_t + plot_h - bh
        cx = pad_l + i * slot_w + slot_w / 2
        c = bar_colors[i % len(bar_colors)] if bar_colors else "#2563EB"

        if bh > 0:
            rects_clip += f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" rx="{rx}" />'
            stroke_attr = 'stroke="rgba(255,255,255,0.45)" stroke-width="1"' if is_histogram else ''
            colored_bars += f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" rx="{rx}" fill="{c}" {stroke_attr}/>'

        val_str = f"{val:.1f}" if not is_histogram else (f"{int(val)}" if val > 0 else "")
        if val_str:
            if img_url:
                labels_svg += f'<text x="{cx:.1f}" y="{by - 10:.1f}" fill="{axis_color}" font-family="sans-serif" font-size="13" font-weight="bold" text-anchor="start" transform="rotate(-90, {cx:.1f}, {by - 10:.1f})">{val_str}</text>'
            else:
                labels_svg += f'<text x="{cx:.1f}" y="{by - 10:.1f}" fill="{axis_color}" font-family="sans-serif" font-size="13" font-weight="bold" text-anchor="middle">{val_str}</text>'

        if not is_histogram:
            lbl = labels[i]
            ticks_x += f'<line x1="{cx:.1f}" y1="{pad_t+plot_h}" x2="{cx:.1f}" y2="{pad_t+plot_h+10}" stroke="{axis_color}" stroke-width="3"/>'
            ticks_x += f'<text x="{cx:.1f}" y="{pad_t+plot_h+28}" fill="{axis_color}" font-family="sans-serif" font-size="12" font-weight="bold" text-anchor="middle">{lbl}</text>'

    # No modo histograma, os traços do eixo X ficam nas FRONTEIRAS dos bins (0, 1, 2, ..., 10)
    if is_histogram:
        for b in range(n + 1):
            tx = pad_l + b * slot_w
            ticks_x += f'<line x1="{tx:.1f}" y1="{pad_t+plot_h}" x2="{tx:.1f}" y2="{pad_t+plot_h+10}" stroke="{axis_color}" stroke-width="3"/>'
            ticks_x += f'<text x="{tx:.1f}" y="{pad_t+plot_h+28}" fill="{axis_color}" font-family="sans-serif" font-size="12" font-weight="bold" text-anchor="middle">{b}</text>'

    ticks_y = ""
    steps = 5
    for s in range(steps + 1):
        yv = (max_y / steps) * s
        yy = pad_t + plot_h - (yv / max_y) * plot_h
        ticks_y += f'<line x1="{pad_l-10}" y1="{yy:.1f}" x2="{pad_l}" y2="{yy:.1f}" stroke="{axis_color}" stroke-width="3"/>'
        ticks_y += f'<text x="{pad_l-15}" y="{yy+4:.1f}" fill="{axis_color}" font-family="sans-serif" font-size="12" font-weight="bold" text-anchor="end">{int(yv)}</text>'
        if s < steps:
            for m in range(1, 5):
                my = yy - (plot_h / steps) * (m / 5)
                ticks_y += f'<line x1="{pad_l-6}" y1="{my:.1f}" x2="{pad_l}" y2="{my:.1f}" stroke="{axis_color}" stroke-width="2"/>'

    fill_content = (
        f'<image href="{img_url}" x="{pad_l}" y="{pad_t}" width="{plot_w}" height="{plot_h}" preserveAspectRatio="xMidYMid slice" clip-path="url(#barsClip)"/>'
        if img_url else colored_bars
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">
        <defs>
            <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#F5F7FA"/>
                <stop offset="100%" stop-color="#D6DEE8"/>
            </linearGradient>
            <clipPath id="barsClip">{rects_clip}</clipPath>
            <filter id="dropShadow" x="-20%" y="-20%" width="150%" height="150%">
                <feDropShadow dx="-8" dy="14" stdDeviation="7" flood-color="#0F172A" flood-opacity="0.36"/>
            </filter>
        </defs>
        <rect width="100%" height="100%" rx="18" fill="url(#bgGrad)"/>
        <text x="{pad_l}" y="32" fill="{axis_color}" font-family="sans-serif" font-size="16" font-weight="bold">{title}</text>
        <g filter="url(#dropShadow)">{fill_content}</g>
        <line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t+plot_h}" stroke="{axis_color}" stroke-width="3.5"/>
        <line x1="{pad_l}" y1="{pad_t+plot_h}" x2="{svg_w-pad_r}" y2="{pad_t+plot_h}" stroke="{axis_color}" stroke-width="3.5"/>
        {ticks_x}
        {ticks_y}
        {labels_svg}
    </svg>"""
    return svg

PLOTLY_CONFIG = {
    "displayModeBar": "hover",
    "displaylogo": False,
    "toImageButtonOptions": {"format": "png", "filename": "gradeglow_chart", "scale": 3}
}

tab1, tab2, tab3 = st.tabs([
    "📈 Time Series (Lollipops)",
    "📊 Class Comparison (Bars)",
    "🔔 Grade Distribution (10-Bin Histogram)"
])

# --- ABA 1: SÉRIE TEMPORAL (PIRULITOS 3D) ---
with tab1:
    ts_df = df.groupby(["Class", "Exam"], as_index=False)["Grade"].mean()
    exams_order = list(dict.fromkeys(df["Exam"].tolist()))
    classes_order = list(dict.fromkeys(df["Class"].tolist()))
    x_vals = list(range(1, len(exams_order) + 1))

    fig1 = go.Figure()
    start_offsets = [2.4, 1.6, 0.9, 3.1, 0.5]

    for idx, cls_name in enumerate(classes_order):
        sub = ts_df[ts_df["Class"] == cls_name]
        y_map = dict(zip(sub["Exam"], sub["Grade"]))
        x_pts = [i + 1 for i, ex in enumerate(exams_order) if ex in y_map]
        y_pts = [y_map[ex] for ex in exams_order if ex in y_map]
        c = colors[idx % len(colors)]
        y0 = start_offsets[idx % len(start_offsets)]

        fig1.add_trace(go.Scatter(
            x=[0.38] + x_pts, y=[y0] + y_pts,
            mode="lines+markers", name=cls_name,
            line=dict(color=stick_color, width=5.5),
            marker=dict(size=[0] + [29] * len(x_pts), color=c, opacity=1.0, line=dict(width=0)),
            hoverinfo="name+y"
        ))
        fig1.add_trace(go.Scatter(
            x=[x + 0.055 for x in x_pts], y=[y + 0.17 for y in y_pts],
            mode="markers", showlegend=False, hoverinfo="skip",
            marker=dict(size=8.5, color="rgba(255, 255, 255, 0.35)", line=dict(width=0))
        ))
        fig1.add_trace(go.Scatter(
            x=[x + 0.062 for x in x_pts], y=[y + 0.19 for y in y_pts],
            mode="markers", showlegend=False, hoverinfo="skip",
            marker=dict(size=4.0, color="rgba(255, 255, 255, 0.90)", line=dict(width=0))
        ))

    apply_ruler_axes(fig1, [0, len(exams_order) + 0.6], [0, 11], x_vals, exams_order, y_dtick=2)
    st.plotly_chart(fig1, use_container_width=True, config=PLOTLY_CONFIG)

    html_buf = io.StringIO()
    fig1.write_html(html_buf, include_plotlyjs="cdn")
    st.download_button(
        "📥 Download Interactive Lollipop Chart (.html)",
        data=html_buf.getvalue(),
        file_name="gradeglow_timeseries.html",
        mime="text/html"
    )

# --- ABA 2: COMPARAÇÃO DE TURMAS (BARRAS 3D OU MÁSCARA DE FOTO) ---
with tab2:
    c_labels = class_means["Class"].tolist()
    c_values = class_means["Grade"].tolist()
    c_x = list(range(1, len(c_labels) + 1))
    bar_cols = [colors[i % len(colors)] for i in range(len(c_labels))]

    svg_bars = build_bar_svg(
        "Average Grade by Class", c_labels, c_values, max_y=10,
        bar_colors=bar_cols, img_url=photo_url, is_histogram=False
    )

    if fill_mode == "🖼️ Photo Mask":
        components.html(f'<div style="display:flex;justify-content:center;">{svg_bars}</div>', height=445)
    else:
        fig2 = go.Figure(go.Bar(
            x=c_x, y=c_values,
            marker=dict(color=bar_cols, cornerradius=12, line=dict(width=0)),
            width=0.45,
            text=[f"{v:.1f}" for v in c_values],
            textposition="outside",
            textfont=dict(size=14, color=axis_color, weight="bold"),
            showlegend=False
        ))
        apply_ruler_axes(fig2, [0.3, len(c_labels) + 0.7], [0, 10.8], c_x, c_labels, y_dtick=2)
        st.plotly_chart(fig2, use_container_width=True, config=PLOTLY_CONFIG)

    st.download_button(
        "📥 Download Vector Chart with Shadow (.svg / Inkscape Ready)",
        data=svg_bars,
        file_name="gradeglow_class_comparison.svg",
        mime="image/svg+xml"
    )

# --- ABA 3: HISTOGRAMA DE 10 BINS (BARRAS ENTRE DOIS TRAÇOS: 0, 1, 2, ..., 10) ---
with tab3:
    bins_edges = np.linspace(0, 10, 11)
    counts, _ = np.histogram(df["Grade"].clip(0, 10), bins=bins_edges)
    
    # Centros das barras nos meios dos intervalos (0.5, 1.5, ..., 9.5)
    bins_centers = [i + 0.5 for i in range(10)]
    # Traços do eixo X exatamente nas divisas (0, 1, 2, ..., 10)
    edge_ticks = list(range(0, 11))
    edge_labels = [str(i) for i in edge_ticks]
    max_count = max(int(counts.max()) + 3, 10)

    bin_colors = [
        colors[0], colors[0], colors[0],
        colors[2], colors[2], colors[2],
        colors[1], colors[1],
        colors[3], colors[3]
    ]

    svg_hist = build_bar_svg(
        "Grade Distribution (10 Bins)", edge_labels, counts.tolist(), max_y=max_count,
        bar_colors=bin_colors, img_url=photo_url, is_histogram=True
    )

    if fill_mode == "🖼️ Photo Mask":
        components.html(f'<div style="display:flex;justify-content:center;">{svg_hist}</div>', height=445)
    else:
        fig3 = go.Figure(go.Bar(
            x=bins_centers,
            y=counts,
            marker=dict(
                color=bin_colors,
                cornerradius=5,
                line=dict(color="rgba(255,255,255,0.45)", width=1)
            ),
            width=0.98,  # Largura de 1 unidade inteira (fica cravado entre os dois traços!)
            text=[str(c) if c > 0 else "" for c in counts],
            textposition="outside",
            textfont=dict(size=13, color=axis_color, weight="bold"),
            hovertemplate="Score %{customdata}: %{y} students<extra></extra>",
            customdata=[f"{i} to {i+1}" for i in range(10)],
            showlegend=False
        ))
        # Eixo X vai de 0 a 10.4 com ticks em 0, 1, 2, ..., 10
        apply_ruler_axes(fig3, [0, 10.4], [0, max_count], edge_ticks, edge_labels, y_dtick=max(2, max_count // 4))
        fig3.update_layout(yaxis_title="Students", xaxis_title="Score (0 to 10 Scale)")
        st.plotly_chart(fig3, use_container_width=True, config=PLOTLY_CONFIG)

    st.download_button(
        "📥 Download Vector Histogram (.svg / Inkscape Ready)",
        data=svg_hist,
        file_name="gradeglow_histogram.svg",
        mime="image/svg+xml"
    )
