import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { 
  TrendingUp, 
  Award, 
  CheckCircle, 
  AlertCircle, 
  RefreshCw,
  Edit2,
  Trash2,
  Plus
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  CartesianGrid, 
  BarChart, 
  Bar, 
  Cell 
} from 'recharts';
import { api } from '../services/api';

export const ProgressPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showModal, setShowModal] = useState(false);
  const [editingSemId, setEditingSemId] = useState<string | null>(null);
  const [semNumber, setSemNumber] = useState(1);
  const [semSgpa, setSemSgpa] = useState('');
  const [semCgpa, setSemCgpa] = useState('');
  const [semCredits, setSemCredits] = useState('20');
  const [semSaving, setSemSaving] = useState(false);

  const openAddModal = () => {
    setEditingSemId(null);
    setSemNumber(data?.cgpa_progression?.length ? data.cgpa_progression.length + 1 : 1);
    setSemSgpa('');
    setSemCgpa('');
    setSemCredits('20');
    setShowModal(true);
  };

  const openEditModal = (sem: any) => {
    setEditingSemId(sem.id);
    const semNumStr = sem.semester.replace(/\D/g, '');
    setSemNumber(parseInt(semNumStr, 10) || 1);
    setSemSgpa(sem.sgpa ? String(sem.sgpa) : '');
    setSemCgpa(sem.cgpa ? String(sem.cgpa) : '');
    setShowModal(true);
  };

  const handleSaveSemester = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSemSaving(true);
      const payload = {
        semester_number: semNumber,
        academic_year: '2023-2024',
        sgpa: semSgpa ? parseFloat(semSgpa) : null,
        cgpa: semCgpa ? parseFloat(semCgpa) : null,
        total_credits: parseFloat(semCredits),
      };

      if (editingSemId) {
        await api.put(`/api/semesters/${editingSemId}`, payload);
      } else {
        await api.post('/api/semesters', payload);
      }
      setShowModal(false);
      fetchAnalytics();
    } catch (err: any) {
      alert(err.message || 'Failed to save semester');
    } finally {
      setSemSaving(false);
    }
  };

  const handleDeleteSemester = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this semester record?")) return;
    try {
      await api.delete(`/api/semesters/${id}`);
      fetchAnalytics();
    } catch (err: any) {
      alert(err.message || 'Failed to delete semester');
    }
  };

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get<any>('/api/analytics');
      setData(res);
    } catch (err: any) {
      console.error('Failed to load analytics:', err);
      setError(err.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-10 w-64 bg-slate-200 rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-32 bg-slate-200 rounded-2xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-72 bg-slate-200 rounded-2xl" />
          <div className="h-72 bg-slate-200 rounded-2xl" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <Card className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-2" />
        <h3 className="text-lg font-bold text-slate-900">Analytics Unavailable</h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto mb-4">{error}</p>
        <Button onClick={fetchAnalytics} leftIcon={<RefreshCw className="w-4 h-4" />}>
          Retry
        </Button>
      </Card>
    );
  }

  const feasibility = data.goal_feasibility;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Academic Analytics & Trajectory</h2>
        <p className="text-sm text-slate-500">
          Deterministic mathematical models for CGPA progression, attendance margins, and target feasibility.
        </p>
      </div>

      {/* Top Feasibility & Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Goal Feasibility Card */}
        <Card className={feasibility?.feasible ? 'border-emerald-200 bg-emerald-50/15' : 'border-rose-200 bg-rose-50/15'}>
          <div className="flex items-center gap-3 mb-2">
            <div
              className={`w-9 h-9 rounded-xl flex items-center justify-center ${
                feasibility?.feasible ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
              }`}
            >
              <Award className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase block">
                Target CGPA Feasibility
              </span>
              <h3 className="text-base font-bold text-slate-900">
                {feasibility ? (feasibility.feasible ? 'Mathematically Achievable' : 'Mathematically Unattainable') : 'No Target Set'}
              </h3>
            </div>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed mt-1">
            {feasibility?.message || 'Set a target CGPA in your profile to run deterministic feasibility checks.'}
          </p>
        </Card>

        {/* Current CGPA */}
        <Card>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase block">Current Standing</span>
              {data.current_cgpa > 0 ? (
                <h3 className="text-base font-bold text-slate-900">
                  {data.current_cgpa.toFixed(2)} CGPA
                </h3>
              ) : (
                <h3 className="text-sm font-bold text-slate-600">
                  Not calculated yet
                </h3>
              )}
            </div>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed mt-1">
            {data.current_cgpa > 0 
              ? 'Credit-weighted average across all completed semesters.' 
              : 'Add your assessment marks to calculate your current CGPA.'}
          </p>
        </Card>

        {/* Study Plan Completion Rate */}
        <Card>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
              <CheckCircle className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase block">Study Velocity</span>
              <h3 className="text-base font-bold text-slate-900">
                {data.study_plan_completion_rate}% Completed
              </h3>
            </div>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed mt-1">
            Percentage of scheduled daily study blocks successfully executed.
          </p>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CGPA Progression Chart */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">CGPA Growth Trajectory</h3>
              <p className="text-xs text-slate-500">Historical performance by semester</p>
            </div>
            <Badge variant="indigo">Official Transcripts</Badge>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.cgpa_progression} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="semester" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis domain={[5.0, 10.0]} tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderRadius: '12px',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                    border: '1px solid #e2e8f0',
                    fontSize: '12px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="cgpa"
                  name="CGPA"
                  stroke="#4f46e5"
                  strokeWidth={3}
                  dot={{ r: 4, fill: '#4f46e5' }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="sgpa"
                  name="SGPA"
                  stroke="#94a3b8"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  dot={{ r: 3, fill: '#94a3b8' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Attendance Margins Chart */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Attendance Safety Margins</h3>
              <p className="text-xs text-slate-500">Classes you can safely miss (+) vs need to attend (-)</p>
            </div>
            <Badge variant="warning">75% Policy Rule</Badge>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.attendance_margins} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="subject" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip
                  formatter={(val: any) => [`${val} classes`, 'Safety Buffer']}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    borderRadius: '12px',
                    border: '1px solid #e2e8f0',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="buffer_classes" radius={[6, 6, 0, 0]}>
                  {data.attendance_margins.map((entry: any, index: number) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.buffer_classes < 0 ? '#f43f5e' : entry.buffer_classes <= 2 ? '#f59e0b' : '#10b981'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Academic History Section */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900">Academic History</h3>
            <p className="text-xs text-slate-500">Official semester results</p>
          </div>
          <Button size="sm" leftIcon={<Plus className="w-4 h-4" />} onClick={openAddModal}>
            Add Semester
          </Button>
        </div>

        {(!data.cgpa_progression || data.cgpa_progression.length === 0) ? (
          <div className="text-center py-8 bg-slate-50 rounded-xl border border-dashed border-slate-200">
            <h4 className="text-sm font-bold text-slate-700">No semester results added yet.</h4>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Add your official SGPA/CGPA for each completed semester to track your academic progress.
            </p>
            <Button size="sm" className="mt-4" onClick={openAddModal}>
              + Add Semester
            </Button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-xs text-slate-500 uppercase tracking-wider">
                  <th className="pb-3 font-semibold">Semester</th>
                  <th className="pb-3 font-semibold text-center">SGPA</th>
                  <th className="pb-3 font-semibold text-center">CGPA</th>
                  <th className="pb-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data.cgpa_progression.map((sem: any, i: number) => (
                  <tr key={sem.id || i} className="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors">
                    <td className="py-3 text-sm font-semibold text-slate-800">{sem.semester}</td>
                    <td className="py-3 text-sm font-medium text-slate-600 text-center">
                      {sem.sgpa ? sem.sgpa.toFixed(2) : '—'}
                    </td>
                    <td className="py-3 text-sm font-bold text-indigo-600 text-center">
                      {sem.cgpa ? sem.cgpa.toFixed(2) : '—'}
                    </td>
                    <td className="py-3 text-right">
                      {sem.id ? (
                        <div className="flex justify-end gap-2">
                          <button onClick={() => openEditModal(sem)} className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors">
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button onClick={() => handleDeleteSemester(sem.id)} className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400 italic">Auto</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Strong vs Weak Subjects Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h4 className="text-sm font-bold text-emerald-800 flex items-center gap-2 mb-3">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            <span>Academic Strengths (Scores &gt; 80%)</span>
          </h4>
          {data.strong_subjects.length === 0 ? (
            <p className="text-xs text-slate-400 italic">No subjects currently exceeding 80% mark threshold.</p>
          ) : (
            <div className="space-y-2">
              {data.strong_subjects.map((s: any) => (
                <div key={s.code} className="flex justify-between items-center p-2.5 bg-emerald-50/50 rounded-xl border border-emerald-100 text-xs">
                  <div>
                    <span className="font-bold text-slate-800">{s.code}</span>
                    <span className="text-slate-600 ml-2">{s.name}</span>
                  </div>
                  <span className="font-extrabold text-emerald-700">{s.score}%</span>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <h4 className="text-sm font-bold text-rose-800 flex items-center gap-2 mb-3">
            <AlertCircle className="w-4 h-4 text-rose-600" />
            <span>Areas for Attention (Scores &lt; 70%)</span>
          </h4>
          {data.weak_subjects.length === 0 ? (
            <p className="text-xs text-emerald-600 font-medium">All enrolled subjects are currently above 70%.</p>
          ) : (
            <div className="space-y-2">
              {data.weak_subjects.map((s: any) => (
                <div key={s.code} className="flex justify-between items-center p-2.5 bg-rose-50/50 rounded-xl border border-rose-100 text-xs">
                  <div>
                    <span className="font-bold text-slate-800">{s.code}</span>
                    <span className="text-slate-600 ml-2">{s.name}</span>
                  </div>
                  <span className="font-extrabold text-rose-700">{s.score}%</span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm overflow-hidden border border-slate-100">
            <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
              <h3 className="font-bold text-slate-800">{editingSemId ? 'Edit Semester' : 'Add Semester'}</h3>
            </div>
            <form onSubmit={handleSaveSemester} className="p-5 space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Semester Number</label>
                <input
                  type="number"
                  min="1"
                  required
                  value={semNumber}
                  onChange={(e) => setSemNumber(parseInt(e.target.value) || 1)}
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600 transition-colors"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">SGPA</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="10"
                    value={semSgpa}
                    onChange={(e) => setSemSgpa(e.target.value)}
                    className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600 transition-colors"
                    placeholder="e.g. 8.10"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">CGPA</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="10"
                    value={semCgpa}
                    onChange={(e) => setSemCgpa(e.target.value)}
                    className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600 transition-colors"
                    placeholder="e.g. 8.10"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Total Credits (Optional)</label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  value={semCredits}
                  onChange={(e) => setSemCredits(e.target.value)}
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600 transition-colors"
                />
              </div>
              <div className="flex justify-end gap-3 pt-3">
                <Button variant="ghost" type="button" onClick={() => setShowModal(false)}>Cancel</Button>
                <Button type="submit" isLoading={semSaving}>Save Changes</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
