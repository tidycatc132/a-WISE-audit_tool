import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
import io
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="A WISE Website Audit Tool",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------
# Helpers: Markdown table → DataFrame
# ----------------------
TABLE_HEADER_SEP_RE = re.compile(r"^\s*\|?\s*(:?-{3,}:?\s*\|\s*)+:?-{3,}:?\s*$")
HEADING_RE = re.compile(r"^(#+)\s+(.*)")


def _split_md_row(line: str) -> list:
    # Trim leading/trailing pipe, then split by pipes
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    # Split on unescaped pipes (simple case)
    return [cell.strip().strip("` ") for cell in line.split("|")]


def parse_markdown_tables(md_text: str) -> dict:
    """Extract markdown pipe tables from text.
    Returns dict {table_name: DataFrame}.
    Table name is best-effort from the nearest preceding heading, else Table N.
    """
    lines = md_text.splitlines()
    tables = {}
    cur_heading = None
    table_idx = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        # Track most recent heading as a potential table name
        m = HEADING_RE.match(line)
        if m:
            cur_heading = m.group(2).strip()
            i += 1
            continue

        # Detect start of table: header row with at least one pipe, followed by separator row of dashes
        if "|" in line and i + 1 < len(lines) and TABLE_HEADER_SEP_RE.match(lines[i + 1]):
            header_cells = _split_md_row(line)
            # Collect data rows until a blank line or a non-pipe format line
            data_rows = []
            i += 2  # skip header & separator
            while i < len(lines):
                row = lines[i]
                if not row.strip():
                    break
                if "|" not in row:
                    break
                data_rows.append(_split_md_row(row))
                i += 1

            # Build DataFrame (handle ragged rows)
            max_len = max([len(header_cells)] + [len(r) for r in data_rows] or [0])
            header = header_cells + [f"col_{k}" for k in range(len(header_cells), max_len)]
            fixed_rows = [r + [""] * (max_len - len(r)) for r in data_rows]
            df = pd.DataFrame(fixed_rows, columns=header)

            # Name
            table_idx += 1
            name_base = cur_heading or f"Table {table_idx}"
            name = name_base
            # Ensure unique key
            k = 2
            while name in tables:
                name = f"{name_base} ({k})"
                k += 1
            tables[name] = df
            continue  # continue without incrementing i here since we've already moved

        i += 1
    return tables


# --- Gemini API Function ---
def run_gemini_audit(url, brand_name, audience, competitors, api_key):
    """
    Constructs the prompt and calls the Gemini API to perform the audit.
    """
    try:
        genai.configure(api_key=api_key)
        # --- MODEL UPDATED TO 2.5 ---
        model = genai.GenerativeModel('gemini-2.5-pro')

        # Construct the detailed prompt from user inputs
        prompt = f"""
        Act as an expert Digital Marketing Strategist and SEO Analyst.
        Your objective is to perform a comprehensive website and brand audit for the provided business. You will analyze the brand's digital footprint, focusing on its website performance, search engine visibility, and overall online authority. Your analysis must be in-depth, data-driven (using your knowledge base of common metrics and best practices), and conclude with a prioritized list of actionable recommendations.

        ## 1. User-Provided Information:
        - **Website URL:** {url}
        - **Brand/Company Name:** {brand_name}
        - **Primary Target Audience:** {audience}
        - **Top 3 Competitors:** {competitors}

        ## 2. Audit Structure & Execution:
        Please structure your response as a formal audit report using Markdown for clear formatting. Follow these sections precisely:

        ### Executive Summary
        Begin with a high-level overview. Summarize the website's current digital marketing health. Concisely list the top 3 most significant strengths and the top 3 most critical areas for immediate improvement.

        ### Section A: On-Page & Content Analysis
        - **Top Performing Pages:** Based on likely organic traffic and keyword value, identify 3-5 pages that are probably the strongest assets.
        - **Content Quality & E-E-A-T:** Assess the website's content for signals of Experience, Expertise, Authoritativeness, and Trustworthiness (E-E-A-T).
        - **On-Page SEO Elements:** Analyze Title Tags, Meta Descriptions, Header Tags, Internal Linking, and Calls-to-Action (CTAs).

        ### Section B: Keyword & Ranking Analysis
        - **Current Keyword Footprint:** Identify 10-15 commercially important, non-branded keywords the site likely ranks for. Present this in a table with columns: Keyword, Estimated Monthly Search Volume, Estimated Ranking Position, and Ranking URL.
        - **"Striking Distance" Keywords:** Identify 5-7 keywords where the site is likely ranking on page 2 (positions 11-20).
        - **Keyword Gap Analysis:** Identify 3-5 valuable keywords that competitors rank for, but the target website does not.

        ### Section C: Technical SEO Audit
        - **Indexability & Crawlability:** Review robots.txt and XML sitemap presence.
        - **Website Speed & Core Web Vitals:** Analyze LCP, CLS, and INP.
        - **Mobile-Friendliness:** Assess mobile responsiveness.
        - **Site Architecture & URL Structure:** Evaluate URL clarity.
        - **Security:** Confirm HTTPS usage.

        ### Section D: Structured Data (Schema Markup) Analysis
        - **Implementation Check:** Determine if structured data is used.
        - **Types of Schema:** Identify schema types used (e.g., Organization, LocalBusiness).
        - **Opportunities:** Suggest 2-3 new schema types to implement.

        ### Section E: Off-Page & Brand Visibility Audit
        - **Backlink Profile Overview:** Provide a conceptual overview of the domain's authority and link quality.
        - **Brand Mentions:** Analyze brand visibility and unlinked mentions.
        - **Google Business Profile:** Assess its completeness and optimization.
        - **Social Media Presence:** List active profiles and comment on activity.

        ### Section F: Prioritized Actionable Recommendations
        Conclude with a prioritized list of the top 5 most impactful recommendations using the "What, Why, How" framework:
        - **What:** The specific action to take.
        - **Why:** The business or SEO impact.
        - **How:** A high-level summary of implementation.

        IMPORTANT: Whenever you present tabular data, render it as a standard Markdown pipe table with a header row and a separator row (---). Do not embed images of tables. Use concise column headers.
        """

        # Call the API
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"


# --- UI Layout ---
# Sidebar with st.sidebar:
st.title("Audit Configuration")
st.info("Fill in the details below to run a comprehensive, WISE powered website and brand audit.")
api_key = st.text_input("Enter your Gemini API Key", type="password")

st.header("Business Information")
url_input = st.text_input("Website URL", "https://www.wisedigitalpartners.com/")
brand_name_input = st.text_input("Brand/Company Name", "WISE Digital Partners")
audience_input = st.text_area("Primary Target Audience", "Small to medium-sized business owners, aged 30-55")
competitors_input = st.text_area("Top 3 Competitors (URLs)", "https://thriveagency.com/\nhttps://www.scorpion.co/\nhttps://rankings.io/")

st.success("Ready to audit!")

# Main Content
st.title("🤖 A WISE Website Audit Tool")
st.markdown("This tool leverages the Gemini 2.5 Pro model to perform a comprehensive digital marketing and SEO audit based on the prompt you provided. Enter your details in the sidebar and click 'Start Audit' to begin.")

if "audit_results" not in st.session_state:
    st.session_state.audit_results = None
if "audit_tables" not in st.session_state:
    st.session_state.audit_tables = {}

if st.button("🚀 Start Audit", type="primary", use_container_width=True):
    # --- Input Validation ---
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    elif not url_input or not url_input.startswith(("http://", "https://")):
        st.error("Please enter a valid Website URL.")
    elif not brand_name_input:
        st.error("Please enter a Brand/Company Name.")
    else:
        with st.spinner('Performing AI-powered audit... This may take a few moments.'):
            # --- Run Audit and Display Results ---
            audit_results = run_gemini_audit(
                url=url_input,
                brand_name=brand_name_input,
                audience=audience_input,
                competitors=competitors_input,
                api_key=api_key
            )
            st.session_state.audit_results = audit_results
            st.header("Audit Report", divider="rainbow")
            st.markdown(audit_results)

            # Parse markdown tables for CSV export
            tables = parse_markdown_tables(audit_results or "")
            st.session_state.audit_tables = tables

            if tables:
                st.success(f"Found {len(tables)} table(s) in the report. You can preview and export them as CSV below.")
                for name, df in tables.items():
                    with st.expander(f"Preview: {name}", expanded=False):
                        st.dataframe(df, use_container_width=True)
                        csv_buf = io.StringIO()
                        df.to_csv(csv_buf, index=False)
                        st.download_button(
                            label=f"⬇️ Download '{name}' as CSV",
                            data=csv_buf.getvalue(),
                            file_name=f"{re.sub(r'[^A-Za-z0-9_-]+', '_', name.lower())}.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )
            else:
                st.info("No Markdown tables were detected. To enable CSV export, ensure the model outputs tables in Markdown pipe-table format.")

            st.balloons()
            st.success("Audit Complete!")

# --- Standalone CSV Export section (if user navigates or reruns without re-auditing) ---
if st.session_state.audit_results:
    st.divider()
    st.subheader("CSV Export")
    if st.session_state.audit_tables:
        sel = st.selectbox("Choose a table to export:", list(st.session_state.audit_tables.keys()))
        df_sel = st.session_state.audit_tables[sel]
        st.dataframe(df_sel, use_container_width=True)
        csv_buf2 = io.StringIO()
        df_sel.to_csv(csv_buf2, index=False)
        st.download_button(
            label=f"⬇️ Download '{sel}' as CSV",
            data=csv_buf2.getvalue(),
            file_name=f"{re.sub(r'[^A-Za-z0-9_-]+', '_', sel.lower())}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("Run an audit or ensure the response includes Markdown tables to enable CSV export.")
