from flask import Flask, request, render_template, jsonify
import fitz  # PyMuPDF
import os
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
# from langchain.chat_models import ChatAnthropic
from langchain_anthropic import ChatAnthropic
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Claude client
# anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
claude = ChatAnthropic(
    model="claude-3-sonnet-20240229",
    api_key=os.getenv('ANTHROPIC_API_KEY'),
    temperature=0.7,
    max_tokens=10000,
)

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

# Initialize vector store
vectorstore = Chroma(
    persist_directory='db',
    embedding_function=embeddings
)

# Define prompt template
prompt_template = '''Use the following pieces of context to answer the question at the end. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context: {context}

Question: {question}
Answer: Let me help you with that based on the provided context.'''

PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"]
)

# Initialize QA chain
qa = RetrievalQA.from_chain_type(
    llm=claude,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    ),
    return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT}
)

def extract_text(filepath):
    """Extract text from PDF or text files."""
    text = ""
    try:
        if filepath.endswith('.pdf'):
            with fitz.open(filepath) as doc:
                for page in doc:
                    text += page.get_text()
        elif filepath.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8') as file:
                text = file.read()
        return text.strip()
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None

def process_document(text):
    """Process and store document text in chunks."""
    try:
        # Split text into chunks of approximately 1000 characters
        chunk_size = 1000
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        
        # Add chunks to vector store
        vectorstore.add_texts(chunks)
        return True
    except Exception as e:
        print(f"Error processing document: {e}")
        return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def handle_upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and file.filename.lower().endswith(('.pdf', '.txt')):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            
            # Extract and process text
            extracted_text = extract_text(filepath)
            if not extracted_text:
                return jsonify({'error': 'Failed to extract text from file'}), 400
            
            if process_document(extracted_text):
                return jsonify({'response': 'File uploaded and processed successfully'})
            else:
                return jsonify({'error': 'Failed to process document'}), 500
        else:
            return jsonify({'error': 'Invalid file type'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        user_input = data['message']
        response = qa({"query": user_input})
        
        return jsonify({
            'response': response['result'],
            'source_documents': [doc.page_content for doc in response['source_documents']]
        })
        
    except Exception as e:
        return jsonify({'error': f'Chat failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
