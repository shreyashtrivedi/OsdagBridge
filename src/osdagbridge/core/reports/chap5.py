# =============================================================================
# Chapter 5: Design Checks
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING
import os

from osdagbridge.core.utils.common import (
    KEY_DD_AS_BOT,
    KEY_DD_AS_LONG,
    KEY_DD_AS_MIN,
    KEY_DD_AS_REQ_BOT,
    KEY_DD_AS_REQ_TOP,
    KEY_DD_AS_TOP,
    KEY_DD_COVER_OK,
    KEY_DD_DIA_BOT,
    KEY_DD_D_BOT,
    KEY_DD_FY,
    KEY_DD_GAMMA_DL,
    KEY_DD_GAMMA_LL,
    KEY_DD_HAS_OVERHANG,
    KEY_DD_IMPACT_FACTOR,
    KEY_DD_MIN_COVER,
    KEY_DD_MU_BOT,
    KEY_DD_MU_OH,
    KEY_DD_MU_TOP,
    KEY_DD_M_BARRIER,
    KEY_DD_M_DL,
    KEY_DD_M_DL_OH,
    KEY_DD_M_LL,
    KEY_DD_M_LL_OH,
    KEY_DD_M_ULS_HOG,
    KEY_DD_M_ULS_OH,
    KEY_DD_M_ULS_SAG,
    KEY_DD_PUNCH_C1,
    KEY_DD_PUNCH_C2,
    KEY_DD_PUNCH_OK,
    KEY_DD_PUNCH_U1,
    KEY_DD_PUNCH_VED,
    KEY_DD_PUNCH_VED_KN,
    KEY_DD_SHEAR_OK,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_SPACING_MAX,
    KEY_DD_SPAN,
    KEY_DD_SPC_BOT,
    KEY_DD_TYRE_LENGTH,
    KEY_DD_TYRE_WIDTH,
    KEY_DD_VEHICLE,
    KEY_DD_VRD_C_MPA,
    KEY_DD_WDL,
    KEY_DD_WHEEL_LOAD,
    KEY_DD_WK_BOT,
    KEY_DD_WK_LIMIT,
    KEY_DD_WK_OH,
    KEY_DD_WK_TOP,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DS_BOTTOM_CLEAR_COVER,
    KEY_DS_REINF_MATERIAL,
    KEY_DS_STUD_DIAMETER,
    KEY_DS_TOP_CLEAR_COVER,
    KEY_MATERIAL_DECK_FCK,
    KEY_MATERIAL_DECK_FCTM,
    KEY_MP_ED_TYPE,
    KEY_SD_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_BOTTOM_FLANGE_WIDTH,
    KEY_SD_BS_FCD,
    KEY_SD_BS_FCDW_LC,
    KEY_SD_BS_FCDW_WB,
    KEY_SD_BS_FPSD,
    KEY_SD_BS_R,
    KEY_SD_CLASS_FLANGE,
    KEY_SD_CLASS_WEB,
    KEY_SD_COMPOSITE_IZ,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
    KEY_SD_EFFECTIVE_SLAB_WIDTH,
    KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_FLANGE_SLENDERNESS,
    KEY_SD_HIGH_SHEAR,
    KEY_SD_IS_FQ,
    KEY_SD_IS_FQD,
    KEY_SD_IS_IYS_MIN,
    KEY_SD_IS_IYS_PROV,
    KEY_SD_LTB_CHI,
    KEY_SD_LTB_LAMBDA,
    KEY_SD_LTB_MB,
    KEY_SD_LTB_MCR,
    KEY_SD_MDV,
    KEY_SD_MD_CAPACITY,
    KEY_SD_MN_AXIAL,
    KEY_SD_MN_MOMENT,
    KEY_SD_MN_RATIO,
    KEY_SD_MU_APPLIED,
    KEY_SD_PANEL_CD,
    KEY_SD_PNA_DEPTH,
    KEY_SD_SC_D_LIMIT,
    KEY_SD_SC_EDGE_DIST,
    KEY_SD_SC_Qr_kN,
    KEY_SD_SC_Qu_kN,
    KEY_SD_SC_REQ_EDGE_DIST,
    KEY_SD_SC_SL1,
    KEY_SD_SC_SL2,
    KEY_SD_SC_SR,
    KEY_SD_SECTION_CLASS,
    KEY_SD_SECTION_PROP_AREA,
    KEY_SD_SECTION_PROP_IZ,
    KEY_SD_SECTION_PROP_ZUZ,
    KEY_SD_SECTION_PROP_ZZ,
    KEY_SD_SHEAR_AV,
    KEY_SD_SHEAR_KV,
    KEY_SD_SHEAR_LAMBDA_W,
    KEY_SD_SHEAR_TAU_B,
    KEY_SD_SHEAR_VCR,
    KEY_SD_SHEAR_VU,
    KEY_SD_STIFF_END_COUNT,
    KEY_SD_STIFF_END_THICK,
    KEY_SD_STIFF_INT_SPACING,
    KEY_SD_STIFF_INT_THICK,
    KEY_SD_STIFF_LONG,
    KEY_SD_STIFF_METHOD,
    KEY_SD_STRESS_STEEL,
    KEY_SD_STRESS_STEEL_ALLOWABLE,
    KEY_SD_TOP_FLANGE_THICKNESS,
    KEY_SD_TOP_FLANGE_WIDTH,
    KEY_SD_TOTAL_DEPTH,
    KEY_SD_TS_VL,
    KEY_SD_TS_VRD,
    KEY_SD_ULS_PER_GIRDER,
    KEY_SD_WEB_CLASS_LIMIT,
    KEY_SD_WEB_SLENDERNESS,
    KEY_SD_WEB_THICKNESS,
    KEY_SPAN,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_NO_OF_GIRDERS,
    KEY_UTIL_FLEXURE,
    KEY_UTIL_INTERACTION,
    KEY_UTIL_LTB,
    KEY_UTIL_SHEAR
)

from osdagbridge.core.reports.report_utils import _tex, _render_value, get_girder_entries

from osdagbridge.core.reports.report_tables import Col, ReportTable, kv_table, multicol
from osdagbridge.core.reports.report_charts import (
    figure_tex, safe_chart, ur_component_chart, ur_detail_chart)
from osdagbridge.core.reports.styles import note, status, ur_value

if TYPE_CHECKING:
    pass

# Column presets shared by the per-girder check tables
_CHECK_COLS = lambda c2, c3, c4="Value", c5="Status": [  # noqa: E731
    Col("Girder", 0.8, "c"), Col(c2, 2.2, "l"), Col(c3, 1.9, "c"), Col(c4, 1.6, "c"), Col(c5, 0.9, "c")]


def ch5_design_checks(checks_data, bridge, img_dir=None) -> str:
    """Chapter 5 — Design Checks.

    Parameters
    ----------
    checks_data : dict
        Raw checks payload (currently unused; data is sourced from bridge).
    bridge : ReportDataBridge
        Provides input_dict, output_dict, and helper methods.
    img_dir : str
        Directory where generated charts (Section 5.5) are written.
    """
    girder_entries = get_girder_entries(bridge.input_dict)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", "M1") for i in range(1, n + 1)]
    od = bridge.output_dict

    def rv(key, unit=""):
        return _render_value(od, key, unit)

    # Deck slab design report values (Tables 5.17(a)-(g)), keyed to
    # common.KEY_DD_*. Populated by deckdesign.design_deck_slab(); empty
    # dict when deck design has not been run. Look up with deck_rpt.get(KEY_...).
    deck_rpt = od.get("deck_report_values", {}) or {}

    def _ratio_status(ur, warn_bands=False):
        if ur is None:
            return "---"
        if warn_bands:   # interaction DCR engine bands: PASS <0.90, WARN <1.00, FAIL >=1.00
            return status("PASS" if ur < 0.90 else ("WARN" if ur < 1.00 else "FAIL"))
        return status(ur <= 1.0)

    def _pct_ur(key):
        """URs stored as percent (cat_urs x 100) -> ratio float or None."""
        try:
            return float(od.get(key)) / 100.0
        except (TypeError, ValueError):
            return None

    def _ge_status(provided, required):
        try:
            return status(float(provided) >= float(required))
        except (TypeError, ValueError):
            return "---"

    def _le_status(actual, allowable):
        try:
            return status(float(actual) <= float(allowable))
        except (TypeError, ValueError):
            return "---"

    def _dfmt(v, nd=2):
        try:
            return f"{float(v):.{nd}f}"
        except (TypeError, ValueError):
            return ""

    def _unit(v, unit, nd=2):
        s = _dfmt(v, nd)
        return (s + " " + unit) if s else ""

    lbls = [_tex(lbl) for lbl, _ in girder_entries]

    # ── 5.1 Girder section properties ────────────────────────────────────────
    t51 = ReportTable("Girder Section Properties (Final Optimized / User-selected)", [
        Col("Girder", 0.8, "c"), Col("Property", 3.2, "l"), Col("Value", 1.6, "c")])
    props = [
        (r"Depth, D (mm)", KEY_SD_TOTAL_DEPTH),
        (r"Top Flange Width, $b_f$ (mm)", KEY_SD_TOP_FLANGE_WIDTH),
        (r"Bottom Flange Width, $b_f$ (mm)", KEY_SD_BOTTOM_FLANGE_WIDTH),
        (r"Top Flange Thickness, $t_f$ (mm)", KEY_SD_TOP_FLANGE_THICKNESS),
        (r"Bottom Flange Thickness, $t_f$ (mm)", KEY_SD_BOTTOM_FLANGE_THICKNESS),
        (r"Web Thickness, $t_w$ (mm)", KEY_SD_WEB_THICKNESS),
        (r"Gross Area, A (cm$^2$)", KEY_SD_SECTION_PROP_AREA),
        (r"Moment of Inertia, $I_z$ (cm$^4$)", KEY_SD_SECTION_PROP_IZ),
        (r"Elastic Section Modulus, $Z_{ez}$ (cm$^3$)", KEY_SD_SECTION_PROP_ZZ),
        (r"Plastic Section Modulus, $Z_{pz}$ (cm$^3$)", KEY_SD_SECTION_PROP_ZUZ),
        (r"Effective Slab Width, $b_{eff}$ (mm)", KEY_SD_EFFECTIVE_SLAB_WIDTH),
        (r"Transformed Composite $I_z$ (cm$^4$)", KEY_SD_COMPOSITE_IZ),
        (r"Depth to Plastic Neutral Axis (mm)", KEY_SD_PNA_DEPTH),
    ]
    for lbl in lbls:
        t51.group(lbl, [(name, rv(key)) for name, key in props])

    # ── 5.2 Classification ───────────────────────────────────────────────────
    t52 = ReportTable("Girder Section Classification", [
        Col("Girder", 0.8, "c"), Col("Element", 1.5), Col("Slenderness Ratio", 1.3, "c"),
        Col("Class Limit", 1.2, "c"), Col("Classification", 1.6, "c")], note="IS 800:2007 Table 2")
    for lbl in lbls:
        t52.group(lbl, [
            ("Top Flange", rv(KEY_SD_FLANGE_SLENDERNESS), rv(KEY_SD_FLANGE_CLASS_LIMIT), rv(KEY_SD_CLASS_FLANGE)),
            ("Web", rv(KEY_SD_WEB_SLENDERNESS), rv(KEY_SD_WEB_CLASS_LIMIT), rv(KEY_SD_CLASS_WEB)),
            ("Overall Section", "---", "---", rv(KEY_SD_SECTION_CLASS)),
        ])

    # ── 5.3 Moment capacity ──────────────────────────────────────────────────
    flex_ur = _pct_ur(KEY_UTIL_FLEXURE)
    t53 = ReportTable("Moment Capacity Check", _CHECK_COLS("Parameter", "Formula / Reference"),
                      note="IRC 22 Cl. 603.3.1, IS 800 Cl. 8.2.1")
    for lbl in lbls:
        t53.group(lbl, [
            (r"Applied Moment, $M_u$", "Governing LC (ULS)", rv(KEY_SD_MU_APPLIED, " kN-m"), "---"),
            (r"Design Moment Capacity, $M_d$", "IRC 22 Cl. 603.3.1", rv(KEY_SD_MD_CAPACITY, " kN-m"), "---"),
            (r"Utilization Ratio, $M_u / M_d$", r"$M_u / M_d$", ur_value(flex_ur), _ratio_status(flex_ur)),
        ])

    # ── 5.4 Shear capacity ───────────────────────────────────────────────────
    shear_ur = _pct_ur(KEY_UTIL_SHEAR)
    t54 = ReportTable("Shear Capacity Check", _CHECK_COLS("Parameter", "Formula / Reference"),
                      note="IS 800 Cl. 8.4, IRC 22 Cl. 603.3.3.2")
    for lbl in lbls:
        t54.group(lbl, [
            (r"Applied Shear, $V_u$", "Governing LC (ULS)", rv(KEY_SD_SHEAR_VU, " kN"), "---"),
            (r"Shear Area, $A_v$", r"$d_w \times t_w$", rv(KEY_SD_SHEAR_AV, " mm$^2$"), "---"),
            (r"Panel Aspect Ratio, c/d", "---", rv(KEY_SD_PANEL_CD), "---"),
            (r"Shear Buckling Coefficient, $k_v$", "IS 800 Cl. 8.4.2.2", rv(KEY_SD_SHEAR_KV), "---"),
            (r"Web Slenderness, $\lambda_w$", r"$\sqrt{f_{yw}/(\sqrt{3}\,\tau_{cr})}$", rv(KEY_SD_SHEAR_LAMBDA_W), "---"),
            (r"Design Shear Stress, $\tau_b$", "IRC 22 Cl. 603.3.3.2", rv(KEY_SD_SHEAR_TAU_B, " MPa"), "---"),
            (r"Shear Buckling Resistance, $V_{cr}$", r"$A_v \times \tau_b$", rv(KEY_SD_SHEAR_VCR, " kN"), "---"),
            (r"Utilization Ratio, $V_u / V_d$", r"$V_u / V_d$", ur_value(shear_ur), _ratio_status(shear_ur)),
        ])

    # ── 5.5 Interaction (M-V, M-N) ───────────────────────────────────────────
    mv_ur = _pct_ur(KEY_UTIL_INTERACTION)
    _mn_r, _mn_ax, _mn_mo = od.get(KEY_SD_MN_RATIO), od.get(KEY_SD_MN_AXIAL), od.get(KEY_SD_MN_MOMENT)
    if _mn_r is None or _mn_ax is None or _mn_mo is None:
        mn_cond = mn_val = mn_status = "N/A"
    else:
        mn_cond = f"{_mn_ax:.2f} + {_mn_mo:.2f} = {_mn_r:.3f}"
        mn_val = f"{_mn_r:.3f}"
        mn_status = _ratio_status(float(_mn_r), warn_bands=True)
    t55 = ReportTable("Interaction Checks (M-V and M-N)", _CHECK_COLS("Check", "Condition"),
                      note=r"IRC 22 Cl. 603.3.3.3. Bands: PASS $<0.90$, WARN $<1.00$, FAIL $\geq 1.00$.")
    for lbl in lbls:
        t55.group(lbl, [
            ("High Shear Condition?", r"$V_u > 0.6\,V_d$", rv(KEY_SD_HIGH_SHEAR), "---"),
            (r"Reduced Moment Capacity, $M_{dv}$", "IRC 22 Cl. 603.3.3.3", rv(KEY_SD_MDV, " kN-m"), "---"),
            (r"Interaction Check: $M_u \leq M_{dv}$", "---", ur_value(mv_ur), _ratio_status(mv_ur, True)),
            (r"Interaction Check: $N_u/N_{Rd} + M_u/M_{dv} \leq 1.0$", mn_cond, mn_val, mn_status),
        ])

    # ── 5.6 LTB (construction stage) ─────────────────────────────────────────
    ltb_ur = _pct_ur(KEY_UTIL_LTB)
    t56 = ReportTable("Lateral Torsional Buckling Check --- Construction Stage",
                      _CHECK_COLS("Parameter", "Formula / Reference"),
                      note="IRC 22 Cl. 603.3.3.1, IS 800 Cl. 8.2.2")
    for lbl in lbls:
        t56.group(lbl, [
            (r"Elastic Critical Moment, $M_{cr}$", "IRC 22 Cl. 603.3.3.1", rv(KEY_SD_LTB_MCR, " kN-m"), "---"),
            (r"Non-dim. Slenderness, $\bar{\lambda}_{LT}$", r"$\sqrt{M_p / M_{cr}}$", rv(KEY_SD_LTB_LAMBDA), "---"),
            (r"LTB Reduction Factor, $\chi_{LT}$", "IS 800 Cl. 8.2.2", rv(KEY_SD_LTB_CHI), "---"),
            (r"LTB Resistance, $M_b$", r"$\chi_{LT}\,M_p / \gamma_{m0}$", rv(KEY_SD_LTB_MB, " kN-m"), "---"),
            (r"$M_u \leq M_b$", r"$M_u / M_b$", ur_value(ltb_ur), _ratio_status(ltb_ur, True)),
        ])

    # ── 5.7 Stiffener design summary ─────────────────────────────────────────
    t57 = ReportTable("Stiffener Design Summary", [
        Col("Girder", 0.8, "c"), Col("Parameter", 3.0), Col("Value", 2.2)])
    for lbl in lbls:
        t57.group(lbl, [
            ("Shear Buckling Design Method", rv(KEY_SD_STIFF_METHOD)),
            ("Intermediate Stiffener Thickness (mm)", rv(KEY_SD_STIFF_INT_THICK)),
            ("Intermediate Stiffener Spacing (mm)", rv(KEY_SD_STIFF_INT_SPACING)),
            ("End Panel Stiffener Thickness (mm)", rv(KEY_SD_STIFF_END_THICK)),
            ("No. of End Panel Stiffeners", rv(KEY_SD_STIFF_END_COUNT)),
            ("Longitudinal Stiffeners", rv(KEY_SD_STIFF_LONG)),
        ])

    # Intermediate stiffener checks — verification table only exists in Custom
    # mode (stiffener sizes supplied by the user); omitted in Optimized mode.
    _is_custom = str(bridge.input_dict.get(KEY_DESIGN_MODE, "Optimized")).strip().lower() in {"custom", "customized"}
    t58_tex = ""
    if _is_custom:
        t58 = ReportTable("Intermediate Stiffener Checks",
                          _CHECK_COLS("Check", "Required", "Provided"), note="IS 800 Cl. 8.7.1.2")
        iys = _ge_status(od.get(KEY_SD_IS_IYS_PROV), od.get(KEY_SD_IS_IYS_MIN))
        fqd = _ge_status(od.get(KEY_SD_IS_FQD), od.get(KEY_SD_IS_FQ))
        for lbl in lbls:
            t58.group(lbl, [
                (r"Min. Moment of Inertia, $I_s$", rv(KEY_SD_IS_IYS_MIN, " mm$^4$"), rv(KEY_SD_IS_IYS_PROV, " mm$^4$"), iys),
                (r"Buckling Resistance, $F_{qd} \geq F_q$", rv(KEY_SD_IS_FQ, " kN"), rv(KEY_SD_IS_FQD, " kN"), fqd),
            ])
        t58_tex = t58.dumps()

    # ── 5.9 End panel (bearing) stiffener checks ─────────────────────────────
    _bs_r = od.get(KEY_SD_BS_R)

    def _bs_check(resist_key):
        prov = od.get(resist_key)
        # Resistance not computed (guidance mode) -> N/A.
        if prov is None or float(prov) <= 0.0 or _bs_r is None:
            return ("N/A", "N/A", "N/A")
        return (f"{_bs_r} kN", f"{prov} kN", status(float(prov) >= float(_bs_r)))

    t59 = ReportTable("End Panel Stiffener Checks", _CHECK_COLS("Check", "Required", "Provided"),
                      note="IS 800 Cl. 8.7.3 (bearing stiffener resistances vs. support reaction R).")
    bs_rows = [(name,) + _bs_check(key) for name, key in (
        ("Web Buckling Resistance", KEY_SD_BS_FCDW_WB), ("Local Crushing Resistance", KEY_SD_BS_FCDW_LC),
        ("Bearing Capacity", KEY_SD_BS_FPSD), ("Column Buckling Resistance", KEY_SD_BS_FCD))]
    for lbl in lbls:
        t59.group(lbl, bs_rows)

    # ── 5.10 Serviceability — deflection (IRC 22 Cl. 604.3.2) ────────────────
    try:
        _span_m = float(bridge.input_dict.get(KEY_SPAN))
        _allow_live_mm, _allow_total_mm = _span_m * 1000.0 / 800.0, _span_m * 1000.0 / 600.0
    except (TypeError, ValueError):
        _allow_live_mm = _allow_total_mm = None
    _allow_live_str = f"L/800 = {_allow_live_mm:.1f} mm" if _allow_live_mm is not None else ""
    _allow_total_str = f"L/600 = {_allow_total_mm:.1f} mm" if _allow_total_mm is not None else ""
    t510 = ReportTable("Serviceability --- Deflection Checks", _CHECK_COLS("Check", "Allowable", "Actual (mm)"),
                       note="IRC 22 Cl. 604.3.2")
    for gi, lbl in enumerate(lbls, start=1):
        live = od.get(f"{KEY_SD_DEFL_LIVE}.G{gi}")
        total = od.get(f"{KEY_SD_DEFL_TOTAL}.G{gi}")
        t510.group(lbl, [
            (r"Live Load Deflection, $\delta_{LL}$", _allow_live_str, _dfmt(live, 3), _le_status(live, _allow_live_mm)),
            (r"Total Load Deflection, $\delta_{total}$", _allow_total_str, _dfmt(total, 3), _le_status(total, _allow_total_mm)),
        ])

    # ── 5.11 Serviceability — steel stress (IRC 22 Cl. 604.3.1) ──────────────
    dr = od.get("design_results", {}) or {}
    sig, allow = dr.get(KEY_SD_STRESS_STEEL), dr.get(KEY_SD_STRESS_STEEL_ALLOWABLE)
    t511 = ReportTable("Serviceability --- Maximum Stress Limitation", [
        Col("Girder", 0.8, "c"), Col("Element", 2.2), Col("Allowable Stress", 1.5, "c"),
        Col("Actual Stress", 1.5, "c"), Col("Status", 0.9, "c")],
        note=r"IRC 22 Cl. 604.3.1; allowable $= 0.9\,f_y$ (envelope SLS).")
    for lbl in lbls:
        t511.row(lbl, r"Structural Steel ($0.9\,f_y$)", _unit(allow, "MPa"), _unit(sig, "MPa"), _le_status(sig, allow))

    # ── 5.12 Fatigue (IRC 22 Cl. 605) ────────────────────────────────────────
    fat = (dr.get(KEY_SD_ULS_PER_GIRDER, {}) or {}).get("fatigue", {}) or {}
    t512 = ReportTable("Serviceability --- Fatigue Assessment", [
        Col("Girder", 0.8, "c"), Col(r"Stress Range, $\Delta\sigma$", 1.6, "c"),
        Col(r"Fatigue Limit, $f_{fd}$", 1.6, "c"), Col("Utilization Ratio", 1.4, "c"), Col("Status", 1.0, "c")],
        note=r"IRC 22 Cl. 605 --- governing of normal and shear fatigue (worst by DCR). Capacity reduction "
             r"factor $\mu_r$ applied where plate thickness $>$ 25 mm.")
    for gi, lbl in enumerate(lbls, start=1):
        g = fat.get(f"G{gi}", {}) or {}
        t512.row(lbl, _unit(g.get("demand"), "MPa"), _unit(g.get("capacity"), "MPa"),
                 ur_value(g.get("ur")), status(g.get("status")))

    # ── 5.13 Girder design summary (controlling check per girder) ────────────
    pg = dr.get("per_girder", {}) or {}

    def _with_unit(value, unit):
        s = _dfmt(value)
        if not s:
            return ""
        return (s + " " + unit) if unit and str(unit) not in ("-", "–") else s

    t513 = ReportTable("Girder Design Summary (DCR / Utilization Ratio)", [
        Col("Girder", 0.7, "c"), Col("Controlling LC / Combination", 2.2, "l"), Col("Controlling Check", 1.6, "l"),
        Col("Demand", 1.1, "c"), Col("Capacity", 1.1, "c"), Col("UR", 0.7, "c"), Col("Status", 0.9, "c")],
        note="UR = Demand / Capacity. A value $\\leq 1.0$ indicates a passing check. The controlling check is the "
             "criterion with the highest UR for each girder, with the real load case/combination that drives it.")
    girder_controlling = []     # (label, ur) for charts
    for gi, lbl in enumerate(lbls, start=1):
        g_data = pg.get(f"G{gi}", {}) or {}
        checks = g_data.get("checks") or []
        if not checks:
            t513.row(lbl, "", "", "", "", "", "")
            continue
        ctrl = max(checks, key=lambda c: c.get("dcr") or 0.0)
        ctrl_lc, best_dcr = None, None
        for lc_name, lc_data in (g_data.get("per_lc") or {}).items():
            if str(lc_name).lower().startswith("envelope"):
                continue
            for chk in lc_data.get("checks") or []:
                if chk.get("id") == ctrl.get("check_id"):
                    d = chk.get("dcr") or 0.0
                    if best_dcr is None or d > best_dcr:
                        best_dcr, ctrl_lc = d, lc_name
        if ctrl_lc is None:
            ctrl_lc = (g_data.get("demand") or {}).get("governing_combination") or ""
        girder_controlling.append((lbl, ctrl.get("dcr")))
        t513.row(lbl, _tex(str(ctrl_lc)), _tex(str(ctrl.get("name", ""))),
                 _with_unit(ctrl.get("demand"), ctrl.get("demand_unit")),
                 _with_unit(ctrl.get("capacity"), ctrl.get("capacity_unit")),
                 ur_value(ctrl.get("dcr"), 3), status(ctrl.get("status")))

    # ── 5.14 – 5.16 Shear connectors ─────────────────────────────────────────
    t514 = ReportTable("Shear Connector Capacity", [
        Col("Parameter", 1.6), Col("Formula", 2.6, "c"), Col("Value", 1.0, "c"), Col("Reference", 1.4)])
    t514.row(r"Design Resistance, $Q_u$",
             r"\footnotesize\makecell{$Q_u=\min(Q_{u,s},\,Q_{u,c})$\\[3pt]$Q_{u,s}=\dfrac{0.8\,f_u\,(\pi d^2/4)}{\gamma_v}$"
             r"\\[3pt]$Q_{u,c}=\dfrac{0.29\,\alpha\,d^2\sqrt{f_{ck}\,E_{cm}}}{\gamma_v}$}",
             _unit(dr.get(KEY_SD_SC_Qu_kN), "kN"), "IRC 22 Cl. 606.3.1 (Eq. 6.1)")
    t514.row(r"Fatigue Shear Resistance, $Q_r$", r"IRC 22 Table 8 ($\phi d$, $N_{sc}$)",
             _unit(dr.get(KEY_SD_SC_Qr_kN), "kN"), "IRC 22 Cl. 606.3.2 (Table 8)")

    sc_prov = dr.get("stud_spacing_provided_mm")
    t515 = ReportTable("Shear Connector Spacing", [
        Col("Criterion", 1.6), Col("Governing Spacing", 1.4, "c"), Col("Actual Spacing Provided", 1.6, "c"),
        Col("Status", 0.9, "c")], note=r"IRC 22 Cl. 606.4, 606.9. Governing spacing $= \min(S_{L1}, S_{L2}, S_R)$.")
    for crit, req in (("ULS Shear (SL1)", dr.get(KEY_SD_SC_SL1)), ("Full Composite (SL2)", dr.get(KEY_SD_SC_SL2)),
                      ("SLS Fatigue (SR)", dr.get(KEY_SD_SC_SR)),
                      ("Max Spacing Limit (IRC 22)", dr.get("stud_spacing_max_mm"))):
        t515.row(crit, _unit(req, "mm", 1), _unit(sc_prov, "mm", 1), _le_status(sc_prov, req))

    ts_vl, ts_vrd = dr.get(KEY_SD_TS_VL), dr.get(KEY_SD_TS_VRD)
    try:
        ts_ur = float(ts_vl) / float(ts_vrd) if float(ts_vrd) > 0 else None
    except (TypeError, ValueError):
        ts_ur = None
    ts_ok = dr.get("transverse_shear_ok")
    ts_status = status(ts_ok) if ts_ok is not None else "---"
    # Provided transverse steel = deck main (bottom + top) bars crossing the shear plane
    # (from deck design; the steel designer's own Ast_provided is computed before the deck).
    dd = od.get("deck_design_results", {}) or {}
    try:
        ast_prov = (float(dd.get("rebar_bottom_area") or 0) + float(dd.get("rebar_top_area") or 0)) / 100.0
    except (TypeError, ValueError):
        ast_prov = None
    ast_req = dr.get("Ast_required_cm2_per_m")
    stud_d = bridge.input_dict.get(KEY_DS_STUD_DIAMETER)
    d_lim, edge, edge_req = dr.get(KEY_SD_SC_D_LIMIT), dr.get(KEY_SD_SC_EDGE_DIST), dr.get(KEY_SD_SC_REQ_EDGE_DIST)
    t516 = ReportTable("Transverse Shear and Detailing Checks", [
        Col("Check", 2.2), Col("Value", 2.8), Col("Status", 0.8, "c")], note="IRC 22 Cl. 606.6, 606.10.")
    t516.row(r"Longitudinal Shear per unit length, $V_L$", _unit(ts_vl, "kN/m"), "---")
    t516.row(r"Transverse Shear Capacity of Slab, $V_{Rd}$", _unit(ts_vrd, "kN/m"), "---")
    t516.row("Transverse Shear Check", r"$V_L/V_{Rd}$ = " + (ur_value(ts_ur) or "---"), ts_status)
    t516.row(r"Min. Transverse Reinforcement, $A_{st,min}$",
             "Required " + _unit(ast_req, r"cm$^2$/m") + ", Provided " + _unit(ast_prov, r"cm$^2$/m"),
             _ge_status(ast_prov, ast_req))
    t516.row(r"Stud Diameter $\leq 2\,t_f$", r"$d$ = " + _unit(stud_d, "mm", 1) + r" $\leq 2t_f$ = " + _unit(d_lim, "mm", 1),
             _le_status(stud_d, d_lim))
    t516.row("Stud Edge Distance", "Provided " + _unit(edge, "mm", 1) + r" (req. $\geq$ " + _unit(edge_req, "mm", 1) + ")",
             _ge_status(edge, edge_req))

    # ── Deck slab value helpers (Tables 5.17 a-g) ────────────────────────────
    _dk_has = bool(deck_rpt)
    _dk_oh = bool(deck_rpt.get(KEY_DD_HAS_OVERHANG))
    _DKPH = r"\placeholder{---}"

    def _dkv(key, default=0.0):
        v = deck_rpt.get(key)
        if v is None or v == "":
            return default
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    def _dkf(key, nd=2, scale=1.0):
        if not _dk_has:
            return _DKPH
        v = deck_rpt.get(key)
        if v is None or v == "":
            return _DKPH
        try:
            return f"{float(v) * scale:.{nd}f}"
        except (TypeError, ValueError):
            return _tex(v)

    def _dks(ok):
        return status(bool(ok)) if _dk_has else "---"

    def _dkoh(key, nd=2, scale=1.0, unit=""):
        if not _dk_has:
            return _DKPH
        if not _dk_oh:
            return "N/A"
        return _dkf(key, nd=nd, scale=scale) + unit

    _dk_wks = [_dkv(KEY_DD_WK_BOT), _dkv(KEY_DD_WK_TOP)] + ([_dkv(KEY_DD_WK_OH)] if _dk_oh else [])
    _dk_gov_wk = max(_dk_wks)
    _dk_crack_ok = _dk_has and _dk_gov_wk <= _dkv(KEY_DD_WK_LIMIT)
    gdl, gll = _dkf(KEY_DD_GAMMA_DL, nd=2), _dkf(KEY_DD_GAMMA_LL, nd=2)
    ivr = lambda key: _render_value(bridge.input_dict, key)  # noqa: E731

    deck_geom = kv_table("Deck Slab --- Loading and Geometry", [
        (r"Effective Span of Deck Slab, $l_{eff}$", _dkf(KEY_DD_SPAN, nd=0, scale=1000.0) + " mm (girder spacing, c/c)"),
        (r"Deck Thickness, $t_s$", ivr(KEY_TS_DECK_THICKNESS) + " mm"),
        ("Clear Cover (IRC 112 Cl. 15.2)", "Top " + ivr(KEY_DS_TOP_CLEAR_COVER) + " / Bottom " + ivr(KEY_DS_BOTTOM_CLEAR_COVER) + " mm"),
        ("Concrete Grade (IRC 112 Cl. 6.4)", ivr(KEY_DECK_CONCRETE_GRADE_BASIC) + r" ($f_{ck}$ = " + ivr(KEY_MATERIAL_DECK_FCK)
         + r" MPa, $f_{ctm}$ = " + ivr(KEY_MATERIAL_DECK_FCTM) + " MPa)"),
        ("Reinforcement Grade (IRC 112 Cl. 6.2)", ivr(KEY_DS_REINF_MATERIAL) + r" ($f_y$ = " + _dkf(KEY_DD_FY, nd=0) + " MPa)"),
        (r"Dead Load per Unit Area, $w_{DL}$", _dkf(KEY_DD_WDL) + r" kN/m$^2$ (slab self-weight)"),
        ("IRC 6 Wheel Load (Class A / 70R)", _dkf(KEY_DD_WHEEL_LOAD, nd=1) + " kN"),
        (r"Tyre Contact Width (IRC 6 Annex A)", _dkf(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0) + " mm (transverse)"),
        ("Impact Factor (IRC 6 Cl. 208.2)", _dkf(KEY_DD_IMPACT_FACTOR, nd=3)),
        ("Governing Live Load Case", _dkf(KEY_DD_VEHICLE)),
    ], weights=(0.45, 0.55))

    deck_flex = ReportTable("Deck Slab --- Flexure Check: Interior Panel (Pigeaud's Method)", [
        Col("Location", 1.0, "c"), Col("Parameter", 2.0), Col("Formula / Reference", 1.7, "c"),
        Col("Value", 1.4, "c"), Col("Status", 0.8, "c")],
        note="IRC 112 Cl. 12.2. Distribution (longitudinal) reinforcement designed for 20\\% of main steel "
             "moment (IRC 21 Cl. 305.18).")
    deck_flex.group(r"At Midspan\\(Sagging)", [
        (r"Transverse BM (DL), $M_{T,DL}$", r"$w_{DL}\,l_{eff}^2/10$", _dkf(KEY_DD_M_DL) + " kN-m/m", "---"),
        (r"Transverse BM (LL), $M_{T,LL}$", "Effective width (IRC 112 B3.1)", _dkf(KEY_DD_M_LL) + " kN-m/m", "---"),
        (r"Total Design BM, $M_{u,sag}$", gdl + " DL + " + gll + " LL", _dkf(KEY_DD_M_ULS_SAG) + " kN-m/m", "---"),
        (r"Effective depth, $d$", r"$t_s - c_{nom} - \phi/2$", _dkf(KEY_DD_D_BOT, nd=1) + " mm", "---"),
        (r"Moment Capacity, $M_{Rd}$", "IRC 112 Cl. 12.2", _dkf(KEY_DD_MU_BOT) + " kN-m/m",
         _dks(_dkv(KEY_DD_MU_BOT) >= _dkv(KEY_DD_M_ULS_SAG))),
    ])
    deck_flex.group(r"At Support\\(Hogging)", [
        (r"Total Design BM, $M_{u,hog}$", gdl + " DL + " + gll + " LL (at support)", _dkf(KEY_DD_M_ULS_HOG) + " kN-m/m", "---"),
        (r"Required Top Steel, $A_{st,top}$", r"$M_u / (0.87\,f_y\,d)$", _dkf(KEY_DD_AS_REQ_TOP, nd=0) + r" mm$^2$/m", "---"),
        (r"Moment Capacity, $M_{Rd}$", "IRC 112 Cl. 12.2", _dkf(KEY_DD_MU_TOP) + " kN-m/m",
         _dks(_dkv(KEY_DD_MU_TOP) >= _dkv(KEY_DD_M_ULS_HOG))),
    ])

    pfs_cols = [Col("Parameter", 2.3), Col("Formula / Reference", 1.8, "c"), Col("Value", 1.5, "c"), Col("Status", 0.8, "c")]
    deck_oh = ReportTable("Deck Slab --- Cantilever Overhang Flexure Check", pfs_cols,
                          note="IRC 6 Cl. 206.4 crash barrier loads applied at kerb face; IRC 112 Cl. 12.2 flexure.")
    deck_oh.rows([
        (r"Overhang Length, $l_{oh}$", "---", ivr(KEY_TS_DECK_OVERHANG) + " m", "---"),
        ("Crash Barrier Load Moment", "IRC 6 Cl. 206.4", _dkoh(KEY_DD_M_BARRIER, unit=" kN-m/m"), "---"),
        ("Dead Load Moment", r"$w_{DL}\,l_{oh}^2/2$ + railing", _dkoh(KEY_DD_M_DL_OH, unit=" kN-m/m"), "---"),
        ("Live Load Moment (eccentric wheel)", r"Wheel load $\times$ arm", _dkoh(KEY_DD_M_LL_OH, unit=" kN-m/m"), "---"),
        (r"Total Hogging Moment, $M_{u,oh}$", gdl + " DL + " + gll + " (LL + CB)", _dkoh(KEY_DD_M_ULS_OH, unit=" kN-m/m"), "---"),
        (r"Moment Capacity (top steel), $M_{Rd,oh}$", "IRC 112 Cl. 12.2", _dkoh(KEY_DD_MU_OH, unit=" kN-m/m"),
         (_dks(_dkv(KEY_DD_MU_OH) >= _dkv(KEY_DD_M_ULS_OH)) if _dk_oh else ("N/A" if _dk_has else "---"))),
    ])

    def _ratio_str(num_key, den_key):
        return (f"{_dkv(num_key) / _dkv(den_key):.2f}" if (_dk_has and _dkv(den_key) > 0) else _DKPH)

    deck_punch = ReportTable("Deck Slab --- Punching Shear Check (IRC 112 Cl. 10.4.6)", pfs_cols,
                             note=r"Punching shear reinforcement not typically required for deck slabs with $d \geq 200$ mm "
                                  "and adequate longitudinal reinforcement.")
    deck_punch.rows([
        (r"Design Wheel Load (ULS), $V_{Ed}$", r"$\gamma_Q\,(1+IF)\,P_w$", _dkf(KEY_DD_PUNCH_VED_KN, nd=1) + " kN", "---"),
        ("Tyre Contact Area", r"$a \times b$ (IRC 6 Annex A)",
         _dkf(KEY_DD_TYRE_WIDTH, nd=0, scale=1000.0) + r" $\times$ " + _dkf(KEY_DD_TYRE_LENGTH, nd=0) + " mm", "---"),
        (r"Loaded Area at mid-depth, $b_0$", r"$c_1 \times c_2$ (incl.\ WC dispersion)",
         _dkf(KEY_DD_PUNCH_C1, nd=0) + r" $\times$ " + _dkf(KEY_DD_PUNCH_C2, nd=0) + " mm", "---"),
        (r"Control Perimeter, $u_1$", r"$2(c_1+c_2) + 4\pi d$", _dkf(KEY_DD_PUNCH_U1, nd=0) + " mm", "---"),
        (r"Punching Shear Stress, $v_{Ed}$", r"$V_{Ed} / (u_1\,d)$", _dkf(KEY_DD_PUNCH_VED, nd=3) + " MPa", "---"),
        (r"Punching Resistance, $v_{Rd,c}$", r"IRC 112 Eq.\ 10.1", _dkf(KEY_DD_VRD_C_MPA, nd=3) + " MPa", "---"),
        ("Punching Shear Check", r"$v_{Ed} \leq v_{Rd,c}$", _ratio_str(KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA),
         _dks(bool(deck_rpt.get(KEY_DD_PUNCH_OK)))),
    ])

    deck_crack = kv_table("Crack Width Check (Deck Slab)", [
        (r"Min. Reinforcement for Crack Control, $A_{s,min}$", _dkf(KEY_DD_AS_MIN, nd=0) + r" mm$^2$/m [IRC 112 Cl. 16.5.1]"),
        ("Provided Reinforcement (bottom)", r"$\phi$" + _dkf(KEY_DD_DIA_BOT, nd=0) + " @ " + _dkf(KEY_DD_SPC_BOT, nd=0)
         + " mm c/c (" + _dkf(KEY_DD_AS_BOT, nd=0) + r" mm$^2$/m)"),
        ("Max. Permissible Crack Width", _dkf(KEY_DD_WK_LIMIT) + " mm"),
        (r"Calculated Crack Width, $w_k$ (governing)", (f"{_dk_gov_wk:.4f}" if _dk_has else _DKPH) + " mm"),
        ("Crack Width Check", _dks(_dk_crack_ok)),
    ], headers=("Parameter", "Value / Reference"), weights=(0.5, 0.5))

    _d_bot = _dkv(KEY_DD_D_BOT)
    deck_shear = ReportTable("One-Way (Beam) Shear Check (Deck Slab)", pfs_cols,
                             note="IRC 112 Cl. 10.3.2. Shear reinforcement not provided in deck slabs; capacity relies on "
                                  "concrete and main reinforcement.")
    deck_shear.rows([
        (r"Design Shear per unit width, $V_{Ed}$", r"$\gamma_{DL} V_{DL} + \gamma_{LL}(1{+}IF)V_{LL}$",
         _dkf(KEY_DD_SHEAR_VED) + " kN/m", "---"),
        (r"Effective depth, $d$", r"$t_s - c_{nom} - \phi/2$", _dkf(KEY_DD_D_BOT, nd=1) + " mm", "---"),
        (r"Size factor, $k$", r"$1 + \sqrt{200/d} \leq 2.0$",
         f"{min(1.0 + (200.0 / _d_bot) ** 0.5, 2.0):.3f}" if (_dk_has and _d_bot > 0) else _DKPH, "---"),
        (r"Long.\ reinforcement ratio, $\rho_l$", r"$A_{sl}/(b_w\,d) \leq 0.02$",
         f"{min(_dkv(KEY_DD_AS_BOT) / (1000.0 * _d_bot), 0.02):.4f}" if (_dk_has and _d_bot > 0) else _DKPH, "---"),
        (r"Shear resistance (no stirrups), $V_{Rd,c}$", r"$v_{Rd,c}\,b_w\,d$ (Cl.\ 10.3.2)", _dkf(KEY_DD_SHEAR_VRDC) + " kN/m", "---"),
        ("One-Way Shear Check", r"$V_{Ed} \leq V_{Rd,c}$", _ratio_str(KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC),
         _dks(bool(deck_rpt.get(KEY_DD_SHEAR_OK)))),
    ])

    deck_det = ReportTable("Reinforcement Detailing Summary (Deck Slab)", [
        Col("Parameter", 2.3), Col("Required / Limit", 1.6, "c"), Col("Provided", 1.7, "c"), Col("Status", 0.8, "c")],
        note="IRC 112 Cl. 16.3, IS 456 Cl. 26.5.")
    deck_det.section(r"Main Reinforcement --- Bottom (Transverse)")
    deck_det.rows([
        (r"Required Area, $A_{st,req}$", _dkf(KEY_DD_AS_REQ_BOT, nd=0) + r" mm$^2$/m", _dkf(KEY_DD_AS_BOT, nd=0) + r" mm$^2$/m",
         _dks(_dkv(KEY_DD_AS_BOT) >= _dkv(KEY_DD_AS_REQ_BOT))),
        (r"Bar Diameter $\times$ Spacing", r"$\phi \geq 10$ mm (IRC 112)",
         r"$\phi$" + _dkf(KEY_DD_DIA_BOT, nd=0) + " @ " + _dkf(KEY_DD_SPC_BOT, nd=0) + " mm c/c", "---"),
        (r"Min.\ Reinforcement $A_{s,min}$ (IRC 112 Cl. 16.3.1)", _dkf(KEY_DD_AS_MIN, nd=0) + r" mm$^2$/m",
         _dkf(KEY_DD_AS_BOT, nd=0) + r" mm$^2$/m", _dks(_dkv(KEY_DD_AS_BOT) >= _dkv(KEY_DD_AS_MIN))),
        (r"Max.\ Bar Spacing (IRC 112 Cl. 16.3.2)", _dkf(KEY_DD_SPACING_MAX, nd=0) + " mm", _dkf(KEY_DD_SPC_BOT, nd=0) + " mm",
         _dks(0.0 < _dkv(KEY_DD_SPC_BOT) <= _dkv(KEY_DD_SPACING_MAX))),
    ])
    deck_det.section(r"Distribution Reinforcement --- Longitudinal")
    deck_det.row(r"Required Area, $A_{st,dist}$", r"$\geq 20\%$ of main steel", _dkf(KEY_DD_AS_LONG, nd=0) + r" mm$^2$/m",
                 _dks(_dkv(KEY_DD_AS_LONG) >= max(0.20 * _dkv(KEY_DD_AS_BOT), _dkv(KEY_DD_AS_MIN))))
    deck_det.section(r"Top Reinforcement (Support / Cantilever Overhang)")
    deck_det.row(r"Required Area, $A_{st,top}$", _dkf(KEY_DD_AS_REQ_TOP, nd=0) + r" mm$^2$/m",
                 _dkf(KEY_DD_AS_TOP, nd=0) + r" mm$^2$/m", _dks(_dkv(KEY_DD_AS_TOP) >= _dkv(KEY_DD_AS_REQ_TOP)))
    deck_det.section(r"Cover and Detailing")
    deck_det.row("Clear Cover (IRC 112 Cl. 15.2)", r"$\geq$ " + _dkf(KEY_DD_MIN_COVER, nd=0) + " mm (Table 14.2)",
                 "Top " + ivr(KEY_DS_TOP_CLEAR_COVER) + " / Bottom " + ivr(KEY_DS_BOTTOM_CLEAR_COVER) + " mm",
                 _dks(bool(deck_rpt.get(KEY_DD_COVER_OK))))

    # ── 5.3 / 5.4 Cross bracing & end diaphragm tables ───────────────────────
    cb_tex = _transverse_member_tables(bridge, "Cross Bracing")
    ed_view = bridge.end_diaphragm()
    ed_type = ""
    for _k, _v in bridge.input_dict.items():
        if str(_k).startswith(KEY_MP_ED_TYPE) and _v:
            ed_type = str(_v)
            break
    ed_is_cb = "brac" in ed_type.strip().lower()
    ed_tex = _transverse_member_tables(ed_view, "End Diaphragm", rolled=not ed_is_cb)

    # ── 5.5 Overall design check summary (table + UR charts) ─────────────────
    summary_tex, chart_groups = _overall_summary(bridge, ed_view, ed_is_cb, deck_rpt, _dkv, _dk_has, _dk_oh,
                                                 _dk_gov_wk, girder_controlling)
    charts_tex = ""
    if img_dir:
        comp = []
        for name, items in chart_groups:
            vals = [u for _, u in items if u is not None]
            comp.append((name, max(vals) if vals else None))
        p1 = safe_chart(ur_component_chart, comp, os.path.join(img_dir, "ur_by_element.png"))
        p2 = safe_chart(ur_detail_chart, chart_groups, os.path.join(img_dir, "ur_by_check.png"))
        charts_tex = (figure_tex(p1, "Governing Utilization Ratio by Primary Element (UR = Demand / Capacity; "
                                     "red dashed line: UR = 1.0 limit)", label="fig:ur-elements")
                      + figure_tex(p2, "Utilization Ratio of Individual Design Checks by Element "
                                       "(bars above the red dashed UR = 1.0 line fail)", label="fig:ur-checks"))

    return r"""
\chapter{Design Checks}

This section presents all structural design checks performed by OsdagBridge. For each member, the demand from the governing load combination, the code-based capacity, and the utilization ratio are tabulated. All checks reference IS 800:2007 and IRC 22:2014 unless stated otherwise.

\section{Plate Girder Design}
\label{sec:plate-girder}
""" + t51.dumps() + t52.dumps() + t53.dumps() + t54.dumps() + t55.dumps() + t56.dumps() + t57.dumps() \
        + t58_tex + t59.dumps() + t510.dumps() + t511.dumps() + t512.dumps() + t513.dumps() \
        + t514.dumps() + t515.dumps() + t516.dumps() + r"""

\section{Deck Slab Design}
\label{sec:deck-design}

The reinforced concrete deck slab is designed per IRC~112:2011 (flexure, shear, crack width) and IRC~22:2014 (composite construction). Wheel loads are distributed using Pigeaud's method. The deck is checked for flexure in the transverse and longitudinal directions, punching shear, one-way (beam) shear, crack width, and reinforcement detailing.
""" + deck_geom + deck_flex.dumps() + deck_oh.dumps() + deck_punch.dumps() + deck_crack + deck_shear.dumps() \
        + deck_det.dumps() + r"""

\section{Cross Bracing Design}
\label{sec:cross-bracing}

Cross bracing between adjacent plate girders provides lateral stability during construction, resists transverse loads (wind, seismic, braking) in service, and prevents lateral torsional buckling of the girders. Members are designed per IS~800:2007 Cl.~7 (compression) and Cl.~6 (tension). Forces are derived from the grillage model under the governing load combination (DL + LL + WL).
""" + cb_tex + r"""

\section{End Diaphragm Design}
\label{sec:end-diaphragm}

End diaphragms at the supports transfer transverse loads to the bearings, restrain the bottom flanges against lateral displacement, and maintain the girder cross-section geometry during construction and in service. They are designed per IS~800:2007 and IRC~24:2010 Cl.~507.
""" + ed_tex + r"""

\section{Overall Design Check Summary}
\label{sec:overall-summary}

The table below collects the governing utilization ratio (UR = Demand / Capacity) of every primary element. The charts that follow visualise the same values: the red dashed line marks the UR = 1.0 limit; bars above it indicate failing checks.
""" + summary_tex + charts_tex


# =============================================================================
# Transverse members (cross bracing / end diaphragm) — shared table builder
# =============================================================================

def _transverse_member_tables(br, title, rolled=False):
    """Section-property, slenderness and capacity tables for one family of
    transverse members. ``br`` is a ReportDataBridge (cross bracing or the
    end-diaphragm view), so each family reports its OWN data."""
    pairs = br.get_cb_pairs()
    has_forces = any(br.get_cb_governing_force(p, m)[0] for p in pairs for m in ("diagonal", "chord"))

    def _mm2(pair, member):
        v = br.section_prop(pair, member, "A")
        return f"{float(v) * 100:.1f}" if v is not None else ""

    def _rmin(pair, member):
        v = br.section_prop(pair, member, "rv")
        return f"{float(v) * 10:.1f}" if v is not None else ""

    def _designation(pair, member):
        """Section designation from the bridge inputs for this member family."""
        idx = pair.split("-")[0].lstrip("G")
        if br.kind == "ed":
            base, mem = "member_properties.end_diaphragm_details", f"E{idx}M1"
        else:
            base, mem = "member_properties.cross_bracing_details", f"B{idx}M1"
        key = {"diagonal": "bracing_section_designation", "top_chord": "top_chord_section_designation",
               "bottom_chord": "bottom_chord_section_designation"}[member]
        return _tex(br.input_dict.get(f"{base}.{key}.{pair.replace('-', '')}.{mem}") or "")

    def _connection(pair):
        idx = pair.split("-")[0].lstrip("G")
        base, mem = (("member_properties.end_diaphragm_details", f"E{idx}M1") if br.kind == "ed"
                     else ("member_properties.cross_bracing_details", f"B{idx}M1"))
        return _tex(br.input_dict.get(f"{base}.bracing_connection.{pair.replace('-', '')}.{mem}") or "")

    props = ReportTable(f"{title} --- Connection and Section Properties", [
        Col("Panel", 0.9, "c"), Col("Member", 1.2), Col("Connection", 1.1), Col("Section", 1.6, "c"),
        Col(r"$A_g$ (mm$^2$)", 1.0, "c"), Col(r"$r_{min}$ (mm)", 1.0, "c")],
        note=r"$A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.")
    slender = ReportTable(f"{title} --- Slenderness Ratio Check (IS 800 Cl. 3.8)", [
        Col("Panel", 0.9, "c"), Col("Member", 1.2), Col("Nature", 0.8, "c"), Col(r"Eff.\ Length $KL$ (mm)", 1.3, "c"),
        Col(r"$KL/r$", 0.9, "c"), Col("Limit", 0.7, "c"), Col("Status", 0.9, "c")],
        note="Limit = 250 for compression members, 400 for tension members. $K = 1.0$ for members with both ends pinned.")
    cap = ReportTable(f"{title} Design --- Capacity Summary", [
        Col("Panel", 0.8, "c"), Col("Member", 0.9), Col("Section", 1.3, "c"), Col("Governing LC", 1.6, "c"),
        Col(r"Demand (kN)", 0.9, "c"), Col(r"Capacity (kN)", 0.9, "c"), Col("UR", 0.6, "c"), Col("Status", 0.8, "c")],
        note="Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension).")

    if not pairs:
        props.row(["---"] * 6)
        slender.row(["---"] * 7)
        cap.row(["---"] * 8)
        return props.dumps() + slender.dumps() + cap.dumps()

    top_on = br.output_dict.get("member_properties.cross_bracing_details.top_chord", True)
    bot_on = br.output_dict.get("member_properties.cross_bracing_details.bottom_chord", True)

    for pair in pairs:
        p = _tex(pair)
        rows = []
        for member, label in (("diagonal", "Diagonal"), ("top_chord", "Top chord"), ("bottom_chord", "Bottom chord")):
            if member == "top_chord" and not top_on or member == "bottom_chord" and not bot_on:
                continue
            ftype = br.get_cb_governing_force(pair, "diagonal" if member == "diagonal" else "chord")[1]
            sec = br.get_cb_section(pair, "diagonal" if member == "diagonal" else "chord", ftype) or _designation(pair, member)
            conn = br.get_cb_connection(pair, "diagonal" if member == "diagonal" else "chord", ftype)                 or _connection(pair)
            rows.append((label, conn, sec, _mm2(pair, member), _rmin(pair, member)))
        props.group(p, rows)

        srows = []
        for member, label, nature, lim in (("diagonal", "Diagonal", "C", 250), ("chord", "Top chord", "C", 250),
                                           ("chord", "Bottom chord", "T", 400)):
            if label == "Top chord" and not top_on or label == "Bottom chord" and not bot_on:
                continue
            kl = br.get_cb_effective_length(member)
            sl = br.get_cb_slenderness(pair, member)
            try:
                st = status(float(sl) <= lim)
            except (TypeError, ValueError):
                st = "---"
            srows.append((label, nature, kl if has_forces or br.kind == "cb" else "", sl, str(lim), st))
        slender.group(p, srows)

        crows = []
        for member, label in (("diagonal", "Diagonal"), ("chord", "Chord")):
            force, ftype = br.get_cb_governing_force(pair, member)
            crows.append((label, br.get_cb_section(pair, member, ftype) or _designation(
                pair, "diagonal" if member == "diagonal" else "top_chord"),
                br.get_cb_gov_lc(pair, member, ftype), force, br.get_cb_capacity(pair, member, ftype),
                ur_value(br.get_cb_efficiency(pair, member, ftype)), br.get_cb_status(pair, member, ftype)))
        cap.group(p, crows)

    out = props.dumps()
    if not has_forces:
        reason = ("Rolled / welded beam end-diaphragm design is not implemented in this version."
                  if rolled else
                  f"Member forces for the {title.lower()} were not returned by the analysis, so the slenderness "
                  "and capacity checks could not be evaluated.")
        out += note(r"\textbf{Note:} " + reason + " Section properties above are reported from the member input.")
        return out
    return out + slender.dumps() + cap.dumps()


# =============================================================================
# 5.5 Overall design check summary
# =============================================================================

_CHART_LABELS = {   # short tick labels for the UR charts (table keeps full names)
    "LTB (constr.)": "LTB", "Flexure (sagging)": "Sagging", "Flexure (hogging)": "Hogging",
    "Cantilever overhang": "Overhang", "Punching shear": "Punching", "One-way shear": "1-way shear",
    "Crack width": "Crack", "Transverse shear": "Transv. shear",
}


def _overall_summary(bridge, ed_view, ed_is_cb, deck_rpt, _dkv, _dk_has, _dk_oh, _dk_gov_wk, girder_controlling):
    """Build the overall summary table and return (tex, chart_groups).

    chart_groups : [(element, [(check, ur_float_or_None), ...]), ...] — the same
    numbers as the table, used for the UR bar charts.
    """
    od = bridge.output_dict
    pg = (od.get("design_results", {}) or {}).get("per_girder", {}) or {}

    def _dfmt(v, nd=2):
        try:
            return f"{float(v):.{nd}f}"
        except (TypeError, ValueError):
            return ""

    def _vu(v, unit):
        s = _dfmt(v)
        if not s:
            return ""
        u = (unit or "").strip()
        return (s + " " + u) if u else s

    def _lc(lc):
        return _tex(str(lc).strip())

    def _gov_lc(g, ids):
        best = None
        for name, ld in ((pg.get(g) or {}).get("per_lc") or {}).items():
            if str(name).lower().startswith("envelope"):
                continue
            for chk in (ld.get("checks") or []):
                if chk.get("id") in ids:
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (d, name)
        return _lc(best[1]) if best else "---"

    def _dcr(ids, fallback_unit=""):
        """(gov_lc, demand, capacity, ur_float) — worst girder by DCR."""
        best = None
        for g, gd in pg.items():
            if str(g).startswith("EB"):
                continue
            for chk in (gd.get("checks") or []):
                if chk.get("check_id") in ids:
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (d, chk.get("demand"), chk.get("capacity"),
                                chk.get("demand_unit") or "", chk.get("capacity_unit") or "", g)
        if best is not None:
            d, dem, cap, du, cu, g = best
            return (_gov_lc(g, ids), _vu(dem, du), _vu(cap, cu), d)
        best = None   # SLS-conditional checks appear only per load case (no units)
        for g, gd in pg.items():
            if str(g).startswith("EB"):
                continue
            for name, ld in (gd.get("per_lc") or {}).items():
                if str(name).lower().startswith("envelope"):
                    continue
                for chk in (ld.get("checks") or []):
                    if chk.get("id") in ids:
                        d = chk.get("dcr") or 0.0
                        if best is None or d > best[0]:
                            best = (d, chk.get("demand"), chk.get("capacity"), name)
        if best is None:
            return ("", "", "", None)
        d, dem, cap, name = best
        return (_lc(name), _vu(dem, fallback_unit), _vu(cap, fallback_unit), d)

    def _member(br, force_type):
        best = None
        for pair in br.get_cb_pairs():
            for member in ("diagonal", "chord"):
                cap = br.get_cb_capacity(pair, member, force_type)
                try:
                    ur = float(br.get_cb_efficiency(pair, member, force_type))
                except (TypeError, ValueError):
                    continue
                if best is None or ur > best[0]:
                    best = (ur, pair, member, cap)
        if best is None:
            return ("", "", "", None)
        ur, pair, member, cap = best
        return (br.get_cb_gov_lc(pair, member, force_type),
                f"{float(cap) * ur:.2f} kN" if cap else "", (cap + " kN") if cap else "", ur)

    def _slender(br):
        best = None
        for pair in br.get_cb_pairs():
            for member in ("diagonal", "chord"):
                try:
                    sf = float(br.get_cb_slenderness(pair, member))
                except (TypeError, ValueError):
                    continue
                lim = 400.0 if member == "chord" else 250.0
                if best is None or sf / lim > best[0]:
                    best = (sf / lim, sf, lim)
        if best is None:
            return ("", "", "", None)
        r, sf, lim = best
        return ("---", f"{sf:.1f}", f"{lim:.0f}", r)

    deck_combo = (r"Basic ULS: " + _tex(f"{_dkv(KEY_DD_GAMMA_DL):g}DL + {_dkv(KEY_DD_GAMMA_LL):g}LL")) if _dk_has else ""

    def _deck(dem_key, cap_key, unit, is_oh=False):
        if not _dk_has:
            return ("", "", "", None)
        if is_oh and not _dk_oh:
            return (deck_combo, "N/A", "N/A", None)
        dem, cap = _dkv(dem_key), _dkv(cap_key)
        return (deck_combo, f"{dem:.2f} {unit}", f"{cap:.2f} {unit}", (dem / cap) if cap > 0 else None)

    def _gov_frequent():
        best = None
        for g, gd in pg.items():
            if str(g).startswith("EB"):
                continue
            for name, ld in (gd.get("per_lc") or {}).items():
                if "frequent" in str(name).lower():
                    d = ld.get("max_dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (d, name)
        return _tex(str(best[1]).strip()) if best else "Frequent SLS"

    wk_lim = _dkv(KEY_DD_WK_LIMIT)
    crack = ((_gov_frequent(), f"{_dk_gov_wk:.3f} mm", f"{wk_lim:.3f} mm",
              _dk_gov_wk / wk_lim if wk_lim > 0 else None) if _dk_has else ("", "", "", None))

    # Transverse shear (IRC 22 Cl. 606.10): use the DCR engine entry when it
    # exists, otherwise the same V_L / V_Rd values reported in its own table.
    trans = _dcr({16})
    if trans[3] is None:
        _dr = od.get("design_results", {}) or {}
        try:
            vl, vrd = float(_dr.get(KEY_SD_TS_VL)), float(_dr.get(KEY_SD_TS_VRD))
            if vrd > 0:
                trans = ("ULS design value", f"{vl:.2f} kN/m", f"{vrd:.2f} kN/m", vl / vrd)
        except (TypeError, ValueError):
            pass

    girder = [("Moment", _dcr({1})), ("Shear", _dcr({2})), ("LTB (constr.)", _dcr({5})),
              ("Deflection", _dcr({13, 14}, "mm")), ("Stress", _dcr({11}, "MPa")), ("Fatigue", _dcr({8, 9}, "MPa"))]
    deck = [("Flexure (sagging)", _deck(KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT, "kN-m/m")),
            ("Flexure (hogging)", _deck(KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP, "kN-m/m")),
            ("Cantilever overhang", _deck(KEY_DD_M_ULS_OH, KEY_DD_MU_OH, "kN-m/m", is_oh=True)),
            ("Punching shear", _deck(KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA, "MPa")),
            ("One-way shear", _deck(KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, "kN/m")),
            ("Crack width", crack),
            ("Transverse shear", trans)]
    cb = [("Compression", _member(bridge, "compression")), ("Tension", _member(bridge, "tension")),
          ("Slenderness", _slender(bridge))]
    ed = ([("Compression", _member(ed_view, "compression")), ("Tension", _member(ed_view, "tension")),
           ("Slenderness", _slender(ed_view))] if ed_is_cb else [])

    t = ReportTable("Overall Design Check Summary --- All Members", [
        Col("Member / Check", 1.7), Col("Governing Load Combination", 2.4, "l"), Col("Demand", 1.2, "c"),
        Col("Capacity", 1.2, "c"), Col("UR", 0.6, "c"), Col("Status", 0.8, "c")],
        note="UR = Demand / Capacity. All values $\\leq 1.0$ indicate passing checks. The governing check for "
             "each component is highlighted in the individual design check sections above.")

    groups = []
    for element, rows in (("Steel Plate Girders", girder), ("Concrete Deck Slab", deck),
                          ("Cross Bracing", cb), ("End Diaphragms", ed)):
        t.section(element)
        chart_items = []
        if not rows:
            msg = ("Member forces not available from the analysis --- checks not evaluated"
                   if ed_is_cb else "Rolled / welded section --- design to be added")
            t.row("All checks", multicol(r"\textit{" + msg + "}", 5, "c"))
            chart_items.append(("Not evaluated", None))
        for check, (lc, dem, cap, ur) in rows:
            st = status(ur <= 1.0) if ur is not None else "---"
            t.row(check, lc, dem, cap, ur_value(ur), st)
            chart_items.append((_CHART_LABELS.get(check, check), ur))
        if all(u is None for _, u in chart_items) and element == "End Diaphragms":
            chart_items = [("Not evaluated", None)]
        groups.append((element, chart_items))
    return t.dumps(), groups
