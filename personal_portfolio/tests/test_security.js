const http = require('node:http');

const BASE_URL = 'http://127.0.0.1:3000';

function makeRequest(path, options = {}) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, BASE_URL);
    const req = http.request(url, options, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    });
    req.on('error', reject);
    if (options.body) {
      req.write(options.body);
    }
    req.end();
  });
}

async function runSecurityTests() {
  console.log('── Running Portfolio Security & Boundary Test Suite ──\n');
  let passed = 0;
  let failed = 0;

  async function test(description, fn) {
    try {
      await fn();
      console.log(`  ✓ PASS: ${description}`);
      passed++;
    } catch (err) {
      console.error(`  ✗ FAIL: ${description}`);
      console.error(`    ${err.message}`);
      failed++;
    }
  }

  // 1. Direct private path access
  await test('Direct access to /private/confidential_notes.txt is blocked', async () => {
    const res = await makeRequest('/private/confidential_notes.txt');
    if (res.statusCode !== 403 && res.statusCode !== 404) {
      throw new Error(`Expected 403 or 404, got ${res.statusCode}`);
    }
  });

  // 2. Directory traversal attempt targeting private directory
  await test('Traversal /public/../private/confidential_notes.txt is blocked', async () => {
    const res = await makeRequest('/public/../private/confidential_notes.txt');
    if (res.statusCode !== 403 && res.statusCode !== 404) {
      throw new Error(`Expected 403 or 404, got ${res.statusCode}`);
    }
  });

  // 3. Encoded traversal attempt
  await test('Encoded traversal /..%2fprivate/confidential_notes.txt is blocked', async () => {
    const res = await makeRequest('/..%2fprivate/confidential_notes.txt');
    if (res.statusCode !== 403 && res.statusCode !== 404 && res.statusCode !== 400) {
      throw new Error(`Expected 403/404/400, got ${res.statusCode}`);
    }
  });

  // 4. Unauthorized access to protected CMS API
  await test('Unauthorized GET /api/admin/content returns 401', async () => {
    const res = await makeRequest('/api/admin/content');
    if (res.statusCode !== 401) {
      throw new Error(`Expected 401 Unauthorized, got ${res.statusCode}`);
    }
  });

  // 5. Unauthorized access to diagnostics API
  await test('Unauthorized GET /api/admin/diagnostics returns 401', async () => {
    const res = await makeRequest('/api/admin/diagnostics');
    if (res.statusCode !== 401) {
      throw new Error(`Expected 401 Unauthorized, got ${res.statusCode}`);
    }
  });

  // 6. Public content API works
  await test('Public GET /api/content returns 200 with valid JSON', async () => {
    const res = await makeRequest('/api/content');
    if (res.statusCode !== 200) {
      throw new Error(`Expected 200 OK, got ${res.statusCode}`);
    }
    const json = JSON.parse(res.body);
    if (!json.profile || !json.projects) {
      throw new Error('Invalid portfolio payload schema');
    }
  });

  // 7. Public homepage serves HTML
  await test('Public GET / serves index.html with text/html', async () => {
    const res = await makeRequest('/');
    if (res.statusCode !== 200) {
      throw new Error(`Expected 200 OK, got ${res.statusCode}`);
    }
    if (!res.headers['content-type'].includes('text/html')) {
      throw new Error(`Expected text/html, got ${res.headers['content-type']}`);
    }
  });

  console.log(`\nResults: ${passed} passed, ${failed} failed.\n`);
  if (failed > 0) process.exit(1);
}

if (require.main === module) {
  runSecurityTests().catch(err => {
    console.error('Test suite error:', err);
    process.exit(1);
  });
}

module.exports = { runSecurityTests };
