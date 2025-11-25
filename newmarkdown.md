# GitHub Copilot Instructions for ArchiveSMP Configuration Manager

## CRITICAL: Development Environment Context

**YOU ARE WORKING IN THE DEVELOPER'S HOME WINDOWS PC - THIS IS THE DEVELOPMENT ENVIRONMENT**

### Environment Setup:
- **Location**: Developer's Windows PC at `d:\homeamp.ampdata\`
- **Purpose**: Software development and testing environment
- **Data Structure**:
  - `utildata/`: Contains replicated server config state from production
    - Snapshots from both bare metal servers (Hetzner and OVH)
    - All instances reflected as they were at time of snapshot
  - `software/homeamp-config-manager/`: The actual software being built
- **Your Access**: You do NOT have direct access to production servers

### Production Servers:
- **Hetzner Xeon** (archivesmp.site, 135.181.212.169): First deployment target
  - 11 instances currently deployed and running
  - Services: archivesmp-webapi.service, homeamp-agent.service
  - MariaDB runs locally on this server (no `-h` or `-P` needed for mysql commands)
- **OVH Ryzen** (archivesmp.online, 37.187.143.41): Second deployment target (pending)
- **Access Model**: Developer has RDP access via Nom Machine (NOT SSH)
- **Your Role**: Provide commands for the developer to execute on production via RDP terminal

### User Accounts & Permissions:
- **webadmin**: Admin user for sudo commands and system operations
- **amp**: Application user - runs all services and agents
- **Development Rule**: Avoid hardcoded values; features should dynamically detect what agents find

### Workflow Rules:

#### DO:
- ✅ Fix all code in the local development environment first (`d:\homeamp.ampdata\software\homeamp-config-manager\`)
- ✅ Test locally when possible
- ✅ Provide clear, copy-paste ready bash/shell commands for production deployment
- ✅ Commit all working fixes to the local repo before deploying to second server
- ✅ Use tools like `replace_string_in_file`, `create_file` on local files
- ✅ Provide direct commands that developer can run via SSH

#### DO NOT:
- ❌ Attempt to modify files on production servers directly with tools
- ❌ Assume you're on the production server when using tools
- ❌ Tell the developer to "upload" files without providing the exact commands
- ❌ Create complex multi-step solutions when simple sed/script commands work
- ❌ Use relative imports or assumptions about production file structure

### Command Format for Production:
When providing commands to run on production (Debian 12), format them as:

```bash
# Clear description of what this does
# Run as webadmin user for sudo operations
sudo <command>
```

**Local Commands (Windows PowerShell/CMD):**
```cmd
REM Description
<command>
```

**Important:**
- MariaDB on Hetzner: Use `mysql -u sqlworkerSMP -p asmp_config` (local connection, no host/port)
- Production access: Via RDP/Nom Machine, NOT SSH
- Sudo user: `webadmin`
- Service user: `amp`

### Deployment Process:
1. **Fix Locally**: Edit code in `d:\homeamp.ampdata\software\homeamp-config-manager\`
2. **Test**: Verify syntax, logic locally if possible
3. **Generate Fix Script**: Create Python script or sed command to apply fix
4. **Provide Command**: Give developer exact command to run on production
5. **Verify**: Developer runs command and provides log output
6. **Commit**: Once working, commit to repo for next deployment

### Current State:
- Web API: Running on Hetzner, port 8000, 4 workers
- Agent: Running on Hetzner, discovering 11 instances
- Database: MariaDB on localhost:3369 (not default 3306)
- Code Formatting: Black (120 line length), Pylint, isort, Prettier configured

### File Locations:
- **Local Dev**: `d:\homeamp.ampdata\software\homeamp-config-manager\`
- **Production**: `/opt/archivesmp-config-manager/`
- **Production Config**: `/etc/archivesmp/agent.yaml`
- **Production Data**: `/var/lib/archivesmp/`
- **Production Logs**: `/var/log/archivesmp/` and `journalctl -u <service>`

## Project Context

This is a configuration management system for managing Minecraft server plugin configurations across multiple AMP (Application Management Panel) instances on two bare metal servers. The system detects configuration drift, manages plugin updates, and provides a web interface for review and deployment.

### Critical Instruction: Always Verify Before Making Architectural Claims

**BEFORE making claims about what the system can/cannot do:**
1. ✅ **Ask for evidence**: Request logs, config files, actual behavior
2. ✅ **State certainty level**: Use "I assume..." vs "The logs show..." vs "I don't know..."
3. ✅ **Ask clarifying questions**: Don't fill gaps with assumptions
4. ✅ **Request verification**: "Can you run X command to confirm Y?"
5. ✅ **Check deployment state**: What's actually installed where?

**NEVER assume without evidence:**
- ❌ What's deployed on which server
- ❌ Network topology or connectivity
- ❌ Service capabilities without reading actual logs
- ❌ Architecture limitations without testing
- ❌ Why something isn't working without diagnostics

**Both human and AI can be wrong - always verify critical facts before proposing solutions**

## PAMPA Code Memory System

**🤖 MANDATORY WORKFLOW - This is your project memory. Use it continuously to avoid duplicating work and understand existing codebase architecture.**

### Configuration:
- **Provider**: `ollama`
- **Embedding Model**: `nomic-embed-text-v2-moe`
- **Reranker Model**: `mxbai-rerank-large-v2`
- **Indexed**: 1,439 functions (1,188 Python, 251 JavaScript)
- **Project Path**: `software/homeamp-config-manager`
- **Database**: `.pampa/` directory (gitignored)

---

### 🔄 ALWAYS Start Every Session With This:

```
1. get_project_stats(path="software/homeamp-config-manager")
   → Check project status and statistics
   
2. update_project(path="software/homeamp-config-manager", provider="ollama")
   → Sync with recent changes (new/modified/deleted functions)
   
3. search_code(query="main application logic", limit=10, path="software/homeamp-config-manager", hybrid="on", bm25="on", reranker="transformers", symbol_boost="on")
   → Understand project structure
```

**Why**: Ensures your memory is current and you understand the codebase before making changes.

---

### 🔍 Smart Search Strategies

**Be semantic, not literal:**
- ✅ `search_code(query="user authentication logic")`
- ❌ `search_code(query="login() function")`

**Use context:**
- ✅ `search_code(query="error handling for API calls")`
- ❌ `search_code(query="error")`

**Check variations:**
- ✅ `search_code(query="create user OR add user OR register user OR new user")`

**Explore related concepts:**
- After finding auth → search "validation", "security", "permissions"

**Scope your searches:**
- ✅ `search_code(query="payment processing", path_glob=["src/api/**"], lang=["python"])`
- ✅ `search_code(query="database connection", path_glob=["src/database/**"])`

---

### ⚡ Complete Development Workflow

#### 1. Project Discovery (New Session)
```
1. get_project_stats() → Overview
2. search_code("main entry point") → Find starting point
3. search_code("configuration") → Find config files
4. search_code("API endpoints") → Find interfaces
5. search_code("database") → Find data layer
```

#### 2. Before Creating Any Function
```
1. search_code("similar functionality description", limit=10, hybrid="on", reranker="transformers")
2. search_code("related helper functions")
3. search_code("validation patterns")
4. get_code_chunk(sha=<interesting_result>) → Study existing patterns
5. Only create if nothing suitable exists or can be extended
```

**Example:**
```
User: "Add user validation for email addresses"

Step 1: search_code("email validation")
Step 2: search_code("user input validation")
Step 3: search_code("validation helper functions")
Step 4: get_code_chunk(sha=<best_match>)
Step 5: Extend existing validator OR create new one following patterns
```

#### 3. During Development
```
✅ search_code("description of your planned function") → Check for duplicates
✅ search_code("utility helper functions") → Find existing utilities
✅ search_code("validation patterns") → Follow established patterns
✅ search_code("error handling") → Use consistent error patterns
```

**Advanced Scoping:**
```
# Search only in API layer
search_code("request validation", path_glob=["src/api/**"], lang=["python"])

# Search only in agent components
search_code("instance discovery", path_glob=["src/agent/**"])

# Search with hybrid search for better recall
search_code("configuration parsing", hybrid="on", bm25="on", reranker="transformers")
```

#### 4. After Making Changes
```
1. update_project(path="software/homeamp-config-manager", provider="ollama")
   → Index your changes immediately
   
2. search_code("your new function name")
   → Verify indexing worked
   
3. search_code("related functionality")
   → Check integration points
```

---

### 🔧 Available MCP Tools Reference

#### `search_code(query, limit=10, path=".", ...)`
**Purpose**: Advanced semantic search with scoping and hybrid ranking

**Basic Parameters:**
- `query`: Natural language description ("user validation", "error handling")
- `limit`: Number of results (default: 10)
- `path`: Project root (use `"software/homeamp-config-manager"`)

**Advanced Filtering & Ranking:**
- `path_glob`: Filter by file patterns (e.g., `["src/api/**"]`, `["src/agent/**"]`)
- `tags`: Filter by semantic tags (e.g., `["database", "mysql"]`)
- `lang`: Filter by language (e.g., `["python"]`, `["javascript"]`)
- `provider`: Override embedding provider (`"ollama"`, `"transformers"`)
- `hybrid`: Enable hybrid search (`"on"`, `"off"`) - **DEFAULT: "on"**
- `bm25`: Enable BM25 keyword search (`"on"`, `"off"`) - **DEFAULT: "on"**
- `reranker`: Use cross-encoder reranker (`"transformers"`, `"off"`) - **DEFAULT: "transformers"**
- `symbol_boost`: Enable symbol-aware ranking (`"on"`, `"off"`) - **DEFAULT: "on"**

**Returns**: Array of `{file, symbol, line, similarity, sha, meta}`

**Interpreting Results:**
- **Similarity > 0.7**: Excellent match, highly relevant
- **Similarity > 0.5**: Good match, worth examining
- **Similarity > 0.3**: Moderate match, might be useful
- **Similarity < 0.3**: Poor match, probably not relevant

**Examples:**
```javascript
// Basic semantic search
search_code("user authentication logic", limit=5, path="software/homeamp-config-manager")

// Scoped to API layer
search_code("endpoint validation", path_glob=["src/api/**"], lang=["python"])

// Maximum precision with all features
search_code("database transaction handling", 
  limit=10,
  path="software/homeamp-config-manager",
  path_glob=["src/database/**"],
  lang=["python"],
  hybrid="on",
  bm25="on", 
  reranker="transformers",
  symbol_boost="on"
)
```

#### `get_code_chunk(sha, path=".")`
**Purpose**: Retrieve complete source code of a specific chunk

- `sha`: SHA identifier from search results
- `path`: Project root (use `"software/homeamp-config-manager"`)
- **Returns**: Complete source code with context

**Example:**
```javascript
// After search_code returns results
get_code_chunk(sha="abc123def456", path="software/homeamp-config-manager")
```

#### `index_project(path=".", provider="auto")`
**Purpose**: Create initial project index (first time setup)

- `path`: Directory to index
- `provider`: Embedding provider (`"ollama"`, `"transformers"`, `"openai"`)
- **Creates**: `.pampa/` directory with database and chunks

**You should NOT need to call this - project is already indexed.**

#### `update_project(path=".", provider="auto")`
**Purpose**: Update index after code changes (use frequently!)

- `path`: Project directory (use `"software/homeamp-config-manager"`)
- `provider`: Embedding provider (use `"ollama"`)
- **Updates**: Adds new functions, removes deleted ones, updates modified

**Call this:**
- ✅ At start of every session
- ✅ After creating/modifying/deleting any functions
- ✅ After user makes changes outside your view

**Example:**
```javascript
update_project(path="software/homeamp-config-manager", provider="ollama")
```

#### `get_project_stats(path=".")`
**Purpose**: Get project overview and statistics

- `path`: Project directory (use `"software/homeamp-config-manager"`)
- **Returns**: File counts, languages, function statistics

**Example Response:**
```json
{
  "total_functions": 1439,
  "languages": ["python", "javascript"],
  "files_by_language": {
    "python": 94,
    "javascript": 12
  }
}
```

---

### 🎯 Sample Prompts for Common Tasks

#### Understanding a New Project
```
🔍 "Let me explore this codebase structure"
→ get_project_stats(path="software/homeamp-config-manager")

🔍 "Show me the main application logic"
→ search_code("main application entry point", limit=10, hybrid="on")

🔍 "Find authentication and security functions"
→ search_code("authentication security login", limit=10)
```

#### Before Coding
```
🔍 "Does this project have user validation?"
→ search_code("user validation input validation", limit=10)

🔍 "How is error handling implemented?"
→ search_code("error handling exception handling", limit=10)

🔍 "Are there existing API endpoints?"
→ search_code("API endpoint route handler", path_glob=["src/api/**"])

🔍 "What database operations exist?"
→ search_code("database query CRUD operations", path_glob=["src/database/**"])
```

#### During Development
```
🔍 "Find functions similar to what I'm building"
→ search_code("description of your planned function", limit=10, hybrid="on")

🔍 "Check existing utility functions"
→ search_code("utility helper functions", limit=10)

🔍 "Look for validation patterns"
→ search_code("validation pattern schema", limit=10)

🔍 "Focus search on specific directories"
→ search_code("payment processing", path_glob=["src/api/**"], lang=["python"])

🔍 "Get better results with hybrid search"
→ search_code("checkout flow", hybrid="on", reranker="transformers")
```

#### After Coding
```
🔄 "Update the project index with my changes"
→ update_project(path="software/homeamp-config-manager", provider="ollama")

🔍 "Verify my new function was indexed"
→ search_code("your new function name", limit=5)

🔍 "Check integration with existing code"
→ search_code("related functionality", limit=10)
```

---

### 🚨 Critical Reminders

#### DO THIS ALWAYS:
- ✅ Start sessions with `get_project_stats()` and `update_project()`
- ✅ Search before creating any new function
- ✅ Update after changes with `update_project()`
- ✅ Use semantic queries not exact function names
- ✅ Use scoped searches for better precision: `path_glob`, `lang`, `tags`
- ✅ Enable all performance features: `hybrid="on"`, `bm25="on"`, `reranker="transformers"`, `symbol_boost="on"`
- ✅ Study existing code with `get_code_chunk()` before writing new code
- ✅ Follow existing patterns and conventions found in searches

#### NEVER DO THIS:
- ❌ Skip searching before writing code
- ❌ Forget to update after making changes
- ❌ Search with exact code instead of descriptions
- ❌ Ignore existing implementations that could be extended
- ❌ Search entire codebase when you can scope to relevant areas
- ❌ Create duplicate functionality that already exists
- ❌ Assume you know what's in the codebase without searching

---

### 🎉 Success Stories

**Before PAMPA:**
- "I'll create a new validation function"

**With PAMPA:**
- "Let me search for existing validation → Found 3 similar functions → Extended the best one"

---

**Before PAMPA:**
- "I need an API endpoint for users"

**With PAMPA:**
- "Searched for API patterns → Found consistent structure → Followed same pattern"

---

**Before PAMPA:**
- "Where's the database connection code?"

**With PAMPA:**
- `search_code('database connection')` → Found in 2 seconds

---

### 🚨 Troubleshooting

**If PAMPA tools are not available:**
1. Inform user that PAMPA MCP server may not be configured
2. Ask them to check MCP configuration in Claude/Cursor settings
3. Verify with `npx pampa --version`

**If indexing fails:**
1. Check if `.pampa/` directory exists
2. Verify Ollama is running with `nomic-embed-text-v2-moe` model
3. Try running `npx pampa update` manually

**If search results are poor:**
1. Use more semantic descriptions
2. Enable hybrid search: `hybrid="on"`
3. Use scoped searches: `path_glob`, `lang`
4. Enable reranker: `reranker="transformers"`

---

## Context7 Library Documentation Usage

**ALWAYS use Context7 tools when working with external libraries or frameworks:**

### When to Use Context7:
1. ✅ **Before generating code** for any external library (FastAPI, Bootstrap, Jinja2, SQLAlchemy, etc.)
2. ✅ **When debugging** import errors, API changes, or deprecated methods
3. ✅ **When user mentions** a specific library or asks "how do I use X"
4. ✅ **When implementing new features** that require library-specific patterns
5. ✅ **When upgrading** or changing library versions

### How to Use:
1. First call `mcp_context7_resolve-library-id` with the library name (e.g., "FastAPI", "Bootstrap", "Jinja2")
2. Then call `mcp_context7_get-library-docs` with the resolved library ID and relevant topic
3. Use the documentation to generate accurate, up-to-date code

### Example Workflow:
```
User: "Add a new FastAPI endpoint for uploading files"
→ Call mcp_context7_resolve-library-id(libraryName="FastAPI")
→ Call mcp_context7_get-library-docs(context7CompatibleLibraryID="/tiangolo/fastapi", topic="file upload")
→ Generate code using the latest API patterns from documentation
```

### Libraries We Use:
- **FastAPI**: Web framework for APIs
- **Jinja2**: Template engine
- **Bootstrap 4/5**: Frontend CSS framework
- **SQLAlchemy**: Database ORM (if we add it)
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server
- **mysql-connector-python**: MySQL driver

**Don't assume you know the API - verify with Context7 first!**

---

## Code Quality Standards

### Formatting (Enforced):
- **Python**: Black formatter, 120 line length, Python 3.11 target
- **JavaScript/JSON/YAML**: Prettier, 120 print width, trailing commas ES5
- **Imports**: isort with black profile
- **Linting**: Pylint with relaxed docstring rules

### formatOnSave Enabled:
- Python files auto-format with Black
- JS/JSON/YAML auto-format with Prettier
- All files configured in `.vscode/settings.json`

### Configuration Files:
- `pyproject.toml`: Black/isort/pylint settings
- `.prettierrc`: Prettier configuration
- `.prettierignore`: Prettier exclusions

### Before Committing:
```bash
# Format all Python files
python -m black src/ --line-length 120

# Check for syntax errors
python -m py_compile src/**/*.py
```

---

## Summary: The PAMPA-Powered Development Cycle

1. **Session Start**:
   ```
   get_project_stats() → update_project() → search_code("main logic")
   ```

2. **Before Writing Code**:
   ```
   search_code("similar functionality") → get_code_chunk(sha) → Study patterns
   ```

3. **During Development**:
   ```
   search_code("helpers") → search_code("validation") → Use existing code
   ```

4. **After Changes**:
   ```
   update_project() → search_code("new function") → Verify indexing
   ```

**🤖 Remember: PAMPA is your perfect memory. Use it continuously to avoid duplicating work and understand existing architecture!**

