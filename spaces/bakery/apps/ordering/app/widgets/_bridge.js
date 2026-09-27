/* ============================================================
   Maison Levain — widget bridge
   Thin, defensive wrapper over the ChatGPT `window.openai` host API:
     - read the tool's structuredContent (window.openai.toolOutput)
     - re-render when the host pushes new globals (openai:set_globals)
     - apply the host light/dark theme
     - call server tools back and send follow-up messages
   Falls back to window.__BAKERY_PREVIEW__ when opened outside ChatGPT, so the
   files can be previewed standalone while designing.
   ============================================================ */
(function () {
  'use strict';

  var openai = window.openai || null;

  function host() { return window.openai || openai || null; }

  function readToolOutput() {
    var h = host();
    if (h) {
      if (h.toolOutput != null) return h.toolOutput;
      if (typeof h.getInitialData === 'function') {
        try { return h.getInitialData(); } catch (e) { /* ignore */ }
      }
    }
    if (window.__BAKERY_PREVIEW__ != null) return window.__BAKERY_PREVIEW__;
    return null;
  }

  function readTheme(detail) {
    var g = (detail && (detail.globals || detail)) || host() || {};
    var theme = g.theme || (g.colorScheme) || 'light';
    return String(theme).indexOf('dark') !== -1 ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
  }

  function callTool(name, args) {
    var h = host();
    if (!h || typeof h.callTool !== 'function') {
      return Promise.reject(new Error('callTool unavailable outside ChatGPT'));
    }
    return Promise.resolve(h.callTool(name, args || {})).then(function (res) {
      // The result may be the raw CallToolResult or already-unwrapped content.
      if (res && res.structuredContent != null) return res.structuredContent;
      return res;
    });
  }

  function sendMessage(prompt) {
    var h = host();
    if (h && typeof h.sendFollowUpMessage === 'function') {
      try { h.sendFollowUpMessage({ prompt: prompt }); return; } catch (e) { /* ignore */ }
    }
    if (h && typeof h.sendFollowupTurn === 'function') {
      try { h.sendFollowupTurn({ prompt: prompt }); } catch (e) { /* ignore */ }
    }
  }

  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* -- inline pastry illustrations (no image host, tight CSP) ---------- */

  var PASTRY = {
    'croissant':
      '<svg viewBox="0 0 80 80" aria-hidden="true"><g transform="rotate(-18 40 40)">' +
      '<path d="M22 58 A28 28 0 1 1 60 20 A21 21 0 1 0 22 58 Z" fill="var(--dough)" stroke="var(--dough-edge)" stroke-width="1.5"/>' +
      '<path d="M31 50 A19 19 0 0 1 50 31" fill="none" stroke="var(--dough-edge)" stroke-width="1.4" opacity=".7"/>' +
      '<path d="M27 44 A24 24 0 0 1 44 27" fill="none" stroke="var(--dough-edge)" stroke-width="1.4" opacity=".55"/>' +
      '</g></svg>',
    'pain-au-chocolat':
      '<svg viewBox="0 0 80 80" aria-hidden="true">' +
      '<rect x="11" y="34" width="7" height="18" rx="3.5" fill="var(--choc)"/>' +
      '<rect x="62" y="34" width="7" height="18" rx="3.5" fill="var(--choc)"/>' +
      '<rect x="15" y="27" width="50" height="32" rx="13" fill="var(--dough)" stroke="var(--dough-edge)" stroke-width="1.5"/>' +
      '<path d="M40 30 V56 M30 32 V54 M50 32 V54" stroke="var(--dough-edge)" stroke-width="1.3" opacity=".55" fill="none"/>' +
      '</svg>',
    'chouquette':
      '<svg viewBox="0 0 80 80" aria-hidden="true">' +
      '<path d="M40 60 q-6 0 -7 -6" fill="none" stroke="var(--dough-edge)" stroke-width="1.4"/>' +
      '<circle cx="40" cy="40" r="22" fill="var(--dough)" stroke="var(--dough-edge)" stroke-width="1.5"/>' +
      '<g fill="var(--sugar-dot)">' +
      '<circle cx="33" cy="33" r="2.6"/><circle cx="45" cy="30" r="2.2"/><circle cx="50" cy="41" r="2.6"/>' +
      '<circle cx="31" cy="45" r="2.3"/><circle cx="41" cy="47" r="2.5"/><circle cx="39" cy="37" r="2.1"/></g>' +
      '</svg>',
    'eclair':
      '<svg viewBox="0 0 80 80" aria-hidden="true">' +
      '<rect x="11" y="35" width="58" height="20" rx="10" fill="var(--dough)" stroke="var(--dough-edge)" stroke-width="1.5"/>' +
      '<rect x="16" y="33" width="48" height="10" rx="5" fill="var(--glaze)"/>' +
      '<rect x="22" y="35.5" width="20" height="2.4" rx="1.2" fill="var(--sugar-dot)" opacity=".5"/>' +
      '</svg>',
    'brioche':
      '<svg viewBox="0 0 80 80" aria-hidden="true">' +
      '<path d="M17 58 Q17 35 40 35 Q63 35 63 58 Z" fill="var(--dough)" stroke="var(--dough-edge)" stroke-width="1.5"/>' +
      '<path d="M28 57 Q28 40 40 40 Q52 40 52 57 M22 58 Q22 46 32 40 M58 58 Q58 46 48 40" stroke="var(--dough-edge)" stroke-width="1.2" fill="none" opacity=".55"/>' +
      '<circle cx="40" cy="30" r="9" fill="var(--dough)" stroke="var(--dough-edge)" stroke-width="1.5"/>' +
      '</svg>',
    'mille-feuille':
      '<svg viewBox="0 0 80 80" aria-hidden="true">' +
      '<g stroke="var(--dough-edge)" stroke-width="1.2">' +
      '<rect x="16" y="24" width="48" height="9" rx="2" fill="var(--dough)"/>' +
      '<rect x="16" y="33" width="48" height="6" rx="1.5" fill="var(--cream)"/>' +
      '<rect x="16" y="39" width="48" height="9" rx="2" fill="var(--dough)"/>' +
      '<rect x="16" y="48" width="48" height="6" rx="1.5" fill="var(--cream)"/>' +
      '<rect x="16" y="54" width="48" height="9" rx="2" fill="var(--dough)"/></g>' +
      '<path d="M20 28 h40 M20 28 q6 4 8 0 q6 4 8 0 q6 4 8 0 q6 4 8 0" stroke="var(--glaze)" stroke-width="1.3" fill="none" opacity=".8"/>' +
      '</svg>'
  };

  function pastrySvg(shape, emoji) {
    return PASTRY[shape] || '<span class="emoji" aria-hidden="true">' + escapeHtml(emoji || '🥐') + '</span>';
  }

  /* -- boot ----------------------------------------------------------- */

  function boot(render) {
    function paint() {
      applyTheme(readTheme());
      var data = readToolOutput();
      try { render(data || {}); } catch (e) { console.error('render failed', e); }
    }

    // Re-render whenever the host pushes updated globals or a new tool output.
    window.addEventListener('openai:set_globals', function (event) {
      applyTheme(readTheme(event && event.detail));
      var data = readToolOutput();
      try { render(data || {}); } catch (e) { console.error('render failed', e); }
    });

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', paint);
    } else {
      paint();
    }
  }

  window.Bakery = {
    boot: boot,
    callTool: callTool,
    sendMessage: sendMessage,
    pastrySvg: pastrySvg,
    escapeHtml: escapeHtml
  };
})();
