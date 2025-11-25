# N8N Agent Flow Architecture - Dev/Admin Tooling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL INTERFACES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Code-Server (VS Code Web)  │  GitLab (SCM)  │  Docker Management Console   │
└──────────────────┬──────────────────┬────────────────────┬─────────────────┘
                   │                  │                    │
                   └──────────────────┴────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              N8N WORKFLOW LAYER                              │
│                    (Low-Code Orchestration & Routing)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐             │
│  │   Webhook    │      │  Scheduler   │      │  Manual      │             │
│  │   Triggers   │──────│   Triggers   │──────│  Triggers    │             │
│  └──────────────┘      └──────────────┘      └──────────────┘             │
│         │                     │                      │                      │
│         └─────────────────────┴──────────────────────┘                      │
│                               │                                             │
│                               ▼                                             │
│                    ┌─────────────────────┐                                  │
│                    │  Query Classifier   │                                  │
│                    │  (Intent Router)    │                                  │
│                    └─────────────────────┘                                  │
│                               │                                             │
│         ┌─────────────────────┼─────────────────────┐                      │
│         ▼                     ▼                     ▼                      │
│  ┌────────────┐        ┌────────────┐       ┌────────────┐               │
│  │ Code Query │        │ Data Query │       │ Admin Task │               │
│  │   Branch   │        │   Branch   │       │   Branch   │               │
│  └────────────┘        └────────────┘       └────────────┘               │
│         │                     │                     │                      │
└─────────┼─────────────────────┼─────────────────────┼──────────────────────┘
          │                     │                     │
          ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LLM PROCESSING LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────┐            │
│  │                    OLLAMA (Local LLM Server)                │            │
│  │                      http://localhost:11434                 │            │
│  ├────────────────────────────────────────────────────────────┤            │
│  │  Models Loaded:                                            │            │
│  │  • nomic-embed-text-v2-moe (Embeddings - 305M params)     │            │
│  │  • mxbai-rerank-large-v2 (Reranker - 1.5B params)         │            │
│  │  • qwen2.5-coder-14b-instruct (Code Generation)           │            │
│  │  • qwen2.5-coder-3b-instruct (Fast Code Tasks)            │            │
│  │  • deepseek-r1-qwen3-8b (Reasoning Tasks)                 │            │
│  │  • gemma-3-12b-it (General Purpose)                       │            │
│  │  • llama-3.2-1b-instruct (Ultra-Fast Tasks)               │            │
│  └────────────────────────────────────────────────────────────┘            │
│                                                                              │
└──────────────────────────────┬───────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         KNOWLEDGE/DATA LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────┐    ┌──────────────────────┐                      │
│  │  QDRANT (Vector DB)  │    │  PostgreSQL (SQL)    │                      │
│  │  Semantic Search     │    │  Structured Data     │                      │
│  ├──────────────────────┤    ├──────────────────────┤                      │
│  │ • Code Embeddings    │    │ • Config History     │                      │
│  │ • Documentation      │    │ • User Data          │                      │
│  │ • Past Conversations │    │ • Audit Logs         │                      │
│  │ • Solution Archive   │    │ • Metadata Store     │                      │
│  └──────────────────────┘    └──────────────────────┘                      │
│                                                                              │
└──────────────────────────────┬───────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MCP SERVER INTEGRATION LAYER                          │
│                    (Available in VS Code - For N8N Extension)                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  PAMPA MCP Server                                            │           │
│  │  • search_code() - Semantic code search                      │           │
│  │  • get_code_chunk() - Retrieve code by SHA                   │           │
│  │  • update_project() - Re-index codebase                      │           │
│  │  • get_project_stats() - Project overview                    │           │
│  │  Provider: ollama (nomic-embed-text-v2-moe)                  │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  Context7 MCP Server (Library Documentation)                 │           │
│  │  • resolve-library-id() - Find library by name               │           │
│  │  • get-library-docs() - Fetch latest API docs                │           │
│  │  Supports: FastAPI, Bootstrap, Jinja2, SQLAlchemy, etc.      │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  Docker MCP Server (Container Management)                    │           │
│  │  • search() - Find Docker Hub images                         │           │
│  │  • checkRepository() - Verify image exists                   │           │
│  │  • getRepositoryInfo() - Get image metadata                  │           │
│  │  • listNamespaces() - List user's Docker namespaces          │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  GitKraken MCP Server (Git Operations)                       │           │
│  │  • git_add_or_commit() - Stage/commit changes                │           │
│  │  • git_branch_operations() - Branch management               │           │
│  │  • git_diff() - View changes                                 │           │
│  │  • git_log() - Commit history                                │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  Azure MCP Server (Cloud Resources)                          │           │
│  │  • Deploy operations (azd, bicep, terraform)                 │           │
│  │  • Resource management (SQL, PostgreSQL, containers)         │           │
│  │  • Subscription/resource group queries                       │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  MSSQL MCP Server (Database Operations)                      │           │
│  │  • mssql_list_databases() - List available databases         │           │
│  │  • mssql_execute_query() - Run SQL queries                   │           │
│  │  • mssql_change_database() - Switch context                  │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  ArXiv MCP Server (Research Papers)                          │           │
│  │  • search_papers() - Semantic paper search                   │           │
│  │  • download_paper() - Fetch & convert to markdown            │           │
│  │  • read_paper() - Get paper contents                         │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATA FLOW EXAMPLE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  USER QUERY: "How do we handle database connections in the agent code?"     │
│       │                                                                      │
│       ▼                                                                      │
│  N8N Webhook Trigger → Query Classifier                                     │
│       │                                                                      │
│       ▼                                                                      │
│  Code Query Branch → PAMPA search_code("database connection agent")         │
│       │                                                                      │
│       ▼                                                                      │
│  OLLAMA (nomic-embed-text-v2-moe) → Generate embeddings                     │
│       │                                                                      │
│       ▼                                                                      │
│  QDRANT Vector Search → Top 5 matches (similarity > 0.85)                   │
│       │                                                                      │
│       ▼                                                                      │
│  PAMPA get_code_chunk() → Retrieve full source code                         │
│       │                                                                      │
│       ▼                                                                      │
│  OLLAMA (qwen2.5-coder-14b) → Generate explanation + context                │
│       │                                                                      │
│       ▼                                                                      │
│  MXBAI Reranker → Re-score results for precision                            │
│       │                                                                      │
│       ▼                                                                      │
│  PostgreSQL → Log query + results for future reference                      │
│       │                                                                      │
│       ▼                                                                      │
│  RESPONSE: Formatted answer with code snippets, file locations, patterns    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         INFRASTRUCTURE STACK                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Platform: Docker (Cross-platform, x86-64)                                  │
│  Installer: https://desktop.docker.com/win/main/amd64/                      │
│             Docker%20Desktop%20Installer.exe                                 │
│                                                                              │
│  Base Pack: n8n-io/self-hosted-ai-starter-kit                               │
│  GitHub: https://github.com/n8n-io/self-hosted-ai-starter-kit               │
│                                                                              │
│  Components:                                                                 │
│  ├─ N8N: Low-code workflow automation (400+ integrations)                   │
│  ├─ Ollama: Local LLM server (.gguf models, Q4_K quantization)              │
│  ├─ Qdrant: Vector database (768-dimensional embeddings)                    │
│  └─ PostgreSQL: Relational database (high-performance, production-ready)    │
│                                                                              │
│  Additional Services:                                                        │
│  ├─ Code-Server: VS Code in browser                                         │
│  └─ GitLab: Self-hosted Git SCM                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                      N8N WORKFLOW RECOMMENDATIONS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Workflow 1: Code Search & Documentation Assistant                          │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │ Webhook → IF (query type) → PAMPA search_code()          │              │
│  │    ├─ Code Query → Ollama (embeddings) → Qdrant          │              │
│  │    ├─ Library Docs → Context7 resolve + fetch            │              │
│  │    └─ General → Ollama (qwen2.5-coder) → Response        │              │
│  └──────────────────────────────────────────────────────────┘              │
│                                                                              │
│  Workflow 2: GitLab CI/CD Integration                                       │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │ GitLab Webhook → Parse Event → IF (event type)           │              │
│  │    ├─ Push → GitKraken diff → Analyze changes            │              │
│  │    ├─ MR → PAMPA search similar code → Review            │              │
│  │    └─ Tag → Docker build → Deploy                        │              │
│  └──────────────────────────────────────────────────────────┘              │
│                                                                              │
│  Workflow 3: Research Paper Archive                                         │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │ Scheduled → ArXiv search → Download papers               │              │
│  │    → Ollama (embeddings) → Qdrant store                  │              │
│  │    → PostgreSQL metadata → GitLab commit                 │              │
│  └──────────────────────────────────────────────────────────┘              │
│                                                                              │
│  Workflow 4: Infrastructure Monitoring                                      │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │ Cron → Docker list containers → Check health             │              │
│  │    ├─ Unhealthy → MSSQL log → Alert                      │              │
│  │    └─ OK → PostgreSQL metrics → Dashboard                │              │
│  └──────────────────────────────────────────────────────────┘              │
│                                                                              │
│  Workflow 5: Deployment Pipeline                                            │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │ Manual Trigger → PAMPA update_project()                  │              │
│  │    → GitKraken commit → Docker build                     │              │
│  │    → Azure deploy → MSSQL migrate schema                 │              │
│  │    → PostgreSQL log → Notification                       │              │
│  └──────────────────────────────────────────────────────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         PERFORMANCE CONSIDERATIONS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Model Selection Strategy:                                                  │
│  • Ultra-Fast (<100ms): llama-3.2-1b-instruct (simple classification)       │
│  • Fast (~500ms): qwen2.5-coder-3b-instruct (quick code tasks)              │
│  • Balanced (~2s): qwen2.5-coder-14b-instruct (main code generation)        │
│  • Reasoning (~5s): deepseek-r1-qwen3-8b (complex logic)                    │
│  • General (~3s): gemma-3-12b-it (documentation, explanations)              │
│                                                                              │
│  Embedding Pipeline:                                                         │
│  • Ollama (nomic-embed-text-v2-moe) → 8192 token context                    │
│  • Qdrant vector search → Cosine similarity, top-k=5                        │
│  • MXBAI reranker → Cross-encoder precision boost                           │
│                                                                              │
│  Caching Strategy:                                                           │
│  • PostgreSQL: Query results, conversation history                          │
│  • Qdrant: Pre-computed embeddings for static docs                          │
│  • N8N: Workflow execution state                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Notes

- **MCP Servers**: All listed MCP servers are currently available in VS Code. To use them in N8N, you'll need to create HTTP endpoints that proxy the MCP stdio interface.

- **Ollama Models**: All models listed are already imported and ready for use. Use model routing in N8N to select appropriate model based on task complexity.

- **Vector Search**: PAMPA already has 1,439 functions indexed. Qdrant can store additional embeddings for documentation, conversations, and solutions.

- **Cross-Platform**: Docker ensures all components run on Windows, Linux, or macOS without modification.

- **Tuning Required**: LLMs will need prompt engineering and temperature/top_p tuning for optimal results in production workflows.
