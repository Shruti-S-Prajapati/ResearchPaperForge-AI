import streamlit as st
import json
import zipfile
import io
import re
from datetime import datetime
import google.generativeai as genai
try:
    import fitz
except ImportError:
    fitz = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResearchPaperForge AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main { background: #0f1117; }
section[data-testid="stSidebar"] { background: #161b27 !important; border-right: 1px solid #2a3045; }
section[data-testid="stSidebar"] * { color: #c9d1e0 !important; }

.forge-header {
    background: linear-gradient(135deg, #1a2035 0%, #0d1b2a 50%, #1a2035 100%);
    border: 1px solid #2a4080;
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.forge-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #3b6cf8, #7c3aed, #3b6cf8);
}
.forge-header h1 { color: #e8edf5; font-size: 1.8rem; font-weight: 700; margin: 0; letter-spacing: -0.02em; }
.forge-header p { color: #6b7fa3; margin: 0.4rem 0 0; font-size: 0.9rem; }

.card {
    background: #161b27;
    border: 1px solid #2a3045;
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.card-header { font-size: 0.75rem; font-weight: 600; color: #4a6fa5; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.8rem; }

.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 0.8rem; margin-bottom: 1rem; }
.kpi-card {
    background: #1a2035;
    border: 1px solid #2a3045;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}
.kpi-value { font-size: 1.6rem; font-weight: 700; color: #4f8ef7; font-family: 'JetBrains Mono', monospace; }
.kpi-label { font-size: 0.7rem; color: #6b7fa3; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.25rem; }

.status-pill {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 500;
}
.status-done { background: #0d2e1a; color: #4ade80; border: 1px solid #166534; }
.status-pending { background: #1c1a0d; color: #facc15; border: 1px solid #713f12; }
.status-empty { background: #1a1a1a; color: #6b7fa3; border: 1px solid #2a3045; }

.section-badge {
    background: #1a2035;
    border-left: 3px solid #3b6cf8;
    padding: 0.6rem 1rem;
    border-radius: 0 6px 6px 0;
    margin-bottom: 0.8rem;
    font-size: 0.85rem;
    color: #c9d1e0;
    font-weight: 500;
}

.cite-row { border-bottom: 1px solid #1e2535; padding: 0.6rem 0; font-size: 0.82rem; color: #a0aec0; }
.cite-row:last-child { border-bottom: none; }

.stButton > button {
    background: #1e3a6e !important;
    color: #93c5fd !important;
    border: 1px solid #2d5ca8 !important;
    border-radius: 7px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 0.4rem 1rem !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #2d4fa0 !important;
    border-color: #4a7fd4 !important;
    color: #bfdbfe !important;
}
.stButton > button[kind="primary"] {
    background: #1e3a6e !important;
}

.stTextArea textarea, .stTextInput input, .stSelectbox select {
    background: #1a2035 !important;
    border: 1px solid #2a3045 !important;
    color: #c9d1e0 !important;
    border-radius: 7px !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #3b6cf8 !important;
    box-shadow: 0 0 0 2px rgba(59,108,248,0.15) !important;
}

.workflow-step {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.55rem 0.75rem;
    border-radius: 7px;
    margin-bottom: 0.3rem;
    font-size: 0.8rem;
}
.step-active { background: #1a2a4a; border: 1px solid #2d5ca8; color: #93c5fd; }
.step-done { background: #0d2218; border: 1px solid #166534; color: #4ade80; }
.step-idle { background: transparent; border: 1px solid #1e2535; color: #4a5568; }

.latex-preview {
    background: #0a0f1a;
    border: 1px solid #2a3045;
    border-radius: 8px;
    padding: 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #a8c7fa;
    white-space: pre-wrap;
    max-height: 300px;
    overflow-y: auto;
}

div[data-testid="stExpander"] {
    background: #161b27 !important;
    border: 1px solid #2a3045 !important;
    border-radius: 8px !important;
}
.streamlit-expanderHeader { color: #a0aec0 !important; font-size: 0.85rem !important; }

div[data-testid="stTab"] { background: transparent; }
.stTabs [data-baseweb="tab-list"] { background: #161b27; border-radius: 8px; border: 1px solid #2a3045; padding: 4px; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #6b7fa3; border-radius: 6px; }
.stTabs [aria-selected="true"] { background: #1e3a6e !important; color: #93c5fd !important; }

.stSuccess { background: #0d2218 !important; border-color: #166534 !important; }
.stError { background: #2e0a0a !important; border-color: #7f1d1d !important; }
.stInfo { background: #0d1b2e !important; border-color: #1e3a6e !important; }
</style>
""", unsafe_allow_html=True)

# ─── SESSION STATE INIT ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "paper_state": {
            "title": "", "authors": [], "affiliations": [], "paper_type": "Experimental",
            "journal": "IEEE", "pdf_data": [], "citations": [],
            "introduction": "", "literature_review": "", "methodology": "",
            "experimental_setup": "", "results": "", "discussion": "", "conclusion": "",
            "analytics": {}, "latex_project": {}
        },
        "knowledge_base": {"methodology_index": {}, "dataset_index": {}, "citation_index": {}, "keyword_index": {}},
        "experiment_details": {
            "objective": "", "problem": "", "dataset": "", "methodology": "",
            "tools": "", "hardware": "", "metrics": "", "results_desc": "", "future_work": ""
        },
        "metadata": {
            "title": "", "authors": "", "affiliations": "", "corresponding": "",
            "keywords": "", "paper_type": "Experimental", "journal": "IEEE"
        },
        "api_key": "",
        "active_stage": "upload",
        "pdf_cache": {},
        "gemini_model": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def get_model():
    if not GENAI_AVAILABLE:
        st.error("google-generativeai package not installed.")
        return None

    key = st.session_state.get("api_key", "").strip()

    if not key:
        st.error("No API key provided.")
        return None

    try:
        genai.configure(api_key=key)

        model = genai.GenerativeModel("gemini-2.5-flash")

        # Test connection
        model.generate_content("Hello")

        return model

    except Exception as e:
        st.error(f"Gemini Error: {e}")
        return None

def call_gemini(prompt: str, max_tokens: int = 2000) -> str:
    model = get_model()
    if model is None:
        return "[ERROR: Gemini not available. Enter API key in sidebar.]"
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(max_output_tokens=max_tokens, temperature=0.7)
        )
        return response.text.strip()
    except Exception as e:
        return f"[ERROR: {str(e)}]"

def extract_pdf_pymupdf(file_bytes: bytes, filename: str) -> dict:
    if fitz is None:
        return {}
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        return parse_paper_text(full_text, filename)
    except Exception as e:
        return {"filename": filename, "error": str(e), "raw_text": ""}

def extract_pdf_pdfplumber(file_bytes: bytes, filename: str) -> dict:
    if pdfplumber is None:
        return {}
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            full_text = ""
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    full_text += t + "\n"
        return parse_paper_text(full_text, filename)
    except Exception as e:
        return {"filename": filename, "error": str(e), "raw_text": ""}

def parse_paper_text(text: str, filename: str) -> dict:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    title = lines[0] if lines else filename.replace(".pdf", "")
    abstract = ""
    references = []
    sections = {}
    in_abstract = False
    in_references = False
    current_section = ""
    section_text = []
    abstract_lines = []

    section_patterns = [
        r'^(abstract|introduction|related work|literature review|methodology|'
        r'method|experimental setup|experiments|results|discussion|conclusion|'
        r'references|bibliography|acknowledgements?)\s*$'
    ]

    for line in lines:
        low = line.lower()
        if re.match(r'^abstract\s*$', low):
            in_abstract = True
            in_references = False
            continue
        if re.match(r'^(references|bibliography)\s*$', low):
            in_references = True
            in_abstract = False
            if current_section and section_text:
                sections[current_section] = " ".join(section_text)
            current_section = ""
            section_text = []
            continue
        is_section = any(re.match(p, low) for p in section_patterns)
        if is_section and not in_references:
            in_abstract = False
            if current_section and section_text:
                sections[current_section] = " ".join(section_text)
            current_section = line
            section_text = []
            continue
        if in_abstract:
            abstract_lines.append(line)
            if len(" ".join(abstract_lines)) > 1500:
                in_abstract = False
        elif in_references:
            if re.match(r'^\[?\d+[\].]', line) or re.match(r'^[A-Z][a-z]+,\s', line):
                references.append(line)
        elif current_section:
            section_text.append(line)

    abstract = " ".join(abstract_lines)[:2000]
    if current_section and section_text:
        sections[current_section] = " ".join(section_text)

    authors = []
    keywords = []
    for line in lines[1:8]:
        if re.search(r'\b(and|,)\b', line) and len(line) < 200 and not any(c.isdigit() for c in line[:5]):
            if not authors:
                authors = [a.strip() for a in re.split(r',|\band\b', line) if a.strip()]
    for line in lines:
        if re.match(r'^keywords?[:\s]', line.lower()):
            kw_text = re.sub(r'^keywords?[:\s]*', '', line, flags=re.IGNORECASE)
            keywords = [k.strip() for k in re.split(r'[;,]', kw_text) if k.strip()]

    return {
        "filename": filename,
        "title": title[:200],
        "abstract": abstract,
        "authors": authors[:6],
        "keywords": keywords[:10],
        "references": references[:80],
        "sections": sections,
        "raw_text": text[:5000],
        "word_count": len(text.split()),
    }

def build_knowledge_base(pdf_data_list: list) -> dict:
    kb = {"methodology_index": {}, "dataset_index": {}, "citation_index": {}, "keyword_index": {}}
    for paper in pdf_data_list:
        fname = paper.get("filename", "unknown")
        for kw in paper.get("keywords", []):
            kb["keyword_index"].setdefault(kw.lower(), []).append(fname)
        for ref in paper.get("references", []):
            kb["citation_index"].setdefault(fname, []).append(ref)
        for section, text in paper.get("sections", {}).items():
            sl = section.lower()
            if any(m in sl for m in ["method", "approach", "algorithm"]):
                kb["methodology_index"][fname] = text[:500]
            if any(d in sl for d in ["dataset", "data", "experiment"]):
                kb["dataset_index"][fname] = text[:500]
    return kb

def latex_escape(text: str) -> str:
    replacements = [
        ('\\', r'\textbackslash{}'), ('&', r'\&'), ('%', r'\%'), ('$', r'\$'),
        ('#', r'\#'), ('_', r'\_'), ('{', r'\{'), ('}', r'\}'),
        ('~', r'\textasciitilde{}'), ('^', r'\textasciicircum{}'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text

def section_to_latex(section_text: str, label: str) -> str:
    if not section_text:
        return f"% {label} - not generated\n"
    escaped = latex_escape(section_text)
    paragraphs = [p.strip() for p in escaped.split('\n\n') if p.strip()]
    body = "\n\n".join(paragraphs)
    return body

def generate_bibtex(citations: list) -> str:
    entries = []
    for i, cite in enumerate(citations):
        key = f"ref{i+1}"
        title = latex_escape(cite.get("title", f"Reference {i+1}"))
        authors = latex_escape(cite.get("authors", "[USER INPUT REQUIRED]"))
        year = cite.get("year", "[USER INPUT REQUIRED]")
        doi = cite.get("doi", "")
        source = cite.get("source", "")
        entry = f"@article{{{key},\n  author = {{{authors}}},\n  title = {{{title}}},\n  year = {{{year}}},"
        if doi:
            entry += f"\n  doi = {{{doi}}},"
        if source:
            entry += f"\n  note = {{Source: {latex_escape(source)}}},"
        entry += "\n}\n"
        entries.append(entry)
    return "\n".join(entries) if entries else "% No references extracted\n"

def generate_latex_project(ps: dict, metadata: dict, exp: dict) -> dict:
    journal = metadata.get("journal", "IEEE")
    title = latex_escape(metadata.get("title", "Research Paper Title"))
    authors = latex_escape(metadata.get("authors", "Author Names"))

    if journal == "IEEE":
        doc_class = r"\documentclass[conference]{IEEEtran}"
        pkg_extra = r"\usepackage{cite}" + "\n" + r"\usepackage{amsmath,amssymb,amsfonts}"
    elif journal == "ACM":
        doc_class = r"\documentclass[sigconf]{acmart}"
        pkg_extra = r"\usepackage{booktabs}"
    elif journal == "Springer":
        doc_class = r"\documentclass[twocolumn]{svjour3}"
        pkg_extra = r"\usepackage{mathptmx}"
    elif journal == "Elsevier":
        doc_class = r"\documentclass[preprint,12pt]{elsarticle}"
        pkg_extra = r"\usepackage{amssymb}"
    else:
        doc_class = r"\documentclass[12pt,a4paper]{article}"
        pkg_extra = r"\usepackage{amsmath}"

    main_tex = f"""{doc_class}
{pkg_extra}
\\usepackage{{graphicx}}
\\usepackage{{hyperref}}
\\usepackage{{listings}}
\\usepackage{{xcolor}}

\\title{{{title}}}
\\author{{{authors}}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle

\\begin{{abstract}}
{latex_escape(ps.get("introduction", "[USER INPUT REQUIRED - write abstract here]")[:400])}
\\end{{abstract}}

\\input{{sections/introduction}}
\\input{{sections/literature_review}}
\\input{{sections/methodology}}
\\input{{sections/experimental_setup}}
\\input{{sections/results}}
\\input{{sections/discussion}}
\\input{{sections/conclusion}}

\\bibliographystyle{{{"IEEEtran" if journal == "IEEE" else "plain"}}}
\\bibliography{{references}}

\\end{{document}}
"""
    sections = {
        "introduction": f"\\section{{Introduction}}\n\n{section_to_latex(ps.get('introduction',''), 'Introduction')}",
        "literature_review": f"\\section{{Literature Review}}\n\n{section_to_latex(ps.get('literature_review',''), 'Literature Review')}",
        "methodology": f"\\section{{Methodology}}\n\n{section_to_latex(ps.get('methodology',''), 'Methodology')}",
        "experimental_setup": f"\\section{{Experimental Setup}}\n\n{section_to_latex(ps.get('experimental_setup',''), 'Experimental Setup')}",
        "results": f"\\section{{Results}}\n\n{section_to_latex(ps.get('results',''), 'Results')}",
        "discussion": f"\\section{{Discussion}}\n\n{section_to_latex(ps.get('discussion',''), 'Discussion')}",
        "conclusion": f"\\section{{Conclusion}}\n\n{section_to_latex(ps.get('conclusion',''), 'Conclusion')}",
    }
    bib = generate_bibtex(ps.get("citations", []))
    return {"main.tex": main_tex, "sections": sections, "references.bib": bib}

def create_zip(latex_project: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project/main.tex", latex_project.get("main.tex", ""))
        zf.writestr("project/references.bib", latex_project.get("references.bib", ""))
        for sec_name, sec_content in latex_project.get("sections", {}).items():
            zf.writestr(f"project/sections/{sec_name}.tex", sec_content)
    buf.seek(0)
    return buf.read()

def compute_analytics(ps: dict) -> dict:
    all_text = " ".join(filter(None, [
        ps.get("introduction",""), ps.get("literature_review",""),
        ps.get("methodology",""), ps.get("experimental_setup",""),
        ps.get("results",""), ps.get("discussion",""), ps.get("conclusion","")
    ]))
    words = len(all_text.split()) if all_text.strip() else 0
    chars = len(all_text)
    sections_done = sum(1 for k in ["introduction","literature_review","methodology",
                                     "experimental_setup","results","discussion","conclusion"]
                        if ps.get(k,"").strip())
    return {
        "word_count": words,
        "char_count": chars,
        "estimated_pages": max(1, round(words / 500)),
        "reference_count": len(ps.get("citations", [])),
        "sections_done": sections_done,
        "pdfs_loaded": len(ps.get("pdf_data", [])),
    }

def parse_references_from_pdfs(pdf_data_list: list) -> list:
    citations = []
    seen = set()
    for paper in pdf_data_list:
        for ref in paper.get("references", []):
            if ref not in seen:
                seen.add(ref)
                year_match = re.search(r'\b(19|20)\d{2}\b', ref)
                doi_match = re.search(r'10\.\d{4,}/\S+', ref)
                citations.append({
                    "title": ref[:120],
                    "authors": "[USER INPUT REQUIRED]",
                    "year": year_match.group() if year_match else "[USER INPUT REQUIRED]",
                    "doi": doi_match.group() if doi_match else "",
                    "source": paper.get("filename", ""),
                    "raw": ref
                })
    return citations

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ResearchPaperForge AI")
    st.markdown("---")
    api_key = st.text_input("Gemini API Key", type="password", value=st.session_state.api_key,
                             placeholder="AIzaSy...")
    if api_key != st.session_state.api_key:
        st.session_state.api_key = api_key
        st.session_state.gemini_model = None

    key_status = "Connected" if st.session_state.api_key else "Not set"
    key_color = "status-done" if st.session_state.api_key else "status-empty"
    st.markdown(f'<span class="status-pill {key_color}">API {key_status}</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Workflow**")
    ps = st.session_state.paper_state
    kb = st.session_state.knowledge_base

    stages = [
        ("upload", "PDF Upload", bool(ps["pdf_data"])),
        ("knowledge", "Knowledge Base", bool(kb["citation_index"])),
        ("metadata", "Paper Metadata", bool(ps.get("title") or st.session_state.metadata.get("title"))),
        ("experiment", "Experiment Details", bool(st.session_state.experiment_details.get("objective"))),
        ("generate", "Section Generation", any(ps.get(s) for s in ["introduction","literature_review","methodology"])),
        ("citations", "Citation Manager", bool(ps.get("citations"))),
        ("analytics", "Analytics", True),
        ("export", "LaTeX Export", True),
    ]
    active = st.session_state.active_stage
    for sid, label, done in stages:
        if done:
            cls = "step-done"
            icon = "✓"
        elif sid == active:
            cls = "step-active"
            icon = "→"
        else:
            cls = "step-idle"
            icon = "○"
        if st.button(f"{icon} {label}", key=f"nav_{sid}", use_container_width=True):
            st.session_state.active_stage = sid
            st.rerun()

    st.markdown("---")
    analytics = compute_analytics(ps)
    st.markdown(f"""
    <div style="font-size:0.75rem; color:#6b7fa3;">
    <div style="margin-bottom:0.3rem;">📄 PDFs loaded: <strong style="color:#93c5fd;">{analytics['pdfs_loaded']}</strong></div>
    <div style="margin-bottom:0.3rem;">✍️ Sections done: <strong style="color:#93c5fd;">{analytics['sections_done']}/7</strong></div>
    <div style="margin-bottom:0.3rem;">📝 Words: <strong style="color:#93c5fd;">{analytics['word_count']:,}</strong></div>
    <div>📚 References: <strong style="color:#93c5fd;">{analytics['reference_count']}</strong></div>
    </div>
    """, unsafe_allow_html=True)

# ─── MAIN CONTENT ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="forge-header">
    <h1>ResearchPaperForge AI</h1>
    <p>Multi-stage research paper generation · LaTeX export · Citation intelligence</p>
</div>
""", unsafe_allow_html=True)

stage = st.session_state.active_stage
ps = st.session_state.paper_state

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1: PDF UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
if stage == "upload":
    st.markdown('<div class="card-header">Stage 1 · PDF Ingestion</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_files = st.file_uploader(
            "Upload reference papers (PDF)",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload one or more PDF papers to build your knowledge base."
        )
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">Extraction Engine</div>', unsafe_allow_html=True)
        engine = st.radio("PDF Engine", ["PyMuPDF (recommended)", "pdfplumber", "Both"], index=0)
        st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_files:
        if st.button("Extract Papers", type="primary"):
            extracted = []
            progress = st.progress(0)
            status_text = st.empty()
            for i, f in enumerate(uploaded_files):
                status_text.text(f"Processing {f.name}...")
                cache_key = f"{f.name}_{f.size}"
                if cache_key in st.session_state.pdf_cache:
                    extracted.append(st.session_state.pdf_cache[cache_key])
                else:
                    file_bytes = f.read()
                    if "PyMuPDF" in engine or "Both" in engine:
                        data = extract_pdf_pymupdf(file_bytes, f.name)
                    else:
                        data = extract_pdf_pdfplumber(file_bytes, f.name)
                    if not data and "Both" in engine:
                        data = extract_pdf_pdfplumber(file_bytes, f.name)
                    if not data:
                        data = {"filename": f.name, "title": f.name, "abstract": "",
                                "authors": [], "keywords": [], "references": [],
                                "sections": {}, "raw_text": "", "word_count": 0}
                    st.session_state.pdf_cache[cache_key] = data
                    extracted.append(data)
                progress.progress((i + 1) / len(uploaded_files))

            ps["pdf_data"] = extracted
            ps["citations"] = parse_references_from_pdfs(extracted)
            status_text.text("")
            progress.empty()
            st.success(f"Extracted {len(extracted)} paper(s) · {len(ps['citations'])} references found")
            st.rerun()

    if ps["pdf_data"]:
        st.markdown("---")
        st.markdown(f'<div class="card-header">Extracted Papers ({len(ps["pdf_data"])})</div>', unsafe_allow_html=True)
        for paper in ps["pdf_data"]:
            with st.expander(f"📄 {paper.get('title', paper.get('filename', 'Unknown'))[:80]}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Authors:** {', '.join(paper.get('authors', []) or ['[not detected]'])}")
                    st.markdown(f"**Keywords:** {', '.join(paper.get('keywords', []) or ['[not detected]'])}")
                    st.markdown(f"**References found:** {len(paper.get('references', []))}")
                    st.markdown(f"**Sections:** {', '.join(paper.get('sections', {}).keys()) or '[none detected]'}")
                with c2:
                    st.markdown(f"**Word count:** {paper.get('word_count', 0):,}")
                    if paper.get("abstract"):
                        st.markdown("**Abstract excerpt:**")
                        st.caption(paper["abstract"][:400] + "...")

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2: KNOWLEDGE BASE
# ══════════════════════════════════════════════════════════════════════════════
elif stage == "knowledge":
    st.markdown('<div class="card-header">Stage 2 · Knowledge Base</div>', unsafe_allow_html=True)
    if not ps["pdf_data"]:
        st.info("Upload and extract PDFs first (Stage 1).")
    else:
        if st.button("Build Knowledge Base", type="primary"):
            with st.spinner("Indexing papers..."):
                kb = build_knowledge_base(ps["pdf_data"])
                st.session_state.knowledge_base = kb
            st.success("Knowledge base built successfully.")

        kb = st.session_state.knowledge_base
        if any(kb.values()):
            tab1, tab2, tab3, tab4 = st.tabs(["Methodology", "Dataset", "Citations", "Keywords"])
            with tab1:
                if kb["methodology_index"]:
                    for fname, text in kb["methodology_index"].items():
                        st.markdown(f"**{fname}**")
                        st.caption(text[:300] + "...")
                else:
                    st.caption("No methodology sections detected.")
            with tab2:
                if kb["dataset_index"]:
                    for fname, text in kb["dataset_index"].items():
                        st.markdown(f"**{fname}**")
                        st.caption(text[:300] + "...")
                else:
                    st.caption("No dataset sections detected.")
            with tab3:
                if kb["citation_index"]:
                    for fname, refs in kb["citation_index"].items():
                        st.markdown(f"**{fname}** — {len(refs)} references")
                else:
                    st.caption("No citations indexed.")
            with tab4:
                if kb["keyword_index"]:
                    for kw, sources in list(kb["keyword_index"].items())[:30]:
                        st.markdown(f"**{kw}** → {', '.join(sources[:3])}")
                else:
                    st.caption("No keywords indexed.")

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3: METADATA
# ══════════════════════════════════════════════════════════════════════════════
elif stage == "metadata":
    st.markdown('<div class="card-header">Stage 3 · Paper Metadata</div>', unsafe_allow_html=True)
    meta = st.session_state.metadata
    c1, c2 = st.columns(2)
    with c1:
        meta["title"] = st.text_input("Paper Title", value=meta["title"], placeholder="Enter the full paper title")
        meta["authors"] = st.text_input("Authors", value=meta["authors"], placeholder="Author 1, Author 2, Author 3")
        meta["affiliations"] = st.text_input("Affiliations", value=meta["affiliations"], placeholder="University / Institute names")
        meta["corresponding"] = st.text_input("Corresponding Author Email", value=meta["corresponding"])
    with c2:
        meta["keywords"] = st.text_input("Keywords", value=meta["keywords"], placeholder="keyword1, keyword2, keyword3")
        meta["paper_type"] = st.selectbox("Paper Type",
            ["Experimental", "Review", "Survey", "Comparative", "Case Study"],
            index=["Experimental","Review","Survey","Comparative","Case Study"].index(meta.get("paper_type","Experimental")))
        meta["journal"] = st.selectbox("Journal Format",
            ["IEEE", "ACM", "Springer", "Elsevier", "Generic"],
            index=["IEEE","ACM","Springer","Elsevier","Generic"].index(meta.get("journal","IEEE")))

    if st.button("Save Metadata"):
        ps["title"] = meta["title"]
        ps["authors"] = [a.strip() for a in meta["authors"].split(",") if a.strip()]
        ps["affiliations"] = [a.strip() for a in meta["affiliations"].split(",") if a.strip()]
        ps["paper_type"] = meta["paper_type"]
        ps["journal"] = meta["journal"]
        st.success("Metadata saved.")

    if ps["pdf_data"] and st.button("Auto-fill from PDFs"):
        first = ps["pdf_data"][0]
        if first.get("title"):
            meta["title"] = first["title"]
        if first.get("authors"):
            meta["authors"] = ", ".join(first["authors"])
        if first.get("keywords"):
            meta["keywords"] = ", ".join(first["keywords"])
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 4: EXPERIMENT DETAILS
# ══════════════════════════════════════════════════════════════════════════════
elif stage == "experiment":
    st.markdown('<div class="card-header">Stage 4 · Experiment Details</div>', unsafe_allow_html=True)
    exp = st.session_state.experiment_details
    c1, c2 = st.columns(2)
    with c1:
        exp["objective"] = st.text_area("Research Objective", value=exp["objective"], height=90,
                                         placeholder="What is the core objective of your research?")
        exp["problem"] = st.text_area("Problem Statement", value=exp["problem"], height=90,
                                       placeholder="Describe the problem you are solving.")
        exp["dataset"] = st.text_area("Dataset Description", value=exp["dataset"], height=90,
                                       placeholder="Name, size, source, and characteristics of datasets used.")
        exp["methodology"] = st.text_area("Methodology / Approach", value=exp["methodology"], height=90,
                                           placeholder="Algorithms, models, frameworks used.")
        exp["tools"] = st.text_area("Tools & Software", value=exp["tools"], height=70,
                                     placeholder="Python, TensorFlow, PyTorch, scikit-learn, etc.")
    with c2:
        exp["hardware"] = st.text_area("Hardware / Infrastructure", value=exp["hardware"], height=70,
                                        placeholder="GPU, CPU, RAM, cloud services.")
        exp["metrics"] = st.text_area("Evaluation Metrics", value=exp["metrics"], height=90,
                                       placeholder="Accuracy, F1-score, BLEU, RMSE, etc. with values.")
        exp["results_desc"] = st.text_area("Results Description", value=exp["results_desc"], height=100,
                                            placeholder="Summarize the quantitative and qualitative results.")
        exp["future_work"] = st.text_area("Future Work", value=exp["future_work"], height=90,
                                           placeholder="Limitations and directions for future research.")

    if st.button("Save Experiment Details"):
        st.success("Experiment details saved.")

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 5 & 6: SECTION GENERATION + EDITOR
# ══════════════════════════════════════════════════════════════════════════════
elif stage == "generate":
    st.markdown('<div class="card-header">Stage 5–6 · Section Generation & Editing</div>', unsafe_allow_html=True)
    if not st.session_state.api_key:
        st.error("Enter your Gemini API key in the sidebar to generate sections.")
    else:
        meta = st.session_state.metadata
        exp = st.session_state.experiment_details
        pdf_data = ps["pdf_data"]

        def abstracts_summary():
            parts = []
            for p in pdf_data[:5]:
                if p.get("title"):
                    parts.append(f"Title: {p['title']}")
                if p.get("abstract"):
                    parts.append(f"Abstract: {p['abstract'][:400]}")
            return "\n---\n".join(parts) if parts else "[No reference papers uploaded]"

        def refs_summary():
            refs = []
            for p in pdf_data[:5]:
                refs.extend(p.get("references", [])[:10])
            return "\n".join(refs[:30]) if refs else "[No references extracted]"

        def methodology_snippets():
            kb = st.session_state.knowledge_base
            parts = []
            for fname, text in list(kb.get("methodology_index", {}).items())[:3]:
                parts.append(f"[{fname}]: {text[:300]}")
            return "\n".join(parts) if parts else "[No methodology sections detected]"

        JOURNAL_STYLE = meta.get("journal", "IEEE")
        PAPER_TYPE = meta.get("paper_type", "Experimental")
        PAPER_TITLE = meta.get("title") or "[Title not set]"
        KEYWORDS = meta.get("keywords") or "[Keywords not set]"

        sections_config = [
            {
                "key": "introduction",
                "label": "Introduction",
                "prompt": lambda: f"""You are an academic writing assistant. Write a professional Introduction section for a {PAPER_TYPE} paper titled "{PAPER_TITLE}" formatted for {JOURNAL_STYLE} style.

Keywords: {KEYWORDS}

Research Objective: {exp.get('objective','[USER INPUT REQUIRED]')}
Problem Statement: {exp.get('problem','[USER INPUT REQUIRED]')}

Reference papers (use for context only, do NOT fabricate citations):
{abstracts_summary()}

Write 4-6 paragraphs:
1. Broad motivation and importance
2. Problem statement and research gap
3. Limitations of existing approaches
4. Contributions and objectives of this work
5. Paper organization

Rules:
- Do NOT fabricate citations or statistics not provided.
- Use [USER INPUT REQUIRED] where specific data is missing.
- Academic tone, no bullet points, flowing prose.
- Do not include section heading."""
            },
            {
                "key": "literature_review",
                "label": "Literature Review",
                "prompt": lambda: f"""Write a Literature Review section for a {PAPER_TYPE} paper on "{PAPER_TITLE}" for {JOURNAL_STYLE} style.

Reference paper titles and abstracts:
{abstracts_summary()}

Extracted references:
{refs_summary()}

Write a structured literature review:
- Thematic groupings based on the reference papers above
- Compare methodologies and findings
- Identify research gaps
- Use only information from provided references. 
- If author/year not confirmed, write: [USER INPUT REQUIRED - cite source]
- 5-8 paragraphs, academic prose.
- Do not include section heading."""
            },
            {
                "key": "methodology",
                "label": "Methodology",
                "prompt": lambda: f"""Write a Methodology section for a {PAPER_TYPE} research paper titled "{PAPER_TITLE}" for {JOURNAL_STYLE}.

Methodology provided by researcher:
{exp.get('methodology','[USER INPUT REQUIRED]')}

Dataset: {exp.get('dataset','[USER INPUT REQUIRED]')}
Tools & Software: {exp.get('tools','[USER INPUT REQUIRED]')}
Hardware: {exp.get('hardware','[USER INPUT REQUIRED]')}

Related methodology from references:
{methodology_snippets()}

Write clear, reproducible methodology description:
- System overview and architecture
- Data collection and preprocessing
- Model/algorithm description
- Implementation details
- Use only provided information; insert [USER INPUT REQUIRED] for gaps.
- 4-6 paragraphs. Do not include section heading."""
            },
            {
                "key": "experimental_setup",
                "label": "Experimental Setup",
                "prompt": lambda: f"""Write an Experimental Setup section for a {PAPER_TYPE} paper titled "{PAPER_TITLE}".

Dataset: {exp.get('dataset','[USER INPUT REQUIRED]')}
Tools: {exp.get('tools','[USER INPUT REQUIRED]')}
Hardware: {exp.get('hardware','[USER INPUT REQUIRED]')}
Metrics: {exp.get('metrics','[USER INPUT REQUIRED]')}

Write:
- Dataset details (size, splits, source)
- Baseline configurations
- Evaluation metrics definitions
- Training/test environment
- Hyperparameters if provided
Use [USER INPUT REQUIRED] for missing specifics. 3-5 paragraphs. Do not include section heading."""
            },
            {
                "key": "results",
                "label": "Results",
                "prompt": lambda: f"""Write a Results section for a {PAPER_TYPE} paper titled "{PAPER_TITLE}".

Metrics and values provided: {exp.get('metrics','[USER INPUT REQUIRED]')}
Results description: {exp.get('results_desc','[USER INPUT REQUIRED]')}

Write:
- Quantitative results using ONLY the numbers provided above
- Comparison with baselines if mentioned
- Table descriptions (e.g., "Table 1 shows...") as placeholders
- Key findings summary
CRITICAL: Do NOT invent any numerical results. Use [USER INPUT REQUIRED] for any missing values.
4-6 paragraphs. Do not include section heading."""
            },
            {
                "key": "discussion",
                "label": "Discussion",
                "prompt": lambda: f"""Write a Discussion section for a {PAPER_TYPE} paper titled "{PAPER_TITLE}".

Results: {exp.get('results_desc','[USER INPUT REQUIRED]')}
Methodology: {exp.get('methodology','[USER INPUT REQUIRED]')}
Previously generated results section: {ps.get('results','')[:500] or '[not yet generated]'}

Write:
- Interpretation of results
- Why the approach works (or limitations found)
- Comparison with related work (thematic, avoid fabricating citations)
- Implications and significance
- Threats to validity
3-5 paragraphs. Do not include section heading."""
            },
            {
                "key": "conclusion",
                "label": "Conclusion",
                "prompt": lambda: f"""Write a Conclusion section for a {PAPER_TYPE} paper titled "{PAPER_TITLE}".

Summary of generated sections:
- Introduction summary: {ps.get('introduction','')[:300] or '[not generated]'}
- Results summary: {ps.get('results','')[:300] or '[not generated]'}
- Discussion summary: {ps.get('discussion','')[:300] or '[not generated]'}
Future work: {exp.get('future_work','[USER INPUT REQUIRED]')}

Write:
- Summary of contributions
- Key findings reiterated concisely
- Limitations
- Future research directions
2-4 paragraphs. Do not include section heading."""
            },
        ]

        for i, sec in enumerate(sections_config):
            st.markdown(f'<div class="section-badge">{sec["label"]}</div>', unsafe_allow_html=True)
            c1, c2 = st.columns([1, 4])
            with c1:
                status = "Generated" if ps.get(sec["key"]) else "Not generated"
                cls = "status-done" if ps.get(sec["key"]) else "status-empty"
                st.markdown(f'<span class="status-pill {cls}">{status}</span>', unsafe_allow_html=True)
                if st.button(f"Generate", key=f"gen_{sec['key']}"):
                    with st.spinner(f"Generating {sec['label']}..."):
                        result = call_gemini(sec["prompt"](), max_tokens=1800)
                    ps[sec["key"]] = result
                    st.rerun()
                if ps.get(sec["key"]):
                    if st.button("Clear", key=f"clr_{sec['key']}"):
                        ps[sec["key"]] = ""
                        st.rerun()
            with c2:
                if ps.get(sec["key"]):
                    new_val = st.text_area(
                        f"Edit {sec['label']}",
                        value=ps[sec["key"]],
                        height=180,
                        key=f"edit_{sec['key']}",
                        label_visibility="collapsed"
                    )
                    if new_val != ps[sec["key"]]:
                        ps[sec["key"]] = new_val
                else:
                    st.caption(f"{sec['label']} not yet generated. Click Generate.")

            st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 7: CITATIONS
# ══════════════════════════════════════════════════════════════════════════════
elif stage == "citations":
    st.markdown('<div class="card-header">Stage 7 · Citation Intelligence</div>', unsafe_allow_html=True)
    citations = ps.get("citations", [])
    if not citations:
        st.info("Extract PDFs first to populate citations (Stage 1).")
    else:
        search_q = st.text_input("Search citations", placeholder="Search by title, author, or year...")
        filtered = [c for c in citations if
                    not search_q or search_q.lower() in c.get("title","").lower()
                    or search_q.lower() in c.get("authors","").lower()
                    or search_q in c.get("year","")]

        st.markdown(f'<div class="card-header">{len(filtered)} of {len(citations)} references</div>', unsafe_allow_html=True)

        if pd is not None:
            df = pd.DataFrame(filtered)[["title","authors","year","doi","source"]]
            df.columns = ["Title","Authors","Year","DOI","Source PDF"]
            st.dataframe(df, use_container_width=True, height=350)
        else:
            for c in filtered[:50]:
                st.markdown(f'<div class="cite-row"><b>{c.get("year","?")}</b> · {c.get("title","")[:100]} <span style="color:#4a5568">— {c.get("source","")}</span></div>', unsafe_allow_html=True)

        st.markdown("---")
        if st.button("Generate BibTeX Preview"):
            bib = generate_bibtex(filtered[:30])
            st.markdown('<div class="latex-preview">' + bib.replace('\n','<br>') + '</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="card-header">Add Manual Reference</div>', unsafe_allow_html=True)
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            m_title = st.text_input("Title", key="m_title")
        with mc2:
            m_authors = st.text_input("Authors", key="m_authors")
        with mc3:
            m_year = st.text_input("Year", key="m_year")
        m_doi = st.text_input("DOI (optional)", key="m_doi")
        if st.button("Add Reference"):
            if m_title:
                ps["citations"].append({"title": m_title, "authors": m_authors, "year": m_year, "doi": m_doi, "source": "manual"})
                st.success("Reference added.")
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 8: ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif stage == "analytics":
    st.markdown('<div class="card-header">Stage 8 · Paper Analytics</div>', unsafe_allow_html=True)
    analytics = compute_analytics(ps)

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card"><div class="kpi-value">{analytics['word_count']:,}</div><div class="kpi-label">Words</div></div>
        <div class="kpi-card"><div class="kpi-value">{analytics['char_count']:,}</div><div class="kpi-label">Characters</div></div>
        <div class="kpi-card"><div class="kpi-value">{analytics['estimated_pages']}</div><div class="kpi-label">Est. Pages</div></div>
        <div class="kpi-card"><div class="kpi-value">{analytics['reference_count']}</div><div class="kpi-label">References</div></div>
        <div class="kpi-card"><div class="kpi-value">{analytics['sections_done']}/7</div><div class="kpi-label">Sections Done</div></div>
        <div class="kpi-card"><div class="kpi-value">{analytics['pdfs_loaded']}</div><div class="kpi-label">PDFs Loaded</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    sections_status = {
        "Introduction": bool(ps.get("introduction")),
        "Literature Review": bool(ps.get("literature_review")),
        "Methodology": bool(ps.get("methodology")),
        "Exp. Setup": bool(ps.get("experimental_setup")),
        "Results": bool(ps.get("results")),
        "Discussion": bool(ps.get("discussion")),
        "Conclusion": bool(ps.get("conclusion")),
    }

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="card-header">Section Completion</div>', unsafe_allow_html=True)
        for sec_name, done in sections_status.items():
            cls = "status-done" if done else "status-pending"
            label = "Generated" if done else "Pending"
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid #1e2535;"><span style="color:#c9d1e0;font-size:0.85rem;">{sec_name}</span><span class="status-pill {cls}">{label}</span></div>', unsafe_allow_html=True)

    with c2:
        if PLOTLY_AVAILABLE:
            done_count = sum(sections_status.values())
            fig = go.Figure(go.Pie(
                labels=["Generated", "Remaining"],
                values=[done_count, 7 - done_count],
                hole=0.6,
                marker_colors=["#3b6cf8", "#1e2535"],
                textinfo="none",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                margin=dict(t=0,b=0,l=0,r=0),
                height=200,
                annotations=[dict(text=f"{done_count}/7", x=0.5, y=0.5, font_size=22,
                                  font_color="#4f8ef7", showarrow=False)]
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            done_count = sum(sections_status.values())
            bar = "█" * done_count + "░" * (7 - done_count)
            st.markdown(f'<div style="font-family:monospace;font-size:1.2rem;color:#3b6cf8;">{bar}</div>', unsafe_allow_html=True)
            st.caption(f"{done_count}/7 sections generated")

    st.markdown("---")
    st.markdown('<div class="card-header">Word Distribution per Section</div>', unsafe_allow_html=True)
    section_keys = ["introduction","literature_review","methodology","experimental_setup","results","discussion","conclusion"]
    section_words = {k: len(ps.get(k,"").split()) for k in section_keys}
    if PLOTLY_AVAILABLE and any(section_words.values()):
        fig2 = go.Figure(go.Bar(
            x=list(section_words.keys()),
            y=list(section_words.values()),
            marker_color="#3b6cf8",
            marker_line_color="#2d5ca8",
            marker_line_width=1,
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#0f1117",
            font_color="#6b7fa3",
            xaxis=dict(gridcolor="#1e2535", tickfont=dict(size=10)),
            yaxis=dict(gridcolor="#1e2535"),
            margin=dict(t=10,b=30,l=40,r=10),
            height=220,
        )
        st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 9 & 10: LATEX EXPORT
# ══════════════════════════════════════════════════════════════════════════════
elif stage == "export":
    st.markdown('<div class="card-header">Stage 9–10 · LaTeX Project & ZIP Export</div>', unsafe_allow_html=True)
    meta = st.session_state.metadata
    exp = st.session_state.experiment_details

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Project Overview**")
        st.markdown(f"- Title: `{meta.get('title') or '[not set]'}`")
        st.markdown(f"- Journal: `{meta.get('journal','IEEE')}`")
        st.markdown(f"- Paper Type: `{meta.get('paper_type','Experimental')}`")
        st.markdown(f"- Sections generated: `{sum(1 for k in ['introduction','literature_review','methodology','experimental_setup','results','discussion','conclusion'] if ps.get(k))}/7`")
        st.markdown(f"- References: `{len(ps.get('citations',[]))}`")
    with c2:
        st.markdown("**LaTeX File Structure**")
        st.code("""project/
├── main.tex
├── references.bib
└── sections/
    ├── introduction.tex
    ├── literature_review.tex
    ├── methodology.tex
    ├── experimental_setup.tex
    ├── results.tex
    ├── discussion.tex
    └── conclusion.tex""", language="text")

    st.markdown("---")
    if st.button("Generate LaTeX Project", type="primary"):
        with st.spinner("Generating LaTeX files..."):
            latex_proj = generate_latex_project(ps, meta, exp)
            ps["latex_project"] = latex_proj
        st.success("LaTeX project generated successfully.")

    if ps.get("latex_project"):
        lp = ps["latex_project"]
        tab1, tab2, tab3 = st.tabs(["main.tex Preview", "references.bib Preview", "Section Files"])
        with tab1:
            st.markdown('<div class="latex-preview">' + lp.get("main.tex","").replace('\n','<br>').replace(' ','&nbsp;') + '</div>', unsafe_allow_html=True)
        with tab2:
            bib_preview = lp.get("references.bib","")[:2000]
            st.markdown('<div class="latex-preview">' + bib_preview.replace('\n','<br>').replace(' ','&nbsp;') + '</div>', unsafe_allow_html=True)
        with tab3:
            for sec_name, sec_content in lp.get("sections",{}).items():
                with st.expander(f"{sec_name}.tex"):
                    st.markdown('<div class="latex-preview">' + sec_content[:800].replace('\n','<br>').replace(' ','&nbsp;') + '...</div>', unsafe_allow_html=True)

        st.markdown("---")
        zip_bytes = create_zip(lp)
        paper_title_safe = re.sub(r'[^a-zA-Z0-9_-]', '_', meta.get("title","paper"))[:40]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{paper_title_safe}_{timestamp}.zip"
        st.download_button(
            label="Download project.zip",
            data=zip_bytes,
            file_name=filename,
            mime="application/zip",
        )
        st.caption(f"ZIP size: {len(zip_bytes)/1024:.1f} KB · {len(lp.get('sections',{}))+2} files")

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center;font-size:0.72rem;color:#2a3045;padding:0.5rem 0;">'
    'ResearchPaperForge AI · Multi-stage generation pipeline · '
    'Never fabricates citations or numerical results'
    '</div>',
    unsafe_allow_html=True
)