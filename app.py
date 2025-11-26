import streamlit as st
import pandas as pd
import altair as alt

# -----------------------------
# Helpers de formato
# -----------------------------
def fmt_eur(x: float) -> str:
    """Formatea número en estilo europeo: 8.800 €"""
    return f"{x:,.0f} €".replace(",", ".")

def fmt_eur_signed(x: float) -> str:
    sign = "-" if x < 0 else ""
    return f"{sign}{fmt_eur(abs(x))}"

def fmt_pct(x: float) -> str:
    """35,7 %"""
    return f"{x*100:,.1f} %".replace(".", ",")


# -----------------------------
# Cálculo de P&L
# -----------------------------
def compute_pnl(params: dict):
    # Días abiertos al mes
    open_days = params["days_open_per_week"] * params["weeks_per_month"]

    # --- INGRESOS ---
    rev_menu = params["menus_per_day"] * params["menu_price"] * open_days
    rev_cafe = params["cafe_tickets_per_day"] * params["cafe_ticket"] * open_days
    rev_shop = params["shop_tickets_per_day"] * params["shop_ticket"] * open_days
    total_revenue = rev_menu + rev_cafe + rev_shop

    # --- FOOD & BEV COST ---
    food_menu = params["menus_per_day"] * params["menu_food_cost_unit"] * open_days
    food_cafe = rev_cafe * params["cafe_food_cost_pct"]
    food_shop = rev_shop * params["shop_food_cost_pct"]
    total_food_cost = food_menu + food_cafe + food_shop

    # --- LABOR COST ---
    gross_salaries = params["cook_gross_salary"] + params["partner_gross_salary"]
    labor_ss = gross_salaries * (params["ss_factor"] - 1.0)
    labor_total = gross_salaries + labor_ss + params["partner_cash_extra"] + params["other_labor_cost"]

    # --- COSTES FIJOS ---
    fixed_cost_total = (
        params["rent"]
        + params["utilities"]
        + params["insurance"]
        + params["accounting"]
        + params["tpv_reservations"]
        + params["fixed_overheads"]
    )

    # --- RESULTADOS ---
    gross_profit = total_revenue - total_food_cost  # antes de labor + fijos
    gross_margin_pct = gross_profit / total_revenue if total_revenue > 0 else 0.0
    ebitda = gross_profit - labor_total - fixed_cost_total

    break_even_sales = (labor_total + fixed_cost_total) / gross_margin_pct if gross_margin_pct > 0 else None
    safety_ratio = total_revenue / break_even_sales if break_even_sales and break_even_sales > 0 else None

    results = {
        "open_days": open_days,
        "rev_menu": rev_menu,
        "rev_cafe": rev_cafe,
        "rev_shop": rev_shop,
        "total_revenue": total_revenue,
        "food_menu": food_menu,
        "food_cafe": food_cafe,
        "food_shop": food_shop,
        "total_food_cost": total_food_cost,
        "labor_total": labor_total,
        "fixed_cost_total": fixed_cost_total,
        "gross_profit": gross_profit,
        "gross_margin_pct": gross_margin_pct,
        "ebitda": ebitda,
        "break_even_sales": break_even_sales,
        "safety_ratio": safety_ratio,
    }
    return results


# -----------------------------
# Config Streamlit
# -----------------------------
st.set_page_config(
    page_title="Los Falcone - Simulador P&L",
    layout="wide"
)

# Un poco de estilo global (fondo suave + card oscura arriba)
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
        margin: auto;
    }
    .lf-header {
        background-color: #000000;
        color: #ffffff;
        padding: 1.8rem 2rem;
        border-radius: 0.75rem;
        margin-bottom: 1.8rem;
        border: 1px solid #333333;
    }
    .lf-title {
        font-size: 2.4rem;
        letter-spacing: 0.35rem;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }
    .lf-subtitle {
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.25rem;
        opacity: 0.9;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Cabecera tipo branding
st.markdown(
    """
    <div class="lf-header">
        <div class="lf-title">LOS FALCONE</div>
        <div class="lf-subtitle">PASTA E BOTTEGA · BARCELONA</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption("Simulador económico para jugar con volumen, precios y estructura de costes de Los Falcone.")

# =============================
# 1) CONFIGURACIÓN (TABS)
# =============================
tab_operacion, tab_ajustes = st.tabs(["📆 Operación diaria", "🔧 Ajustes finos"])

with tab_operacion:
    st.subheader("Supuestos básicos de operación")

    col_days, col_weeks = st.columns(2)
    with col_days:
        days_open_per_week = st.slider("Días abiertos por semana", 1, 7, 5)
    with col_weeks:
        weeks_per_month = st.slider("Semanas promedio por mes", 3.5, 5.0, 4.3, step=0.1)

    st.markdown("### Volumen diario medio")
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        menus_per_day = st.number_input("Menús por día", 0, 200, 18, step=1)
    with col_v2:
        cafe_tickets_per_day = st.number_input("Tickets café/bollería por día", 0, 200, 20, step=1)
    with col_v3:
        shop_tickets_per_day = st.number_input("Tickets tienda por día", 0, 200, 5, step=1)

    st.markdown("### Precios medios")
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        menu_price = st.number_input("Precio menú (€)", 5.0, 50.0, 13.0, step=0.5)
    with col_p2:
        cafe_ticket = st.number_input("Ticket medio café/bollería (€)", 1.0, 20.0, 5.0, step=0.5)
    with col_p3:
        shop_ticket = st.number_input("Ticket medio tienda (€)", 5.0, 100.0, 15.0, step=1.0)

    st.markdown("### Food cost por línea")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        menu_food_cost_unit = st.number_input("Coste unitario menú (€/menú)", 0.0, 10.0, 3.0, step=0.1)
    with col_f2:
        cafe_food_cost_pct = st.slider("Food cost café/bollería (% ventas)", 0, 100, 30) / 100.0
    with col_f3:
        shop_food_cost_pct = st.slider("Food cost tienda (% ventas)", 0, 100, 35) / 100.0

with tab_ajustes:
    st.subheader("Coste laboral")
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        cook_gross_salary = st.number_input("Sueldo bruto cocinero (€ / mes)", 0.0, 4000.0, 1300.0, step=50.0)
        partner_gross_salary = st.number_input("Sueldo bruto socia (€ / mes)", 0.0, 4000.0, 1300.0, step=50.0)
        ss_factor = st.slider("Multiplicador coste empresa (bruto → coste)", 1.0, 2.0, 1.32, step=0.01)
    with col_l2:
        partner_cash_extra = st.number_input("Extra en efectivo socia (€ / mes)", 0.0, 3000.0, 400.0, step=50.0)
        other_labor_cost = st.number_input("Otros laborales (limpieza, sustituciones, etc.) (€ / mes)", 0.0, 3000.0, 100.0, step=50.0)

    st.subheader("Costes fijos")
    col_fi1, col_fi2, col_fi3 = st.columns(3)
    with col_fi1:
        rent = st.number_input("Alquiler (€ / mes)", 0.0, 5000.0, 920.0, step=50.0)
        utilities = st.number_input("Suministros (luz+gas+agua+internet) (€ / mes)", 0.0, 2000.0, 450.0, step=50.0)
    with col_fi2:
        insurance = st.number_input("Seguro local (€ / mes)", 0.0, 500.0, 60.0, step=10.0)
        accounting = st.number_input("Gestoría / contabilidad (€ / mes)", 0.0, 1000.0, 120.0, step=10.0)
    with col_fi3:
        tpv_reservations = st.number_input("TPV + sistema reservas / SaaS (€ / mes)", 0.0, 1000.0, 80.0, step=10.0)
        fixed_overheads = st.number_input(
            "Otros fijos (tasas, plagas, APPCC, marketing, menaje, imprevistos) (€ / mes)",
            0.0, 5000.0, 700.0, step=50.0
        )

# Empaquetar parámetros
params = {
    "days_open_per_week": days_open_per_week,
    "weeks_per_month": weeks_per_month,
    "menus_per_day": menus_per_day,
    "cafe_tickets_per_day": cafe_tickets_per_day,
    "shop_tickets_per_day": shop_tickets_per_day,
    "menu_price": menu_price,
    "cafe_ticket": cafe_ticket,
    "shop_ticket": shop_ticket,
    "menu_food_cost_unit": menu_food_cost_unit,
    "cafe_food_cost_pct": cafe_food_cost_pct,
    "shop_food_cost_pct": shop_food_cost_pct,
    "cook_gross_salary": cook_gross_salary,
    "partner_gross_salary": partner_gross_salary,
    "ss_factor": ss_factor,
    "partner_cash_extra": partner_cash_extra,
    "other_labor_cost": other_labor_cost,
    "rent": rent,
    "utilities": utilities,
    "insurance": insurance,
    "accounting": accounting,
    "tpv_reservations": tpv_reservations,
    "fixed_overheads": fixed_overheads,
}

results = compute_pnl(params)

# =============================
# 2) RESUMEN DE MÉTRICAS
# =============================
st.markdown("## Foto mensual del negocio")

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("Ingresos mensuales", fmt_eur(results["total_revenue"]))
with col_m2:
    st.metric("EBITDA mensual", fmt_eur_signed(results["ebitda"]))
with col_m3:
    st.metric("Margen bruto sobre ventas", fmt_pct(results["gross_margin_pct"]))
with col_m4:
    if results["break_even_sales"]:
        st.metric("Ventas necesarias (break-even)", fmt_eur(results["break_even_sales"]))
    else:
        st.metric("Ventas necesarias (break-even)", "N/A")

st.caption(f"Días abiertos al mes (estimados): **{results['open_days']:.1f}**")

st.markdown("---")

# =============================
# 3) TABS DE RESULTADOS
# =============================
tab_pnl, tab_costs, tab_sens = st.tabs(["📊 P&L detallado", "📉 Costes + resultado", "🧪 Sensibilidad"])

with tab_pnl:
    st.subheader("P&L mensual")

    pnl_data = {
        "Concepto": [
            "Ingresos - Menú",
            "Ingresos - Café/Bollería",
            "Ingresos - Tienda",
            "TOTAL INGRESOS",
            "Coste comida - Menú",
            "Coste comida - Café/Bollería",
            "Coste comida - Tienda",
            "TOTAL FOOD COST",
            "MARGEN BRUTO (Ingresos - Food)",
            "Coste laboral total",
            "Costes fijos",
            "EBITDA"
        ],
        "€ / mes": [
            results["rev_menu"],
            results["rev_cafe"],
            results["rev_shop"],
            results["total_revenue"],
            -results["food_menu"],
            -results["food_cafe"],
            -results["food_shop"],
            -results["total_food_cost"],
            results["gross_profit"],
            -results["labor_total"],
            -results["fixed_cost_total"],
            results["ebitda"]
        ]
    }
    pnl_df = pd.DataFrame(pnl_data)

    # Versión para mostrar (string + estilo)
    display_df = pnl_df.copy()
    display_df["€ / mes"] = display_df["€ / mes"].apply(fmt_eur_signed)

    def highlight_totals(row):
        concepts_total = [
            "TOTAL INGRESOS",
            "TOTAL FOOD COST",
            "MARGEN BRUTO (Ingresos - Food)",
            "EBITDA"
        ]
        if row["Concepto"] in concepts_total:
            return ['background-color: #f2f2f2; font-weight: 600;'] * len(row)
        return [''] * len(row)

    styled = display_df.style.apply(highlight_totals, axis=1)
    st.dataframe(styled, use_container_width=True)

with tab_costs:
    st.subheader("Distribución de costes")
    costs_df = pd.DataFrame({
        "Tipo": ["Food cost", "Labor", "Costes fijos"],
        "€ / mes": [
            results["total_food_cost"],
            results["labor_total"],
            results["fixed_cost_total"]
        ]
    })

    cost_chart = alt.Chart(costs_df).mark_bar().encode(
        x=alt.X("Tipo", sort=None),
        y="€ / mes",
        color=alt.Color("Tipo", scale=alt.Scale(
            range=["#c0c0c0", "#888888", "#444444"]
        ))
    )
    st.altair_chart(cost_chart, use_container_width=True)

    st.markdown("### Resultado (EBITDA)")
    ebitda_df = pd.DataFrame({"Resultado": ["EBITDA"], "Valor": [results["ebitda"]]})
    color = "#4caf50" if results["ebitda"] >= 0 else "#f44336"

    ebitda_chart = alt.Chart(ebitda_df).mark_bar(color=color).encode(
        x="Resultado",
        y="Valor"
    )
    st.altair_chart(ebitda_chart, use_container_width=True)

with tab_sens:
    st.subheader("Sensibilidad simple (menús y tickets tienda)")
    st.caption("Cómo cambia el resultado al variar menús/día y tickets tienda/día en ±2.")

    sens_rows = []
    for delta_menus in [-2, 0, 2]:
        for delta_shop in [-2, 0, 2]:
            local_params = params.copy()
            local_params["menus_per_day"] = max(0, params["menus_per_day"] + delta_menus)
            local_params["shop_tickets_per_day"] = max(0, params["shop_tickets_per_day"] + delta_shop)
            r = compute_pnl(local_params)
            sens_rows.append({
                "Δ menús/día": delta_menus,
                "Δ tienda/día": delta_shop,
                "Ingresos (€ / mes)": fmt_eur(r["total_revenue"]),
                "EBITDA (€ / mes)": fmt_eur_signed(r["ebitda"])
            })

    sens_df = pd.DataFrame(sens_rows)
    st.dataframe(sens_df, use_container_width=True)
