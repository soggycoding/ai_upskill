# Local Academic & Professional Portfolio

A localhost-only, framework-free, offline-first personal portfolio and local Content Management System (CMS) designed specifically for academic reviewers, recruiters, and technical peers.

Built with **vanilla HTML, CSS, JavaScript**, and a zero-dependency **Node.js standard-library server** binding strictly to `127.0.0.1:3000`.

---

## 1. Quick Start

### Prerequisites
- Node.js (v18+ recommended; v24 installed). No external `npm install` packages required.

### Starting the Server
Run the local server from the project directory:
```bash
node server/index.js
```

The server will output:
```
╔══════════════════════════════════════════════════════════════╗
║   ACADEMIC & PROFESSIONAL PORTFOLIO LOCALHOST SERVER         ║
╠══════════════════════════════════════════════════════════════╣
║  Local URL:    http://127.0.0.1:3000                          ║
║  CMS Admin:    http://127.0.0.1:3000/admin                    ║
║  Printable CV: http://127.0.0.1:3000/cv                       ║
║  Binding:      127.0.0.1 (Strict Localhost Only)             ║
║  Security:     Private boundary active (/private/* blocked)  ║
║  Offline Mode: 100% Zero-CDN & Framework-Free                ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 2. Key URLs

| Endpoint | Description |
|---|---|
| `http://127.0.0.1:3000` | Main Portfolio (Hero, Projects Grid, Capabilities, Experience, Education, Contact) |
| `http://127.0.0.1:3000/project.html?slug=<slug>` | Deep-dive technical case study page |
| `http://127.0.0.1:3000/cv` | Print-friendly CV and PDF export (uses the same underlying data) |
| `http://127.0.0.1:3000/admin` | Local CMS Console (passcode protected) |

---

## 3. Architecture & Conceptual Directory Structure

```
personal_portfolio/
├── public/                     # Publicly served resources (safe for visitors)
│   ├── css/
│   │   ├── style.css           # Typography, layout, light & dark theme variables
│   │   └── cv.css              # Print & PDF optimized stylesheet (@media print)
│   ├── js/
│   │   ├── main.js             # Data hydration, rendering, search & tag filtering
│   │   ├── theme.js            # Flash-free theme toggle & localStorage persistence
│   │   └── webgl-proto.js      # Restrained 3D WebGL prototype & evaluation harness
│   ├── assets/
│   │   └── placeholders/       # SVG technical schematics & documents
│   ├── index.html              # Main portfolio homepage
│   ├── project.html            # Deep-dive technical case study page
│   └── cv.html                 # Print-friendly CV / Resume page
├── content/                    # Data Layer
│   ├── portfolio.json          # Unified human-readable portfolio content
│   ├── settings.json           # Server configuration & hashed admin passcode
│   ├── history/                # Automated timestamped snapshots for 1-click restore
│   └── uploads/                # User asset uploads
├── private/                    # HARD SECURITY BOUNDARY: Never served over HTTP
│   ├── confidential_notes.txt  # Sample sensitive notes (access returns 403 Forbidden)
│   └── (private documents)
├── admin/                      # Local CMS Interface
│   ├── index.html              # CMS dashboard, project manager modal, diagnostics
│   ├── admin.css               # Clean utility-first admin styling
│   └── admin.js                # Authentication, reactive CRUD, snapshot rollback
├── server/                     # Backend Logic (Zero NPM Dependencies)
│   ├── index.js                # Localhost HTTP server (127.0.0.1:3000)
│   ├── routes.js               # Route dispatcher (Public, Admin, API)
│   ├── security.js             # Private directory blocking & path traversal sanitization
│   ├── storage.js              # JSON persistence, atomic writes & snapshot history
│   └── diagnostics.js          # Systemic audit engine (content, assets, links, security)
├── tests/
│   └── test_security.js        # Automated security test suite
└── README.md                   # Operations and maintenance documentation
```

---

## 4. Hard Security Boundary (`private/`)

> [!CAUTION]
> The `private/` directory is a strict security boundary.

- Any HTTP request attempting to access `/private/*`, `/public/../private/*`, or URL-encoded variations (`%2e%2e`) is intercepted and rejected with **403 Forbidden**.
- Tested and verified via `node tests/test_security.js`.
- Store sensitive drafts, confidential research datasets, or unreleased papers in `personal_portfolio/private/`. They will never be exposed over the network.

---

## 5. Local CMS & Content Management

- **Access**: Navigate to `http://127.0.0.1:3000/admin`.
- **Default Passcode**: `admin123` (Change this in the "Security & Settings" tab).
- **Session**: Issues a secure, `HttpOnly`, `SameSite=Strict` cookie valid for 24 hours.

### Capabilities in the CMS:
1. **Projects Manager**: Create, edit, delete, reorder, and tag projects. Supports Section 13 distinction between **Role** and **Individual Contribution**.
2. **Profile & Bio Editor**: Update academic identity, intro, biography, contact email, and research links.
3. **Experience & Education**: Maintain chronological appointments, degrees, and academic honors.
4. **Version History & Recovery**: Every modification automatically snapshots `content/portfolio.json` to `content/history/snapshot-<timestamp>.json`. Revert to any past state with a single click.
5. **Portfolio Health & Diagnostics**: Audits your portfolio for:
   - Missing titles, descriptions, or individual contribution statements
   - Broken project relationships or missing image/document assets
   - Unreplaced placeholders (e.g. `[YOUR NAME]`)
   - Hard security boundary validation

---

## 6. Printable CV / Resume (`/cv`)

The printable CV dynamically reads the **exact same dataset** (`content/portfolio.json`) as the website.
- Optimized for printing to A4 and Letter paper or saving as a crisp PDF via your browser's Print dialog (`Ctrl+P` / `Cmd+P` or clicking the "Print / Save PDF" button).
- Screen-only controls (navigation, print buttons) are stripped automatically during printing.
- Uses strict black on white typography with `break-inside: avoid` rules to ensure clean page breaks.

---

## 7. WebGL Prototype Evaluation (Section 23 & 45)

A restrained 3D wireframe cluster topology element was prototyped in `public/js/webgl-proto.js`.
- **Evaluation**: The wireframe renders at 60fps with low memory overhead, but in a serious academic/professional portfolio, an ambient 3D animation distracts from empirical case study evidence and adds unnecessary cognitive load.
- **Decision**: In compliance with Section 23 & 45, the WebGL element is **default-disabled** in favor of minimal typography clarity. An optional toggle (`View 3D Cluster Topology (Prototype)`) is preserved on the homepage for visitors who wish to inspect the interactive canvas, paired with a clean graceful fallback for reduced-motion users.

---

## 8. Backup & Maintenance

- **Backing up your content**: Simply copy the `personal_portfolio/content/` folder or `content/portfolio.json`. It is human-readable, JSON-formatted, and completely portable.
- **Restoring accidental edits**: Use the "Version History" tab in the CMS, or copy any file from `content/history/` back over `content/portfolio.json`.
- **Running Security Tests**:
  ```bash
  node tests/test_security.js
  ```
