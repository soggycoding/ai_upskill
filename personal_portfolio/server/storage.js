const fs = require('node:fs');
const path = require('node:path');

const ROOT_DIR = path.resolve(__dirname, '..');
const PORTFOLIO_FILE = path.resolve(ROOT_DIR, 'content', 'portfolio.json');
const HISTORY_DIR = path.resolve(ROOT_DIR, 'content', 'history');

// Ensure history directory exists
if (!fs.existsSync(HISTORY_DIR)) {
  fs.mkdirSync(HISTORY_DIR, { recursive: true });
}

/**
 * Load current portfolio data
 */
function loadPortfolio() {
  if (!fs.existsSync(PORTFOLIO_FILE)) {
    throw new Error('portfolio.json does not exist');
  }
  const raw = fs.readFileSync(PORTFOLIO_FILE, 'utf8');
  return JSON.parse(raw);
}

/**
 * Save new portfolio data with automatic historical snapshot
 */
function savePortfolio(newData, changeDescription = 'Manual CMS Update') {
  const timestamp = Date.now();
  const dateString = new Date().toISOString();

  // 1. Snapshot current version before overwriting
  try {
    if (fs.existsSync(PORTFOLIO_FILE)) {
      const currentRaw = fs.readFileSync(PORTFOLIO_FILE, 'utf8');
      const currentData = JSON.parse(currentRaw);

      const snapshot = {
        metadata: {
          timestamp,
          dateString,
          description: changeDescription,
          counts: {
            projects: Array.isArray(currentData.projects) ? currentData.projects.length : 0,
            experience: Array.isArray(currentData.experience) ? currentData.experience.length : 0,
            education: Array.isArray(currentData.education) ? currentData.education.length : 0
          }
        },
        data: currentData
      };

      const snapshotFilename = `snapshot-${timestamp}.json`;
      const snapshotPath = path.join(HISTORY_DIR, snapshotFilename);
      fs.writeFileSync(snapshotPath, JSON.stringify(snapshot, null, 2), 'utf8');

      // Prune history to last 50 entries
      pruneHistory(50);
    }
  } catch (err) {
    console.error('[Storage] Error creating snapshot:', err.message);
  }

  // 2. Write new data atomically
  const tempFile = `${PORTFOLIO_FILE}.tmp.${timestamp}`;
  fs.writeFileSync(tempFile, JSON.stringify(newData, null, 2), 'utf8');
  fs.renameSync(tempFile, PORTFOLIO_FILE);

  return {
    success: true,
    timestamp,
    dateString,
    message: 'Portfolio data saved and snapshot created.'
  };
}

/**
 * List all historical snapshots
 */
function listHistory() {
  if (!fs.existsSync(HISTORY_DIR)) return [];

  const files = fs.readdirSync(HISTORY_DIR).filter(f => f.startsWith('snapshot-') && f.endsWith('.json'));

  const snapshots = [];
  for (const file of files) {
    try {
      const filePath = path.join(HISTORY_DIR, file);
      const raw = fs.readFileSync(filePath, 'utf8');
      const parsed = JSON.parse(raw);
      snapshots.push({
        filename: file,
        timestamp: parsed.metadata ? parsed.metadata.timestamp : 0,
        dateString: parsed.metadata ? parsed.metadata.dateString : 'Unknown date',
        description: parsed.metadata ? parsed.metadata.description : 'Snapshot',
        counts: parsed.metadata ? parsed.metadata.counts : {}
      });
    } catch (e) {
      // Ignore corrupted snapshot files
    }
  }

  // Sort newest first
  snapshots.sort((a, b) => b.timestamp - a.timestamp);
  return snapshots;
}

/**
 * Restore a historical snapshot
 */
function restoreSnapshot(filename) {
  const safeName = path.basename(filename);
  const targetPath = path.join(HISTORY_DIR, safeName);

  if (!fs.existsSync(targetPath)) {
    throw new Error(`Snapshot file ${safeName} does not exist`);
  }

  const snapshotRaw = fs.readFileSync(targetPath, 'utf8');
  const snapshot = JSON.parse(snapshotRaw);

  if (!snapshot.data) {
    throw new Error('Invalid snapshot structure: missing data payload');
  }

  // Save current before restoring
  savePortfolio(snapshot.data, `Restored from snapshot: ${safeName}`);

  return {
    success: true,
    message: `Restored portfolio data from ${safeName}`,
    data: snapshot.data
  };
}

/**
 * Prune history snapshots to keep maxCount
 */
function pruneHistory(maxCount = 50) {
  try {
    const files = fs.readdirSync(HISTORY_DIR)
      .filter(f => f.startsWith('snapshot-') && f.endsWith('.json'))
      .map(f => ({
        name: f,
        time: fs.statSync(path.join(HISTORY_DIR, f)).mtimeMs
      }))
      .sort((a, b) => b.time - a.time);

    if (files.length > maxCount) {
      for (let i = maxCount; i < files.length; i++) {
        fs.unlinkSync(path.join(HISTORY_DIR, files[i].name));
      }
    }
  } catch (err) {
    console.error('[Storage] History prune failed:', err.message);
  }
}

module.exports = {
  loadPortfolio,
  savePortfolio,
  listHistory,
  restoreSnapshot
};
