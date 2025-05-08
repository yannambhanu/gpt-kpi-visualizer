# app.py

import streamlit as st
import pandas as pd
import altair as alt
import openai
import json

# HARD-CODED OPENAI API KEY
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Balanced Card", layout="wide")
st.title("📊 Balanced Card")
st.caption("Give your data → Our LLM picks KPIs → Visualizations is auto-generated")

st.markdown("---")

# -------------------------------
# Input Section (Sidebar)
# -------------------------------
with st.sidebar:
    st.header("📥 JSON Input")
    json_input = st.text_area("Paste your JSON data here", height=300)
    run_analysis = st.button("🔍 Analyze")

# -------------------------------
# Main App Logic
# -------------------------------
if run_analysis:
    if not json_input.strip():
        st.error("Please paste some JSON data.")
        st.stop()

    try:
        # -------------------------------
        # Load JSON and Convert to DataFrame
        # -------------------------------
        data = json.loads(json_input)
        df = pd.DataFrame(data)

        if df.empty:
            st.warning("JSON is valid but has no rows.")
            st.stop()

        st.success("✅ JSON parsed successfully")

        st.markdown("### 🔢 Raw Data Preview")
        st.dataframe(df, use_container_width=True)

        sample = df.head(10).to_markdown(index=False)

        # -------------------------------
        # GPT-4: Ask for KPIs and chart
        # -------------------------------
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        prompt = f"""
You are a senior data analyst. Below is a sample of a dataset:

{sample}

1. Identify 2–3 key KPIs or numeric metrics.
2. Suggest the best chart to visualize them.
3. Output strictly in this format:

SUMMARY:
<brief summary>

CHART_INSTRUCTIONS:
- type: <bar|line|scatter>
- x: <column_name>
- y: <column_name>
"""

        st.info("🧠 Asking LLM to analyze and recommend chart...")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        gpt_output = response.choices[0].message.content
        st.code(gpt_output, language='markdown')

        # -------------------------------
        # Parse GPT Output
        # -------------------------------
        summary = ""
        chart_type = ""
        x_field = ""
        y_field = ""

        for line in gpt_output.splitlines():
            if line.startswith("SUMMARY:"):
                summary = line.replace("SUMMARY:", "").strip()
            elif line.startswith("- type:"):
                chart_type = line.replace("- type:", "").strip()
            elif line.startswith("- x:"):
                x_field = line.replace("- x:", "").strip()
            elif line.startswith("- y:"):
                y_field = line.replace("- y:", "").strip()

        if not all([chart_type, x_field, y_field]):
            st.error("❌ LLM output could not be parsed. Please verify format.")
            st.stop()

        # -------------------------------
        # Show Summary + Chart
        # -------------------------------
        col1, col2 = st.columns([2, 3])

        with col1:
            st.markdown("### 🧠 Balanced Card LLM KPI Summary")
            st.success(summary)

        with col2:
            st.markdown("### 📊 Visualizations")
            if chart_type == "bar":
                chart = alt.Chart(df).mark_bar().encode(x=x_field, y=y_field, tooltip=list(df.columns))
            elif chart_type == "line":
                chart = alt.Chart(df).mark_line(point=True).encode(x=x_field, y=y_field, tooltip=list(df.columns))
            elif chart_type == "scatter":
                chart = alt.Chart(df).mark_circle(size=60).encode(x=x_field, y=y_field, tooltip=list(df.columns))
            else:
                st.warning(f"Unknown chart type: {chart_type}")
                st.stop()

            st.altair_chart(chart.interactive(), use_container_width=True)

    except json.JSONDecodeError:
        st.error("❌ Invalid JSON format.")
    except Exception as e:
        st.error(f"🚨 Error: {e}")
