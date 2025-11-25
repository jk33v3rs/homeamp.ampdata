# PAMPA MCP Usage Rule

You have access to PAMPA, a code memory system that indexes and allows semantic search in projects.

## Basic Instructions

1. **ALWAYS at the start of a session:**
   - Run `get_project_stats` to check if the project is indexed
   - If no database exists, run `index_project`
   - Run `update_project` to sync with recent changes

2. **BEFORE creating any function:**
   - Use `search_code` with semantic queries like "user authentication", "validate email", "error handling"
   - Review existing code with `get_code_chunk` before writing new code

3. **AFTER modifying code:**
   - Run `update_project` to update the knowledge base
   - This keeps the project memory synchronized

## Available Tools

- `search_code(query, limit, path, filters...)` - 🆕 Advanced semantic search with scoping
- `get_code_chunk(sha, path)` - Get complete code of a chunk
- `index_project(path, provider)` - Index project for the first time
- `update_project(path, provider)` - Update index after changes
- `get_project_stats(path)` - Get project statistics
- `use_context_pack(name, path)` - 🆕 Activate predefined search scopes

## Strategy

Use PAMPA as your project memory. Search before creating, keep updated after changes, and leverage existing knowledge to avoid code duplication.

## 🔄 ALWAYS Start Every Session With This

```
1. get_project_stats() → Check if project is indexed
2. update_project() → Sync with recent changes
3. search_code("main functionality") → Understand project structure
```

## 🔍 Smart Search Strategies

Be semantic, not literal:
- ✅ "user authentication logic"
- ❌ "login() function"

Use context:
- ✅ "error handling for API calls"
- ❌ "error"

Check variations:
- ✅ "create user", "add user", "register user", "new user"

Explore related concepts:
- After finding auth → search "validation", "security", "permissions"

## 🎯 Advanced Usage Patterns

### Project Discovery
```
1. get_project_stats() → Overview
2. search_code("main entry point") → Find starting point
3. search_code("configuration") → Find config files
4. search_code("API endpoints") → Find interfaces
5. search_code("database") → Find data layer
```

### Before Creating Any Function
```
1. search_code("similar functionality description")
2. search_code("related helper functions")
3. search_code("validation patterns")
4. get_code_chunk(interesting_results) → Study patterns
5. Only create if nothing suitable exists
```

### After Making Changes
```
1. update_project() → Index your changes
2. search_code("your new function name") → Verify indexing
3. search_code("related functionality") → Check integration
```

## 🔧 Available MCP Tools Reference

### `search_code(query, limit=10, path=".", ...filters)`

Purpose: Advanced semantic search with scoping and hybrid ranking

Basic Parameters:
- `query`: Natural language description ("user validation", "error handling")
- `limit`: Number of results (default: 10)
- `path`: Project root directory (usually current directory)

🆕 NEW: Advanced Filtering & Ranking:
- `path_glob`: Filter by file patterns (e.g., "app/Services/", "src/components/")
- `tags`: Filter by semantic tags (e.g., ["stripe", "payment"])
- `lang`: Filter by languages (e.g., ["php", "typescript"])
- `provider`: Override embedding provider ("auto", "openai", "transformers")
- `hybrid`: Enable hybrid search ("on", "off") - combines semantic + keyword
- `bm25`: Enable BM25 keyword search ("on", "off")
- `reranker`: Use cross-encoder reranker ("off", "transformers")
- `symbol_boost`: Enable symbol-aware ranking ("on", "off")

Returns: Array of {file, symbol, line, similarity, sha, meta}

### `get_code_chunk(sha, path=".")`

Purpose: Retrieve complete source code of a specific chunk
- `sha`: SHA identifier from search results
- `path`: Project root directory
- Returns: Complete source code with context

### `index_project(path=".", provider="auto")`

Purpose: Create initial project index (first time setup)
- `path`: Directory to index
- `provider`: Embedding provider (auto/openai/transformers/ollama/cohere)
- Creates: `.pampa/` directory with database and chunks

### `update_project(path=".", provider="auto")`

Purpose: Update index after code changes (use frequently!)
- `path`: Directory to update
- `provider`: Embedding provider
- Updates: Adds new functions, removes deleted ones, updates modified

### `get_project_stats(path=".")`

Purpose: Get project overview and statistics
- `path`: Directory to analyze
- Returns: File counts, languages, function statistics

### `use_context_pack(name, path=".")` 🆕

Purpose: Activate predefined search scopes and filters
- `name`: Context pack name (e.g., "stripe-backend", "react-components")
- `path`: Project root directory
- Effect: Sets default filters for subsequent `search_code` calls
- Use case: Focus searches on specific domains or technologies

## 📊 Interpreting Results

### Search Results Quality
- Similarity > 0.7: Excellent match, highly relevant
- Similarity > 0.5: Good match, worth examining
- Similarity > 0.3: Moderate match, might be useful
- Similarity < 0.3: Poor match, probably not relevant

## 🚨 Critical Reminders

### DO THIS ALWAYS:
- ✅ Start sessions with `get_project_stats()` and `update_project()`
- ✅ Search before creating any new function
- ✅ Update after changes with `update_project()`
- ✅ Use semantic queries not exact function names
- 🆕 ✅ Use scoped searches for better precision: `path_glob`, `lang`, `tags`
- 🆕 ✅ Leverage context packs for domain-specific work
- 🆕 ✅ Enable hybrid search for better recall (default in v1.12+)

### NEVER DO THIS:
- ❌ Skip searching before writing code
- ❌ Forget to update after making changes
- ❌ Search with exact code instead of descriptions
- ❌ Ignore existing implementations that could be extended
- 🆕 ❌ Search entire codebase when you can scope to relevant areas
- 🆕 ❌ Ignore context packs that match your current task domain

## 🆕 New in v1.12: Advanced Features

### 🎯 Scoped Search Examples
```javascript
// Search only in service layer
search_code('payment processing', { path_glob: ['app/Services/**'] });

// Search PHP backend only
search_code('user authentication', { lang: ['php'] });

// Search with tags
search_code('create session', { tags: ['stripe', 'payment'] });

// Combine multiple scopes
search_code('validation', {
    path_glob: ['app/Http/**'],
    lang: ['php'],
    tags: ['api']
});
```

### 🔄 Hybrid Search Benefits
- Better recall: Finds functions even with different terminology
- Keyword + semantic: Combines exact matches with meaning-based search
- Default enabled: No configuration needed in v1.12+

### 📦 Context Packs Workflow
```javascript
// 1. Activate domain-specific context
use_context_pack('stripe-backend');

// 2. All searches now automatically scoped
search_code('create payment');      // → Only Stripe backend results
search_code('handle webhook');      // → Only Stripe webhook handlers
search_code('refund transaction');  // → Only Stripe refund logic
```

### ⚡ Performance Tips
- Use scoped searches for faster, more relevant results
- Enable file watching (`pampa watch`) for real-time updates
- Use reranker for critical searches: `reranker: "transformers"`
- Leverage symbol boost for function-specific searches

.## 🚨 Troubleshooting for AI Agents

### If PAMPA tools are not available:
1. Check MCP configuration: Ensure your human configured the MCP server correctly
2. Verify installation: Ask them to run `npx pampa --version`
3. Enable debug mode: Add `--debug` to MCP args for detailed logs
4. Check permissions: Ensure write access to project directory

### If indexing fails:
1. Check embedding provider: Transformers.js (free) vs OpenAI (requires API key)
2. Verify project structure: Must be a valid code project with supported files
3. Check disk space: Indexing creates `.pampa/` directory with database

🤖 Remember: PAMPA is your project memory. Use it continuously to avoid duplicating work and to understand existing codebase architecture. It's like having perfect memory of every function ever written in the project!
