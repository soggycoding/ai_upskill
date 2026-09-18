const path = require('node:path');
const fs = require('node:fs');
const crypto = require('node:crypto');

const ROOT_DIR = path.resolve(__dirname, '..');
const PRIVATE_DIR = path.resolve(ROOT_DIR, 'private');
const PUBLIC_DIR = path.resolve(ROOT_DIR, 'public');
const ADMIN_DIR = path.resolve(ROOT_DIR, 'admin');
const UPLOADS_DIR = path.resolve(ROOT_DIR, 'content', 'uploads');
const SETTINGS_FILE = path.resolve(ROOT_DIR, 'content', 'settings.json');

// In-memory active session tokens: token -> { createdAt, expiresAt }
const activeSessions = new Map();

/**
 * Load settings JSON safely
 */
function getSettings() {
  try {
    const raw = fs.readFileSync(SETTINGS_FILE, 'utf8');
    return JSON.parse(raw);
  } catch (err) {
    // Fallback default
    return {
      adminPasscodeHash: '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', // admin123
      sessionExpiryHours: 24,
      server: { host: '127.0.0.1', port: 3000 }
    };
  }
}

/**
 * Save updated settings
 */
function saveSettings(settings) {
  fs.writeFileSync(SETTINGS_FILE, JSON.stringify(settings, null, 2), 'utf8');
}

/**
 * Hash a plain passcode using SHA-256
 */
function hashPasscode(passcode) {
  return crypto.createHash('sha256').update(String(passcode)).digest('hex');
}

/**
 * Timing-safe passcode verification
 */
function verifyPasscode(inputPasscode) {
  const settings = getSettings();
  const inputHash = hashPasscode(inputPasscode);
  const targetHash = settings.adminPasscodeHash;

  const bufA = Buffer.from(inputHash, 'hex');
  const bufB = Buffer.from(targetHash, 'hex');

  if (bufA.length !== bufB.length) return false;
  return crypto.timingSafeEqual(bufA, bufB);
}

/**
 * Update the admin passcode
 */
function updatePasscode(newPasscode) {
  const settings = getSettings();
  settings.adminPasscodeHash = hashPasscode(newPasscode);
  settings.passcodeHint = 'Custom passcode configured.';
  saveSettings(settings);
}

/**
 * Create a new admin session token
 */
function createSession() {
  const token = crypto.randomBytes(32).toString('hex');
  const settings = getSettings();
  const expiryHours = settings.sessionExpiryHours || 24;
  const expiresAt = Date.now() + expiryHours * 60 * 60 * 1000;

  activeSessions.set(token, {
    createdAt: Date.now(),
    expiresAt
  });

  return { token, expiresAt };
}

/**
 * Invalidate a session
 */
function destroySession(token) {
  if (token) {
    activeSessions.delete(token);
  }
}

/**
 * Verify session token
 */
function isValidSession(token) {
  if (!token) return false;
  const session = activeSessions.get(token);
  if (!session) return false;

  if (Date.now() > session.expiresAt) {
    activeSessions.delete(token);
    return false;
  }

  return true;
}

/**
 * Extract token from Cookie header or Authorization header
 */
function extractToken(req) {
  // Check Authorization header: Bearer <token>
  const authHeader = req.headers['authorization'];
  if (authHeader && authHeader.startsWith('Bearer ')) {
    return authHeader.slice(7).trim();
  }

  // Check Cookie header: portfolio_admin_session=<token>
  const cookieHeader = req.headers['cookie'];
  if (cookieHeader) {
    const cookies = cookieHeader.split(';').map(c => c.trim());
    for (const cookie of cookies) {
      if (cookie.startsWith('portfolio_admin_session=')) {
        return cookie.slice('portfolio_admin_session='.length);
      }
    }
  }

  return null;
}

/**
 * Strict Security Guard for requested file paths.
 * Checks for:
 * 1. Path traversal attempts (.., %2e%2e, null bytes)
 * 2. Any path accessing or resolving into private/
 * 3. Confines public access strictly to public/, admin/, content/uploads/
 */
function sanitizeAndResolvePath(rawUrlPath, allowAdmin = false) {
  // 1. Decode URL and strip query strings
  let cleanUrl = rawUrlPath.split('?')[0].split('#')[0];
  try {
    cleanUrl = decodeURIComponent(cleanUrl);
  } catch (e) {
    return { error: 'Malformed URL encoding', status: 400 };
  }

  // 2. Reject null bytes
  if (cleanUrl.indexOf('\0') !== -1) {
    return { error: 'Null byte injection detected', status: 400 };
  }

  // 3. HARD SECURITY BOUNDARY: Explicitly reject any reference to /private
  const lowerUrl = cleanUrl.toLowerCase().replace(/\\/g, '/');
  if (
    lowerUrl === '/private' ||
    lowerUrl.startsWith('/private/') ||
    lowerUrl.includes('/private')
  ) {
    return { error: 'Access to private directory is strictly prohibited', status: 403 };
  }

  // 4. Default route mapping
  if (cleanUrl === '/' || cleanUrl === '') {
    cleanUrl = '/index.html';
  } else if (cleanUrl === '/cv') {
    cleanUrl = '/cv.html';
  } else if (cleanUrl === '/project') {
    cleanUrl = '/project.html';
  }

  let resolvedTarget = null;

  // Determine allowed source directory
  if (cleanUrl.startsWith('/admin')) {
    if (!allowAdmin) {
      return { error: 'Unauthorized admin access', status: 401 };
    }
    const relativeAdminPath = cleanUrl.replace(/^\/admin\/?/, '') || 'index.html';
    resolvedTarget = path.resolve(ADMIN_DIR, relativeAdminPath);
    if (!resolvedTarget.startsWith(ADMIN_DIR)) {
      return { error: 'Directory traversal forbidden', status: 403 };
    }
  } else if (cleanUrl.startsWith('/uploads/')) {
    const relativeUploadPath = cleanUrl.replace(/^\/uploads\//, '');
    resolvedTarget = path.resolve(UPLOADS_DIR, relativeUploadPath);
    if (!resolvedTarget.startsWith(UPLOADS_DIR)) {
      return { error: 'Directory traversal forbidden', status: 403 };
    }
  } else {
    // Normal public assets
    const relativePublicPath = cleanUrl.replace(/^\//, '');
    resolvedTarget = path.resolve(PUBLIC_DIR, relativePublicPath);
    if (!resolvedTarget.startsWith(PUBLIC_DIR)) {
      return { error: 'Directory traversal forbidden', status: 403 };
    }
  }

  // 5. Final check: Ensure target does NOT resolve into PRIVATE_DIR or ROOT_DIR outside public
  if (resolvedTarget.startsWith(PRIVATE_DIR)) {
    return { error: 'Forbidden private resource', status: 403 };
  }

  return { filePath: resolvedTarget };
}

module.exports = {
  ROOT_DIR,
  PRIVATE_DIR,
  PUBLIC_DIR,
  ADMIN_DIR,
  getSettings,
  verifyPasscode,
  updatePasscode,
  createSession,
  destroySession,
  isValidSession,
  extractToken,
  sanitizeAndResolvePath
};
