import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { 
  Save, 
  CheckCircle2, 
  RefreshCw, 
  AlertCircle 
} from 'lucide-react';
import { api } from '../services/api';
import type { StudentProfile } from '../types';

export const ProfilePage: React.FC = () => {
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [name, setName] = useState('');
  const [college, setCollege] = useState('');
  const [program, setProgram] = useState('');
  const [department, setDepartment] = useState('');
  const [targetCgpa, setTargetCgpa] = useState('8.50');
  const [attendanceMin, setAttendanceMin] = useState(75);
  const [studyHours, setStudyHours] = useState('2.0');

  const fetchProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get<StudentProfile>('/api/auth/profile');
      setProfile(res);
      setName(res.name);
      setCollege(res.college);
      setProgram(res.program);
      setDepartment(res.department);
      setTargetCgpa(res.target_cgpa ? String(res.target_cgpa) : '8.50');
      setAttendanceMin(res.attendance_minimum_pct || 75);
      setStudyHours(String(res.daily_study_hours || 2.0));
    } catch (err: any) {
      console.error('Failed to load profile:', err);
      setError(err.message || 'Failed to load student profile');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setSavedSuccess(false);
      const updated = await api.put<StudentProfile>('/api/auth/profile', {
        name,
        college,
        program,
        department,
        target_cgpa: parseFloat(targetCgpa) || undefined,
        attendance_minimum_pct: attendanceMin,
        daily_study_hours: parseFloat(studyHours) || 2.0,
      });
      setProfile(updated);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err: any) {
      alert(err.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto animate-pulse">
        <div className="h-10 w-48 bg-slate-200 rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="h-64 bg-slate-200 rounded-2xl" />
          <div className="md:col-span-2 h-96 bg-slate-200 rounded-2xl" />
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <Card className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-2" />
        <h3 className="text-lg font-bold text-slate-900">Profile Unavailable</h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto mb-4">{error}</p>
        <Button onClick={fetchProfile} leftIcon={<RefreshCw className="w-4 h-4" />}>
          Retry
        </Button>
      </Card>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Student Academic Profile</h2>
        <p className="text-sm text-slate-500">
          Manage your institutional requirements, target CGPA, and daily study capacity.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column Profile Card */}
        <Card className="text-center flex flex-col items-center justify-center py-8">
          <div className="w-20 h-20 rounded-2xl bg-indigo-100 text-indigo-600 font-extrabold text-2xl flex items-center justify-center mb-3 shadow-inner">
            {profile.name
              .split(' ')
              .map((n) => n[0])
              .join('')}
          </div>
          <h3 className="text-lg font-bold text-slate-900">{profile.name}</h3>
          <p className="text-xs text-slate-500">{profile.department}</p>
          <div className="mt-4 flex gap-1.5 flex-wrap justify-center">
            <Badge variant="indigo">Year {profile.current_year}</Badge>
            <Badge variant="slate">Semester {profile.current_semester}</Badge>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 text-left w-full space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">Grading System:</span>
              <span className="font-semibold text-slate-700 capitalize">
                {profile.grading_scale.replace('_', ' ')} Scale
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Policy Threshold:</span>
              <span className="font-semibold text-slate-700">
                {profile.attendance_minimum_pct}% Min
              </span>
            </div>
          </div>
        </Card>

        {/* Right Column Editable Settings */}
        <Card className="md:col-span-2">
          <form onSubmit={handleSave} className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h4 className="text-base font-bold text-slate-900">Academic Preferences</h4>
              {savedSuccess && (
                <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" /> Preferences Saved!
                </span>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Student Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">College / University</label>
                <input
                  type="text"
                  required
                  value={college}
                  onChange={(e) => setCollege(e.target.value)}
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Degree / Program</label>
                <input
                  type="text"
                  required
                  value={program}
                  onChange={(e) => setProgram(e.target.value)}
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Department</label>
                <input
                  type="text"
                  required
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Target CGPA</label>
                <input
                  type="number"
                  step="0.05"
                  value={targetCgpa}
                  onChange={(e) => setTargetCgpa(e.target.value)}
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
                />
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Used in mathematical feasibility analysis.
                </span>
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Daily Available Study Hours</label>
                <select
                  value={studyHours}
                  onChange={(e) => setStudyHours(e.target.value)}
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
                >
                  <option value="1.0">1.0 Hour</option>
                  <option value="1.5">1.5 Hours</option>
                  <option value="2.0">2.0 Hours (Recommended)</option>
                  <option value="3.0">3.0 Hours</option>
                  <option value="4.0">4.0 Hours</option>
                </select>
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Used by daily study planner for capacity balancing.
                </span>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Attendance Policy Minimum Requirement (%)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="60"
                  max="90"
                  step="5"
                  value={attendanceMin}
                  onChange={(e) => setAttendanceMin(Number(e.target.value))}
                  className="flex-1 accent-indigo-600"
                />
                <span className="text-sm font-bold text-slate-900 w-12 text-right">{attendanceMin}%</span>
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">
                Subjects below this threshold are flagged as critical attendance risks.
              </span>
            </div>

            <div className="pt-3 flex justify-end">
              <Button type="submit" isLoading={saving} leftIcon={<Save className="w-4 h-4" />}>
                Save Preferences
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
};
