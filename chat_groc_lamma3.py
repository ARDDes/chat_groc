import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
import time
import tempfile
from dotenv import load_dotenv

# # Load environment variables
load_dotenv()
groq_api_key = os.getenv('GROQ_API_KEY')
# HUGGING_FACE_TOKEN = os.getenv("HUGGING_FACE_TOKEN")
hg=st.secrets.huggingface_api.token
os.environ["HUGGINGFACEHUB_API_TOKEN"] = hg
option = st.selectbox(
    'Which model you want to use',
    ('FPHam/MissLizzy_7b_HF', 'recogna-nlp/Phi-Bode', 'meta-llama/Meta-Llama-3-8B'))

st.write('You selected:', option)
# Initialize session state variables if not already done
if 'embeddings' not in st.session_state:
    st.session_state.embeddings = HuggingFaceEmbeddings()

if 'loader' not in st.session_state:
    st.session_state.loader = None

if 'docs' not in st.session_state:
    st.session_state.docs = None

if 'text_splitter' not in st.session_state:
    st.session_state.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

if 'final_documents' not in st.session_state:
    st.session_state.final_documents = None

if 'vectors' not in st.session_state:
    st.session_state.vectors = None

# File upload widget
uploaded_file = st.file_uploader("File upload", type="pdf")
if uploaded_file is not None:
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getvalue())

    # Load the PDF and process it
    st.session_state.loader = PyPDFLoader(file_path)
    st.session_state.docs = st.session_state.loader.load()
    st.session_state.final_documents = st.session_state.text_splitter.split_documents(st.session_state.docs[:50])
    st.session_state.vectors = FAISS.from_documents(st.session_state.final_documents, st.session_state.embeddings)
    
    content = st.session_state.loader.load()
    st.write(content)
    st.success(f"Successfully loaded the PDF: {uploaded_file.name}")

# Ensure all required session state variables are initialized before using them
if st.session_state.vectors is not None:
    st.title("ChatGroq Demo")
    llm = ChatGroq(groq_api_key=groq_api_key, model_name="mixtral-8x7b-32768")

    # Choose the appropriate prompt template based on the selected model
    if option == 'FPHam/MissLizzy_7b_HF':
        prompt_template = """
        You are a helpful and knowledgeable assistant. Please provide a detailed and accurate response to the following question based on the given context.

        <context>
        {context}
        <context>

        Question: {input}
        Answer: 
        """
    elif option == 'recogna-nlp/Phi-Bode':
        prompt_template = """
        You are an expert in technical and analytical problem-solving. Use the context provided to answer the question precisely and comprehensively.

        <context>
        {context}
        <context>

        Question: {input}
        Detailed Answer: 
        """
    else:  # meta-llama/Meta-Llama-3-8B
        prompt_template = """
        You are a creative and insightful assistant. Use the given context to provide an in-depth and thoughtful response to the following question.

        <context>
        {context}
        <context>

        Question: {input}
        Insightful Answer: 
        """



    prompt = ChatPromptTemplate.from_template(prompt_template)
    document_chain = create_stuff_documents_chain(llm, prompt)
    retriever = st.session_state.vectors.as_retriever()
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    user_prompt = st.text_input("Input your prompt here")

    if user_prompt:
        start = time.process_time()
        response = retrieval_chain.invoke({"input": user_prompt})
        st.write("Response time:", time.process_time() - start)
        st.write(response['answer'])
        
#         # With a Streamlit expander
#         with st.expander("Document Similarity Search"):
#             # Find the relevant chunks
#             for i, doc in enumerate(response["context"]):
#                 st.write(doc.page_content)
#                 st.write("--------------------------------")
# else:
#     st.warning("Please upload a PDF file to proceed.")
