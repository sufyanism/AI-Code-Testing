import streamlit as st
import ast
import json
import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
import base64

# ------------------ 1. Configuration & API Setup ------------------
load_dotenv()

st.set_page_config(page_title="Zeba Academy | Multi-Lang AI Forensics", layout="wide", initial_sidebar_state="collapsed")

# --- 2. Enhanced CSS (Fixing Overlap & Layout) ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stDecoration"] {display: none;}

    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 2rem;
        background-color: #ffffff;
        border-bottom: 2px solid #f0f2f6;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 80px;
        z-index: 9999;
    }
    
    .logo-text {
        font-size: 24px;
        font-weight: bold;
        color: #0e1117;
        font-family: 'Helvetica Neue', sans-serif;
    }

    .header-container img {
        height: 60px;
        width: auto;
    }

    .footer-container {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f8f9fa;
        color: #31333F;
        text-align: center;
        padding: 10px 0;
        font-weight: 500;
        border-top: 1px solid #dee2e6;
        z-index: 9999;
    }

    .stApp {
        margin-top: 80px;
        margin-bottom: 60px;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 10rem !important;
    }
    
    /* Scrollable error container */
    .error-scroll {
        max-height: 150px;
        overflow-y: auto;
        background-color: #fff2f2;
        border: 1px solid #ff4b4b;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. Header & Footer Implementation ---

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None

img_path = "./Logo.png"
img_base64 = get_base64_image(img_path)

header_html = f"""
    <div class="header-container">
        <div class="logo-text">Zeba Academy</div>
        <div style="display: flex;">
            {f'<img src="data:image/png;base64,{img_base64}" />' if img_base64 else ''}
        </div>
    </div>
"""
st.markdown(header_html, unsafe_allow_html=True)
st.markdown('<div class="footer-container">© 2026 Zeba Academy | Empowering Academic Integrity</div>', unsafe_allow_html=True)

# --- 4. Logic Functions ---

api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    # Gemini 1.5 Flash is highly recommended for speed and efficiency
    model = genai.GenerativeModel("gemini-2.5-flash")
else:
    st.error("🔑 Gemini API Key missing!")

def extract_python_ast(code_text):
    try:
        tree = ast.parse(code_text)
        node_types = [type(node).__name__ for node in ast.walk(tree)]
        num_nodes = len(node_types)
        unique_nodes = len(set(node_types))
        score = 0
        ratio = unique_nodes / max(num_nodes, 1)
        if ratio < 0.25: score += 30
        if node_types.count("FunctionDef") == 1: score += 20
        if num_nodes > 150: score += 10
        return {"score": min(score, 100), "nodes": num_nodes, "ratio": f"{ratio:.2f}"}
    except:
        return None

def analyze_with_gemini(code_text, file_ext):
    system_prompt = f"Analyze this {file_ext} code for AI patterns. Return ONLY JSON with keys: 'overall_ai_probability', 'suspected_source_site', 'reasoning', 'text_summary'."
    user_prompt = f"Code:\n```{file_ext}\n{code_text}\n```"
    response = model.generate_content([system_prompt, user_prompt])
    match = re.search(r"\{[\s\S]*\}", response.text)
    return json.loads(match.group(0)) if match else None

# --- 5. UI Layout ---

st.title("🧠 Universal AI Code Forensics")
st.markdown("Deep pattern analysis for **Python, JS, Java, PHP, HTML, CSS, and more.**")

uploaded_file = st.file_uploader(
    "Upload source code", 
    type=["py", "js", "java", "php", "html", "css", "ts", "cpp", "c", "cs"]
)

if uploaded_file:
    code_content = uploaded_file.read().decode("utf-8", errors="ignore")
    file_extension = uploaded_file.name.split(".")[-1].lower()
    
    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        st.subheader(f"📄 Source: {uploaded_file.name}")
        st.code(code_content, language=file_extension, line_numbers=True)

    with col_right:
        st.subheader("🛠️ Forensic Tools")
        btn_ast, btn_ai = st.columns(2)
        
        is_python = file_extension == "py"
        run_ast = btn_ast.button("🚀 Structural Scan", use_container_width=True, disabled=not is_python)
        run_ai = btn_ai.button("✨ Deep AI Scan", use_container_width=True, type="primary")

        # Result Section
        if run_ast and is_python:
            st.markdown("---")
            data = extract_python_ast(code_content)
            if data:
                st.info(f"**Structural Analysis:** Found {data['nodes']} nodes with a complexity ratio of {data['ratio']}.")
                st.metric("Heuristic Score", f"{data['score']}%")
                st.progress(data['score'] / 100)
            else:
                st.error("Could not parse Python AST.")

        if run_ai:
            st.markdown("---")
            with st.spinner(f"Analyzing {file_extension}..."):
                try:
                    res = analyze_with_gemini(code_content, file_extension)
                    if res:
                        # Text Result ABOVE visual results
                        st.subheader("📝 Forensic Summary")
                        st.write(res.get('text_summary', "No summary provided."))
                        
                        st.markdown("---")
                        
                        # Visual Metrics
                        st.metric("AI Confidence Score", f"{res['overall_ai_probability']}%")
                        st.progress(res['overall_ai_probability'] / 100)
                        st.success(f"**Likely Origin:** {res['suspected_source_site']}")
                        st.write(f"**Detailed Reasoning:** {res['reasoning']}")

                except Exception as e:
                    st.error("⚠️ API Limit or Error Detected")
                    # Scrollable error output
                    error_msg = str(e)
                    st.markdown(f'<div class="error-scroll">{error_msg}</div>', unsafe_allow_html=True)
                    st.warning("If this is a 429 error, the API quota is exhausted. Please try again in a few minutes.")