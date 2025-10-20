import streamlit as st
import PyPDF2
import docx2txt
import re
import openai

# -------------------------------
# OpenAI API Key (Directly)
# -------------------------------
openai.api_key = "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"

# -------------------------------
# Page Setup
# -------------------------------
st.set_page_config(page_title="ATS Resume Checker + AI Bot", page_icon="📄🤖", layout="wide")
st.title("📄 ATS Resume Checker + AI Bot 🚀")

# -------------------------------
# Functions
# -------------------------------
def get_text_from_file(file):
    text = ""
    file_type = file.name.split(".")[-1].lower()
    if file_type == "pdf":
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    elif file_type == "docx":
        text = docx2txt.process(file)
    return text

def extract_keywords(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    stopwords = ["and","or","the","a","an","in","on","with","for","to","of"]
    return set([w for w in text.split() if w not in stopwords])

def calculate_ats(resume_text, jd_text):
    resume_keywords = extract_keywords(resume_text)
    jd_keywords = extract_keywords(jd_text)
    matches = resume_keywords.intersection(jd_keywords)
    missing = jd_keywords - resume_keywords
    ats_score = int((len(matches)/len(jd_keywords))*100) if jd_keywords else 0
    priority_keywords = {"python","java","sql","aws"}
    weighted_score = min(ats_score + len(matches.intersection(priority_keywords))*2,100)
    return ats_score, weighted_score, matches, missing

# -------------------------------
# Layout
# -------------------------------
left_col, right_col = st.columns([2,1])

# -------------------------------
# Left Column: ATS + Compare + Summary
# -------------------------------
with left_col:
    st.header("📂 Resume Upload & ATS Analysis")

    # Single Resume
    resume_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf","docx"])
    resume_text = get_text_from_file(resume_file) if resume_file else ""

    jd_text = st.text_area("Paste Job Description here", height=150)

    if resume_file and jd_text.strip():
        ats_score, weighted_score, matches, missing = calculate_ats(resume_text, jd_text)

        st.subheader("🔹 ATS Score")
        st.write(f"Resume matches **{ats_score}%** of JD keywords")
        st.progress(ats_score)

        st.subheader("🔹 Weighted ATS Score")
        st.write(f"{weighted_score}% (priority skills considered)")

        st.subheader("🔹 Matching Keywords")
        st.write(", ".join(matches) if matches else "No keywords matched")

        st.subheader("🔹 Missing Keywords")
        st.write(", ".join(missing) if missing else "No missing keywords! 🎉")

        # -------------------------------
        # AI-generated Resume Summary
        # -------------------------------
        st.subheader("📝 Resume Summary (AI)")
        with st.spinner("Generating summary..."):
            try:
                summary_resp = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert career coach."},
                        {"role": "user", "content": f"Summarize this resume and highlight key skills:\n{resume_text}"}
                    ],
                    temperature=0.7
                )
                summary = summary_resp["choices"][0]["message"]["content"]
                st.write(summary)
            except Exception as e:
                st.error(f"AI Error: {e}")

    # Compare Two Resumes
    st.subheader("📊 Compare Two Resumes")
    comp_file1 = st.file_uploader("Upload First Resume", type=["pdf","docx"], key="comp1")
    comp_file2 = st.file_uploader("Upload Second Resume", type=["pdf","docx"], key="comp2")
    comp_jd = st.text_area("Paste JD for comparison", key="comp_jd")

    if comp_file1 and comp_file2 and comp_jd.strip():
        text1 = get_text_from_file(comp_file1)
        text2 = get_text_from_file(comp_file2)
        ats1, weighted1, matches1, missing1 = calculate_ats(text1, comp_jd)
        ats2, weighted2, matches2, missing2 = calculate_ats(text2, comp_jd)

        st.write(f"**Resume 1 ATS:** {ats1}% | Matches: {', '.join(matches1)}")
        st.write(f"**Resume 2 ATS:** {ats2}% | Matches: {', '.join(matches2)}")

        if ats1 > ats2:
            st.success("✅ Resume 1 is a better match")
        elif ats2 > ats1:
            st.success("✅ Resume 2 is a better match")
        else:
            st.info("⚖️ Both resumes match equally")

# -------------------------------
# Right Column: AI Bot
# -------------------------------
with right_col:
    st.header("💬 AI Resume Assistant")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Ask me anything about resumes/ATS:")

    if st.button("Send"):
        if user_input.strip():
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.spinner("🤖 Thinking..."):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "system", "content": "You are an expert career coach giving resume and ATS advice."}]
                                 + st.session_state.chat_history,
                        temperature=0.7
                    )
                    answer = response["choices"][0]["message"]["content"]
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"AI Error: {e}")

    # Display chat history
    for msg in st.session_state.chat_history:
        role = "🧑 You" if msg["role"] == "user" else "🤖 AI"
        st.markdown(f"**{role}:** {msg['content']}")
