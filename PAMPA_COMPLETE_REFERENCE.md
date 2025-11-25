# PAMPA Complete Reference

**Protocol for Augmented Memory of Project Artifacts (MCP)**

Version: 1.12+  
Provider: Ollama (nomic-embed-text-v2-moe)  
Project: software/homeamp-config-manager  
Status: Indexed (1,439 functions: 1,188 Python, 251 JavaScript)

---

## Table of Contents

1. [Overview](#overview)
2. [Installation & Configuration](#installation--configuration)
3. [CLI Commands](#cli-commands)
4. [MCP Tools for AI Agents](#mcp-tools-for-ai-agents)
5. [Advanced Features](#advanced-features)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Overview

PAMPA is a code memory system that indexes projects and enables semantic search over codebases. It uses embeddings to understand code semantically rather than relying on exact keyword matches.

### Key Capabilities

- **Semantic Code Search**: Find functions by describing what they do, not by name
- **Hybrid Search**: Combines BM25 keyword search with vector similarity
- **Cross-Encoder Reranking**: Uses transformer models to re-score results for precision
- **Symbol-Aware Ranking**: Boosts results based on function signatures and symbols
- **Scoped Filtering**: Search by file patterns, languages, or semantic tags
- **Context Packs**: Predefined search scopes for domain-specific work
- **MCP Integration**: Works with AI agents (GitHub Copilot, Claude, etc.)

### What Gets Indexed

- **Languages**: Python, JavaScript, TypeScript, PHP, Java, Go, Rust, C/C++, and more
- **Chunks**: Functions, classes, methods, and significant code blocks
- **Metadata**: File paths, line numbers, symbols, language tags
- **Embeddings**: 768-dimensional vectors (nomic-embed-text-v2-moe)

---

## Installation & Configuration

### Installation

```bash
# Via npx (no installation needed)
npx -y pampa --version

# Or install globally
npm install -g pampa
```

### Environment Configuration

Create `.env` file in your project root:

```bash
# Ollama Configuration (recommended for local development)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text-v2-moe

# Or use OpenAI
OPENAI_API_KEY=sk-...

# Or use Cohere
COHERE_API_KEY=...

# Optional: Encryption for sensitive codebases
PAMPA_ENCRYPTION_KEY=your-32-char-encryption-key-here
```

### VS Code MCP Configuration

Add to `.vscode/settings.json`:

```json
{
  "mcpServers": {
    "pampa": {
      "command": "npx",
      "args": ["-y", "pampa", "mcp"],
      "env": {
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_EMBEDDING_MODEL": "nomic-embed-text-v2-moe"
      }
    }
  }
}
```

### Gitignore

Add to `.gitignore`:

```gitignore
# PAMPA code memory database and cache
.pampa/
```

---

## CLI Commands

### `pampa index [options] [path]`

Index a project for the first time and build `pampa.codemap.json`.

**Options:**
- `-p, --provider <provider>` - Embedding provider: `auto`, `openai`, `transformers`, `ollama`, `cohere` (default: `auto`)
- `--project <path>` - Alias for project path
- `--directory <path>` - Alias for project directory
- `--encrypt <mode>` - Encrypt chunk payloads when `PAMPA_ENCRYPTION_KEY` is set: `on`, `off`

**Examples:**
```bash
# Index current directory with auto-detected provider
pampa index

# Index specific project with Ollama
pampa index /path/to/project --provider ollama

# Index with encryption
pampa index --encrypt on
```

**Output:**
- `.pampa/pampa.db` - SQLite database with embeddings and chunks
- `.pampa/chunks/` - Compressed code chunks (.gz files)
- `pampa.codemap.json` - Git-friendly JSON with function metadata

---

### `pampa update [options] [path]`

Update the index by re-scanning all files. Recommended after code changes.

**Options:**
- Same as `pampa index`

**Examples:**
```bash
# Update index in current directory
pampa update

# Update specific project
pampa update ~/my-project --provider ollama
```

**What It Does:**
- Detects new, modified, and deleted files
- Re-embeds changed functions
- Updates `pampa.codemap.json` and `.pampa/pampa.db`

---

### `pampa watch [options] [path]`

Watch project files and incrementally update the index as changes occur.

**Options:**
- `-p, --provider <provider>` - Embedding provider (default: `auto`)
- `--project <path>` - Project path
- `--directory <path>` - Project directory
- `-d, --debounce <ms>` - Debounce interval in milliseconds (default: `500`)
- `--encrypt <mode>` - Encrypt chunks: `on`, `off`

**Examples:**
```bash
# Watch current directory
pampa watch

# Watch with custom debounce
pampa watch --debounce 1000

# Watch specific project
pampa watch ~/my-project
```

**Use Case:**
- Development environments where code changes frequently
- Real-time indexing without manual `update` commands

---

### `pampa search [options] <query> [path]`

Search indexed code with semantic queries, filters, and advanced ranking.

**Options:**

**Basic:**
- `-k, --limit <num>` - Maximum number of results (default: `10`)
- `-p, --provider <provider>` - Embedding provider: `auto`, `openai`, `transformers`, `ollama`, `cohere` (default: `auto`)
- `--project <path>` - Project path
- `--directory <path>` - Project directory

**Filtering:**
- `--path_glob <pattern...>` - Limit results to files matching glob patterns
- `--tags <tag...>` - Filter by semantic tags
- `--lang <language...>` - Filter by languages (e.g., `php`, `ts`, `python`)

**Ranking & Performance:**
- `--hybrid <mode>` - Reciprocal-rank-fused hybrid search: `on`, `off` (default: `on`)
- `--bm25 <mode>` - BM25 keyword candidate generation: `on`, `off` (default: `on`)
- `--reranker <mode>` - Reranker strategy: `off`, `transformers` (default: `off`)
- `--symbol_boost <mode>` - Symbol-aware ranking boost: `on`, `off` (default: `on`)

**Examples:**

```bash
# Basic semantic search
pampa search "database connection logic"

# Search with file filtering
pampa search "user authentication" --path_glob "src/api/**"

# Search specific language
pampa search "error handling" --lang python

# Search with reranker for precision
pampa search "payment processing" --reranker transformers

# Combine multiple filters
pampa search "validation logic" --path_glob "app/Services/**" --tags stripe --lang php

# Override provider
pampa search "token refresh" --provider openai

# Disable symbol boost
pampa search "helper functions" --symbol_boost off
```

**Output:**
```
[1] settings.py:45-67 (similarity: 0.98)
  → get_database_config()
  File: src/core/settings.py
  SHA: abc123def456...

[2] db_config.py:12-34 (similarity: 0.85)
  → initialize_connection_pool()
  File: src/api/db_config.py
  SHA: def789ghi012...
```

---

### `pampa context`

Manage context packs for scoped search defaults.

#### `pampa context list [path]`

List available context packs for a project.

**Example:**
```bash
pampa context list
```

**Output:**
```
Available context packs:
- stripe-backend
- react-components
- api-endpoints
```

---

#### `pampa context show <name> [path]`

Show the definition of a context pack.

**Example:**
```bash
pampa context show stripe-backend
```

**Output:**
```json
{
  "name": "stripe-backend",
  "path_glob": ["app/Services/Stripe/**", "app/Http/Controllers/Stripe/**"],
  "tags": ["stripe", "payment"],
  "lang": ["php"]
}
```

---

#### `pampa context use <name> [path]`

Activate a context pack as the default scope for CLI searches.

**Examples:**
```bash
# Activate context pack
pampa context use stripe-backend

# Clear active context pack
pampa context use clear
```

**Effect:**
- All subsequent `pampa search` commands use the context pack's filters
- CLI flags override pack defaults

---

### `pampa mcp`

Start MCP server for AI agent integration.

**Usage:**
```bash
pampa mcp
```

**What It Does:**
- Starts stdio MCP server for AI agents
- Exposes tools: `search_code`, `get_code_chunk`, `index_project`, `update_project`, `get_project_stats`, `use_context_pack`
- Reads configuration from `.env` and project root

**Integration:**
- GitHub Copilot
- Claude Desktop
- VS Code extensions
- Custom MCP clients

---

### `pampa info`

Show information about the indexed project.

**Usage:**
```bash
pampa info
```

**Output:**
```
Project: software/homeamp-config-manager
Database: .pampa/pampa.db
Functions: 1,439
Languages:
  - Python: 1,188 functions
  - JavaScript: 251 functions
Provider: ollama (nomic-embed-text-v2-moe)
Last Updated: 2025-11-25 14:32:15
```

---

## MCP Tools for AI Agents

### `search_code(query, limit, path, filters...)`

**Purpose:** Advanced semantic search with scoping and hybrid ranking.

**Parameters:**
- `query` (string, required): Natural language description (e.g., "user validation", "error handling")
- `limit` (number, optional): Number of results (default: 10)
- `path` (string, optional): Project root directory (default: ".")
- `path_glob` (array[string], optional): File patterns (e.g., `["app/Services/**", "src/api/**"]`)
- `tags` (array[string], optional): Semantic tags (e.g., `["stripe", "payment"]`)
- `lang` (array[string], optional): Languages (e.g., `["php", "typescript", "python"]`)
- `provider` (string, optional): Embedding provider (`auto`, `openai`, `transformers`, `ollama`, `cohere`)
- `hybrid` (string, optional): Hybrid search mode (`on`, `off`) - default: `on`
- `bm25` (string, optional): BM25 keyword search (`on`, `off`) - default: `on`
- `reranker` (string, optional): Reranker strategy (`off`, `transformers`) - default: `off`
- `symbol_boost` (string, optional): Symbol-aware ranking (`on`, `off`) - default: `on`

**Returns:**
```json
[
  {
    "file": "src/core/settings.py",
    "symbol": "get_database_config",
    "line": 45,
    "similarity": 0.98,
    "sha": "abc123def456...",
    "meta": {
      "language": "python",
      "type": "function"
    }
  }
]
```

**Examples:**
```javascript
// Basic search
search_code("database connection logic");

// Scoped search
search_code("user authentication", {
  path_glob: ["src/api/**"],
  lang: ["python"]
});

// High-precision search with reranker
search_code("payment processing", {
  tags: ["stripe"],
  reranker: "transformers"
});

// Hybrid search (default in v1.12+)
search_code("error handling", {
  hybrid: "on",
  bm25: "on",
  symbol_boost: "on"
});
```

---

### `get_code_chunk(sha, path)`

**Purpose:** Retrieve complete source code of a specific chunk.

**Parameters:**
- `sha` (string, required): SHA identifier from search results
- `path` (string, optional): Project root directory (default: ".")

**Returns:**
```json
{
  "sha": "abc123def456...",
  "file": "src/core/settings.py",
  "symbol": "get_database_config",
  "line": 45,
  "code": "def get_database_config():\n    \"\"\"Get database connection config.\"\"\"\n    return {\n        'host': os.getenv('DB_HOST'),\n        'port': int(os.getenv('DB_PORT', 3306)),\n        'database': os.getenv('DB_NAME')\n    }"
}
```

**Example:**
```javascript
// Get code from search result
const results = search_code("database connection");
const chunk = get_code_chunk(results[0].sha);
console.log(chunk.code);
```

---

### `index_project(path, provider)`

**Purpose:** Create initial project index (first time setup).

**Parameters:**
- `path` (string, optional): Directory to index (default: ".")
- `provider` (string, optional): Embedding provider (default: "auto")

**Returns:**
```json
{
  "status": "success",
  "functions": 1439,
  "files": 87,
  "languages": ["python", "javascript"]
}
```

**Example:**
```javascript
// Index current project
index_project(".", "ollama");
```

---

### `update_project(path, provider)`

**Purpose:** Update index after code changes (use frequently!).

**Parameters:**
- `path` (string, optional): Directory to update (default: ".")
- `provider` (string, optional): Embedding provider (default: "auto")

**Returns:**
```json
{
  "status": "success",
  "added": 5,
  "modified": 12,
  "removed": 3
}
```

**Example:**
```javascript
// Update after code changes
update_project(".", "ollama");
```

---

### `get_project_stats(path)`

**Purpose:** Get project overview and statistics.

**Parameters:**
- `path` (string, optional): Directory to analyze (default: ".")

**Returns:**
```json
{
  "functions": 1439,
  "files": 87,
  "languages": {
    "python": 1188,
    "javascript": 251
  },
  "provider": "ollama",
  "model": "nomic-embed-text-v2-moe",
  "last_updated": "2025-11-25T14:32:15Z"
}
```

**Example:**
```javascript
// Get project stats
const stats = get_project_stats(".");
console.log(`Functions: ${stats.functions}`);
```

---

### `use_context_pack(name, path)`

**Purpose:** Activate predefined search scopes and filters.

**Parameters:**
- `name` (string, required): Context pack name (e.g., "stripe-backend", "react-components")
- `path` (string, optional): Project root directory (default: ".")

**Returns:**
```json
{
  "status": "success",
  "pack": "stripe-backend",
  "filters": {
    "path_glob": ["app/Services/Stripe/**"],
    "tags": ["stripe", "payment"],
    "lang": ["php"]
  }
}
```

**Example:**
```javascript
// Activate context pack
use_context_pack("stripe-backend");

// All searches now scoped to Stripe backend
search_code("create payment");  // Only Stripe results
search_code("handle webhook");  // Only Stripe webhooks
```

---

## Advanced Features

### Hybrid Search (v1.12+)

Combines BM25 keyword search with vector similarity using reciprocal rank fusion.

**Benefits:**
- Better recall: Finds functions with different terminology
- Keyword + semantic: Exact matches AND meaning-based search
- Default enabled: No configuration needed

**Example:**
```bash
# Hybrid search is ON by default
pampa search "user validation"

# Explicitly enable
pampa search "user validation" --hybrid on --bm25 on

# Disable for pure semantic search
pampa search "user validation" --hybrid off --bm25 off
```

---

### Cross-Encoder Reranking

Uses transformer models to re-score search results for higher precision.

**When to Use:**
- Critical searches where precision matters
- Large codebases with many similar functions
- Domain-specific queries that need context

**Example:**
```bash
# Enable reranker
pampa search "payment processing logic" --reranker transformers

# Combine with hybrid search
pampa search "error handling" --hybrid on --reranker transformers
```

**Performance:**
- Adds ~200-500ms per search
- Significantly improves top-3 accuracy
- Uses mixedbread-ai/mxbai-rerank-large-v2 (if available)

---

### Symbol-Aware Ranking

Boosts results based on function signatures and symbol names.

**When to Use:**
- Function-specific searches
- Looking for specific method names
- API endpoint discovery

**Example:**
```bash
# Symbol boost ON (default)
pampa search "create_user function"

# Disable for broader semantic search
pampa search "user creation logic" --symbol_boost off
```

---

### Scoped Filtering

Narrow searches to specific files, languages, or tags.

**Path Glob Examples:**
```bash
# Search in specific directory
pampa search "validation" --path_glob "src/api/**"

# Multiple directories
pampa search "helper functions" --path_glob "src/utils/**" "src/helpers/**"

# Specific file types
pampa search "config" --path_glob "**/*.config.js"
```

**Language Filtering:**
```bash
# Python only
pampa search "async functions" --lang python

# Multiple languages
pampa search "HTTP client" --lang python javascript
```

**Tag Filtering:**
```bash
# Semantic tags
pampa search "payment" --tags stripe payment

# Domain-specific
pampa search "authentication" --tags api security
```

---

### Context Packs

Predefined search scopes for domain-specific work.

**Create Context Pack:**

Create `.pampa/contextpacks/stripe-backend.json`:
```json
{
  "name": "stripe-backend",
  "description": "Stripe payment backend services",
  "path_glob": [
    "app/Services/Stripe/**",
    "app/Http/Controllers/Stripe/**"
  ],
  "tags": ["stripe", "payment"],
  "lang": ["php"]
}
```

**Activate:**
```bash
pampa context use stripe-backend
```

**Search with Context:**
```bash
# All searches now scoped to Stripe backend
pampa search "create session"  # Only Stripe-related results
pampa search "handle webhook"  # Only Stripe webhooks
pampa search "refund"          # Only Stripe refund logic
```

**Clear Context:**
```bash
pampa context use clear
```

---

### Encryption

Encrypt chunk payloads for sensitive codebases.

**Setup:**
```bash
# Generate 32-character encryption key
export PAMPA_ENCRYPTION_KEY="your-32-char-encryption-key-here"
```

**Index with Encryption:**
```bash
pampa index --encrypt on
```

**Update with Encryption:**
```bash
pampa update --encrypt on
```

**Note:**
- Chunks are encrypted at rest in `.pampa/chunks/`
- Embeddings are NOT encrypted (they're already obfuscated)
- Search works normally (decryption is automatic)

---

## Best Practices

### AI Agent Workflow

**Every Session Start:**
1. `get_project_stats()` → Check if project is indexed
2. `update_project()` → Sync with recent changes

**Before Writing Any Function:**
1. `search_code("semantic description", {hybrid: "on", bm25: "on", reranker: "transformers", symbol_boost: "on"})` → Find existing code
2. `get_code_chunk(sha)` → Study existing patterns
3. Only create new code if nothing suitable exists

**After Code Modifications:**
1. `update_project()` → Re-index changes

---

### Search Strategies

**Be Semantic, Not Literal:**
- ✅ "user authentication logic"
- ❌ "login() function"

**Use Context:**
- ✅ "error handling for API calls"
- ❌ "error"

**Check Variations:**
- ✅ "create user", "add user", "register user", "new user"

**Explore Related Concepts:**
- After finding auth → search "validation", "security", "permissions"

---

### Performance Tips

**Use Scoped Searches:**
```javascript
// Faster, more relevant
search_code("validation", {
  path_glob: ["src/api/**"],
  lang: ["python"]
});

// Slower, less relevant
search_code("validation");
```

**Enable File Watching:**
```bash
# Real-time updates during development
pampa watch
```

**Use Reranker for Critical Searches:**
```javascript
// High-precision (slower)
search_code("payment processing", {reranker: "transformers"});

// Fast (good enough)
search_code("helper functions");
```

**Leverage Context Packs:**
```javascript
// Activate domain-specific scope
use_context_pack("stripe-backend");

// All searches now scoped automatically
search_code("create session");  // Fast + relevant
```

---

### Interpreting Results

**Similarity Scores:**
- `> 0.7`: Excellent match, highly relevant
- `> 0.5`: Good match, worth examining
- `> 0.3`: Moderate match, might be useful
- `< 0.3`: Poor match, probably not relevant

**Use get_code_chunk for Context:**
```javascript
const results = search_code("database connection");

// Check similarity first
if (results[0].similarity > 0.7) {
  const chunk = get_code_chunk(results[0].sha);
  console.log(chunk.code);
}
```

---

## Troubleshooting

### PAMPA Tools Not Available

**Check MCP Configuration:**
1. Verify `.vscode/settings.json` has `mcpServers.pampa`
2. Ensure `command: "npx"` and `args: ["-y", "pampa", "mcp"]`
3. Check environment variables: `OLLAMA_BASE_URL`, `OLLAMA_EMBEDDING_MODEL`

**Verify Installation:**
```bash
npx pampa --version
```

**Enable Debug Mode:**
```json
{
  "mcpServers": {
    "pampa": {
      "command": "npx",
      "args": ["-y", "pampa", "mcp", "--debug"]
    }
  }
}
```

---

### Indexing Fails

**Check Embedding Provider:**
- Transformers.js (free, local, slower)
- Ollama (free, local, fast if server running)
- OpenAI (paid, cloud, fast)
- Cohere (paid, cloud, fast)

**Verify Project Structure:**
- Must be a valid code project
- Supported file types: `.py`, `.js`, `.ts`, `.php`, `.java`, `.go`, `.rs`, `.c`, `.cpp`, etc.

**Check Disk Space:**
- Indexing creates `.pampa/` directory
- ~1MB per 1000 functions

---

### Search Returns No Results

**Verify Indexing:**
```bash
pampa info
```

**Check Query:**
- Use semantic descriptions, not exact code
- Try broader queries: "user" instead of "create_user_account"

**Update Index:**
```bash
pampa update
```

---

### Slow Search Performance

**Use Scoped Filtering:**
```javascript
search_code("validation", {
  path_glob: ["src/**"],
  lang: ["python"]
});
```

**Disable Reranker:**
```javascript
search_code("helper", {reranker: "off"});
```

**Reduce Result Limit:**
```javascript
search_code("config", {limit: 5});
```

---

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_EMBEDDING_MODEL` | Ollama embedding model | `nomic-embed-text-v2-moe` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `COHERE_API_KEY` | Cohere API key | `...` |
| `PAMPA_ENCRYPTION_KEY` | 32-char encryption key | `your-32-char-key-here` |

---

## File Structure

```
project-root/
├── .env                         # Environment configuration
├── .gitignore                   # Git ignore (.pampa/ excluded)
├── pampa.codemap.json           # Git-friendly function metadata
└── .pampa/
    ├── pampa.db                 # SQLite database (embeddings + chunks)
    ├── chunks/                  # Compressed code chunks (.gz)
    │   ├── abc123def456.gz
    │   └── def789ghi012.gz
    └── contextpacks/            # Context pack definitions
        ├── stripe-backend.json
        └── react-components.json
```

---

## Version History

**v1.12+ (Current):**
- Hybrid search (BM25 + vector) enabled by default
- Cross-encoder reranking support
- Symbol-aware ranking boost
- Context packs for scoped searches
- Advanced filtering (path_glob, tags, lang)

**v1.11:**
- MCP server integration
- Multi-provider support (OpenAI, Ollama, Cohere, Transformers.js)
- Git-friendly codemap.json

**v1.10:**
- Initial release
- Semantic code search
- CLI tools

---

## Links

- **GitHub**: [PAMPA Repository](https://github.com/pampa-ai/pampa) (assumed)
- **MCP Protocol**: [Model Context Protocol](https://modelcontextprotocol.io/)
- **Ollama**: [Ollama Documentation](https://ollama.ai/)
- **Transformers.js**: [Xenova Transformers.js](https://github.com/xenova/transformers.js)

---

**Last Updated:** November 25, 2025  
**Configuration Status:** ✅ Ollama (nomic-embed-text-v2-moe), 1,439 functions indexed  
**Project:** software/homeamp-config-manager
