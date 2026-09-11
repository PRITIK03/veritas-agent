import streamlit as st
import requests

API_URL = "http://localhost:8000/query"

st.title("Veritas Agent")

query = st.text_input("Enter your query:")

if st.button("Submit") and query.strip():
    with st.spinner("Running pipeline..."):
        try:
            resp = requests.post(API_URL, json={"query": query}, timeout=120)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API. Is uvicorn running on port 8000?")
            st.stop()
        except Exception as e:
            st.error(f"Request failed: {e}")
            st.stop()

    st.subheader("Answer")
    st.text_area("", value=data["answer"], height=200, label_visibility="collapsed")

    grounded_icon = "✅" if data["grounded"] else "❌"

    with st.expander("Details"):
        st.write(f"**Route:** {data['route']}")
        st.write(f"**Grounded:** {grounded_icon}")
        if data.get("failure_reason"):
            st.write(f"**Failure reason:** {data['failure_reason']}")
        st.write(f"**Latency:** {data['latency_ms']} ms")
        st.write(f"**Tokens:** in={data['input_tokens']} out={data['output_tokens']}")
        st.write(f"**Estimated cost:** ${data['estimated_cost_usd']}")

        if data["sources"]:
            st.write("**Sources:**")
            st.table(data["sources"])
