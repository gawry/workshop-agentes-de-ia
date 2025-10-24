"""
Document ingestion script for RAG evaluation demo.
Loads Petrobras reports into Chroma DB for vector search.
"""
import os
from pathlib import Path
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from config import (
    CHROMA_DB_PATH, 
    RELATORIO_FINANCEIRO, 
    RELATORIO_ADMINISTRACAO,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    get_llm_config,
    validate_config
)

def load_document(file_path: Path, source_name: str) -> str:
    """Load document from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ Loaded {source_name}: {len(content)} characters")
        return content
    except Exception as e:
        print(f"❌ Error loading {source_name}: {e}")
        raise

def create_documents():
    """Create document chunks from source files."""
    print("📄 Loading documents...")
    
    # Load financial report
    financial_content = load_document(RELATORIO_FINANCEIRO, "Financial Report")
    
    # Load administration report  
    admin_content = load_document(RELATORIO_ADMINISTRACAO, "Administration Report")
    
    # Split documents into chunks
    print("✂️ Splitting documents into chunks...")
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on, strip_headers=False
    )
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    
    all_chunks = []
    
    # Process financial report
    print("📊 Processing financial report...")
    financial_doc = Document(
        page_content=financial_content,
        metadata={"source": "relatorio-financeiro.txt", "type": "financial"}
    )
    
    # First split by markdown headers to preserve structure
    financial_header_splits = markdown_splitter.split_text(financial_content)
    # Add source metadata to each header split
    for split in financial_header_splits:
        split.metadata.update(financial_doc.metadata)
    # The split_text method returns Document objects, so we can use them directly
    financial_chunks = text_splitter.split_documents(financial_header_splits)
    all_chunks.extend(financial_chunks)
    print(f"   Created {len(financial_chunks)} chunks from financial report")
    
    # Process administration report
    print("📋 Processing administration report...")
    admin_doc = Document(
        page_content=admin_content,
        metadata={"source": "Relatorio-da-administracao.txt", "type": "administrative"}
    )
    
    # First split by markdown headers to preserve structure
    admin_header_splits = markdown_splitter.split_text(admin_content)
    # Add source metadata to each header split
    for split in admin_header_splits:
        split.metadata.update(admin_doc.metadata)
    # The split_text method returns Document objects, so we can use them directly
    admin_chunks = text_splitter.split_documents(admin_header_splits)
    all_chunks.extend(admin_chunks)
    print(f"   Created {len(admin_chunks)} chunks from administration report")
    
    print(f"📦 Total chunks created: {len(all_chunks)}")
    
    # Add chunk index to metadata
    for i, chunk in enumerate(all_chunks):
        chunk.metadata["chunk_index"] = i
    
    return all_chunks

def create_embeddings_and_store(chunks):
    """Create embeddings and store in Chroma DB."""
    print("🔗 Creating embeddings...")
    
    # Get LLM configuration
    llm_config = get_llm_config()
    
    # Create embeddings
    if llm_config["provider"] == "openai":
        embeddings = OpenAIEmbeddings(
            openai_api_key=llm_config["api_key"],
            model="text-embedding-3-small"
        )
    else:
        # For OpenRouter, we'll use OpenAI embeddings through their API
        embeddings = OpenAIEmbeddings(
            openai_api_key=llm_config["api_key"],
            model="text-embedding-3-small"
        )
    
    # Create Chroma DB
    print(f"💾 Storing in Chroma DB at {CHROMA_DB_PATH}")
    
    # Remove existing DB if it exists
    if CHROMA_DB_PATH.exists():
        import shutil
        shutil.rmtree(CHROMA_DB_PATH)
        print("🗑️ Removed existing Chroma DB")
    
    # Create new Chroma DB
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DB_PATH),
        collection_name="petrobras_docs"
    )
    
    print(f"✅ Chroma DB created with {len(chunks)} documents")
    print(f"📁 Database location: {CHROMA_DB_PATH}")
    
    return vectorstore

def test_retrieval(vectorstore):
    """Test retrieval functionality."""
    print("\n🧪 Testing retrieval...")
    
    test_queries = [
        "Qual foi o EBITDA no 1T25?",
        "Qual foi a produção de óleo e gás?",
        "Qual é a política de remuneração aos acionistas?"
    ]
    
    for query in test_queries:
        print(f"\n❓ Query: {query}")
        docs = vectorstore.similarity_search(query, k=3)
        for i, doc in enumerate(docs, 1):
            print(f"  {i}. Source: {doc.metadata}")
            print(f"     Preview: {doc.page_content[:100]}...")
            print()

def main():
    """Main ingestion process."""
    print("🚀 Starting document ingestion...")
    
    try:
        # Validate configuration
        validate_config()
        print("✅ Configuration validated")
        
        # Create document chunks
        chunks = create_documents()
        
        # Create embeddings and store
        vectorstore = create_embeddings_and_store(chunks)
        
        # Test retrieval
        test_retrieval(vectorstore)
        
        print("\n🎉 Ingestion completed successfully!")
        print(f"📊 Total chunks: {len(chunks)}")
        print(f"📁 Database: {CHROMA_DB_PATH}")
        
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        raise

if __name__ == "__main__":
    main()
