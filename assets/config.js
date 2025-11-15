// Supabase configuration.
// Do NOT hardcode project URL or anon key here. If you want to enable
// client-side Supabase for non-sensitive features, inject values via an
// inline script or environment at build/deploy time.
// When unset, frontend will operate without Supabase and use local fallbacks.

window.SUPABASE_URL = (typeof window.SUPABASE_URL !== 'undefined') ? window.SUPABASE_URL : null;
window.SUPABASE_ANON_KEY = (typeof window.SUPABASE_ANON_KEY !== 'undefined') ? window.SUPABASE_ANON_KEY : null;

// Basic app-wide config
window.APP_CONFIG = Object.assign({
  brandName: 'Competence CRM',
  environment: 'dev',
}, window.APP_CONFIG || {});