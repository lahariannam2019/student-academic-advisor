import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './layouts/AppLayout';
import { TodayPage } from './pages/TodayPage';
import { SubjectsPage } from './pages/SubjectsPage';
import { ProgressPage } from './pages/ProgressPage';
import { AdvisorPage } from './pages/AdvisorPage';
import { ProfilePage } from './pages/ProfilePage';
import { AuthPage } from './pages/AuthPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { api } from './services/api';
import type { StudentProfile } from './types';

const getSafeStorageItem = (key: string): string | null => {
  try {
    const val = localStorage.getItem(key);
    if (!val || val === 'undefined' || val === 'null') return null;
    return val;
  } catch {
    return null;
  }
};

const setSafeStorageItem = (key: string, value: string) => {
  try {
    localStorage.setItem(key, value);
  } catch {}
};

const removeSafeStorageItem = (key: string) => {
  try {
    localStorage.removeItem(key);
  } catch {}
};

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return Boolean(getSafeStorageItem('access_token'));
  });
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState<boolean>(() => {
    return getSafeStorageItem('onboarding_completed') === 'true';
  });
  const [studentName, setStudentName] = useState<string>(() => {
    return getSafeStorageItem('student_name') || 'Student';
  });
  const [initialLoading, setInitialLoading] = useState<boolean>(true);

  // Verify active profile upon application mount
  useEffect(() => {
    const checkSession = async () => {
      const token = getSafeStorageItem('access_token');
      if (token) {
        try {
          const profile = await api.get<StudentProfile>('/api/auth/profile');
          if (profile && profile.name) {
            setStudentName(profile.name);
            setSafeStorageItem('student_name', profile.name);
            const isCompleted = Boolean(profile.onboarding_completed && profile.name && profile.college);
            setHasCompletedOnboarding(isCompleted);
            setSafeStorageItem('onboarding_completed', isCompleted ? 'true' : 'false');
          } else {
            setHasCompletedOnboarding(false);
          }
          setIsAuthenticated(true);
        } catch (err) {
          console.warn('Session expired or invalid:', err);
          handleLogout();
        } finally {
          setInitialLoading(false);
        }
      } else {
        setInitialLoading(false);
      }
    };
    checkSession();
  }, []);

  const handleLoginSuccess = (name: string, needsOnboarding: boolean) => {
    setIsAuthenticated(true);
    setStudentName(name || 'Student');
    setHasCompletedOnboarding(!needsOnboarding);
    setSafeStorageItem('onboarding_completed', !needsOnboarding ? 'true' : 'false');
  };

  const handleLogout = () => {
    removeSafeStorageItem('access_token');
    removeSafeStorageItem('is_authenticated');
    removeSafeStorageItem('student_name');
    removeSafeStorageItem('onboarding_completed');
    removeSafeStorageItem('user_id');
    removeSafeStorageItem('profile_id');
    setIsAuthenticated(false);
    setHasCompletedOnboarding(false);
    setStudentName('Student');
  };

  const handleOnboardingComplete = (completedName: string) => {
    setStudentName(completedName);
    setSafeStorageItem('student_name', completedName);
    setSafeStorageItem('onboarding_completed', 'true');
    setHasCompletedOnboarding(true);
  };

  if (initialLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Public Auth Route */}
        <Route
          path="/auth"
          element={
            isAuthenticated ? (
              hasCompletedOnboarding ? <Navigate to="/" replace /> : <Navigate to="/onboarding" replace />
            ) : (
              <AuthPage onLoginSuccess={handleLoginSuccess} />
            )
          }
        />

        {/* 7-Step Onboarding Flow */}
        <Route
          path="/onboarding"
          element={
            isAuthenticated ? (
              hasCompletedOnboarding ? (
                <Navigate to="/" replace />
              ) : (
                <OnboardingPage onComplete={handleOnboardingComplete} />
              )
            ) : (
              <Navigate to="/auth" replace />
            )
          }
        />

        {/* Protected App Layout & Sub-routes */}
        <Route
          path="/"
          element={
            isAuthenticated ? (
              hasCompletedOnboarding ? (
                <AppLayout
                  studentName={studentName}
                  onLogout={handleLogout}
                />
              ) : (
                <Navigate to="/onboarding" replace />
              )
            ) : (
              <Navigate to="/auth" replace />
            )
          }
        >
          <Route index element={<TodayPage />} />
          <Route path="subjects" element={<SubjectsPage />} />
          <Route path="progress" element={<ProgressPage />} />
          <Route path="advisor" element={<AdvisorPage />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
