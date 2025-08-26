import os


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
