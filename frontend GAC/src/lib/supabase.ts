import { createClient } from '@supabase/supabase-js';

// 1. Go to Supabase Dashboard -> Project Settings -> API
// 2. Paste the "URL" and "anon public" key here:
const SUPABASE_URL = 'https://lwstwekouztglkoescog.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_dmwRDftSHwm7PlapTWGlIg_rVHCrN9y';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
