import { createClient } from '@supabase/supabase-js';

// Credentials derived from project
const SUPABASE_URL = 'https://lwstwekouztglkoescog.supabase.co';
// CORRECT KEY (Validated)
const SUPABASE_ANON_KEY = 'sb_publishable_dmwRDftSHwm7PlapTWGlIg_rVHCrN9y';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
