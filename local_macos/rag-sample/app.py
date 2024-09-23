from flask import Flask, request, render_template, jsonify
import fitz  # PyMuPDF
import os
# from langchain.vectorstores import Chroma
# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
# from langchain.embeddings import HuggingFaceEmbeddings
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
# from langchain_community.llms import HuggingFacePipeline
from langchain_huggingface import HuggingFacePipeline
from transformers import pipeline, AutoTokenizer, AutoModel
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 設定の変更
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

# qa = VectorDBQA(vectorstore=index, llm=llm)
# qa = RetrievalQA(vectorstore=index, llm=llm)

prompt_template = '''Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Answer:'''

PROMPT = PromptTemplate(
    template=prompt_template, input_variables=["context", "question"]
)

# 使用するベクトルストアの変更
# index = Chroma(persist_directory='db')
# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
index = Chroma(persist_directory='db', embedding_function=embeddings)
# QA パイプラインの設定
qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")
llm = HuggingFacePipeline(pipeline=qa_pipeline)
# RetrievalQAの設定
qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=index.as_retriever(),
    return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT}
)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def handle_upload():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        extracted_text = extract_text(filepath)
        embeddings = embed_text([extracted_text])
        # index.add_texts([extracted_text], embeddings)
        index.add_texts([extracted_text])
        return jsonify({'response': 'File uploaded and processed successfully'})

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    response = qa({"query": user_input})
    return jsonify({'response': response['result']})


def extract_text(filepath):
    text = ""
    if filepath.endswith('.pdf'):
        with fitz.open(filepath) as doc:
            for page in doc:
                text += page.get_text()
    elif filepath.endswith('.txt'):
        with open(filepath, 'r', encoding='utf-8') as file:
            text = file.read()
    return text

def embed_text(texts):
    embeddings = []
    for text in texts:
        inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True)
        outputs = model(**inputs)
        embeddings.append(outputs.last_hidden_state.mean(dim=1).detach().numpy())
    return np.vstack(embeddings)


if __name__ == '__main__':
    app.run(debug=True)
