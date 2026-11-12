from typing import TYPE_CHECKING
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
)
from osdagbridge.core.reports.report_utils import _tex, _fig_embed
from osdagbridge.core.reports.report_tables import Col, ReportTable, kv_table
from osdagbridge.core.reports.styles import status

if TYPE_CHECKING:
    from .report_generator import ReportDataBridge


def ch4_analysis(asum, fig_paths, bridge: "ReportDataBridge", span_m: float):
    lc_summary  = (asum or {}).get('load_cases', {})
    rxn_summary = (asum or {}).get('reactions',  {})

    def _is_moving(lc_name: str) -> bool:
        n = lc_name.lower()
        return "moving" in n or " pos_" in n

    lc_summary  = {k: v for k, v in lc_summary.items()  if not _is_moving(k)}
    rxn_summary = {k: v for k, v in rxn_summary.items() if not _is_moving(k)}

    def _fmt(val, nd=3):
        try:
            return f"{float(val):.{nd}f}"
        except (TypeError, ValueError):
            return r"---"

    all_lcs = list(lc_summary.keys()) + [k for k in rxn_summary if k not in lc_summary]

    # ── Table 4.1: Summary of maximum demands (two-level header, repeats per page)
    hdr = [
        r" & \multicolumn{3}{c|}{\textbf{Bending Moment}} & "
        r"\multicolumn{3}{c|}{\textbf{Shear Force}} & \multicolumn{2}{c|}{\textbf{Reaction (kN)}}\\ \cline{2-9}",
        r"\multirow{-2}{=}{\textbf{Load Case / Combination}} & \textbf{Max (kNm)} & \textbf{Girder} & "
        r"\textbf{Loc. (m)} & \textbf{Max (kN)} & \textbf{Girder} & \textbf{Loc. (m)} & "
        r"\textbf{Left} & \textbf{Right}\\",
    ]
    demands = ReportTable("Summary of Maximum Demands", [
        Col("", 3.0, "l"), Col("", 1.35, "c"), Col("", 0.9, "c"), Col("", 0.9, "c"),
        Col("", 1.2, "c"), Col("", 0.9, "c"), Col("", 0.9, "c"), Col("", 1.25, "c"), Col("", 1.25, "c"),
    ], header_tex=hdr, note="Moving-load position cases are omitted; their effects are captured by the envelopes.")
    if not all_lcs:
        demands.row(["---"] * 9)
    for lc in all_lcs:
        bm_d = lc_summary.get(lc) or {}
        rxn_d = rxn_summary.get(lc) or {}
        demands.row(_tex(lc), _fmt(bm_d.get('max_bm')), _tex(bm_d.get('bm_girder', '---')),
                    _fmt(bm_d.get('bm_location')), _fmt(bm_d.get('max_sf')),
                    _tex(bm_d.get('sf_girder', '---')), _fmt(bm_d.get('sf_location')),
                    _fmt(rxn_d.get('left_kN')), _fmt(rxn_d.get('right_kN')))

    # ── Table 4.2: Governing support reactions (envelopes + absolute maxima)
    reactions = ReportTable("Governing Reactions at Supports", [
        Col("Load Case / Envelope", 2.4, "l"), Col("Left Support (kN)", 1.3, "c"),
        Col("Right Support (kN)", 1.3, "c")],
        note="Absolute maxima are taken over all load cases and combinations listed in the table above.")
    for env in ("Envelope ULS", "Envelope SLS"):
        if env in rxn_summary:
            r = rxn_summary[env] or {}
            reactions.row(env, _fmt(r.get('left_kN')), _fmt(r.get('right_kN')))

    def _absmax(side):
        best = None
        for name, r in rxn_summary.items():
            try:
                v = float((r or {}).get(side))
            except (TypeError, ValueError):
                continue
            if best is None or abs(v) > abs(best[0]):
                best = (v, name)
        return best
    for side, label in (("left_kN", "left"), ("right_kN", "right")):
        b = _absmax(side)
        if b:
            cells = ["---", "---"]
            cells[0 if label == "left" else 1] = _fmt(b[0])
            reactions.row(r"Maximum " + label + r" reaction --- \textit{" + _tex(b[1]) + "}", *cells)
    if not rxn_summary:
        reactions.row("---", "---", "---")

    # ── Table 4.3: Deflection summary
    _span_m         = float(bridge.input_dict.get(KEY_SPAN, 0) or 0)
    _allow_live_mm  = _span_m * 1000.0 / 800.0
    _allow_total_mm = _span_m * 1000.0 / 600.0

    # Find governing girder — worst (max) deflection across all girders
    try:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1) or 1)
    except (TypeError, ValueError):
        n = 1

    _live_mm  = None
    _total_mm = None
    for _gi in range(1, n + 1):
        _l = bridge.output_dict.get(f"{KEY_SD_DEFL_LIVE}.G{_gi}")
        _t = bridge.output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{_gi}")
        if _l is not None:
            _live_mm  = max(_live_mm, float(_l))  if _live_mm  is not None else float(_l)
        if _t is not None:
            _total_mm = max(_total_mm, float(_t)) if _total_mm is not None else float(_t)

    _live_str        = f"{_live_mm:.3f} mm"  if _live_mm  is not None else "---"
    _total_str       = f"{_total_mm:.3f} mm" if _total_mm is not None else "---"
    _allow_live_str  = f"L/800 = {_allow_live_mm:.1f} mm"
    _allow_total_str = f"L/600 = {_allow_total_mm:.1f} mm"
    _live_status     = status(_live_mm <= _allow_live_mm) if _live_mm is not None else "---"
    _total_status    = status(_total_mm <= _allow_total_mm) if _total_mm is not None else "---"

    deflection = kv_table(r"Deflection Summary (Live Load \& Total Load)", [
        (r"Deflection due to Live Load, $\delta_{LL}$", _live_str),
        (r"Allowable Live Load Deflection ($\Delta_{allow}$)", _allow_live_str),
        ("Live Load Deflection Check Status", _live_status),
        (r"Deflection due to Total Load, $\delta_{total}$", _total_str),
        (r"Allowable Total Deflection ($\Delta_{allow}$)", _allow_total_str),
        ("Total Load Deflection Check Status", _total_status),
    ], weights=(0.55, 0.45), note="IRC 22 Cl. 604.3.2. Governing (maximum) girder value shown.")

    return r"""
\chapter{Analysis Results}

A grillage model was used for structural analysis. The deck is idealized as a grid of elastic beam elements --- longitudinal members represent the composite steel girders with effective slab, and transverse members represent the slab or cross frames. This section summarizes the critical output from that analysis.
""" + demands.dumps() + reactions.dumps() + deflection + "\n" \
        + _fig_embed(fig_paths.get('bm_envelope'), 'Bending Moment Envelope (Envelope ULS): Max/min BM along span. X-axis: distance from left support (m). Y-axis: Bending Moment (kN-m).', width=r'0.75\textwidth') + "\n" \
        + _fig_embed(fig_paths.get('sf_envelope'), 'Shear Force Envelope (Envelope ULS): Max/min SF along span. X-axis: distance from left support (m). Y-axis: Shear Force (kN).', width=r'0.75\textwidth') + "\n" \
        + _fig_embed(fig_paths.get('defl_ll'), 'Vertical Deflection D$_y$ (1.0 LL): Maximum deflection along span. Load Case: 1.0 LL, Combination: $D_y$. Nodes shown. Isometric view.', width=r'0.75\textwidth') + "\n"
