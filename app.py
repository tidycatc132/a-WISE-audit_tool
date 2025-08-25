import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
import io
import re
from fpdf import FPDF  # pip install fpdf2

# --- Page Configuration ---
st.set_page_config(
    page_title="A WISE Website Audit Tool",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Helpers: Export ----------

def markdown_to_sections(md: str):
    """Split markdown into [(section, content)] using H2/H3 headings.
    Falls back to a single section if no headings found.
    """
    if not md or not isinstance(md, str):
        return [("Report", str(md))]

    # Normalize line endings
    text = md.replace('\r\n', '\n').strip()

    # Capture H2/H3 headings and their blocks
    pattern = re.compile(r"^(###[ ]+(.*)|##[ ]+(.*))\s*$", re.MULTILINE)
    matches = list(pattern.finditer(text))

    if not matches:
        return [("Report", text)]

    sections = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        heading = m.group(2) or m.group(3) or "Section"
        content = text[start:end].strip('\n')
        sections.append((heading.strip(), content.strip()))
    return sections


def build_csv_bytes_from_markdown(md: str) -> bytes:
    sections = markdown_to_sections(md)
    df = pd.DataFrame(sections, columns=["Section", "Content"])
    return df.to_csv(index=False).encode("utf-8")


class PDF(FPDF):
    def header(self):
        # Title header (set in caller via self.report_title)
        if getattr(self, "report_title", None):
            self.set_font("Helvetica", "B", 14)
            self.multi_cell(0, 8, self.report_title, align="L")
            self.ln(2)
        # thin line
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.2)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", size=8)
        self.set_text_color(120)
        self.cell(0, 8, f"Page {self.page_no()}", align="R")


def build_pdf_bytes_from_markdown(md: str, title: str = "Audit Report") -> bytes:
    pdf = PDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.report_title = title

    pdf.set_font("Helvetica", size=11)

    # Convert simple markdown: treat headings and bullets
    lines = md.replace('\r\n', '\n').split('\n')
    for line in lines:
        stripped = line.strip()
        if not stripped:
            pdf.ln(2)
            continue
        if stripped.startswith("### "):
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(0, 6, stripped[4:])
            pdf.ln(1)
            pdf.set_font("Helvetica", size=11)
        elif stripped.startswith("## "):
            pdf.set_font("Helvetica", "B", 14)
            pdf.multi_cell(0, 7, stripped[3:])
            pdf.ln(1)
            pdf.set_font("Helvetica", size=11)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            pdf.cell(4)  # indent
            pdf.multi_cell(0, 5, "• " + stripped[2:])
        else:
            # Remove basic markdown bold/italics markers for PDF text
            cleaned = re.sub(r"[*_]{1,2}", "", stripped)
            pdf.multi_cell(0, 5, cleaned)
    return pdf.output(dest="S").encode("latin-1")


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

        Maintain a professional, consultative tone throughout the report.
        """

        # Call the API
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"An error occurred: {e}"


# --- UI Layout ---

# Sidebar
with st.sidebar:
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

# Session state to hold last results for exporting
if "audit_results" not in st.session_state:
    st.session_state.audit_results = None
    st.session_state.report_title = None

if st.button("🚀 Start Audit", type="primary", use_container_width=True):
    # --- Input Validation ---
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    elif not url_input or not url_input.startswith(('http://', 'https://')):
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
        st.session_state.report_title = f"Audit Report — {brand_name_input} ({url_input})"
        st.header("Audit Report", divider="rainbow")
        st.markdown(audit_results)
        st.balloons()
        st.success("Audit Complete!")

# --- Export Section (CSV + PDF) ---
if st.session_state.audit_results:
    st.subheader("Export Report")
    col1, col2, col3 = st.columns([1,1,2])

    # CSV export (Section, Content)
    with col1:
        csv_bytes = build_csv_bytes_from_markdown(st.session_state.audit_results)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_bytes,
            file_name="audit_report.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # PDF export (nicely formatted text PDF)
    with col2:
        pdf_bytes = build_pdf_bytes_from_markdown(
            st.session_state.audit_results,
            title=st.session_state.report_title or "Audit Report"
        )
        st.download_button(
            label="⬇️ Download PDF",
            data=pdf_bytes,
            file_name="audit_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    # Optional: raw Markdown download (nice to have)
    with col3:
        st.download_button(
            label="⬇️ Download Markdown (.md)",
            data=(st.session_state.audit_results or "").encode("utf-8"),
            file_name="audit_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

# --- Notes ---
st.caption(
    "Exports: CSV splits the report by sections using H2/H3 headings into two columns (Section, Content). "
    "PDF is a simple, readable text layout. For fully-styled HTML→PDF, consider adding markdown→HTML and a headless renderer (e.g., WeasyPrint/Puppeteer) in your deployment."
)
