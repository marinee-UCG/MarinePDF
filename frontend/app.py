import os
import requests
import streamlit as st

API_URL=os.getenv("API_URL","http://localhost:8001")
REQUEST_TIMEOUT=60


def ask_api(question:str) -> tuple[str,list[dict]]:
    try:
        response=requests.post(f"{API_URL}/ask",json={"question":question},timeout=REQUEST_TIMEOUT)
    except requests.RequestException:
        return "API is not reachable. Is the backend running ?" ,[]
    if response.status_code == 422:
        return "Please enter a longer question. ",[]
    if response.status_code == 503:
        return "LLM service unavailable. Please try again later. ", []
    if not response.ok:
        return f"Unexpected error from API ({response.status_code}).",[]
    data=response.json()
    return data["answer"],data["sources"]


def show_sources(sources:list[dict]) -> None:
    if not sources:
        return
    with st.expander("Sources"):
        for source in sources:
            st.markdown(f"**{source['section_code']} - {source['section_title']}** (p.{source['page_number']})")
            st.caption(source["snippet"])

st.set_page_config(
    page_title="MarinePDF",
    page_icon="⚓"
)
st.title("⚓ MarinePDF - Marine Engineer Assistant",text_alignment="center")
st.caption("Ask questions about the auxiliary engines on board. Answers are grounded in the manual and cite their sources")
if "messages" not in st.session_state:
    st.session_state.messages=[]
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        show_sources(message.get("sources",[]))

question=st.chat_input("Ask your question")
if question:
    st.session_state.messages.append({"role":"user","content":question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Searching the manual..."):
            answer,sources=ask_api(question)
        st.markdown(answer)
        show_sources(sources)
    st.session_state.messages.append({"role":"assistant","content":answer,"sources":sources})