# Copilot Instructions - ArchiveSMP Config Manager

## Development Environment

- **Location**: `d:\homeamp.ampdata\` (Windows dev machine)
- **Production**: Hetzner Xeon (archivesmp.site), OVH Ryzen (pending)
- **Database**: MariaDB localhost:3369
- **Services**: archivesmp-webapi.service, homeamp-agent.service
- **Access**: RDP via Nom Machine (NOT SSH)
- **Users**: webadmin (sudo), amp (services)

## Critical Rules

1. **Verify Before Claiming**: Always ask for logs/evidence before making architectural claims
2. **Fix Locally First**: Edit code in local dev environment, deploy to production only after testing
3. **No Direct Server Edits**: Provide commands for developer to run, don't assume you're on production
4. **Evidence-Based**: Use "The logs show..." not "I assume..." - both human and AI can be wrong

## PAMPA Workflow (MANDATORY)

### Every Session Start:
```javascript
get_project_stats(path="software/homeamp-config-manager")
update_project(path="software/homeamp-config-manager", provider="ollama")
search_code("main logic", limit=10, hybrid="on", bm25="on", reranker="transformers")
```

### Before Creating Functions:
```javascript
search_code("similar functionality", limit=10, hybrid="on", reranker="transformers")
get_code_chunk(sha=<result>) // Study existing patterns
// Only create if nothing suitable exists
```

### After Making Changes:
```javascript
update_project(path="software/homeamp-config-manager", provider="ollama")
search_code("new function name") // Verify indexing
```

### Search Best Practices:
- ✅ **Semantic**: `search_code("user authentication logic")`
- ❌ **Literal**: `search_code("login() function")`
- ✅ **Scoped**: `search_code("validation", path_glob=["src/api/**"], lang=["python"])`
- ✅ **Hybrid**: Always use `hybrid="on", bm25="on", reranker="transformers", symbol_boost="on"`

### PAMPA Tools:
- `search_code(query, limit, path_glob, lang, hybrid, bm25, reranker, symbol_boost)` - Semantic search
- `get_code_chunk(sha, path)` - Retrieve full code
- `update_project(path, provider)` - Sync index after changes
- `get_project_stats(path)` - Project overview

**Similarity Scores**: >0.7 excellent, >0.5 good, >0.3 moderate, <0.3 poor

### Configuration:
- Provider: `ollama`
- Embedding: `nomic-embed-text-v2-moe`
- Reranker: `mxbai-rerank-large-v2`
- Indexed: 1,439 functions (1,188 Python, 251 JS)

## Context7 Library Docs

Always use Context7 for external libraries (FastAPI, Bootstrap, Jinja2, etc.):
```javascript
mcp_context7_resolve-library-id(libraryName="FastAPI")
mcp_context7_get-library-docs(context7CompatibleLibraryID="/tiangolo/fastapi", topic="file upload")
```

## Code Quality

- **Python**: Black (120 line length), Pylint, isort
- **JS/JSON/YAML**: Prettier (120 print width, trailing commas ES5)
- **formatOnSave**: Enabled for all languages
- **Config**: `pyproject.toml`, `.prettierrc`, `.vscode/settings.json`

## Python Functions Index

See `python_functions_index.txt` for complete list of 980 functions across 94 files.

Key modules:
- `agent/`: Core agent logic (discovery, deployment, updates, notifications)
- `api/`: FastAPI endpoints (dashboard, deployment, tags, variance, plugins)
- `web/`: Web UI and templates
- `parsers/`: Config file parsing
- `utils/`: Utilities (YAML, logging, backups)

