# Project Architecture & Planned Features

## Authentication Architecture (Existing)

### Overview
The project uses a standard Flask-Login and Flask-SQLAlchemy setup for authentication, heavily relying on class-based views.

### Core Components
- **Framework**: Flask-Login for session management.
- **Database**: `IndiAllSkyDbUserTable` (SQLAlchemy) in `indi_allsky/flask/models.py`.
- **Password Hashing**: Argon2 via `passlib.hash`.
- **Protection**: CSRF protection via `flask_wtf.CSRFProtect`.

### Authentication Flow
1. **Login**: Handled by `LoginView` in `indi_allsky/flask/auth_views.py`.
   - Path: `/indi-allsky/login`
   - Logic: Credentials validated via `IndiAllskyLoginForm`, compared against DB, and session established via `login_user()`.
2. **Session Persistence**: `load_user` callback in `indi_allsky/flask/__init__.py` re-hydrates `current_user` from the session cookie.
3. **Authorization**: 
   - Strict: `@login_required` (often in `decorators` list of class-based views).
   - Flexible: `login_optional` and `login_optional_media` in `indi_allsky/flask/misc.py` (toggled by config).

### Configuration Management
The project uses a dual configuration system:
1. **System Config (`flask.json`)**: Static infrastructure settings (DB paths, session keys, migration folders). Loaded at app startup.
2. **Application Config (`IndiAllSkyConfig`)**: Dynamic settings stored in the database.
   - **Definition**: Defaults are defined in `IndiAllSkyConfigBase._base_config` within `indi_allsky/config.py`.
   - **UI Exposure**: Managed via `IndiAllskyConfigForm` in `indi_allsky/flask/forms.py`.
   - **Saving**: `AjaxConfigView` in `views.py` updates the database and can trigger a system reload.
   - **Encryption**: Sensitive fields (like passwords/secrets) can be encrypted using `cryptography.fernet` if `ENCRYPT_PASSWORDS` is enabled.

### User Model Metadata
- `is_active`: Standard status check.
- `is_staff`: Basic permission level.
- `is_admin`: Full administrative access.
- `apikey`: Encrypted key for external syncing/API access.

### Configuration
- Auth behavior is controlled by settings like `LOGIN_DISABLED`, `INDI_ALLSKY_AUTH_ALL_VIEWS`, and `INDI_ALLSKY_AUTH_MEDIA_VIEWS` in the Flask config (loaded from `/etc/indi-allsky/flask.json`).

---

## Terminal Emulation (Proposed)

### Overview
Implementation of a browser-based terminal to allow administrative tasks via the Web UI.

### Current Status: Research Paused
Extensive research (documented in `indi_allsky/flask/TERMINAL_RESEARCH.md`) has identified a fundamental disconnect between the Socket.IO engine and Python application handlers when running within Gunicorn worker processes.

### Core Components
- **Frontend**: `xterm.js` for terminal rendering and input handling, hosted locally.
- **Real-time Communication**: `Flask-SocketIO` providing bi-directional data flow. 
- **Backend PTY**: `pty` module to spawn and manage a pseudo-terminal on the server.
- **Known Blocker**: Gunicorn `gthread` worker class combined with `flask-socketio` registry loss during process forks.

### Recommended Next Steps
1.  Evaluate transition to `eventlet` or `gevent` async modes.
2.  Consider a standalone terminal microservice to bypass Flask process management issues.
3.  Implement Session ID sticky emission to handle page reloads gracefully.

---

## Native Metrics Support (Proposed)

### Overview
Integration of a Prometheus-compatible metrics exporter to provide real-time observability into camera performance, sensor data, and system health.

### Core Components
- **Library**: `prometheus_client` for Python.
- **Instrumentation**:
    - **Capture Metrics**: Integrated into `CaptureWorker` to track exposure time, gain, star counts, ADU levels, and SQM readings per-camera.
    - **Sensor Metrics**: Integrated into `SensorWorker` to track environmental data (temperature, humidity, dew point, etc.) and hardware states (fan speed, dew heater level).
    - **System Metrics**: Track disk usage, swap usage, and process uptime.
- **Export Mechanism**: A dedicated Flask route `/metrics` to serve the scraped data in the Prometheus text format.

### Implementation Plan
1. **Dependency Management**: Add `prometheus_client` to `requirements/requirements_latest.txt`.
2. **Registry Initialization**: Create a central metrics registry in a new module `indi_allsky/metrics.py` to manage `Gauge`, `Counter`, and `Histogram` objects.
3. **Worker Instrumentation**:
    - Modify `indi_allsky/capture.py` to update metrics at the end of each successful capture cycle.
    - Modify `indi_allsky/sensor.py` to update metrics after each sensor polling interval.
4. **Flask Integration**:
    - Add a `/metrics` route to `indi_allsky/flask/views.py`.
    - Secure the endpoint: By default, `/metrics` should be accessible locally or authenticated via the existing session/API key if exposed publicly.
5. **Configuration**: 
    - Add `METRICS_ENABLED` (Boolean) to `indi_allsky/config.py`.
    - Allow customization of metric prefixes and labels (e.g., `camera_id`, `location`).

---

## High-Power Theming & Component-Based Redesign (Proposed)

### Overview
Transform the `indi-allsky` web interface into a highly flexible, themeable application using a **Component-Based Architecture**. This allows for deep customization of layout, geometry, and visual appearance via CSS Variables.

### Core Components
- **The Semantic Variable Layer (`themes.css`)**: A three-tier variable system (Palette, Geometry, Component Semantics) defined in `indi_allsky/flask/static/css/themes.css`.
- **Template Abstraction**: Replacing hardcoded Bootstrap utility classes with semantic classes (e.g., `.app-btn`, `.app-card`) in Jinja2 templates.
- **Dynamic Configuration**: `WEBUI_THEME` setting in the database to toggle between themes (e.g., `classic-dark`, `modern-rounded`).

### Implementation Strategy
1.  **Phase 1: Infrastructure**: Add `WEBUI_THEME` to config, create the global stylesheet, and bridge our variables to Bootstrap 5 CSS variables.
2.  **Phase 2: Layout Refactor**: Update `base.html` sidebar and navigation to use variable-driven CSS Grid/Flexbox.
3.  **Phase 3: Modern Theme**: Implement a reference "Modern" theme featuring soft shadows, increased whitespace, and refined typography.
4.  **Phase 4: Customization**: Add a "Custom CSS" override field in the Admin UI for user-specific tweaks.

### Risks & Considerations
- **Styling Debt**: Extensive refactoring required for templates with inline styles (especially `config.html`).
- **Compatibility**: Ensuring themes propagate to third-party components like `xterm.js` and `DataTables`.

---

## daisyUI Migration Strategy (Proposed)

### Overview
To achieve maximum UI power and modern aesthetics, the project will incrementally migrate from Bootstrap 5 to **Tailwind CSS 4 + daisyUI 5**. This provides built-in theme support, semantic components, and a utility-first approach.

### Implementation Strategy (The "Parallel Bridge")
1.  **Phase 1: Installation**: Integrate Tailwind CSS 4 and daisyUI 5 alongside the existing Bootstrap setup.
2.  **Phase 2: Layout Foundation (`base.html`)**: Refactor the main application shell to use a daisyUI **Drawer** (for sidebar) and **Navbar**. This establishes the "modern frame" while the inner content still uses Bootstrap.
3.  **Phase 3: Component Mapping**: Define a CSS abstraction layer (using `@apply`) to map semantic classes (e.g., `.app-btn`) to daisyUI components, ensuring visual consistency across technologies.
4.  **Phase 4: Incremental Template Migration**: Progressively rewrite individual templates (starting with simpler views like `index_img.html`) to replace Bootstrap classes with daisyUI components.
5.  **Phase 5: The "Big Refactor"**: Finally tackle high-complexity templates like `config.html` and `imageprocessing.html`.

### Key Benefits
- **Built-in Themes**: Access to 20+ professional themes (Cyberpunk, Dracula, Retro) out of the box via `data-theme`.
- **Pure CSS Interactions**: Many components (Modals, Drawers, Tabs) use Pure CSS logic, reducing reliance on external JS bundles.
- **Future Proof**: Aligns with modern frontend standards and provides the most flexible customization path for users.



