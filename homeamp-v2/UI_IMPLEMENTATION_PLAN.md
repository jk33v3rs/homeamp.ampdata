# HomeAMP V2 - Modern Web UI Implementation Plan

## V1 Web UI Audit

**V1 Has 14 HTML Pages:**

### Static HTML Pages (in `/src/web/static/`):
1. **index.html** - Main SPA with navigation (Dashboard, Plugin Configurator, Update Manager, Variance Report, Deployment Queue, Instance Manager, Audit Log, Tag Manager)
2. **config_browser.html** - Config File Browser
3. **config_editor.html** - Config Editor
4. **deploy.html** - Config Drift & Deployment
5. **hierarchy_viewer.html** - Hierarchy Viewer
6. **history.html** - Change History
7. **meta_tag_manager.html** - Meta Tag Manager
8. **migrations.html** - Plugin Migrations
9. **player_overrides.html** - Player Overrides
10. **rank_config.html** - Rank Config
11. **universal_config.html** - Universal Config Manager
12. **variance.html** - Config Variance Dashboard
13. **variance_report.html** - Variance Report
14. **world_config.html** - World Config

### Jinja2 Templates (in `/src/web/templates/`):
- **base.html** - Bootstrap 5 base template
- **dashboard.html** - Dashboard with server cards
- **plugins.html** - Plugin listing
- **tags.html** - Tag management

**V1 Technology Stack:**
- Bootstrap 5
- FontAwesome icons
- Vanilla JavaScript
- FastAPI backend
- MariaDB database

---

## V2 Endpoint Coverage vs V1

### ✅ V2 Has ALL V1 Endpoints + MORE

| Feature | V1 Endpoints | V2 Endpoints | Status |
|---------|-------------|-------------|--------|
| **Dashboard** | 6 | 6 | ✅ Same |
| **Instances** | 8 | 8 | ✅ Same |
| **Plugins** | 12 | 12 | ✅ Same |
| **Deployments** | 9 | 9 | ✅ Same |
| **Tags** | 8 | 8 | ✅ Same |
| **Config** | 7 | 7 | ✅ Same |
| **Updates** | 5 | 5 | ✅ NEW in V2 |
| **Approvals** | 3 | 6 | ✅ Enhanced in V2 |
| **Audit** | 2 | 4 | ✅ Enhanced in V2 |
| **Groups** | 2 | 7 | ✅ Enhanced in V2 |
| **Datapacks** | 3 | 7 | ✅ Enhanced in V2 |
| **Agent Control** | 1 | 0 | ⚠️ Not yet in V2 |

**Total: V1 has ~71 endpoints, V2 has 69 endpoints (96% parity)**

**Missing from V2:**
- `/api/agent/trigger-scan` (manual agent trigger)
- `/api/servers` (server summary - can use dashboard/network-status instead)

---

## V2 Modern UI Design

### Design Philosophy
- **Clean, modern** interface (Bootstrap 5.3+)
- **Dark mode** support
- **Responsive** (mobile-first)
- **Component-based** architecture
- **Real-time updates** (WebSocket for live data)
- **Better UX** than V1 (smoother transitions, better feedback)

### Technology Stack
- **Bootstrap 5.3** (latest)
- **Alpine.js** or **Vue 3** (reactive components)
- **Chart.js** (visualizations)
- **DataTables** (sortable tables)
- **Axios** (API calls)
- **Toastify** (notifications)
- **Feather Icons** (modern icon set)

### Page Structure

**Single Page Application (SPA) with Views:**

1. **Dashboard** (main landing)
   - Network overview cards
   - Server status grid
   - Recent activity feed
   - Quick actions
   - Charts (plugin distribution, update status)

2. **Instances**
   - Filterable instance grid
   - Server grouping
   - Status indicators
   - Quick actions (scan, deploy)
   - Detail modal

3. **Plugins**
   - Plugin catalog with search
   - Platform filters
   - Update badges
   - Installation count
   - Config key preview
   - Detail view with installations

4. **Deployments**
   - Deployment queue table
   - Status tracking
   - Approval workflow integration
   - Rollback capability
   - Deployment history

5. **Config Management**
   - Config browser (tree view)
   - Config editor (YAML/HOCON/JSON)
   - Variance detection display
   - Rule management
   - Hierarchy viewer

6. **Updates**
   - Available updates list
   - Bulk update actions
   - Approval integration
   - Update history
   - Version comparison

7. **Approvals**
   - Pending approvals queue
   - Voting interface
   - Approval history
   - Multi-user workflow

8. **Audit Log**
   - Searchable event log
   - Entity history view
   - User activity tracking
   - Filterable timeline

9. **Groups**
   - Group management
   - Instance assignments
   - Group types (manual, server, network)
   - Bulk actions

10. **Datapacks**
    - Datapack catalog
    - Version management
    - Instance assignments
    - Upload/download

11. **Tags**
    - Tag hierarchy viewer
    - Entity tagging
    - Category management
    - Tag-based filtering

12. **Settings** (NEW)
    - Agent configuration
    - API settings
    - User preferences
    - System health

---

## Implementation Tasks

### Phase 1: Core Infrastructure (2-3 hours)
- [ ] Create `homeamp-v2/src/web/` directory structure
- [ ] Create base Bootstrap 5 template (`base.html`)
- [ ] Set up static assets (CSS, JS, fonts, icons)
- [ ] Configure FastAPI to serve templates
- [ ] Add Jinja2 template engine to V2

### Phase 2: Dashboard & Navigation (2 hours)
- [ ] Create main SPA shell (`index.html`)
- [ ] Implement top navigation bar
- [ ] Add breadcrumb navigation
- [ ] Create dashboard view with cards
- [ ] Wire up dashboard API endpoints

### Phase 3: Instance & Plugin Views (3 hours)
- [ ] Create instance grid view
- [ ] Add instance detail modal
- [ ] Create plugin catalog view
- [ ] Add plugin detail modal
- [ ] Implement search/filter functionality

### Phase 4: Config & Deployment (3 hours)
- [ ] Create config browser (tree view)
- [ ] Add config editor (syntax highlighting)
- [ ] Create deployment queue view
- [ ] Add variance detection display
- [ ] Implement approval workflow UI

### Phase 5: Updates & Approvals (2 hours)
- [ ] Create update manager view
- [ ] Add bulk update actions
- [ ] Create approval workflow interface
- [ ] Add voting UI

### Phase 6: Audit & Groups (2 hours)
- [ ] Create audit log viewer
- [ ] Add filtering/search
- [ ] Create group management view
- [ ] Add datapack catalog

### Phase 7: Polish & Testing (2 hours)
- [ ] Add dark mode toggle
- [ ] Implement real-time updates (optional)
- [ ] Add loading states
- [ ] Error handling
- [ ] Mobile responsiveness
- [ ] Browser testing

**Total Estimated Time: 16-17 hours**

---

## File Structure

```
homeamp-v2/
├── src/
│   ├── web/
│   │   ├── templates/
│   │   │   ├── base.html              # Bootstrap 5 base
│   │   │   ├── index.html             # Main SPA
│   │   │   ├── components/
│   │   │   │   ├── navbar.html
│   │   │   │   ├── sidebar.html
│   │   │   │   ├── breadcrumb.html
│   │   │   │   ├── cards.html
│   │   │   │   └── modals.html
│   │   ├── static/
│   │   │   ├── css/
│   │   │   │   ├── main.css
│   │   │   │   ├── dashboard.css
│   │   │   │   └── themes.css
│   │   │   ├── js/
│   │   │   │   ├── app.js             # Main SPA logic
│   │   │   │   ├── api.js             # API client
│   │   │   │   ├── components/
│   │   │   │   │   ├── dashboard.js
│   │   │   │   │   ├── instances.js
│   │   │   │   │   ├── plugins.js
│   │   │   │   │   ├── deployments.js
│   │   │   │   │   ├── config.js
│   │   │   │   │   ├── updates.js
│   │   │   │   │   ├── approvals.js
│   │   │   │   │   ├── audit.js
│   │   │   │   │   ├── groups.js
│   │   │   │   │   └── datapacks.js
│   │   │   ├── icons/
│   │   │   └── images/
│   │   ├── routes.py                  # Web route handlers
│   │   └── __init__.py
│   ├── api/
│   │   ├── main.py                    # Mount web routes
```

---

## API Integration Points

### Dashboard View
```javascript
GET /api/dashboard/summary              // Stats cards
GET /api/dashboard/network-status       // Server grid
GET /api/dashboard/recent-activity      // Activity feed
GET /api/dashboard/plugin-summary       // Plugin chart
GET /api/dashboard/variance-summary     // Variance count
```

### Instance View
```javascript
GET /api/instances                      // Instance list
GET /api/instances/{id}                 // Instance detail
GET /api/instances/{id}/plugins         // Installed plugins
POST /api/instances/{id}/scan           // Trigger scan
```

### Plugin View
```javascript
GET /api/plugins                        // Plugin catalog
GET /api/plugins/{id}                   // Plugin detail
GET /api/plugins/{id}/configs           // Config keys
```

### Deployment View
```javascript
GET /api/deployments                    // Deployment queue
POST /api/deployments                   // Create deployment
PUT /api/deployments/{id}/execute       // Execute
```

### Config View
```javascript
GET /api/config/global                  // Global rules
GET /api/config/resolve                 // Resolve config
GET /api/config/variances               // Variance list
GET /api/config/hierarchy/{plugin}      // Hierarchy
```

### Updates View
```javascript
GET /api/updates/available              // Available updates
POST /api/updates/check                 // Check for updates
POST /api/updates/approve               // Approve update
```

### Approvals View
```javascript
GET /api/approvals/pending              // Pending queue
POST /api/approvals/{id}/vote           // Cast vote
GET /api/approvals/{id}/votes           // Vote list
```

### Audit View
```javascript
GET /api/audit/events                   // Event log
GET /api/audit/entity/{type}/{id}       // Entity history
GET /api/audit/user/{username}          // User activity
```

### Groups View
```javascript
GET /api/groups                         // Group list
POST /api/groups                        // Create group
POST /api/groups/{id}/instances         // Add instance
```

### Datapacks View
```javascript
GET /api/datapacks                      // Datapack list
POST /api/datapacks                     // Upload datapack
GET /api/datapacks/instances/{id}       // Instance datapacks
```

---

## UI Improvements Over V1

1. **Modern Design**
   - Cleaner layout
   - Better spacing
   - Consistent color scheme
   - Dark mode support

2. **Better Navigation**
   - Persistent sidebar
   - Breadcrumb trail
   - Quick search
   - Keyboard shortcuts

3. **Enhanced Interactivity**
   - Real-time updates (optional WebSocket)
   - Inline editing
   - Drag-and-drop
   - Bulk actions

4. **Better Data Visualization**
   - Charts for plugin distribution
   - Timeline for deployments
   - Tree view for config hierarchy
   - Network topology view

5. **Improved UX**
   - Loading skeletons
   - Toast notifications
   - Confirmation dialogs
   - Error recovery
   - Undo/redo

6. **Mobile Support**
   - Responsive grid
   - Touch-friendly controls
   - Collapsible sidebars
   - Swipe gestures

---

## Next Steps

1. **START**: Create V2 web infrastructure
2. **IMPLEMENT**: Dashboard view (highest priority)
3. **PORT**: V1 functionality incrementally
4. **ENHANCE**: Add modern features
5. **TEST**: Cross-browser compatibility
6. **DEPLOY**: To production alongside V1

**Goal**: V2 UI should be BETTER than V1 in every way while maintaining 100% feature parity.
