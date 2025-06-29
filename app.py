import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import zipfile
import base64
import os

st.set_page_config(page_title="Smart I-V Grapher", layout="wide")
st.title("📈 Smart I-V Graph Analyzer")
st.markdown("Upload multiple `.txt` or `.csv` files. This tool will auto-detect Voltage and Current columns and generate I-V graphs.")

uploaded_files = st.file_uploader("Upload your files", type=['csv', 'txt'], accept_multiple_files=True)

if uploaded_files:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for uploaded_file in uploaded_files:
            try:
                # Try to decode
                content = uploaded_file.read().decode('utf-8', errors='ignore')
                lines = content.splitlines()

                # Try to split the lines and infer delimiter
                delimiter = '\t' if '\t' in lines[0] else ',' if ',' in lines[0] else None
                if delimiter:
                    df = pd.read_csv(io.StringIO(content), delimiter=delimiter)
                else:
                    # Handle space-separated or inconsistent data
                    df = pd.DataFrame([line.split() for line in lines if line.strip()])
                    df.columns = df.iloc[0]
                    df = df[1:]

                df = df.apply(pd.to_numeric, errors='coerce')
                df.dropna(how='all', inplace=True)

                # Attempt to auto-detect voltage and current columns
                v_candidates = [col for col in df.columns if str(col).lower().startswith('v')]
                i_candidates = [col for col in df.columns if str(col).lower().startswith('i')]

                v_col = v_candidates[0] if v_candidates else df.columns[0]
                i_col = i_candidates[0] if i_candidates else df.columns[1]

                fig, ax = plt.subplots()
                ax.plot(df[v_col], df[i_col]*1e6)
                ax.set_title(f"I-V Graph: {uploaded_file.name}")
                ax.set_xlabel("Voltage (V)")
                ax.set_ylabel("Current (µA)")
                ax.grid(True)
                st.pyplot(fig)

                # Save to ZIP
                fig_path = f"{uploaded_file.name}_iv.png"
                fig.savefig(fig_path)
                zf.write(fig_path)
                os.remove(fig_path)

            except Exception as e:
                st.error(f"Failed to process {uploaded_file.name}: {str(e)}")

    # Provide ZIP download
    zip_buffer.seek(0)
    b64 = base64.b64encode(zip_buffer.read()).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="iv_graphs.zip">📥 Download All Graphs</a>'
    st.markdown(href, unsafe_allow_html=True)

else:
    st.info("Please upload one or more files to begin.")
