import os
import textwrap
from io import BytesIO
from pathlib import Path
from datetime import datetime

import streamlit as st
import pandas as pd
import google.generativeai as genai
from fpdf import FPDF

APP_TITLE = "a WISE Website Audit"
MODEL_NAME = "gemini-2.5-pro"

# -------------------------
# Helpers
# -------------------------

def load_api_key() -> str:
    key = None
    try:
        key = st.secrets.get("GOOGLE_API_KEY", None)  # type: ignore[attr-defined]
    except Exception:
        key = None
    if not key:
        key = os.getenv("GOOGLE_API_KEY", "")
    return key or ""


def init_gemini(api_key: str):
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
# Unicode-safe PDF Export (fpdf2)
# -------------------------
UNICODE_REPLACEMENTS = {
    "\u2014": "-",  # em dash —
    "\u2013": "-",  # en dash –
    "\u2022": "*",  # bullet •
    "\u00A0": " ",  # nbsp
    "\u2018": "'", "\u2019": "'",  # curly single quotes
    "\u201C": '"', "\u201D": '"',  # curly double quotes
}


def sanitize_unicode(s: str) -> str:
    for bad, good in UNICODE_REPLACEMENTS.items():
        s = s.replace(bad, good)
    return s


class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font(self._body_font, style="I", size=8)
            self.cell(0, 6, APP_TITLE, align="R")
            self.ln(8)

    def set_fonts(self, body_font: str, bold_font: str):
        self._body_font = body_font
        self._bold_font = bold_font


def _setup_fonts(pdf: FPDF) -> tuple[str, str]:
    """Try to use bundled Unicode fonts (DejaVu). Fallback to core fonts + sanitize."""
    fonts_dir = Path(__file__).parent / "fonts"
    regular = fonts_dir / "DejaVuSans.ttf"
    bold = fonts_dir / "DejaVuSans-Bold.ttf"

    if regular.exists() and bold.exists():
        pdf.add_font("DejaVu", "", str(regular), uni=True)
        pdf.add_font("DejaVu", "B", str(bold), uni=True)
        pdf.set_fonts("DejaVu", "DejaVu")
        return "DejaVu", "DejaVu"
    else:
        # Use core Helvetica (non-Unicode) and sanitize text later
        pdf.set_fonts("Helvetica", "Helvetica")
        return "Helvetica", "Helvetica"


def markdown_to_pdf_bytes(markdown_text: str, title: str = "Audit Report") -> bytes:
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=12)

    body_font, bold_font = _setup_fonts(pdf)

    pdf.add_page()

    # Title block
    if bold_font:
        pdf.set_font(bold_font, "B", 16)
    else:
        pdf.set_font("Helvetica", "B", 16)

    safe_title = title if body_font == "DejaVu" else sanitize_unicode(title)
    pdf.multi_cell(0, 10, safe_title)
    pdf.ln(2)

    if body_font:
        pdf.set_font(body_font, size=11)
    else:
        pdf.set_font("Helvetica", size=11)

    in_code_block = False
    code_buffer: list[str] = []

    def flush_code():
        if code_buffer:
            # Use monospace-like rendering with Courier; safe for ASCII
            pdf.set_font("Courier", size=9)
            for line in code_buffer:
                safe = line if body_font == "DejaVu" else sanitize_unicode(line)
                pdf.multi_cell(0, 5, safe)
            if body_font:
                pdf.set_font(body_font, size=11)
            else:
                pdf.set_font("Helvetica", size=11)
            code_buffer.clear()

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip("\n")
        if line.strip().startswith("```"):
            if in_code_block:
                flush_code()
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        if not line.strip():
            pdf.ln(4)
            continue

        safe_line = line if body_font == "DejaVu" else sanitize_unicode(line)

        if line.startswith("### "):
            if bold_font:
                pdf.set_font(bold_font, "B", 12)
            else:
                pdf.set_font("Helvetica", "B", 12)
            pdf.multi_cell(0, 8, safe_line[4:])
            if body_font:
                pdf.set_font(body_font, size=11)
            else:
                pdf.set_font("Helvetica", size=11)
        elif line.startswith("## "):
            if bold_font:
                pdf.set_font(bold_font, "B", 13)
            else:
                pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(0, 9, safe_line[3:])
            if body_font:
                pdf.set_font(body_font, size=11)
            else:
                pdf.set_font("Helvetica", size=11)
        elif line.startswith("# "):
            if bold_font:
                pdf.set_font(bold_font, "B", 15)
            else:
                pdf.set_font("Helvetica", "B", 15)
            pdf.multi_cell(0, 10, safe_line[2:])
            if body_font:
                pdf.set_font(body_font, size=11)
            else:
                pdf.set_font("Helvetica", size=11)
        elif line.startswith(("- ", "* ")):
            pdf.multi_cell(0, 6, f"• {safe_line[2:]}")
        else:
            wrapped = textwrap.fill(safe_line, width=110)
            pdf.multi_cell(0, 6, wrapped)

    flush_code()

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title=APP_TITLE, page_icon="🤖", layout="wide")
st.title(APP_TITLE)
st.caption("Add some quick information and get a WISE website and brand audit in return!")

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
        full_prompt = build_prompt(template, website_url, brand_name, audience, competitors)

        with st.spinner("Generating audit with Gemini 2.5 Pro…"):
            response = model.generate_content(full_prompt)

        audit_md = (getattr(response, "text", None) or "").strip()

        if not audit_md:
            st.warning("The model returned no text. Try again, adjust inputs, or check your API quota.")
        else:
            st.subheader("Audit Preview")
            st.markdown(audit_md)

            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            pdf_title = f"{brand_name} — SEO Website & Brand Audit"
            pdf_bytes = markdown_to_pdf_bytes(audit_md, title=pdf_title)
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_bytes,
                file_name=f"audit_{brand_name}_{timestamp}.pdf".replace(" ", "_"),
                mime="application/pdf",
            )

            st.download_button(
                label="⬇️ Download Markdown",
                data=audit_md.encode("utf-8"),
                file_name=f"audit_{brand_name}_{timestamp}.md".replace(" ", "_"),
                mime="text/markdown",
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")
