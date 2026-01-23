-- ============================================================
-- CASHFLOW ENGINE - SUPABASE SCHEMA MIGRATION
-- Run this SQL in Supabase SQL Editor
-- ============================================================

-- ============================================================
-- STEP 1: Create profiles table for user data
-- ============================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT,
    display_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    privacy_accepted_at TIMESTAMP WITH TIME ZONE,  -- GDPR: When user accepted privacy policy
    preferences JSONB DEFAULT '{}'::jsonb
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);

-- Comment for documentation
COMMENT ON TABLE public.profiles IS 'User profile data for CashFlow Engine users';
COMMENT ON COLUMN public.profiles.privacy_accepted_at IS 'GDPR: Timestamp when user accepted privacy policy';


-- ============================================================
-- STEP 2: Add user_id column to analyses table
-- ============================================================
-- Add user_id column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'analyses'
        AND column_name = 'user_id'
    ) THEN
        ALTER TABLE public.analyses
        ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON public.analyses(user_id);

-- Comment for documentation
COMMENT ON COLUMN public.analyses.user_id IS 'Owner of this analysis (for multi-user data isolation)';


-- ============================================================
-- STEP 3: Enable Row Level Security (RLS)
-- ============================================================

-- Enable RLS on profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Enable RLS on analyses
ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- STEP 4: Create RLS Policies for profiles table
-- ============================================================

-- Drop existing policies if they exist (for clean re-run)
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;

-- Users can only view their own profile
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

-- Users can only update their own profile
CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- Users can only insert their own profile
CREATE POLICY "Users can insert own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);


-- ============================================================
-- STEP 5: Create RLS Policies for analyses table
-- ============================================================

-- Drop existing policies if they exist (for clean re-run)
DROP POLICY IF EXISTS "Users can view own analyses" ON public.analyses;
DROP POLICY IF EXISTS "Users can insert own analyses" ON public.analyses;
DROP POLICY IF EXISTS "Users can update own analyses" ON public.analyses;
DROP POLICY IF EXISTS "Users can delete own analyses" ON public.analyses;

-- Users can only view their own analyses
CREATE POLICY "Users can view own analyses"
    ON public.analyses FOR SELECT
    USING (auth.uid() = user_id);

-- Users can only insert analyses for themselves
CREATE POLICY "Users can insert own analyses"
    ON public.analyses FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can only update their own analyses
CREATE POLICY "Users can update own analyses"
    ON public.analyses FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can only delete their own analyses
CREATE POLICY "Users can delete own analyses"
    ON public.analyses FOR DELETE
    USING (auth.uid() = user_id);


-- ============================================================
-- STEP 6: Create trigger for automatic profile creation
-- ============================================================

-- Function to automatically create a profile when a new user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, display_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(
            NEW.raw_user_meta_data->>'full_name',
            NEW.raw_user_meta_data->>'name',
            split_part(NEW.email, '@', 1)
        )
    )
    ON CONFLICT (id) DO NOTHING;  -- Prevent duplicate inserts
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Create trigger to run the function on new user signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- ============================================================
-- STEP 7: Create function to update profile timestamp
-- ============================================================

-- Function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_profile_updated()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS on_profile_updated ON public.profiles;

-- Create trigger for profile updates
CREATE TRIGGER on_profile_updated
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_profile_updated();


-- ============================================================
-- STEP 8: Grant permissions
-- ============================================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO anon, authenticated;

-- Grant permissions on profiles table
GRANT SELECT, INSERT, UPDATE ON public.profiles TO authenticated;
GRANT SELECT ON public.profiles TO anon;

-- Grant permissions on analyses table
GRANT SELECT, INSERT, UPDATE, DELETE ON public.analyses TO authenticated;


-- ============================================================
-- VERIFICATION QUERIES (run these to verify setup)
-- ============================================================

-- Check if profiles table exists
-- SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'profiles');

-- Check if user_id column exists on analyses
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'analyses' AND column_name = 'user_id';

-- Check RLS is enabled
-- SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('profiles', 'analyses');

-- List all policies
-- SELECT * FROM pg_policies WHERE tablename IN ('profiles', 'analyses');


-- ============================================================
-- MIGRATION FOR EXISTING DATA (run manually if needed)
-- ============================================================

-- If you have existing analyses without user_id, you can assign them to a specific user:
-- IMPORTANT: Replace 'YOUR-ADMIN-USER-UUID' with the actual UUID of the admin user
--
-- UPDATE public.analyses
-- SET user_id = 'YOUR-ADMIN-USER-UUID'
-- WHERE user_id IS NULL;


-- ============================================================
-- DONE!
-- ============================================================
-- Your database is now configured for multi-user authentication.
-- Each user will only see their own data.
