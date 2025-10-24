"""
RAG Agent implementation for Petrobras Q&A system.
"""
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain.schema import Document
from config import (
    CHROMA_DB_PATH, 
    TOP_K_RETRIEVAL, 
    get_llm_config,
    validate_config
)

class PetrobrasRAGAgent:
    """RAG Agent for Petrobras financial and administrative questions."""
    
    def __init__(self):
        """Initialize the RAG agent."""
        self.llm = None
        self.vectorstore = None
        self.retriever = None
        self.chain = None
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
                temperature=0.1
            )
        else:
            # For OpenRouter, use OpenAI client with custom base URL
            self.llm = ChatOpenAI(
                openai_api_key=llm_config["api_key"],
                model=llm_config["model"],
                temperature=0.1,
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
        system_prompt = """Você é um **analista financeiro especializado** trabalhando para análise de relatórios da **Petrobras**.

Seu objetivo é **analisar e responder perguntas sobre os relatórios financeiros da Petrobras, fornecendo insights baseados exclusivamente nos documentos oficiais disponíveis**.

**Domínio de conhecimento:**
- Relatórios de Desempenho Financeiro da Petrobras (1T25)
- Relatório da Administração da Petrobras (2024)
- Demonstrações financeiras consolidadas
- Indicadores de performance operacional e financeira
- Estratégia e planos de negócios da Petrobras
- Métricas de ESG e sustentabilidade

**Limitações importantes:**
- Você tem acesso SOMENTE aos relatórios da Petrobras fornecidos no contexto
- Você NÃO tem acesso à internet ou informações externas sobre a Petrobras
- Suas respostas devem ser baseadas EXCLUSIVAMENTE nos relatórios oficiais recuperados
- NÃO forneça conselhos de investimento ou recomendações de compra/venda de ações

**PROCESSO OBRIGATÓRIO:**
1. **Buscar contexto relevante** - Use o sistema de recuperação para encontrar seções pertinentes
2. **Analisar contexto recuperado** - Leia CUIDADOSAMENTE todos os trechos recuperados
3. **Construir resposta fundamentada** - Use APENAS informação presente nos relatórios oficiais
4. **Adicionar citações obrigatórias** - TODA afirmação factual DEVE ter citação específica

**REGRAS DE CITAÇÃO:**
- Formato obrigatório: **[Nome do Relatório, Seção/Página]**
- Cada fato, número, métrica ou declaração DEVE incluir citação da fonte
- Sempre inclua o período de referência quando disponível

**FORMATO DE SAÍDA OBRIGATÓRIO:**
**RESPOSTA:**
[Sua resposta completa aqui, com citações inline [Fonte, Local]]

**FONTES:**
- Nome completo do relatório 1
- Nome completo do relatório 2

**CONFIANÇA:** alta|média|baixa

**LIMITAÇÕES:** [Se aplicável: o que não pôde ser respondido e por quê]

**PERÍODO DE REFERÊNCIA:** [Período dos dados (ex: 1T25, 2024, etc.)]

**COMPORTAMENTOS PROIBIDOS:**
- NUNCA fabricar informação ou inventar números
- NUNCA fornecer conselhos de investimento
- NUNCA omitir citações em afirmações factuais
- NUNCA fazer interpretações não fundamentadas

**CONTEXTO DISPONÍVEL:**
{context}

**PERGUNTA:** {question}"""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{question}")
        ])
        
        # Create RAG chain
        self.chain = (
            {"context": self.retriever | self._format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
    
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
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the RAG agent with a question.
        
        Args:
            question: The question to ask
            
        Returns:
            Dictionary containing answer, sources, and metadata
        """
        try:
            # Get answer from RAG chain
            answer = self.chain.invoke(question)
            
            # Get retrieved documents for source tracking
            retrieved_docs = self.retriever.get_relevant_documents(question)
            
            # Extract sources with proper report names
            sources = []
            for doc in retrieved_docs:
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
            
            return {
                "question": question,
                "answer": answer,
                "sources": sources,
                "retrieved_docs": len(retrieved_docs),
                "metadata": {
                    "model": self.llm.model_name if hasattr(self.llm, 'model_name') else "unknown",
                    "retrieval_k": TOP_K_RETRIEVAL
                }
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
            if question.lower() in ['quit', 'exit', 'sair']:
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
