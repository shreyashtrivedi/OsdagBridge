# =============================================================================
# Chapter 7: Material Take-off & Quantity Summary
# Quantities are computed by core/boq/boq_generator.py and injected into the
# input dict by generate_report(); this module only presents them.
# =============================================================================
import os

from osdagbridge.core.reports.report_tables import Col, ReportTable, multicol
from osdagbridge.core.reports.report_charts import (
    concrete_rebar_chart, figure_tex, safe_chart, steel_tonnage_chart)

# (S.N., description, BOQ key prefix)
_BOQ_ITEMS = [
    ("1",    "Structural Steel (IS 2062) for Girders", "steel_girders"),
    ("2(a)", "Cross Bracing --- Top Chord",            "bracing_top"),
    ("2(b)", "Cross Bracing --- Bottom Chord",         "bracing_bot"),
    ("2(c)", "Cross Bracing --- Diagonals",            "bracing_diag"),
    ("3",    "End Diaphragms (both supports)",         "end_diaphragm"),
    ("4",    "Concrete (M40) for Deck Slab",           "concrete_deck"),
    ("5",    "Reinforcement Steel (Fe 500)",           "rebar_deck"),
    ("6",    "Shear Stud Connectors",                  "shear_studs"),
    ("7",    "Crash Barrier",                          "crash_barrier"),
]


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _cell(v):
    s = "N.A." if v is None else str(v)
    return s


def ch7_quantities(input_dict, img_dir=None):
    q = input_dict

    boq = ReportTable("Bill of Materials (Steel, Concrete, and Reinforcement Quantities)", [
        Col("S.N.", 0.55, "c"), Col("Item Description", 2.1, "l"), Col("Unit Volume", 2.3, "c"),
        Col("Quantity", 0.85, "c"), Col(r"Total Volume (m$^3$)", 1.0, "c"),
        Col("Unit Weight (MT)", 0.95, "c"), Col("Total Weight (MT)", 0.95, "c")],
        note="MT = metric tonne. Steel density 7.85 t/m$^3$; reinforced concrete 2.5 t/m$^3$. "
             "Reinforcement is estimated at 120 kg per m$^3$ of deck concrete.")
    for sn, desc, key in _BOQ_ITEMS:
        boq.row(sn, desc, _cell(q.get(f"{key}_vol_formula", "N.A.")), _cell(q.get(f"{key}_qty", "N.A.")),
                _cell(q.get(f"{key}_vol_total", "N.A.")), _cell(q.get(f"{key}_wt_single", "N.A.")),
                _cell(q.get(f"{key}_wt_total", "N.A.")))

    # Totals for structural steel (girders + bracing + end diaphragms + studs)
    steel_keys = ("steel_girders", "bracing_top", "bracing_bot", "bracing_diag", "end_diaphragm", "shear_studs")
    steel_vals = [_num(q.get(f"{k}_wt_total")) for k in steel_keys]
    if any(v is not None for v in steel_vals):
        total = sum(v for v in steel_vals if v is not None)
        boq.row(multicol(r"\textbf{Total Structural Steel (items 1--3, 6)}", 6, "r", first=True),
                r"\textbf{" + f"{total:.2f}" + "}")

    # ── Charts ───────────────────────────────────────────────────────────────
    charts = ""
    if img_dir:
        bracing = [_num(q.get(f"{k}_wt_total")) for k in ("bracing_top", "bracing_bot", "bracing_diag")]
        bracing_total = sum(v for v in bracing if v is not None) if any(v is not None for v in bracing) else None
        steel_items = [
            ("Plate Girders", _num(q.get("steel_girders_wt_total"))),
            ("Cross Bracing", bracing_total),
            ("End Diaphragms", _num(q.get("end_diaphragm_wt_total"))),
        ]
        p1 = safe_chart(steel_tonnage_chart, steel_items, os.path.join(img_dir, "qty_steel.png"))

        conc_items = [("Deck Slab", _num(q.get("concrete_deck_vol_total"))),
                      ("Crash Barriers", _num(q.get("crash_barrier_vol_total")))]
        conc_items = [c for c in conc_items if c[1] is not None] or conc_items[:1]
        rebar_items = [("Deck Reinforcement", _num(q.get("rebar_deck_wt_total")))]
        p2 = safe_chart(concrete_rebar_chart, conc_items, rebar_items, os.path.join(img_dir, "qty_concrete.png"))

        density = ""
        c_vol, r_wt = _num(q.get("concrete_deck_vol_total")), _num(q.get("rebar_deck_wt_total"))
        if c_vol and r_wt:
            density = f" Deck reinforcement density: {r_wt * 1000.0 / c_vol:.0f} kg/m$^3$."
        # keep the heading with the first chart (page-bottom threshold)
        charts = (r"\needspace{20\baselineskip}" + "\n" + r"\section{Quantity Charts}" + "\n"
                  + figure_tex(p1, "Structural Steel Tonnage by Element (girders, cross bracing, end diaphragms)",
                               label="fig:qty-steel")
                  + figure_tex(p2, r"Concrete Volume (m$^3$) and Reinforcement Steel Weight (MT) --- separate "
                                   r"scales." + density, label="fig:qty-concrete"))

    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

The quantities below are estimated from the final member sizes and the bridge geometry. They are intended for preliminary costing; detailed fabrication quantities (splices, stiffeners, connection plates, wastage) are not included.

\section{Bill of Materials}
""" + boq.dumps() + charts
