/**
 * POST /api/report-broken-link
 *
 * Receives a broken-link report from the news-story page and forwards it to
 * david@principlesai.org via the Resend API. Replaces the prior mailto:
 * approach so the button works for any user without their mail client.
 *
 * Required env (Cloudflare Pages → Settings → Environment variables):
 *   RESEND_API_KEY    Resend API key (server-side only, never exposed to JS)
 *
 * Optional env:
 *   REPORT_FROM_EMAIL   sender address (default 'noreply@principlesai.org' —
 *                       must be a verified Resend sender domain)
 *   REPORT_TO_EMAIL     destination (default 'david@principlesai.org')
 *
 * Request body (JSON):
 *   { story_title?: string, story_url?: string, source_url?: string,
 *     user_note?: string (optional free-text from a future textarea) }
 */

const SUBJECT_MAX = 80;
const URL_MAX = 600;
const NOTE_MAX = 2000;
const TITLE_MAX = 240;

function clamp(s, n) { return (typeof s === 'string') ? s.slice(0, n) : ''; }

function json(status, payload) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
}

export async function onRequestPost(context) {
  const { request, env } = context;

  if (!env.RESEND_API_KEY) {
    // Helpful error — Pages env var not set yet
    return json(500, { error: 'Server not configured (RESEND_API_KEY missing)' });
  }

  let body;
  try { body = await request.json(); }
  catch (_e) { return json(400, { error: 'Invalid JSON' }); }

  const story_title = clamp(body.story_title, TITLE_MAX);
  const story_url   = clamp(body.story_url,   URL_MAX);
  const source_url  = clamp(body.source_url,  URL_MAX);
  const user_note   = clamp(body.user_note,   NOTE_MAX);

  if (!story_url || !source_url) {
    return json(400, { error: 'story_url and source_url required' });
  }

  const subject = 'PAI broken-link report: ' + (story_title || 'unknown story').slice(0, SUBJECT_MAX);

  const referer  = request.headers.get('Referer')        || '(none)';
  const ua       = request.headers.get('User-Agent')     || '(none)';
  const country  = request.headers.get('CF-IPCountry')   || '(unknown)';

  const NL = '\n';
  const text = [
    'A user reported a broken source link on a PAI news story.',
    '',
    'Story: ' + (story_title || '(unknown)'),
    'Story page: ' + story_url,
    'Source URL (reported broken): ' + source_url,
    user_note ? ('User note: ' + user_note) : null,
    '',
    '— diagnostic ——————————',
    'Referer: ' + referer,
    'User-Agent: ' + ua,
    'CF-IPCountry: ' + country,
    'Received at: ' + new Date().toISOString(),
  ].filter(Boolean).join(NL);

  const fromEmail = env.REPORT_FROM_EMAIL || 'noreply@principlesai.org';
  const toEmail   = env.REPORT_TO_EMAIL   || 'david@principlesai.org';

  const resp = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + env.RESEND_API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: 'PAI Broken-Link Reporter <' + fromEmail + '>',
      to: [toEmail],
      subject,
      text,
    }),
  });

  if (!resp.ok) {
    const errBody = await resp.text().catch(() => '');
    // Surface a generic error to client; log full detail server-side
    console.error('[report-broken-link] Resend error', resp.status, errBody);
    return json(502, { error: 'Email send failed', upstream_status: resp.status });
  }

  return json(200, { ok: true });
}

// Reject anything other than POST so the endpoint doesn't quietly 404 mismatched methods
export function onRequest(context) {
  if (context.request.method === 'POST') return onRequestPost(context);
  return new Response('Method Not Allowed', { status: 405, headers: { 'Allow': 'POST' } });
}
