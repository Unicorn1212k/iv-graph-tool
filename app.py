import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import zipfile
import base64
import os

st.set_page_config(page_title="Smart I-V & J-V Grapher", layout="wide")
st.title("📈 Smart I-V & J-V Graph Analyzer (with Area Support)")
st.markdown("Upload `.txt` or `.csv` files for a single diode area. The app auto-detects Voltage and Current columns, plots both I-V and J-V graphs, and provides insights.")

area_input = st.number_input("📏 Enter Diode Area (in µm²)", min_value=0.0001, format="%.4f")

uploaded_files = st.file_uploader("Upload your files", type=['csv', 'txt'], accept_multiple_files=True)

def generate_insights(df, v_col, i_col, area_cm2):
    insights = []
    df['Current_Density'] = df[i_col] / area_cm2

    max_current = df[i_col].max()
    max_density = df['Current_Density'].max()

    if max_current < 0:
        insights.append("This diode operates under reverse bias conditions.")
    if max_current > 1e-6:
        insights.append("The diode shows a strong forward bias conduction.")
    if max_density > 0.01:
        insights.append("High current density suggests a small area or good conductivity.")
    if df[i_col].min() < -1e-6:
        insights.append("Possible leakage or reverse saturation detected.")

    return insights

if uploaded_files and area_input > 0:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for uploaded_file in uploaded_files:
            try:
                content = uploaded_file.read().decode('utf-8', errors='ignore')
                lines = content.splitlines()

                delimiter = '\t' if '\t' in lines[0] else ',' if ',' in lines[0] else None
                if delimiter:
                    df = pd.read_csv(io.StringIO(content), delimiter=delimiter)
                else:
                    df = pd.DataFrame([line.split() for line in lines if line.strip()])
                    df.columns = df.iloc[0]
                    df = df[1:]

                df = df.apply(pd.to_numeric, errors='coerce')
                df.dropna(how='all', inplace=True)

                v_candidates = [col for col in df.columns if str(col).lower().startswith('v')]
                i_candidates = [col for col in df.columns if str(col).lower().startswith('i')]

                v_col = v_candidates[0] if v_candidates else df.columns[0]
                i_col = i_candidates[0] if i_candidates else df.columns[1]

                df = df[[v_col, i_col]].dropna()
                area_cm2 = area_input * 1e-8  # convert µm² to cm²
                df['Current_Density'] = df[i_col] / area_cm2

                # I-V Plot
                fig_iv, ax_iv = plt.subplots()
                ax_iv.plot(df[v_col], df[i_col]*1e6)
                ax_iv.set_title(f"I-V Graph: {uploaded_file.name}")
                ax_iv.set_xlabel("Voltage (V)")
                ax_iv.set_ylabel("Current (µA)")
                ax_iv.grid(True)
                st.pyplot(fig_iv)

                # J-V Plot
                fig_jv, ax_jv = plt.subplots()
                ax_jv.plot(df[v_col], df['Current_Density']*1e6)
                ax_jv.set_title(f"J-V Graph: {uploaded_file.name}")
                ax_jv.set_xlabel("Voltage (V)")
                ax_jv.set_ylabel("Current Density (µA/cm²)")
                ax_jv.grid(True)
                st.pyplot(fig_jv)

                insights = generate_insights(df, v_col, i_col, area_cm2)
                st.markdown("### 🔍 Observations")
                if insights:
                    for obs in insights:
                        st.markdown(f"- {obs}")
                else:
                    st.markdown("- No significant insights detected.")

                # Save graphs
                for fig, label in zip([fig_iv, fig_jv], ['iv', 'jv']):
                    fig_path = f"{uploaded_file.name}_{label}.png"
                    fig.savefig(fig_path)
                    zf.write(fig_path)
                    os.remove(fig_path)

            except Exception as e:
                st.error(f"Failed to process {uploaded_file.name}: {str(e)}")

    zip_buffer.seek(0)
    b64 = base64.b64encode(zip_buffer.read()).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="iv_jv_graphs.zip">📥 Download All Graphs</a>'
    st.markdown(href, unsafe_allow_html=True)
else:
    st.info("Please enter diode area and upload your files to begin.")
