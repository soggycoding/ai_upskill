const http = require('node:http');
const { handleRequest } = require('./routes');
const { getSettings } = require('./security');

const settings = getSettings();
const HOST = (settings.server && settings.server.host) || '127.0.0.1';
const PORT = (settings.server && settings.server.port) || 3000;

const server = http.createServer(handleRequest);

server.listen(PORT, HOST, () => {
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║   ACADEMIC & PROFESSIONAL PORTFOLIO LOCALHOST SERVER         ║');
  console.log('╠══════════════════════════════════════════════════════════════╣');
  console.log(`║  Local URL:    http://${HOST}:${PORT}                          ║`);
  console.log(`║  CMS Admin:    http://${HOST}:${PORT}/admin                    ║`);
  console.log(`║  Printable CV: http://${HOST}:${PORT}/cv                       ║`);
  console.log('║  Binding:      127.0.0.1 (Strict Localhost Only)             ║');
  console.log('║  Security:     Private boundary active (/private/* blocked)  ║');
  console.log('║  Offline Mode: 100% Zero-CDN & Framework-Free                ║');
  console.log('╚══════════════════════════════════════════════════════════════╝');
});

// Handle graceful shutdown
function shutdown() {
  console.log('\nShutting down portfolio server gracefully...');
  server.close(() => {
    console.log('Server closed. Goodbye.');
    process.exit(0);
  });
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
