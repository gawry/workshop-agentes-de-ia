# Sem ecstasy no prompt

**Workshop prático sobre agentes de IA confiáveis em produção**

Por Gustavo Gawryszewski

## 🎯 Sobre o Workshop

Este workshop ensina como levar agentes de IA de qualidade para produção, eliminando alucinações e garantindo confiabilidade. O foco é no mantra **"Fonte ou silêncio"** - se não tem fonte, o agente NÃO responde.

## 📚 O que você vai aprender

### 🏗️ Construir um agente RAG testável
- Do zero ao deploy em 3 horas
- Usando Flowise (visual) → transferível para código

### 🛡️ Estabelecer guardrails claros
- System Prompt explícito com guardrails definidos
- Comportamentos proibidos documentados

### 📊 Criar processo de avaliação contínua
- Golden set com gabarito humano
- Métricas automáticas de qualidade

### 🚦 Deploy seguro com canários
- Protocolo de pinning e rollback
- Monitoramento em produção

## 🛠️ Tecnologias Utilizadas

- **Flowise** - Interface visual para construir agentes RAG
- **LangChain** - Framework para aplicações LLM
- **LangSmith** - Observabilidade e avaliação
- **DeepEval** - Framework de testing para LLMs
- **Chroma** - Vector database
- **OpenAI/Anthropic** - Modelos de linguagem

## 📁 Estrutura do Projeto

```
├── slides.md                    # Apresentação do workshop
├── python/                      # Implementação prática
│   ├── rag_agent.py            # Agente RAG implementado
│   ├── evaluate_langsmith.py   # Avaliação com LangSmith
│   ├── evaluate_deepeval.py    # Avaliação com DeepEval
│   └── test_rag.py             # Testes automatizados
├── datasets/                    # Documentos da Petrobras
├── templates/                   # Templates de system prompt
└── images/                      # Imagens da apresentação
```

## 🚀 Como usar este repositório

### 1. Configuração inicial

```bash
# Instalar dependências Python
cd python
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp env.example .env
# Editar .env com suas chaves de API
```

### 2. Ingestão de documentos

```bash
python ingest.py
```

### 3. Testar o agente RAG

```bash
python rag_agent.py
```

### 4. Avaliação com LangSmith

```bash
python evaluate_langsmith.py
```

### 5. Avaliação com DeepEval

```bash
python evaluate_deepeval.py
```

### 6. Testes automatizados

```bash
pytest test_rag.py -v
```

## 📊 Dataset: Golden Set Petrobras

O workshop utiliza dados reais da Petrobras com 40 casos de teste:

- **Comum**: Perguntas diretas sobre dados financeiros
- **Edge Case**: Perguntas ambíguas que precisam de esclarecimento  
- **Ataque**: Tentativas de fazer o agente inventar dados

## 🔗 Links Importantes

- **Repositório GitHub**: [github.com/gawry/workshop-agentes-de-ia](https://github.com/gawry/workshop-agentes-de-ia)
- **Template Google Docs**: [bit.ly/workshop-agentes-ia](https://bit.ly/workshop-agentes-ia)
- **Flowise Docs**: [docs.flowiseai.com](https://docs.flowiseai.com)
- **LangChain**: [python.langchain.com](https://python.langchain.com)

## 👨‍🏫 Sobre o Instrutor

**Gustavo Gawryszewski**

- UX Designer & Engenheiro de Software
- Economista & Contador  
- Especialista em ML/IA - UT Austin
- Mestre em Economia

**Contatos:**
- Email: gustavo@gawry.com
- LinkedIn: [linkedin.com/in/gawry](https://linkedin.com/in/gawry)
- GitHub: [github.com/gawry](https://github.com/gawry)

## 📄 Licença

Este projeto é para fins educacionais. Os dados da Petrobras são públicos e podem ser usados conforme política da empresa.

---

**Desenvolvido para demonstração de agentes de IA confiáveis em produção** 🚀