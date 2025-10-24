"""
RAG Agent implementation for Petrobras Q&A system.
"""
from typing import Dict, List, Any, TypedDict
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END
from config import (
    CHROMA_DB_PATH, 
    TOP_K_RETRIEVAL, 
    get_llm_config,
    validate_config
)
from constants import SYSTEM_PROMPT

class GraphState(TypedDict):
    """State for the RAG agent graph."""
    question: str
    documents: List[Document]
    answer: str
    sources: List[str]
    error: str

class PetrobrasRAGAgent:
    """RAG Agent for Petrobras financial and administrative questions."""
    
    def __init__(self):
        """Initialize the RAG agent."""
        self.llm = None
        self.vectorstore = None
        self.retriever = None
        self.chain = None
        self.graph = None
        self._setup()
    
    def _setup(self):
        """Setup the RAG chain components."""
        # Validate configuration
        validate_config()
        
        # Get LLM configuration
        llm_config = get_llm_config()
        
        # Initialize LLM
        if llm_config["provider"] == "openai":
            self.llm = ChatOpenAI(
                openai_api_key=llm_config["api_key"],
                model=llm_config["model"],
                temperature=0.0
            )
        else:
            # For OpenRouter, use OpenAI client with custom base URL
            self.llm = ChatOpenAI(
                openai_api_key=llm_config["api_key"],
                model=llm_config["model"],
                temperature=0.0,
                openai_api_base="https://openrouter.ai/api/v1"
            )
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=llm_config["api_key"],
            model="text-embedding-3-small"
        )
        
        # Load existing Chroma DB
        self.vectorstore = Chroma(
            persist_directory=str(CHROMA_DB_PATH),
            embedding_function=self.embeddings,
            collection_name="petrobras_docs"
        )
        
        # Create retriever
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": TOP_K_RETRIEVAL}
        )
        
        # Create prompt template with comprehensive system prompt
       

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{question}")
        ])
        
        # Create RAG chain
        self.chain = (
            {"context": self.retriever | self._format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        # Create LangGraph workflow
        self._build_graph()
    
    def _format_docs(self, docs: List[Document]) -> str:
        """Format retrieved documents for the prompt."""
        formatted_docs = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "unknown")
            content = doc.page_content.strip()
            
            # Map source files to proper report names
            if "relatorio-financeiro" in source:
                report_name = "Relatório de Desempenho 1T25"
            elif "Relatorio-da-administracao" in source:
                report_name = "Relatório da Administração 2024"
            else:
                report_name = source
            
            formatted_docs.append(f"**{report_name}**\n{content}")
        return "\n\n".join(formatted_docs)
    
    def _build_graph(self):
        """Build the LangGraph workflow."""
        # Define the graph
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("retrieve", self._retrieve_documents)
        workflow.add_node("generate", self._generate_answer)
        
        # Add edges
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        
        # Set entry point
        workflow.set_entry_point("retrieve")
        
        # Compile the graph
        self.graph = workflow.compile()
    
    def _retrieve_documents(self, state: GraphState) -> GraphState:
        """Retrieve relevant documents for the question."""
        try:
            question = state["question"]
            documents = self.retriever.invoke(question)
            
            # Extract sources with proper report names
            sources = []
            for doc in documents:
                source = doc.metadata.get("source", "unknown")
                
                # Map source files to proper report names
                if "relatorio-financeiro" in source:
                    report_name = "Relatório de Desempenho 1T25"
                elif "Relatorio-da-administracao" in source:
                    report_name = "Relatório da Administração 2024"
                else:
                    report_name = source
                
                if report_name not in sources:
                    sources.append(report_name)
            
            state["documents"] = documents
            state["sources"] = sources
            state["error"] = ""
            
        except Exception as e:
            state["documents"] = []
            state["sources"] = []
            state["error"] = str(e)
        
        return state
    
    def _generate_answer(self, state: GraphState) -> GraphState:
        """Generate answer using retrieved documents."""
        try:
            if state["error"]:
                state["answer"] = f"Erro ao recuperar documentos: {state['error']}"
                return state
            
            # Format documents for the prompt
            context = self._format_docs(state["documents"])
            question = state["question"]
            
            # Generate answer using the chain with proper input format
            answer = self.chain.invoke(question)
            
            state["answer"] = answer
            state["error"] = ""
            
        except Exception as e:
            state["answer"] = f"Erro ao gerar resposta: {str(e)}"
            state["error"] = str(e)
        
        return state
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the RAG agent with a question using LangGraph workflow.
        
        Args:
            question: The question to ask
            
        Returns:
            Dictionary containing answer, sources, and metadata
        """
        try:
            # Initialize state
            initial_state = GraphState(
                question=question,
                documents=[],
                answer="",
                sources=[],
                error=""
            )
            
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            return {
                "question": question,
                "answer": final_state["answer"],
                "sources": final_state["sources"],
                "retrieved_docs": len(final_state["documents"]),
                "metadata": {
                    "model": self.llm.model_name if hasattr(self.llm, 'model_name') else "unknown",
                    "retrieval_k": TOP_K_RETRIEVAL
                },
                "error": final_state.get("error", "")
            }
            
        except Exception as e:
            return {
                "question": question,
                "answer": f"Erro ao processar pergunta: {str(e)}",
                "sources": [],
                "retrieved_docs": 0,
                "error": str(e)
            }
    
    def test_queries(self):
        """Test the agent with sample queries."""
        test_questions = [
            "Qual foi o EBITDA Ajustado sem eventos exclusivos no 1T25?",
            "Qual foi a produção total de óleo e gás no 1T25?",
            "Qual é a política de remuneração aos acionistas?",
            "Qual foi o investimento total em 2024?",
            "Devo comprar ações da Petrobras baseado nos resultados do 1T25?"  # Test rejection
        ]
        
        print("🧪 Testing RAG Agent with sample queries...\n")
        
        for question in test_questions:
            print(f"❓ {question}")
            result = self.query(question)
            print(f"✅ {result['answer']}")
            print(f"📚 Fontes: {', '.join(result['sources'])}")
            print(f"📊 Documentos recuperados: {result['retrieved_docs']}")
            print("-" * 80)

def main():
    """Main function for testing the RAG agent."""
    print("🚀 Initializing Petrobras RAG Agent...")
    
    try:
        # Create agent
        agent = PetrobrasRAGAgent()
        print("✅ RAG Agent initialized successfully")
        
        # Test with sample queries
        agent.test_queries()
        
        # Interactive mode
        print("\n💬 Interactive mode (type 'quit' to exit):")
        while True:
            question = input("\n❓ Sua pergunta: ").strip()
            if question.lower() in ['q', 'quit', 'exit', 'sair']:
                break
            
            if question:
                result = agent.query(question)
                print(f"\n✅ {result['answer']}")
                if result['sources']:
                    print(f"📚 Fontes: {', '.join(result['sources'])}")
        
    except Exception as e:
        print(f"❌ Error initializing RAG agent: {e}")
        raise

if __name__ == "__main__":
    main()
