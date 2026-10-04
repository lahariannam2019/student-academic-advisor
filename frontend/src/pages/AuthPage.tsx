import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { GraduationCap, Shield, AlertCircle, CheckCircle2, Mail, KeyRound, ArrowLeft } from 'lucide-react';
import { api } from '../services/api';
import type { AuthResponse } from '../types';

interface AuthPageProps {
  onLoginSuccess: (studentName: string, needsOnboarding: boolean) => void;
}

type AuthMode = 'signin' | 'signup' | 'forgot' | 'verify';

export const AuthPage: React.FC<AuthPageProps> = ({ onLoginSuccess }) => {
  const [mode, setMode] = useState<AuthMode>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const processAuthSuccess = (res: AuthResponse) => {
    localStorage.setItem('access_token', res.access_token);
    localStorage.setItem('is_authenticated', 'true');
    localStorage.setItem('user_id', res.user_id);
    localStorage.setItem('profile_id', res.profile_id);

    if (res.student_name) {
      localStorage.setItem('student_name', res.student_name);
    } else {
      localStorage.removeItem('student_name');
    }

    onLoginSuccess(res.student_name || 'Student', res.needs_onboarding);
  };

  const validateEmail = (val: string): boolean => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(val.trim());
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    const cleanEmail = email.trim().toLowerCase();

    if (!validateEmail(cleanEmail)) {
      setError('Please enter a valid email address.');
      return;
    }

    if (mode === 'signup' && password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setLoading(true);

    try {
      if (mode === 'signin') {
        const res = await api.post<AuthResponse>('/api/auth/login', {
          email: cleanEmail,
          password,
        });
        processAuthSuccess(res);
      } else if (mode === 'signup') {
        const res = await api.post<AuthResponse>('/api/auth/signup', {
          email: cleanEmail,
          password,
        });

        if (res.verification_sent) {
          setSuccessMessage(res.message || 'Account created! Verification code sent to your email.');
          setMode('verify');
        } else {
          processAuthSuccess(res);
        }
      } else if (mode === 'forgot') {
        const res = await api.post<{ status: string; message: string }>('/api/auth/forgot-password', {
          email: cleanEmail,
        });
        setSuccessMessage(res.message || 'If an account exists, password reset instructions have been sent.');
      }
    } catch (err: any) {
      console.error('Auth error:', err);
      setError(err.message || 'Authentication failed. Please check your details.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verificationCode.trim()) {
      setError('Please enter the 6-digit verification code.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await api.post<AuthResponse>('/api/auth/verify-email', {
        email: email.trim().toLowerCase(),
        code: verificationCode.trim(),
      });

      setSuccessMessage('Email verified successfully!');
      processAuthSuccess(res);
    } catch (err: any) {
      setError(err.message || 'Verification failed. Please check your code.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    if (!email.trim()) {
      setError('Please enter your email address to resend verification.');
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const res = await api.post<{ status: string; message: string }>('/api/auth/resend-verification', {
        email: email.trim().toLowerCase(),
      });
      setSuccessMessage(res.message || 'Verification code resent!');
    } catch (err: any) {
      setError(err.message || 'Failed to resend verification code.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-indigo-600 text-white items-center justify-center shadow-lg shadow-indigo-100">
            <GraduationCap className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Student Academic Advisor</h1>
          <p className="text-sm text-slate-500">
            Your personalized, data-driven academic intelligence companion
          </p>
        </div>

        {/* Auth Card */}
        <Card>
          {/* View Mode Header Tabs */}
          {mode !== 'verify' && mode !== 'forgot' ? (
            <div className="flex border-b border-slate-100 mb-6">
              <button
                type="button"
                onClick={() => {
                  setMode('signin');
                  setError(null);
                  setSuccessMessage(null);
                }}
                className={`flex-1 pb-3 text-sm font-semibold border-b-2 transition-colors ${
                  mode === 'signin'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-400 hover:text-slate-700'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode('signup');
                  setError(null);
                  setSuccessMessage(null);
                }}
                className={`flex-1 pb-3 text-sm font-semibold border-b-2 transition-colors ${
                  mode === 'signup'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-400 hover:text-slate-700'
                }`}
              >
                Create Account
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => {
                setMode('signin');
                setError(null);
                setSuccessMessage(null);
              }}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-700 mb-4 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Sign In</span>
            </button>
          )}

          {/* Feedback Messages */}
          {error && (
            <div className="mb-4 p-3 bg-rose-50 border border-rose-200/80 rounded-xl text-xs text-rose-700 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {successMessage && (
            <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200/80 rounded-xl text-xs text-emerald-800 flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <span>{successMessage}</span>
            </div>
          )}

          {/* Mode 1 & 2: Sign In / Sign Up Form */}
          {(mode === 'signin' || mode === 'signup') && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1.5">Student Email</label>
                <div className="relative">
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your.email@college.edu"
                    className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-3.5 py-2.5 outline-none focus:border-indigo-600 focus:bg-white transition-all"
                  />
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-semibold text-slate-700 block">Password</label>
                  {mode === 'signin' && (
                    <button
                      type="button"
                      onClick={() => {
                        setMode('forgot');
                        setError(null);
                        setSuccessMessage(null);
                      }}
                      className="text-xs text-indigo-600 hover:underline font-medium"
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <div className="relative">
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-3.5 py-2.5 outline-none focus:border-indigo-600 focus:bg-white transition-all"
                  />
                  <KeyRound className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                </div>
              </div>

              <Button type="submit" isLoading={loading} className="w-full mt-2">
                {mode === 'signin' ? 'Sign In to Advisor' : 'Create Account & Continue'}
              </Button>
            </form>
          )}

          {/* Mode 3: Forgot Password Form */}
          {mode === 'forgot' && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <h3 className="text-sm font-bold text-slate-800 mb-1">Reset Your Password</h3>
                <p className="text-xs text-slate-500 mb-3">
                  Enter your account email address and we will send password reset instructions.
                </p>
                <div className="relative">
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your.email@college.edu"
                    className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-3.5 py-2.5 outline-none focus:border-indigo-600 focus:bg-white transition-all"
                  />
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                </div>
              </div>

              <Button type="submit" isLoading={loading} className="w-full">
                Send Reset Link
              </Button>
            </form>
          )}

          {/* Mode 4: Email Verification Form */}
          {mode === 'verify' && (
            <form onSubmit={handleVerifyEmail} className="space-y-4">
              <div>
                <h3 className="text-sm font-bold text-slate-800 mb-1">Verify Your Email Address</h3>
                <p className="text-xs text-slate-500 mb-3">
                  Enter the 6-digit verification code sent to <strong className="text-slate-700">{email}</strong>.
                </p>
                <input
                  type="text"
                  maxLength={6}
                  required
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  placeholder="123456"
                  className="w-full text-center text-lg tracking-widest font-mono bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 outline-none focus:border-indigo-600 focus:bg-white transition-all"
                />
              </div>

              <Button type="submit" isLoading={loading} className="w-full">
                Verify Email & Log In
              </Button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={handleResendCode}
                  className="text-xs font-semibold text-indigo-600 hover:underline"
                >
                  Resend verification code
                </button>
              </div>
            </form>
          )}

          {/* Footer Security Note */}
          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-center gap-1.5 text-xs text-slate-400">
            <Shield className="w-3.5 h-3.5" />
            <span>Secure password encryption & isolated student records</span>
          </div>
        </Card>
      </div>
    </div>
  );
};
