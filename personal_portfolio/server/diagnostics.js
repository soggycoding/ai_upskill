const fs = require('node:fs');
const path = require('node:path');

const ROOT_DIR = path.resolve(__dirname, '..');
const PUBLIC_DIR = path.resolve(ROOT_DIR, 'public');
const PRIVATE_DIR = path.resolve(ROOT_DIR, 'private');

/**
 * Run full diagnostic audit on portfolio data and filesystem
 */
function runDiagnostics(portfolioData) {
  const issues = [];
  let checksPassed = 0;
  let totalChecks = 0;

  function addIssue(severity, category, message, itemRef = null) {
    issues.push({
      severity, // 'error', 'warning', 'info'
      category, // 'Content', 'Assets', 'Links', 'Security', 'Placeholders'
      message,
      ref: itemRef
    });
  }

  // ──────────────────────────────────────────
  // 1. Content Audits
  // ──────────────────────────────────────────
  totalChecks++;
  if (!portfolioData.profile || !portfolioData.profile.name) {
    addIssue('error', 'Content', 'Profile is missing a name.');
  } else {
    checksPassed++;
  }

  totalChecks++;
  if (!portfolioData.profile || !portfolioData.profile.identity) {
    addIssue('error', 'Content', 'Profile is missing academic/professional identity statement.');
  } else {
    checksPassed++;
  }

  const projects = Array.isArray(portfolioData.projects) ? portfolioData.projects : [];
  totalChecks++;
  if (projects.length === 0) {
    addIssue('error', 'Content', 'No projects found in portfolio dataset.');
  } else {
    checksPassed++;
  }

  const knownSlugs = new Set();
  projects.forEach((proj, idx) => {
    const pRef = proj.title || `Project #${idx + 1}`;

    // Title & Slug
    totalChecks++;
    if (!proj.title || proj.title.trim() === '') {
      addIssue('error', 'Content', `Project at index ${idx} is missing a title.`, pRef);
    } else {
      checksPassed++;
    }

    totalChecks++;
    if (!proj.slug || proj.slug.trim() === '') {
      addIssue('error', 'Content', `Project "${pRef}" is missing a unique slug identifier.`, pRef);
    } else if (knownSlugs.has(proj.slug)) {
      addIssue('error', 'Content', `Duplicate project slug detected: "${proj.slug}".`, pRef);
    } else {
      knownSlugs.add(proj.slug);
      checksPassed++;
    }

    // Role vs Contribution
    totalChecks++;
    if (!proj.role || proj.role.trim() === '') {
      addIssue('warning', 'Content', `Project "${pRef}" is missing a role declaration.`, pRef);
    } else {
      checksPassed++;
    }

    totalChecks++;
    if (!proj.contribution || proj.contribution.trim() === '') {
      addIssue('warning', 'Content', `Project "${pRef}" is missing individual contribution details.`, pRef);
    } else if (proj.role && proj.role === proj.contribution) {
      addIssue('warning', 'Content', `Project "${pRef}" has identical Role and Contribution fields. Please detail specific individual actions.`, pRef);
    } else {
      checksPassed++;
    }

    // Descriptions
    totalChecks++;
    if (!proj.shortDescription || proj.shortDescription.trim() === '') {
      addIssue('warning', 'Content', `Project "${pRef}" has no short description for quick-scan cards.`, pRef);
    } else {
      checksPassed++;
    }

    totalChecks++;
    if (!proj.fullDescription || proj.fullDescription.trim() === '') {
      addIssue('warning', 'Content', `Project "${pRef}" has no deep-dive full description.`, pRef);
    } else {
      checksPassed++;
    }

    // Deep-dive sections
    totalChecks++;
    if (!proj.objectives || proj.objectives.length === 0) {
      addIssue('info', 'Content', `Project "${pRef}" has no listed technical objectives.`, pRef);
    } else {
      checksPassed++;
    }

    totalChecks++;
    if (!proj.results || proj.results.trim() === '') {
      addIssue('info', 'Content', `Project "${pRef}" has no documented quantitative or qualitative results.`, pRef);
    } else {
      checksPassed++;
    }

    // ──────────────────────────────────────────
    // 2. Assets Audits
    // ──────────────────────────────────────────
    if (Array.isArray(proj.images)) {
      proj.images.forEach(imgRelPath => {
        totalChecks++;
        const absPath = path.join(PUBLIC_DIR, imgRelPath.replace(/^\//, ''));
        if (!fs.existsSync(absPath)) {
          addIssue('warning', 'Assets', `Project "${pRef}" references missing image: "${imgRelPath}".`, pRef);
        } else {
          checksPassed++;
        }
      });
    }

    if (Array.isArray(proj.documents)) {
      proj.documents.forEach(docRelPath => {
        totalChecks++;
        const absPath = path.join(PUBLIC_DIR, docRelPath.replace(/^\//, ''));
        if (!fs.existsSync(absPath)) {
          addIssue('warning', 'Assets', `Project "${pRef}" references missing document: "${docRelPath}".`, pRef);
        } else {
          checksPassed++;
        }
      });
    }

    // ──────────────────────────────────────────
    // 3. Links & Taxonomy Audits
    // ──────────────────────────────────────────
    if (Array.isArray(proj.relatedProjects)) {
      proj.relatedProjects.forEach(relSlug => {
        totalChecks++;
        const exists = projects.some(p => p.slug === relSlug);
        if (!exists) {
          addIssue('warning', 'Links', `Project "${pRef}" references nonexistent related project slug: "${relSlug}".`, pRef);
        } else {
          checksPassed++;
        }
      });
    }

    if (proj.github && !proj.github.startsWith('http://') && !proj.github.startsWith('https://')) {
      addIssue('warning', 'Links', `Project "${pRef}" has malformed GitHub link: "${proj.github}". Must begin with https://`, pRef);
    }

    // ──────────────────────────────────────────
    // 4. Placeholders Audits
    // ──────────────────────────────────────────
    const placeholderRegex = /\[YOUR\s+[A-Z0-9_\-\s]+\]|\[PROJECT\s+[A-Z0-9_\-\s]+\]/i;
    if (placeholderRegex.test(proj.title)) {
      addIssue('info', 'Placeholders', `Project "${pRef}" title contains placeholder text.`, pRef);
    }
    if (placeholderRegex.test(proj.role)) {
      addIssue('info', 'Placeholders', `Project "${pRef}" role contains placeholder text.`, pRef);
    }
    if (placeholderRegex.test(proj.contribution)) {
      addIssue('info', 'Placeholders', `Project "${pRef}" contribution contains placeholder text.`, pRef);
    }
  });

  // Profile placeholders
  if (portfolioData.profile) {
    if (/\[YOUR NAME\]/i.test(portfolioData.profile.name)) {
      addIssue('info', 'Placeholders', 'Profile name is still set to placeholder "[YOUR NAME]".');
    }
    if (/\[YOUR ACADEMIC/i.test(portfolioData.profile.identity)) {
      addIssue('info', 'Placeholders', 'Profile identity is still set to placeholder "[YOUR ACADEMIC / PROFESSIONAL IDENTITY]".');
    }
    if (/\[your\.email/i.test(portfolioData.profile.email)) {
      addIssue('info', 'Placeholders', 'Profile email is still set to placeholder "[your.email@university.edu]".');
    }
  }

  // ──────────────────────────────────────────
  // 5. Architecture & Security Audits
  // ──────────────────────────────────────────
  totalChecks++;
  if (!fs.existsSync(PRIVATE_DIR)) {
    addIssue('error', 'Security', 'Private directory (private/) does not exist on disk.');
  } else {
    checksPassed++;
  }

  totalChecks++;
  // Verify private is NOT within public
  if (PRIVATE_DIR.startsWith(PUBLIC_DIR)) {
    addIssue('error', 'Security', 'CRITICAL: private/ directory is nested inside public/ directory!');
  } else {
    checksPassed++;
  }

  // Calculate health score (weighted: errors = -15, warnings = -5, info = 0)
  const errorsCount = issues.filter(i => i.severity === 'error').length;
  const warningsCount = issues.filter(i => i.severity === 'warning').length;
  const infoCount = issues.filter(i => i.severity === 'info').length;

  let calculatedScore = Math.max(0, 100 - (errorsCount * 15 + warningsCount * 5));
  if (errorsCount > 0 && calculatedScore > 75) calculatedScore = 70;

  return {
    timestamp: new Date().toISOString(),
    totalChecks,
    checksPassed,
    healthScore: calculatedScore,
    counts: {
      errors: errorsCount,
      warnings: warningsCount,
      info: infoCount,
      totalIssues: issues.length
    },
    issues
  };
}

module.exports = {
  runDiagnostics
};
