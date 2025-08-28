import os
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import google.generativeai as genai

APP_TITLE = "a WISE website audit tool"
MODEL_NAME = "gemini-2.5-pro"

# -------------------------
# Helpers
# -------------------------
def load_api_key() -> str:
    """Load API key from Streamlit secrets or environment."""
    key = None
    try:
        key = st.secrets.get("GOOGLE_API_KEY", None)  # type: ignore[attr-defined]
    except Exception:
        key = None
    if not key:
        key = os.getenv("GOOGLE_API_KEY", "")
    return key or ""


def init_gemini(api_key: str):
    """Configure the google-generativeai client and return a model instance."""
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(MODEL_NAME)


def _default_prompt_template() -> str:
    return (
        "Act as an expert Digital Marketing Strategist and SEO Analyst.\n\n"
        "Your objective is to perform a comprehensive SEO website and brand audit for the provided business. "
        "Focus on on-page, technical, content quality, structured data, off-page, and a prioritized action plan.\n\n"
        "Website URL: {{website_url}}\n"
        "Brand/Company Name: {{brand_name}}\n"
        "Primary Target Audience: {{audience}}\n"
        "Top Competitors (one per line):\n{{competitors_block}}\n\n"
        "Please produce a professional Markdown report with: Executive Summary; On-Page & Content; Keywords & Rankings; "
        "Technical SEO; Structured Data; Off-Page & Brand Visibility; and a prioritized What/Why/How Recommendations list."
    )


def read_prompt_template() -> str:
    template_path = Path(__file__).parent / "prompt_template.md"
    if template_path.exists():
        try:
            return template_path.read_text(encoding="utf-8")
        except Exception:
            pass
    return _default_prompt_template()


def build_prompt(template: str, website_url: str, brand_name: str, audience: str, competitors: list[str]) -> str:
    comp_block = "\n".join([c.strip() for c in competitors if c.strip()]) or "N/A"
    audience = (audience or "").strip() or "Not provided"
    prompt = (
        template
        .replace("{{website_url}}", website_url.strip())
        .replace("{{brand_name}}", brand_name.strip())
        .replace("{{audience}}", audience)
        .replace("{{competitors_block}}", comp_block)
    )
    return prompt


# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title=APP_TITLE, page_icon="🤖", layout="wide")
st.title(APP_TITLE)
st.caption("a little information = A LOT OF AUDIT.")

with st.sidebar:
    st.header("API & Settings")
    default_key = load_api_key()
    api_key = st.text_input(
        "Google API Key (Gemini)",
        value=default_key,
        type="password",
        help=(
            "Set via environment variable GOOGLE_API_KEY or Streamlit secrets (\n"
            "Create .streamlit/secrets.toml with: GOOGLE_API_KEY = 'YOUR_API_KEY')."
        ),
    )
    st.markdown("---")
    st.markdown("**Model:** `gemini-2.5-pro`  " + "Library: `google-generativeai`")

col1, col2 = st.columns([1, 1])
with col1:
    website_url = st.text_input("Website URL", placeholder="https://example.com")
    brand_name = st.text_input("Brand/Company Name", placeholder="WISE Digital Partners")
    audience = st.text_area("Primary Target Audience (optional)", placeholder="Describe your primary audience…")
with col2:
    competitors_raw = st.text_area(
        "Top Competitors (one per line, optional)",
        placeholder="https://competitor-1.com\nhttps://competitor-2.com\nhttps://competitor-3.com",
        height=120,
    )

run = st.button("Run Audit", type="primary")

# Compact metadata table using pandas (demonstrates pandas usage)
meta_df = pd.DataFrame(
    {
        "Field": ["Website URL", "Brand", "Audience", "Competitors"],
        "Value": [
            website_url or "—",
            brand_name or "—",
            audience or "—",
            ", ".join([c for c in competitors_raw.splitlines() if c.strip()]) or "—",
        ],
    }
)
with st.expander("Input Summary (pandas)"):
    st.dataframe(meta_df, hide_index=True, use_container_width=True)

# -------------------------
# Run audit
# -------------------------
if run:
    if not api_key:
        st.error("Please provide a Google API key (Gemini) in the sidebar.")
        st.stop()
    if not website_url or not brand_name:
        st.error("Website URL and Brand/Company Name are required.")
        st.stop()

    try:
        model = init_gemini(api_key)
        template = read_prompt_template()
        competitors = [c for c in competitors_raw.splitlines() if c.strip()]
        full_prompt = build_prompt(
            template=template,
            website_url=website_url,
            brand_name=brand_name,
            audience=audience,
            competitors=competitors,
        )

        with st.spinner("Generating audit with Gemini 2.5 Pro…"):
            response = model.generate_content(full_prompt)

        audit_md = (getattr(response, "text", None) or "").strip()

        if not audit_md:
            st.warning("The model returned no text. Try again, adjust inputs, or check your API quota.")
        else:
            st.subheader("Audit Preview")
            st.markdown(audit_md)

            # Markdown download only
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            st.download_button(
                label="⬇️ Download Markdown",
                data=audit_md.encode("utf-8"),
                file_name=f"audit_{brand_name}_{timestamp}.md".replace(" ", "_"),
                mime="text/markdown",
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")
