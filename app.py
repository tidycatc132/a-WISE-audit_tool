import os
import textwrap
from io import BytesIO
from pathlib import Path
from datetime import datetime


import streamlit as st
import pandas as pd
import google.generativeai as genai
from fpdf import FPDF
APP_TITLE = "Website Audit — Streamlit + Gemini 2.5 Pro"
MODEL_NAME = "gemini-2.5-pro"


# -------------------------
# Utilities
# -------------------------


def load_api_key() -> str:
"""Load API key from Streamlit secrets or environment."""
key = st.secrets.get("GOOGLE_API_KEY", None) if hasattr(st, "secrets") else None
if not key:
key = os.getenv("GOOGLE_API_KEY")
return key or ""




def init_gemini(api_key: str):
genai.configure(api_key=api_key)
return genai.GenerativeModel(MODEL_NAME)




def read_prompt_template() -> str:
template_path = Path(__file__).parent / "prompt_template.md"
return template_path.read_text(encoding="utf-8")




def build_prompt(template: str, website_url: str, brand_name: str, audience: str, competitors: list[str]) -> str:
# Prepare competitors block — each on its own line, or N/A
comp_block = "\n".join([c.strip() for c in competitors if c.strip()]) or "N/A"
# Fallback for audience
audience = audience.strip() or "Not provided"


prompt = (
template
.replace("{{website_url}}", website_url.strip())
.replace("{{brand_name}}", brand_name.strip())
.replace("{{audience}}", audience)
.replace("{{competitors_block}}", comp_block)
)
return prompt




# -------------------------
# PDF Export (simple Markdown-ish to PDF)
# -------------------------
class PDF(FPDF):
def header(self):
# Minimal header (skip on first page for a cleaner title block)
if self.page_no() > 1:
self.set_font("Helvetica", style="I", size=8)
self.cell(0, 6, APP_TITLE, align="R")
self.ln(8)




def markdown_to_pdf_bytes(markdown_text: str, title: str = "Audit Report") -> bytes:
pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=12)
pdf.add_page()


# Title block
pdf.set_font("Helvetica", "B", 16)
pdf.multi_cell(0, 10, title)
pdf.ln(2)


pdf.set_font("Helvetica", size=11)


# Naive Markdown handling: headings and bullets
for raw_line in markdown_text.splitlines():
line = raw_line.rstrip()
if not line:
pdf.ln(4)
continue


if line.startswith("### "):
pdf.set_font("Helvetica", "B", 12)
pdf.multi_cell(0, 8, line[4:])
pdf.set_font("Helvetica", size=11)
elif line.startswith("## "):
pdf.set_font("Helvetica", "B", 13)
pdf.multi_cell(0, 9, line[3:])
pdf.set_font("Helvetica", size=11)
elif line.startswith("# "):
pdf.set_font("Helvetica", "B", 15)
pdf.multi_cell(0, 10, line[2:])
pdf.set_font("Helvetica", size=11)
elif line.startswith(("- ", "* ")):
pdf.multi_cell(0, 6, f"• {line[2:]}")
else:
# Wrap long paragraphs
wrapped = textwrap.fill(line, width=110)
pdf.multi_cell(0, 6, wrapped)


buf = BytesIO()
pdf.output(buf)
return buf.getvalue()


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
audit_md = (response.text or "").strip()


if not audit_md:
st.warning("The model returned no text. Try again or adjust inputs.")
else:
st.subheader("Audit Preview")
st.markdown(audit_md)


# PDF Download
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
pdf_bytes = markdown_to_pdf_bytes(
audit_md,
title=f"{brand_name} — SEO Website & Brand Audit",
)
st.download_button(
label="⬇️ Download PDF",
data=pdf_bytes,
file_name=f"audit_{brand_name}_{timestamp}.pdf".replace(" ", "_"),
mime="application/pdf",
)


# Optional raw Markdown download
st.download_button(
label="⬇️ Download Markdown",
data=audit_md.encode("utf-8"),
file_name=f"audit_{brand_name}_{timestamp}.md".replace(" ", "_"),
mime="text/markdown",
)


except Exception as e:
st.error(f"An error occurred: {e}")
