import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import type { DashboardResponse, StudyBlockResponse } from '../types';

export const TodayPage: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completingId, setCompletingId] = useState<string | null>(null);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get<DashboardResponse>('/api/dashboard/today');
      setData(res);
    } catch (err: any) {
      console.error('Failed to load dashboard:', err);
      setError(err.message || 'Failed to load dashboard. Make sure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleUpdateBlockStatus = async (blockId: string, status: 'completed' | 'skipped') => {
    try {
      setCompletingId(blockId);
      await api.post(`/api/planner/blocks/${blockId}/status`, { status });
      // Optimistic update
      setData((prev: DashboardResponse | null) => {
        if (!prev) return prev;
        return {
          ...prev,
          study_blocks: prev.study_blocks.map((b: StudyBlockResponse) =>
            b.id === blockId ? { ...b, status } : b
          ),
        };
      });
    } catch (err) {
      console.error('Failed to update study block status:', err);
    } finally {
      setTimeout(() => setCompletingId(null), 400);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-44 bg-slate-200 rounded-3xl" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="h-28 bg-slate-200 rounded-2xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-72 bg-slate-200 rounded-2xl" />
          <div className="h-72 bg-slate-200 rounded-2xl" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <Card className="text-center py-12 space-y-4">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
        <h3 className="text-lg font-bold text-slate-900">Unable to Load Today's Plan</h3>
        <p className="text-sm text-slate-500 max-w-md mx-auto">{error}</p>
        <Button onClick={fetchDashboard} leftIcon={<RefreshCw className="w-4 h-4" />}>
          Try Again
        </Button>
      </Card>
    );
  }

  const topPriority = data.top_priority;
  const primaryReason =
    topPriority?.reasons && topPriority.reasons.length > 0
      ? topPriority.reasons[0]
      : 'Maintain steady performance across all coursework.';

  return (
    <div className="space-y-8">
      {/* ----------------------------------------
          GREETING
      ---------------------------------------- */}
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight text-slate-900">
          Good morning, {data.student_name}
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Here is your academic overview for today.
        </p>
      </div>

      {/* ----------------------------------------
          YOUR ACADEMIC SNAPSHOT
      ---------------------------------------- */}
      <section className="space-y-4">
        <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Your Academic Snapshot</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          
          {/* Current CGPA */}
          <Card>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-2">
              Current CGPA
            </span>
            {data.cgpa > 0 ? (
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-slate-900">{data.cgpa.toFixed(2)}</span>
                <span className="text-xs text-slate-500 font-medium">/ 10.0</span>
              </div>
            ) : (
              <div className="space-y-1">
                <span className="text-sm font-bold text-slate-600 block">Not calculated yet</span>
                <p className="text-xs text-slate-500 leading-relaxed">Add your assessment marks to calculate your current CGPA.</p>
              </div>
            )}
          </Card>

          {/* Target CGPA */}
          <Card>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-2">
              Target CGPA
            </span>
            {data.target_cgpa ? (
              <div className="space-y-1">
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-indigo-600">{data.target_cgpa.toFixed(2)}</span>
                </div>
                {data.cgpa > 0 && (
                  <p className="text-xs font-medium text-indigo-600/80">
                    {Math.max(0, data.target_cgpa - data.cgpa).toFixed(2)} remaining to goal
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-1">
                <span className="text-sm font-bold text-slate-600 block">No target set</span>
                <p className="text-xs text-slate-500 leading-relaxed">Set a target in your profile.</p>
              </div>
            )}
          </Card>

          {/* Attendance */}
          <Card>
            <div className="flex justify-between items-start mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Attendance
              </span>
              <Badge variant={data.critical_attendance_subjects_count > 0 ? 'danger' : 'success'}>
                {data.critical_attendance_subjects_count > 0 ? `${data.critical_attendance_subjects_count} at Risk` : 'Safe'}
              </Badge>
            </div>
            {data.overall_attendance_pct !== undefined ? (
              <div className="space-y-1">
                <div className="flex items-baseline gap-2">
                  <span className={`text-3xl font-extrabold ${data.overall_attendance_pct < data.attendance_minimum_pct ? 'text-rose-600' : 'text-slate-900'}`}>
                    {data.overall_attendance_pct}%
                  </span>
                  <span className="text-xs text-slate-500 font-medium">overall</span>
                </div>
                <p className="text-xs text-slate-500">Required: {data.attendance_minimum_pct}%</p>
              </div>
            ) : (
              <div className="space-y-1">
                <span className="text-sm font-bold text-slate-600 block">Not tracked yet</span>
                <p className="text-xs text-slate-500 leading-relaxed">Log attendance to monitor risk.</p>
              </div>
            )}
          </Card>

          {/* Next Exam */}
          <Card>
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-2">
              Next Exam
            </span>
            {data.next_exam ? (
              <div className="space-y-1">
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-slate-900">
                    {Math.max(0, Math.round(data.next_exam.days_until || 0))}
                  </span>
                  <span className="text-xs text-slate-500 font-medium">days left</span>
                </div>
                <p className="text-xs font-medium text-slate-700 truncate">{data.next_exam.subject_name}</p>
                <p className="text-[11px] text-slate-500 uppercase tracking-wider">{data.next_exam.exam_type}</p>
              </div>
            ) : (
              <div className="space-y-1">
                <span className="text-sm font-bold text-slate-600 block">No upcoming exams</span>
                <p className="text-xs text-slate-500 leading-relaxed">Add your next exam to unlock exam-based study planning.</p>
              </div>
            )}
          </Card>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column (Priority & Plan) */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* ----------------------------------------
              TODAY'S PRIORITY
          ---------------------------------------- */}
          <section className="space-y-4">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Today's Priority</h3>
            {topPriority ? (
              <Card className="border-l-4 border-l-indigo-600 shadow-sm bg-indigo-50/30">
                <div className="space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <h4 className="text-lg font-bold text-indigo-950">
                        {(topPriority as any).action || `Focus on ${topPriority.subject_name}`}
                      </h4>
                      <div className="flex items-center gap-3 mt-1.5 text-xs font-medium text-indigo-700/80">
                        <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5"/> ~{(topPriority as any).duration_minutes || 45} min</span>
                        <span>•</span>
                        <span>{topPriority.subject_name}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => navigate('/advisor')}
                      className="shrink-0 bg-indigo-600 text-white px-4 py-2 rounded-xl text-xs font-bold hover:bg-indigo-700 transition-colors shadow-xs"
                    >
                      Ask AI Advisor
                    </button>
                  </div>
                  
                  <div className="bg-white rounded-xl p-4 border border-indigo-100 shadow-2xs">
                    <h5 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Why this is prioritized:</h5>
                    <ul className="space-y-2">
                      {topPriority.reasons?.map((reason: string, i: number) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-slate-600 leading-relaxed">
                          <span className="text-indigo-400 mt-0.5">•</span>
                          <span>{reason}</span>
                        </li>
                      ))}
                      {!topPriority.reasons?.length && (
                        <li className="flex items-start gap-2 text-sm text-slate-600 leading-relaxed">
                          <span className="text-indigo-400 mt-0.5">•</span>
                          <span>{primaryReason}</span>
                        </li>
                      )}
                    </ul>
                  </div>
                </div>
              </Card>
            ) : (
              <Card className="bg-slate-50 border-dashed text-center py-8">
                <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                <h4 className="text-sm font-bold text-slate-700">You're all caught up!</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                  There are no critical actions required today based on your current academic records.
                </p>
              </Card>
            )}
          </section>

          {/* ----------------------------------------
              TODAY'S STUDY PLAN
          ---------------------------------------- */}
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Today's Study Plan</h3>
              <span className="text-xs font-semibold text-slate-500">
                {data.study_blocks.reduce((acc: number, b: StudyBlockResponse) => acc + b.duration_minutes, 0)}m total
              </span>
            </div>

            <div className="space-y-3">
              {data.study_blocks.length === 0 ? (
                <Card className="text-center py-6 text-slate-500 text-sm">
                  No study blocks scheduled for today.
                </Card>
              ) : (
                data.study_blocks.slice(0, 5).map((block: StudyBlockResponse) => {
                  const isCompleted = block.status === 'completed';
                  const isSkipped = block.status === 'skipped';
                  const isBeingUpdated = completingId === block.id;

                  return (
                    <Card
                      key={block.id}
                      className={`transition-all ${isCompleted ? 'opacity-60 bg-slate-50 border-slate-200' : isSkipped ? 'opacity-40 bg-slate-100' : 'hover:border-indigo-200'}`}
                    >
                      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant={isCompleted ? 'success' : 'default'} size="sm">{block.duration_minutes} min</Badge>
                            <span className="text-xs font-bold text-slate-700">{block.subject_name}</span>
                          </div>
                          <h4 className={`text-sm font-bold ${isCompleted ? 'line-through text-slate-500' : 'text-slate-900'}`}>
                            {block.task_description}
                          </h4>
                        </div>
                        
                        {!isCompleted && !isSkipped && (
                          <div className="flex items-center gap-2 shrink-0">
                            <button
                              disabled={isBeingUpdated}
                              onClick={() => handleUpdateBlockStatus(block.id, 'skipped')}
                              className="text-xs text-slate-400 hover:text-slate-700 font-medium px-3 py-1.5 transition-colors"
                            >
                              Skip
                            </button>
                            <button
                              disabled={isBeingUpdated}
                              onClick={() => handleUpdateBlockStatus(block.id, 'completed')}
                              className="text-xs bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold px-4 py-1.5 rounded-lg transition-colors"
                            >
                              {isBeingUpdated ? 'Saving...' : 'Done'}
                            </button>
                          </div>
                        )}
                        {isCompleted && (
                          <div className="shrink-0 text-emerald-600 flex items-center gap-1.5 text-xs font-bold bg-emerald-50 px-3 py-1.5 rounded-lg">
                            <CheckCircle2 className="w-4 h-4"/> Completed
                          </div>
                        )}
                      </div>
                    </Card>
                  );
                })
              )}
            </div>
          </section>

        </div>

        {/* Right Column (Upcoming) */}
        <div className="space-y-8">
          
          {/* ----------------------------------------
              UPCOMING
          ---------------------------------------- */}
          <section className="space-y-4">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Upcoming</h3>
            
            <Card className="space-y-5 bg-slate-50/50">
              
              {/* Alert Snippet if Capacity Issue */}
              {data.conflict_message && (
                <div className="bg-amber-50 rounded-xl p-3 border border-amber-200">
                  <div className="flex items-start gap-2.5">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <h6 className="text-[11px] font-bold text-amber-900 uppercase">Capacity Alert</h6>
                      <p className="text-xs text-amber-800 mt-1">{data.conflict_message}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Next Exam Mini */}
              <div>
                <h6 className="text-xs font-bold text-slate-500 uppercase mb-2">Next Exam</h6>
                {data.next_exam ? (
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-bold text-slate-900">{data.next_exam.subject_name}</p>
                      <p className="text-xs text-slate-500">{data.next_exam.exam_type}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-extrabold text-indigo-600">{Math.round(data.next_exam.days_until || 0)}d</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">No pending exams.</p>
                )}
              </div>

              {/* Upcoming Assignment Mini */}
              <div className="pt-4 border-t border-slate-200">
                <h6 className="text-xs font-bold text-slate-500 uppercase mb-2">Pending Assignments</h6>
                {data.pending_assignments_count > 0 ? (
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-bold text-slate-900">{data.pending_assignments_count} Tasks Due</p>
                      {data.overdue_assignments_count > 0 && (
                        <p className="text-xs font-bold text-rose-600">{data.overdue_assignments_count} Overdue</p>
                      )}
                    </div>
                    <button onClick={() => navigate('/progress')} className="text-xs font-bold text-indigo-600 hover:text-indigo-800">
                      View all &rarr;
                    </button>
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">No pending assignments</p>
                )}
              </div>

              {/* Profile Completeness */}
              {data.profile_completeness && data.profile_completeness.percentage < 100 && (
                <div className="pt-4 border-t border-slate-200">
                  <div className="flex justify-between items-center mb-2">
                    <h6 className="text-xs font-bold text-slate-500 uppercase">Profile Completeness</h6>
                    <span className="text-xs font-bold text-indigo-600">{data.profile_completeness.percentage}%</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-1.5 mb-3">
                    <div className="bg-indigo-600 h-1.5 rounded-full" style={{ width: `${data.profile_completeness.percentage}%` }}></div>
                  </div>
                  <div className="space-y-1.5 mb-3">
                    {data.profile_completeness.checks.map((c, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs">
                        <CheckCircle2 className={`w-3.5 h-3.5 ${c.done ? 'text-emerald-500' : 'text-slate-300'}`} />
                        <span className={c.done ? 'text-slate-700' : 'text-slate-400'}>{c.label}</span>
                      </div>
                    ))}
                  </div>
                  {data.profile_completeness.message && (
                    <p className="text-[11px] text-slate-500 leading-relaxed italic">
                      "{data.profile_completeness.message}"
                    </p>
                  )}
                </div>
              )}

            </Card>
          </section>

        </div>
      </div>
    </div>
  );
};
