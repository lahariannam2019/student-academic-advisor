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

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return Boolean(localStorage.getItem('access_token'));
  });
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState<boolean>(() => {
    return localStorage.getItem('onboarding_completed') === 'true';
  });
  const [studentName, setStudentName] = useState<string>(() => {
    return localStorage.getItem('student_name') || 'Student';
  });
  const [initialLoading, setInitialLoading] = useState<boolean>(true);

  // Verify active profile upon application mount
  useEffect(() => {
    const checkSession = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const profile = await api.get<StudentProfile>('/api/auth/profile');
          if (profile && profile.name) {
            setStudentName(profile.name);
            localStorage.setItem('student_name', profile.name);
            const isCompleted = Boolean(profile.onboarding_completed && profile.name && profile.college);
            setHasCompletedOnboarding(isCompleted);
            localStorage.setItem('onboarding_completed', isCompleted ? 'true' : 'false');
          } else {
            setHasCompletedOnboarding(false);
          }
          setIsAuthenticated(true);
        } catch (err) {
          console.warn('Session expired or invalid:', err);
          handleLogout();
        }
      }
      setInitialLoading(false);
    };
    checkSession();
  }, []);

  const handleLoginSuccess = (name: string, needsOnboarding: boolean) => {
    setIsAuthenticated(true);
    setStudentName(name || 'Student');
    setHasCompletedOnboarding(!needsOnboarding);
    localStorage.setItem('onboarding_completed', !needsOnboarding ? 'true' : 'false');
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('is_authenticated');
    localStorage.removeItem('student_name');
    localStorage.removeItem('onboarding_completed');
    localStorage.removeItem('user_id');
    localStorage.removeItem('profile_id');
    setIsAuthenticated(false);
    setHasCompletedOnboarding(false);
    setStudentName('Student');
  };

  const handleOnboardingComplete = (completedName: string) => {
    setStudentName(completedName);
    localStorage.setItem('student_name', completedName);
    localStorage.setItem('onboarding_completed', 'true');
    setHasCompletedOnboarding(true);
  };

  if (initialLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin" />
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
