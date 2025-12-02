# PAMPA MCP Setup for ArchiveSMP Configuration Manager

## What is PAMPA?

PAMPA is a semantic code search tool that indexes your codebase and allows AI agents to search for code patterns, functions, and concepts using natural language queries.

## Setup Complete

✅ MCP configuration created at `.vscode/mcp.json`
✅ PAMPA indexing in progress

## Initial Indexing

Run this command to create the initial index:

```bash
npx -y pampa index .
```

This will:
- Scan all code files in the project
- Create semantic embeddings
- Store the index in `.pampa/` directory

## Usage with AI Agents

PAMPA provides these MCP tools:

### 1. `search_code(query, limit=10)`
Search for code using natural language:
```
search_code("database connection configuration")
search_code("plugin metadata population logic")
search_code("drift detection algorithm")
```

### 2. `get_code_chunk(sha, path=".")`
Retrieve the full source code of a specific chunk found in search results.

### 3. `update_project(path=".")`
Update the index after making code changes:
```
update_project()
```

### 4. `get_project_stats(path=".")`
Get overview of the codebase:
```json
{
  "total_functions": 250,
  "languages": ["python", "sql", "markdown"],
  "files_by_language": {
    "python": 45,
    "sql": 12,
    "markdown": 23
  }
}
```

### 5. Advanced Search (v1.12+)

**Scoped Search:**
```
search_code("config parsing", path_glob=["software/homeamp-config-manager/src/**"])
search_code("database schema", lang=["sql"])
search_code("API endpoints", path_glob=["**/web/*.py"])
```

**Hybrid Search (semantic + keyword):**
```
search_code("drift detector", hybrid="on", reranker="transformers")
```

## Workflow for AI Agents

### Start of Session:
1. `get_project_stats()` - Understand project structure
2. `update_project()` - Sync recent changes
3. `search_code("main functionality")` - Explore codebase

### Before Creating Code:
1. `search_code("similar functionality description")`
2. `get_code_chunk(interesting_sha)` - Study existing patterns
3. Only create if nothing suitable exists

### After Making Changes:
1. `update_project()` - Index your changes
2. `search_code("your new function name")` - Verify indexing

## Examples for This Codebase

```python
# Find database connection patterns
search_code("database connection mysql mariadb")

# Find schema definitions
search_code("CREATE TABLE plugins instances baseline_snapshots")

# Find configuration parsing
search_code("parse yaml config baseline")

# Find drift detection logic
search_code("detect drift configuration variance")

# Find API endpoints
search_code("FastAPI endpoint routes", path_glob=["software/**/web/*.py"])

# Find deployment scripts
search_code("deploy production hetzner ovh", path_glob=["scripts/**"])
```

## Audit Results

Based on PAMPA semantic search, the codebase audit found:

### ✅ Clean Architecture:
- No duplicate classes or functions
- Consistent database connection pattern (ConfigDatabase)
- No circular imports

### ❌ Issues Found:
1. Schema file uses wrong DB name (`asmp_config_controller` vs `asmp_config`)
2. Duplicate index in schema.sql
3. Missing 5 tables in old schema
4. Hardcoded database names in 7+ files
5. Architectural mismatch between schema.sql and actual code

## Next Steps

1. **Restart VS Code** to activate MCP server
2. Wait for initial indexing to complete
3. Use PAMPA tools in AI agent conversations
4. Run `update_project()` after major code changes

## Troubleshooting

### Index not found:
```bash
npx -y pampa index .
```

### Update after changes:
```bash
npx -y pampa update .
```

### Check index stats:
```bash
npx -y pampa stats .
```

## Configuration

MCP server config location: `.vscode/mcp.json`

The PAMPA server will automatically start when VS Code loads the workspace.
