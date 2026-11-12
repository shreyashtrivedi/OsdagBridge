# =============================================================================
# OsdagBridge Report — generated charts (matplotlib → PNG → PyLaTeX Figure)
# =============================================================================
#
# Charts are rendered off-screen (Agg backend) into the report's temporary
# image directory during generation and embedded with ``pylatex.Figure``.
# All colours / sizes come from ``styles.CHART``.
#
# Design rules applied (consistent across all charts):
#   * one value axis per panel (two measures with different units are drawn
#     as side-by-side panels, never as a dual-axis chart);
#   * thin columns growing from a zero baseline, value printed on each cap;
#   * recessive grid and axes; text in neutral ink, never in the bar colour;
#   * failing checks use the reserved critical red AND carry a "FAIL" label,
#     so status is never conveyed by colour alone;
#   * the UR = 1.0 limit is a red dashed horizontal reference line.
# =============================================================================

import logging
import os

from pylatex import Figure, NoEscape

from osdagbridge.core.reports.styles import CHART, FIGURE

logger = logging.getLogger(__name__)


def _plt():
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": CHART["font_family"],
        "font.size": CHART["font_size"],
        "axes.titlesize": CHART["title_size"],
        "axes.titleweight": "bold",
        "axes.edgecolor": CHART["axis"],
        "axes.labelcolor": CHART["ink_secondary"],
        "xtick.color": CHART["ink_secondary"],
        "ytick.color": CHART["ink_secondary"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    })
    return plt


def _to_float(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None   # drop NaN


def _style_axis(ax):
    ax.grid(axis="y", color=CHART["grid"], linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=0)
    ax.spines["left"].set_visible(False)


def _save(fig, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=CHART["dpi"], bbox_inches="tight")
    import matplotlib.pyplot as plt
    plt.close(fig)
    return path


def _wrap(label, width=14):
    """Break long tick labels onto several lines."""
    words, lines, cur = str(label).split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Utilization ratio charts
# ─────────────────────────────────────────────────────────────────────────────

def _ur_bars(ax, labels, values, ymax):
    xs = list(range(len(labels)))
    heights = [v if v is not None else 0.0 for v in values]
    colors = [CHART["fail"] if (v is not None and v > 1.0) else CHART["series"] for v in values]
    ax.bar(xs, heights, width=CHART["bar_width"], color=colors, zorder=2)
    for x, v in zip(xs, values):
        if v is None:
            ax.text(x, 0.02 * ymax, "n/a", ha="center", va="bottom",
                    color=CHART["ink_secondary"], fontsize=CHART["font_size"] - 1)
            continue
        txt = f"{v:.2f}" + (" FAIL" if v > 1.0 else "")
        # Value above the bar on a white chip, so it stays legible where it
        # crosses the dashed UR = 1.0 line.
        ax.text(x, v + 0.025 * ymax, txt, ha="center", va="bottom", zorder=4,
                color=CHART["fail"] if v > 1.0 else CHART["ink"],
                fontsize=CHART["font_size"] - (1.5 if len(labels) > 4 else 0.5),
                fontweight="bold" if v > 1.0 else "normal",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))
    ax.axhline(1.0, color=CHART["limit_line"], linestyle=CHART["limit_style"],
               linewidth=CHART["limit_width"], zorder=3)
    ax.set_xticks(xs)
    ax.set_xticklabels([_wrap(lb, 12) for lb in labels], fontsize=CHART["font_size"] - 1)
    ax.set_ylim(0, ymax)
    ax.set_xlim(-0.6, len(labels) - 0.4)


def ur_component_chart(component_urs, path):
    """Governing UR per primary element.

    component_urs : list of (component_label, ur_or_None)
    """
    if not component_urs or all(_to_float(u) is None for _, u in component_urs):
        return None
    plt = _plt()
    labels = [c for c, _ in component_urs]
    values = [_to_float(u) for _, u in component_urs]
    vmax = max([v for v in values if v is not None] + [1.0])
    ymax = max(1.25, vmax * 1.22)
    fig, ax = plt.subplots(figsize=CHART["figsize"])
    _style_axis(ax)
    _ur_bars(ax, labels, values, ymax)
    ax.set_ylabel("Utilization Ratio (Demand / Capacity)")
    ax.text(len(labels) - 0.45, 1.0 + 0.015 * ymax, "UR = 1.0 limit", ha="right", va="bottom",
            color=CHART["limit_line"], fontsize=CHART["font_size"] - 1)
    return _save(fig, path)


def ur_detail_chart(groups, path):
    """Per-check UR, one panel per primary element (shared UR axis).

    groups : list of (component_label, [(check_label, ur_or_None), ...])
    """
    groups = [(g, items) for g, items in groups if items]
    if not groups:
        return None
    all_vals = [_to_float(u) for _, items in groups for _, u in items]
    if all(v is None for v in all_vals):
        return None
    plt = _plt()
    vmax = max([v for v in all_vals if v is not None] + [1.0])
    ymax = max(1.25, vmax * 1.25)
    # One panel per element on a 2-column grid (shared UR scale) so every
    # check label stays readable regardless of how many checks there are.
    ncols = 2 if len(groups) > 1 else 1
    nrows = (len(groups) + ncols - 1) // ncols
    w, h = CHART["figsize_tall"]
    fig, axes = plt.subplots(nrows, ncols, figsize=(w, 2.9 * nrows), sharey=True, squeeze=False)
    flat = [ax for row in axes for ax in row]
    for i, ax in enumerate(flat):
        if i >= len(groups):
            ax.set_visible(False)
            continue
        title, items = groups[i]
        _style_axis(ax)
        _ur_bars(ax, [lb for lb, _ in items], [_to_float(u) for _, u in items], ymax)
        ax.set_xticklabels([_wrap(lb, 11) for lb, _ in items], rotation=35, ha="right",
                           rotation_mode="anchor", fontsize=CHART["font_size"] - 1)
        vals = [_to_float(u) for _, u in items if _to_float(u) is not None]
        gov = f"governing UR {max(vals):.2f}" if vals else "no data"
        ax.set_title(f"{title} — {gov}", color=CHART["ink"], loc="left", pad=6)
        if i % ncols == 0:
            ax.set_ylabel("UR (Demand / Capacity)")
        else:
            ax.tick_params(axis="y", labelleft=True)
    fig.tight_layout(h_pad=1.6, w_pad=1.6)
    return _save(fig, path)


# ─────────────────────────────────────────────────────────────────────────────
# Material quantity charts
# ─────────────────────────────────────────────────────────────────────────────

def _qty_panel(ax, labels, values, unit, color):
    xs = list(range(len(labels)))
    heights = [v if v is not None else 0.0 for v in values]
    vmax = max([v for v in values if v is not None] + [0.0]) or 1.0
    ax.bar(xs, heights, width=CHART["bar_width"], color=color, zorder=2)
    for x, v in zip(xs, values):
        txt = "n/a" if v is None else f"{v:,.2f}"
        y = 0.02 * vmax if v is None else v + 0.02 * vmax
        ax.text(x, y, txt, ha="center", va="bottom", color=CHART["ink"],
                fontsize=CHART["font_size"] - 0.5)
    ax.set_xticks(xs)
    ax.set_xticklabels([_wrap(lb, 14) for lb in labels], fontsize=CHART["font_size"] - 1)
    ax.set_ylim(0, vmax * 1.2)
    ax.set_xlim(-0.6, len(labels) - 0.4)
    ax.set_ylabel(unit)


def steel_tonnage_chart(items, path):
    """Structural steel weight by element.

    items : list of (label, tonnes_or_None)
    """
    vals = [_to_float(v) for _, v in items]
    if all(v is None for v in vals):
        return None
    plt = _plt()
    fig, ax = plt.subplots(figsize=CHART["figsize"])
    _style_axis(ax)
    _qty_panel(ax, [lb for lb, _ in items], vals, "Weight (MT)", CHART["series"])
    total = sum(v for v in vals if v is not None)
    ax.set_title(f"Girders + bracing + diaphragms — {total:,.2f} MT", color=CHART["ink"], loc="left")
    return _save(fig, path)


def concrete_rebar_chart(concrete_items, rebar_items, path):
    """Concrete volume (m³) beside reinforcement weight (MT) — two panels,
    each with its own axis (no dual-axis chart)."""
    c_vals = [_to_float(v) for _, v in concrete_items]
    r_vals = [_to_float(v) for _, v in rebar_items]
    if all(v is None for v in c_vals + r_vals):
        return None
    plt = _plt()
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=CHART["figsize"],
        gridspec_kw={"width_ratios": [max(len(c_vals), 1), max(len(r_vals), 1)]})
    for ax in (ax1, ax2):
        _style_axis(ax)
    _qty_panel(ax1, [lb for lb, _ in concrete_items], c_vals, "Volume (m³)", CHART["series"])
    _qty_panel(ax2, [lb for lb, _ in rebar_items], r_vals, "Weight (MT)", CHART["series_alt"])
    c_tot = sum(v for v in c_vals if v is not None)
    r_tot = sum(v for v in r_vals if v is not None)
    ax1.set_title(f"Concrete — {c_tot:,.2f} m³", color=CHART["ink"], loc="left")
    ax2.set_title(f"Reinforcement — {r_tot:,.2f} MT", color=CHART["ink"], loc="left")
    fig.tight_layout(w_pad=2.5)
    return _save(fig, path)


# ─────────────────────────────────────────────────────────────────────────────
# PyLaTeX embedding
# ─────────────────────────────────────────────────────────────────────────────

def figure_tex(path, caption, width=None, label=None):
    """Embed an image with ``pylatex.Figure``; returns LaTeX source ('' if no image)."""
    if not path:
        return ""
    fig = Figure(position=FIGURE["placement"])
    fig.append(NoEscape(r"\centering"))
    fig.add_image(path.replace("\\", "/"), width=NoEscape(width or FIGURE["chart_width"]))
    fig.add_caption(NoEscape(caption))
    if label:
        fig.append(NoEscape(r"\label{" + label + "}"))
    return ("\n" + r"\needspace{" + str(FIGURE["needspace_lines"]) + r"\baselineskip}" + "\n"
            + fig.dumps() + "\n")


def safe_chart(fn, *args, **kwargs):
    """Run a chart function; log and return None on any failure so a plotting
    problem can never abort report generation."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:   # pragma: no cover - defensive
        logger.warning("Chart generation failed in %s: %s", getattr(fn, "__name__", fn), exc)
        return None
