const fs = require('node:fs');
const path = require('node:path');
const {
  verifyPasscode,
  updatePasscode,
  createSession,
  destroySession,
  isValidSession,
  extractToken,
  sanitizeAndResolvePath
} = require('./security');
const {
  loadPortfolio,
  savePortfolio,
  listHistory,
  restoreSnapshot
} = require('./storage');
const { runDiagnostics } = require('./diagnostics');

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.webp': 'image/webp',
  '.pdf': 'application/pdf',
  '.ico': 'image/x-icon',
  '.txt': 'text/plain; charset=utf-8'
};

/**
 * Helper to parse JSON request body
 */
function parseJsonBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
      // Cap at 10MB to prevent memory exhaustion
      if (body.length > 10 * 1024 * 1024) {
        reject(new Error('Payload too large'));
      }
    });
    req.on('end', () => {
      if (!body) return resolve({});
      try {
        const parsed = JSON.parse(body);
        resolve(parsed);
      } catch (err) {
        reject(new Error('Invalid JSON format'));
      }
    });
    req.on('error', reject);
  });
}

/**
 * Helper to send JSON responses
 */
function sendJson(res, statusCode, data, headers = {}) {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    ...headers
  });
  res.end(JSON.stringify(data));
}

/**
 * Helper to send HTML or text errors
 */
function sendError(res, statusCode, message) {
  res.writeHead(statusCode, {
    'Content-Type': 'text/html; charset=utf-8',
    'Cache-Control': 'no-cache'
  });
  res.end(`<!DOCTYPE html><html><head><title>${statusCode} ${message}</title><style>body{font-family:monospace;padding:40px;background:#0f172a;color:#f8fafc;}h1{color:#ef4444;}</style></head><body><h1>${statusCode} - ${message}</h1><p>Request rejected by portfolio security boundary.</p><p><a href="/" style="color:#38bdf8;">Return to Portfolio</a></p></body></html>`);
}

/**
 * Main HTTP request router
 */
async function handleRequest(req, res) {
  const parsedUrl = new URL(req.url, 'http://127.0.0.1:3000');
  const pathname = parsedUrl.pathname;
  const token = extractToken(req);
  const authenticated = isValidSession(token);

  // ──────────────────────────────────────────
  // 1. API Routes
  // ──────────────────────────────────────────
  if (pathname.startsWith('/api/')) {
    // GET /api/content (Public)
    if (pathname === '/api/content' && req.method === 'GET') {
      try {
        const data = loadPortfolio();
        return sendJson(res, 200, data);
      } catch (err) {
        return sendJson(res, 500, { error: 'Failed to read portfolio content', details: err.message });
      }
    }

    // POST /api/admin/login
    if (pathname === '/api/admin/login' && req.method === 'POST') {
      try {
        const body = await parseJsonBody(req);
        if (!body.passcode) {
          return sendJson(res, 400, { error: 'Passcode is required' });
        }

        if (!verifyPasscode(body.passcode)) {
          return sendJson(res, 401, { error: 'Incorrect admin passcode' });
        }

        const session = createSession();
        const cookie = `portfolio_admin_session=${session.token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=86400`;
        return sendJson(res, 200, {
          success: true,
          message: 'Authenticated successfully',
          token: session.token,
          expiresAt: session.expiresAt
        }, { 'Set-Cookie': cookie });
      } catch (err) {
        return sendJson(res, 400, { error: err.message });
      }
    }

    // POST /api/admin/logout
    if (pathname === '/api/admin/logout' && req.method === 'POST') {
      if (token) destroySession(token);
      const clearCookie = 'portfolio_admin_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0';
      return sendJson(res, 200, { success: true, message: 'Logged out' }, { 'Set-Cookie': clearCookie });
    }

    // GET /api/admin/check-auth
    if (pathname === '/api/admin/check-auth' && req.method === 'GET') {
      return sendJson(res, 200, { authenticated });
    }

    // ── Protected Admin API Endpoints ──
    if (!authenticated) {
      return sendJson(res, 401, { error: 'Unauthorized: Admin authentication required' });
    }

    // POST /api/admin/content (Save & Snapshot)
    if (pathname === '/api/admin/content' && req.method === 'POST') {
      try {
        const body = await parseJsonBody(req);
        if (!body.data) {
          return sendJson(res, 400, { error: 'Data payload missing' });
        }
        const result = savePortfolio(body.data, body.changeDescription || 'CMS Update');
        return sendJson(res, 200, result);
      } catch (err) {
        return sendJson(res, 500, { error: 'Failed to save portfolio', details: err.message });
      }
    }

    // GET /api/admin/history
    if (pathname === '/api/admin/history' && req.method === 'GET') {
      try {
        const history = listHistory();
        return sendJson(res, 200, { history });
      } catch (err) {
        return sendJson(res, 500, { error: 'Failed to retrieve history', details: err.message });
      }
    }

    // POST /api/admin/history/restore
    if (pathname === '/api/admin/history/restore' && req.method === 'POST') {
      try {
        const body = await parseJsonBody(req);
        if (!body.filename) {
          return sendJson(res, 400, { error: 'Snapshot filename is required' });
        }
        const result = restoreSnapshot(body.filename);
        return sendJson(res, 200, result);
      } catch (err) {
        return sendJson(res, 500, { error: 'Failed to restore snapshot', details: err.message });
      }
    }

    // GET /api/admin/diagnostics
    if (pathname === '/api/admin/diagnostics' && req.method === 'GET') {
      try {
        const data = loadPortfolio();
        const report = runDiagnostics(data);
        return sendJson(res, 200, report);
      } catch (err) {
        return sendJson(res, 500, { error: 'Diagnostics failed', details: err.message });
      }
    }

    // POST /api/admin/change-passcode
    if (pathname === '/api/admin/change-passcode' && req.method === 'POST') {
      try {
        const body = await parseJsonBody(req);
        if (!body.newPasscode || body.newPasscode.length < 4) {
          return sendJson(res, 400, { error: 'New passcode must be at least 4 characters long' });
        }
        updatePasscode(body.newPasscode);
        return sendJson(res, 200, { success: true, message: 'Admin passcode updated successfully' });
      } catch (err) {
        return sendJson(res, 500, { error: 'Passcode update failed', details: err.message });
      }
    }

    return sendJson(res, 404, { error: 'API endpoint not found' });
  }

  // ──────────────────────────────────────────
  // 2. Static Files & Web Pages
  // ──────────────────────────────────────────
  // Admin pages can be loaded directly (the client handles password prompts if not authenticated)
  const isRequestingAdmin = pathname === '/admin' || pathname.startsWith('/admin/');
  const resolution = sanitizeAndResolvePath(pathname, isRequestingAdmin);

  if (resolution.error) {
    return sendError(res, resolution.status || 403, resolution.error);
  }

  let targetPath = resolution.filePath;

  // If path is a directory, look for index.html
  try {
    if (fs.existsSync(targetPath) && fs.statSync(targetPath).isDirectory()) {
      targetPath = path.join(targetPath, 'index.html');
    }
  } catch (e) {}

  if (!fs.existsSync(targetPath)) {
    return sendError(res, 404, 'Resource Not Found');
  }

  // Check stat
  const stat = fs.statSync(targetPath);
  if (!stat.isFile()) {
    return sendError(res, 403, 'Forbidden: Not a readable file');
  }

  const ext = path.extname(targetPath).toLowerCase();
  const contentType = MIME_TYPES[ext] || 'application/octet-stream';

  res.writeHead(200, {
    'Content-Type': contentType,
    'Content-Length': stat.size,
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY'
  });

  const stream = fs.createReadStream(targetPath);
  stream.pipe(res);
}

module.exports = {
  handleRequest
};
