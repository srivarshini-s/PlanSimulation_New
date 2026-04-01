import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import random
from datetime import date
from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# =====================================
# App Config
# =====================================
st.set_page_config(page_title="Plan Simulation", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "input"

# =====================================
# INPUT PAGE (UNCHANGED)
# =====================================
def input_page():
    st.title("Plan Simulation")

    st.header("Simulation Details")

    carrier = st.selectbox(
        "Carrier",
        ["Sun Life", "Manulife", "Canada Life", "Green Shield Canada", "Desjardins"]
    )

    group = st.selectbox(
        "Group",
        [
            "ABC Manufacturing",
            "XYZ Retail",
            "Global Tech Services",
            "Healthcare Partners",
            "Education Services Union"
        ]
    )

    subgroup = st.selectbox(
        "Subgroup",
        [
            "Ontario Staff",
            "Quebec Staff",
            "Management",
            "Unionized Employees",
            "Non‑Union Employees"
        ]
    )

    province = st.selectbox(
        "Province",
        ["Ontario", "Quebec", "British Columbia", "Alberta"]
    )

    st.subheader("Time Frame")
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("From", date(2024, 1, 1))
    with c2:
        end_date = st.date_input("To", date(2024, 12, 31))

    st.header("Plan & Formulary")
    program = st.radio(
        "Formulary Type",
        ["Baseline Plan", "Managed Formulary (DTF)"]
    )

    plan_config = {}
    if program == "Managed Formulary (DTF)":
        selected_plan = st.radio("Choose Plan", ["Plan A", "Plan B"], horizontal=True)
        brand_to_generic = st.checkbox("Branded → Generic")
        bio_to_biosimilar = st.checkbox("Biologic → Biosimilar")

        c1, c2, c3 = st.columns(3)
        with c1:
            coinsurance_adj = st.number_input("Coinsurance Adjustment (%)", -50, 50, 0, 5)
        with c2:
            deductible_adj = st.number_input("Deductible Adjustment ($)", -1000, 1000, 0, 50)
        with c3:
            copay_adj = st.number_input("Copay Adjustment ($)", -50, 50, 0, 5)

        plan_config = {
            "selected_plan": selected_plan,
            "brand_to_generic": brand_to_generic,
            "biosimilar": bio_to_biosimilar,
            "coinsurance_adj_pct": coinsurance_adj,
            "deductible_adj": deductible_adj,
            "copay_adj": copay_adj
        }

    st.header("Claims Inclusion Rules")
    st.toggle("Apply Step Therapy")
    st.toggle("Require Prior Authorization")

    st.header("Drug Price Inflation")
    i1, i2, i3 = st.columns(3)
    i1.number_input("Generic (%)", 0.0, 50.0, 2.0)
    i2.number_input("Branded (%)", 0.0, 50.0, 4.0)
    i3.number_input("Specialty (%)", 0.0, 50.0, 6.0)

    if st.button("Run Simulation"):
        drug_spend = {
            "Humira": random.randint(140000, 180000),
            "Stelara": random.randint(120000, 160000),
            "Skyrizi": random.randint(110000, 150000),
            "Enbrel": random.randint(90000, 130000),
            "Cosentyx": random.randint(80000, 120000),
            "Dupixent": random.randint(70000, 110000),
            "Eliquis": random.randint(60000, 90000),
            "Ozempic": random.randint(55000, 85000),
            "Xarelto": random.randint(50000, 80000),
            "Trulicity": random.randint(45000, 75000),
        }

        df = (
            pd.DataFrame(drug_spend.items(), columns=["Drug", "Annual Spend"])
            .sort_values("Annual Spend", ascending=False)
            .reset_index(drop=True)
        )

        simulated_spend = int(df["Annual Spend"].sum())
        baseline_spend = int(simulated_spend * random.uniform(1.05, 1.15))
        savings = baseline_spend - simulated_spend
        members = random.randint(200, 500)

        st.session_state.results = {
            "df": df,
            "metrics": {
                "current_plan_spend": baseline_spend,
                "simulated_plan_spend": simulated_spend,
                "savings": savings,
                "pmpm": round(simulated_spend / 12 / members, 2),
                "avg_oop": random.randint(300, 600),
                "pct_impacted": random.randint(20, 45),
                "members": members
            },
            "plan_config": plan_config
        }

        st.session_state.page = "results"
        st.rerun()

# =====================================
# PDF GENERATOR
# =====================================
def generate_pdf(df, m, summary):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=LETTER)
    y = LETTER[1] - inch

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(inch, y, "Plan Simulation Results")
    y -= 0.4 * inch

    pdf.setFont("Helvetica", 10)
    pdf.drawString(inch, y, f"Current Plan Spend: ${m['current_plan_spend']:,}")
    y -= 14
    pdf.drawString(inch, y, f"Simulated Plan Spend: ${m['simulated_plan_spend']:,}")
    y -= 14
    pdf.drawString(inch, y, f"Savings: ${m['savings']:,}")
    y -= 14
    pdf.drawString(inch, y, f"PMPM: ${m['pmpm']}")
    y -= 14
    pdf.drawString(inch, y, f"Average OOP: ${m['avg_oop']}")
    y -= 14
    pdf.drawString(inch, y, f"% Members Impacted: {m['pct_impacted']}%")

    y -= 0.3 * inch
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(inch, y, "Top Drugs Driving Spend")

    y -= 0.2 * inch
    pdf.setFont("Helvetica", 9)
    for _, row in df.iterrows():
        pdf.drawString(inch, y, f"{row['Drug']} – ${row['Annual Spend']:,}")
        y -= 12

    y -= 0.3 * inch
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(inch, y, "Summary")

    y -= 0.2 * inch
    pdf.setFont("Helvetica", 9)
    for line in summary.split("\n"):
        pdf.drawString(inch, y, line)
        y -= 12

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer

# =====================================
# RESULTS PAGE (UPDATED)
# =====================================
def results_page():
    st.title("Simulation Results")

    df = st.session_state.results["df"]
    m = st.session_state.results["metrics"]

    st.header("Top 10 Drugs Driving Spend")
    st.dataframe(df, use_container_width=True)

    st.header("Key Performance Indicators")
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Current Plan Spend", f"${m['current_plan_spend']:,}")
    k2.metric("Simulated Plan Spend", f"${m['simulated_plan_spend']:,}")
    k3.metric("Savings", f"${m['savings']:,}", delta=f"-${m['savings']:,}")
    k4.metric("PMPM", f"${m['pmpm']}")
    k5.metric("Avg OOP", f"${m['avg_oop']}")
    k6.metric("% Members Impacted", f"{m['pct_impacted']}%")

    # =========================
    # KPI PIE / DONUT CHARTS
    # =========================
    st.header("KPI Visual Insights")
    c1, c2, c3 = st.columns(3)

    with c1:
        fig, ax = plt.subplots(figsize=(3, 3))
        ax.pie(df["Annual Spend"], autopct="%1.0f%%", startangle=90)
        ax.set_title("Drug Spend Mix")
        st.pyplot(fig)

    with c2:
        fig, ax = plt.subplots(figsize=(3, 3))
        ax.pie(
            [m["pct_impacted"], 100 - m["pct_impacted"]],
            labels=["Impacted", "Not Impacted"],
            wedgeprops=dict(width=0.4),
            autopct="%1.0f%%",
            startangle=90
        )
        ax.set_title("Member Impact")
        st.pyplot(fig)

    with c3:
        fig, ax = plt.subplots(figsize=(3, 3))
        ax.pie(
            [m["savings"], m["current_plan_spend"] - m["savings"]],
            labels=["Savings", "Remaining Spend"],
            wedgeprops=dict(width=0.4),
            autopct="%1.0f%%",
            startangle=90
        )
        ax.set_title("Savings Impact")
        st.pyplot(fig)

    # =========================
    # AI GENERATED SUMMARY
    # =========================
    st.header("AI‑Generated Summary")

    summary = f"""
The current plan spend is estimated at ${m['current_plan_spend']:,}.
Under the simulated managed formulary scenario, plan spend decreases
to approximately ${m['simulated_plan_spend']:,}, generating savings of
${m['savings']:,} annually.

Approximately {m['pct_impacted']}% of members are affected, with an
average out‑of‑pocket cost of ${m['avg_oop']} per impacted member.
"""
    st.write(summary)

    # =========================
    # DOWNLOAD PDF
    # =========================
    pdf = generate_pdf(df, m, summary)
    st.download_button(
        "⬇ Download Full Results as PDF",
        pdf,
        file_name="Plan_Simulation_Results.pdf",
        mime="application/pdf"
    )

    if st.button("← Back to Inputs"):
        st.session_state.page = "input"
        st.rerun()

# =====================================
# ROUTER
# =====================================
if st.session_state.page == "input":
    input_page()
else:
    results_page()
