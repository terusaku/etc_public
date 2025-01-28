from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
import os
from typing import List, Dict

class PDFGuidelinesQA:
    def __init__(self, openai_api_key: str):
        """
        Initialize the PDF Q&A system.
        
        Args:
            openai_api_key (str): Your OpenAI API key
        """
        os.environ["OPENAI_API_KEY"] = openai_api_key
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")
        self.vector_store = None
        
    def load_pdf(self, pdf_path: str) -> None:
        """
        Load and process a PDF file.
        
        Args:
            pdf_path (str): Path to the PDF file
        """
        # Load PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        texts = text_splitter.split_documents(documents)
        
        # Create vector store
        self.vector_store = FAISS.from_documents(texts, self.embeddings)
        
    def setup_qa_chain(self) -> None:
        """
        Set up the question-answering chain.
        """
        if not self.vector_store:
            raise ValueError("Please load a PDF first using load_pdf()")
            
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 3}
            ),
            return_source_documents=True
        )
        
    def get_answer(self, question: str) -> Dict:
        """
        Get answer for a single question.
        
        Args:
            question (str): The question to be answered
            
        Returns:
            Dict: Contains the answer and source documents
        """
        if not hasattr(self, 'qa_chain'):
            raise ValueError("Please set up the QA chain first using setup_qa_chain()")
            
        result = self.qa_chain({"query": question})
        
        return {
            "question": question,
            "answer": result["result"],
            "sources": [doc.page_content for doc in result["source_documents"]]
        }
        
    def batch_qa(self, questions: List[str]) -> List[Dict]:
        """
        Process multiple questions in batch.
        
        Args:
            questions (List[str]): List of questions to be answered
            
        Returns:
            List[Dict]: List of answers with their corresponding questions and sources
        """
        return [self.get_answer(question) for question in questions]

# Example usage
def main():
    # Initialize the system
    qa_system = PDFGuidelinesQA("your-openai-api-key")
    
    # Load and process PDF
    qa_system.load_pdf("guidelines.pdf")
    qa_system.setup_qa_chain()
    
    # Single question
    question = "What is the procedure for handling customer complaints?"
    answer = qa_system.get_answer(question)
    print(f"Q: {answer['question']}")
    print(f"A: {answer['answer']}\n")
    
    # Multiple questions
    questions = [
        "What are the safety protocols?",
        "What are the reporting requirements?",
        "What is the escalation process?"
    ]
    
    answers = qa_system.batch_qa(questions)
    for answer in answers:
        print(f"Q: {answer['question']}")
        print(f"A: {answer['answer']}\n")

if __name__ == "__main__":
    main()
    