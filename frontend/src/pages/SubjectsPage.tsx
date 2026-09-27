import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { 
  Plus, 
  AlertCircle, 
  BookOpen 
} from 'lucide-react';
import { api } from '../services/api';
import type { SubjectDetailResponse } from '../types';

export const SubjectsPage: React.FC = () => {
  const [subjects, setSubjects] = useState<SubjectDetailResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [, setError] = useState<string | null>(null);

  // Modal States
  const [selectedSubject, setSelectedSubject] = useState<SubjectDetailResponse | null>(null);
  const [isAddSubjectOpen, setIsAddSubjectOpen] = useState(false);
  const [isAddMarkOpen, setIsAddMarkOpen] = useState(false);

  // New Subject Form
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [credits, setCredits] = useState('3.0');
  const [instructor, setInstructor] = useState('');
  const [difficulty, setDifficulty] = useState('moderate');
  const [submitting, setSubmitting] = useState(false);

  // New Mark Form
  const [markName, setMarkName] = useState('');
  const [assessmentType, setAssessmentType] = useState('quiz');
  const [maxMarks, setMaxMarks] = useState('20');
  const [obtainedMarks, setObtainedMarks] = useState('17');
  const [weight, setWeight] = useState('10');

  const fetchSubjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get<SubjectDetailResponse[]>('/api/subjects');
      setSubjects(res);
      if (selectedSubject) {
        const updated = res.find((s) => s.id === selectedSubject.id);
        if (updated) setSelectedSubject(updated);
      }
    } catch (err: any) {
      console.error('Failed to load subjects:', err);
      setError(err.message || 'Failed to load subjects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubjects();
  }, []);

  const handleCreateSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await api.post('/api/subjects', {
        code,
        name,
        credits: parseFloat(credits) || 3.0,
        instructor,
        difficulty,
        topics: [],
      });
      setIsAddSubjectOpen(false);
      setCode('');
      setName('');
      setInstructor('');
      await fetchSubjects();
    } catch (err: any) {
      alert(err.message || 'Failed to add subject');
    } finally {
      setSubmitting(false);
    }
  };

  const handleLogAttendance = async (subjectId: string, status: 'present' | 'absent') => {
    try {
      const today = new Date().toISOString().split('T')[0];
      await api.post('/api/attendance/log', {
        subject_id: subjectId,
        date: today,
        status,
        notes: `Quick logged ${status}`,
      });
      await fetchSubjects();
    } catch (err: any) {
      alert(err.message || 'Failed to log attendance');
    }
  };

  const handleAddMark = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSubject) return;
    try {
      setSubmitting(true);
      const today = new Date().toISOString().split('T')[0];
      await api.post('/api/marks', {
        subject_id: selectedSubject.id,
        name: markName,
        assessment_type: assessmentType,
        max_marks: parseFloat(maxMarks) || 100,
        obtained_marks: parseFloat(obtainedMarks) || 0,
        weight: parseFloat(weight) || 10,
        date: today,
      });
      setIsAddMarkOpen(false);
      setMarkName('');
      await fetchSubjects();
    } catch (err: any) {
      alert(err.message || 'Failed to log mark');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && subjects.length === 0) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-10 w-64 bg-slate-200 rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="h-64 bg-slate-200 rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  const totalCredits = subjects.reduce((acc, s) => acc + s.credits, 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Subjects & Coursework</h2>
          <p className="text-sm text-slate-500">
            Current Semester • {subjects.length} Enrolled Subjects • {totalCredits} Total Credits
          </p>
        </div>
        <Button onClick={() => setIsAddSubjectOpen(true)} leftIcon={<Plus className="w-4 h-4" />}>
          Add Subject
        </Button>
      </div>

      {subjects.length === 0 ? (
        <Card className="text-center py-12">
          <BookOpen className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No Subjects Added Yet</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
            Add your semester courses to start tracking attendance policies and assessment grades.
          </p>
          <Button onClick={() => setIsAddSubjectOpen(true)}>Add Your First Subject</Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {subjects.map((sub) => {
            const isCritical = sub.attendance_status === 'critical';
            const isWarning = sub.attendance_status === 'warning';

            return (
              <Card
                key={sub.id}
                hover
                className={`flex flex-col justify-between transition-all ${
                  isCritical ? 'border-rose-300 bg-rose-50/15' : ''
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span
                        className={`text-xs font-bold px-2 py-0.5 rounded ${
                          isCritical
                            ? 'text-rose-700 bg-rose-100'
                            : 'text-indigo-600 bg-indigo-50'
                        }`}
                      >
                        {sub.code}
                      </span>
                      <h3 className="text-base font-bold text-slate-900 mt-1 line-clamp-1">
                        {sub.name}
                      </h3>
                      <p className="text-xs text-slate-500">
                        {sub.credits} Credits {sub.instructor ? `• ${sub.instructor}` : ''}
                      </p>
                    </div>

                    <Badge
                      variant={
                        isCritical ? 'danger' : isWarning ? 'warning' : 'success'
                      }
                      size="sm"
                    >
                      {sub.attendance_pct}%
                    </Badge>
                  </div>

                  {/* Attendance Section */}
                  <div className="mt-4 pt-3 border-t border-slate-100 space-y-2.5">
                    <div>
                      <div className="flex justify-between text-xs font-medium text-slate-600 mb-1">
                        <span>
                          Attendance: {sub.attended_classes} / {sub.total_classes} classes
                        </span>
                        <span
                          className={`font-bold ${
                            isCritical ? 'text-rose-600' : 'text-emerald-600'
                          }`}
                        >
                          {sub.attendance_pct}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-2 rounded-full transition-all duration-500 ${
                            isCritical
                              ? 'bg-rose-500'
                              : isWarning
                              ? 'bg-amber-500'
                              : 'bg-emerald-500'
                          }`}
                          style={{ width: `${Math.min(100, sub.attendance_pct)}%` }}
                        />
                      </div>
                      <span className="text-[11px] block mt-1 font-medium">
                        {isCritical ? (
                          <span className="text-rose-600 flex items-center gap-1 font-bold">
                            <AlertCircle className="w-3 h-3" />
                            Must attend next {sub.classes_needed} consecutive classes
                          </span>
                        ) : (
                          <span className="text-slate-500">
                            Can miss up to {sub.classes_can_miss} classes safely
                          </span>
                        )}
                      </span>
                    </div>

                    {/* Academic Performance & Next Exam */}
                    <div className="flex justify-between text-xs py-1 border-t border-slate-50">
                      <span className="text-slate-500">Current Score:</span>
                      <span className="font-semibold text-slate-800">
                        {sub.current_marks_pct !== null ? `${sub.current_marks_pct}%` : 'No marks yet'}
                      </span>
                    </div>

                    <div className="flex justify-between text-xs py-1">
                      <span className="text-slate-500">Trend:</span>
                      <span className="font-semibold text-slate-800 flex items-center gap-1">
                        {sub.performance_trend === 'improving' && <span className="text-emerald-600">↑ Improving</span>}
                        {sub.performance_trend === 'declining' && <span className="text-rose-600">↓ Declining</span>}
                        {sub.performance_trend === 'stable' && <span className="text-slate-600">- Stable</span>}
                        {sub.performance_trend === 'insufficient_data' && <span className="text-slate-400">N/A</span>}
                      </span>
                    </div>

                    <div className="flex justify-between text-xs py-1">
                      <span className="text-slate-500">Next Exam:</span>
                      <span className="font-semibold text-slate-800">
                        {sub.upcoming_exam_date || 'None scheduled'}
                      </span>
                    </div>

                    <div className="flex justify-between text-xs py-1 border-t border-slate-100 mt-1 pt-2">
                      <span className="text-slate-500">Status:</span>
                      <span className={`font-bold ${isCritical || sub.performance_trend === 'declining' ? 'text-rose-600' : 'text-emerald-600'}`}>
                        {isCritical || sub.performance_trend === 'declining' ? 'Needs Attention' : 'On Track'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Quick Log Buttons and Details */}
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => handleLogAttendance(sub.id, 'present')}
                      title="Log Present (+1)"
                      className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-2 py-1 rounded-md transition-colors"
                    >
                      + Present
                    </button>
                    <button
                      onClick={() => handleLogAttendance(sub.id, 'absent')}
                      title="Log Absent (+1)"
                      className="text-[11px] font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 px-2 py-1 rounded-md transition-colors"
                    >
                      + Absent
                    </button>
                  </div>
                  <button
                    onClick={() => setSelectedSubject(sub)}
                    className="text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                  >
                    Details →
                  </button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Add Subject Modal */}
      <Modal
        isOpen={isAddSubjectOpen}
        onClose={() => setIsAddSubjectOpen(false)}
        title="Add New Subject"
        description="Register a course for your current semester."
      >
        <form onSubmit={handleCreateSubject} className="space-y-3.5">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Subject Code</label>
              <input
                type="text"
                required
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="e.g. CS304"
                className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Credits</label>
              <input
                type="number"
                step="0.5"
                required
                value={credits}
                onChange={(e) => setCredits(e.target.value)}
                className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">Subject Name</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Operating Systems"
              className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Instructor (Optional)</label>
              <input
                type="text"
                value={instructor}
                onChange={(e) => setInstructor(e.target.value)}
                placeholder="e.g. Dr. Vance"
                className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Difficulty</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
              >
                <option value="easy">Easy</option>
                <option value="moderate">Moderate</option>
                <option value="challenging">Challenging</option>
              </select>
            </div>
          </div>

          <div className="pt-3 flex justify-end gap-2 border-t border-slate-100">
            <Button variant="ghost" type="button" onClick={() => setIsAddSubjectOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={submitting}>
              Add Subject
            </Button>
          </div>
        </form>
      </Modal>

      {/* Subject Detailed View Modal */}
      {selectedSubject && (
        <Modal
          isOpen={!!selectedSubject}
          onClose={() => setSelectedSubject(null)}
          title={`${selectedSubject.code}: ${selectedSubject.name}`}
          description={`${selectedSubject.credits} Credits • ${selectedSubject.instructor || 'Faculty'}`}
          maxWidth="lg"
        >
          <div className="space-y-4">
            {/* Quick Metrics */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-[11px] text-slate-500 uppercase block font-semibold">Attendance</span>
                <span className="text-lg font-extrabold text-slate-900">{selectedSubject.attendance_pct}%</span>
                <span className="text-[11px] text-slate-500 block mt-0.5">
                  {selectedSubject.attended_classes}/{selectedSubject.total_classes} attended
                </span>
              </div>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-[11px] text-slate-500 uppercase block font-semibold">Current Score</span>
                <span className="text-lg font-extrabold text-slate-900">
                  {selectedSubject.current_marks_pct !== null ? `${selectedSubject.current_marks_pct}%` : 'N/A'}
                </span>
                <span className="text-[11px] text-slate-500 block mt-0.5">
                  {selectedSubject.assessments_count} assessments
                </span>
              </div>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-[11px] text-slate-500 uppercase block font-semibold">Priority</span>
                <span className="text-lg font-extrabold text-indigo-600">{selectedSubject.priority_score}</span>
                <span className="text-[11px] text-slate-500 block mt-0.5">/ 100 score</span>
              </div>
            </div>

            {/* Attendance Buffer Guidance */}
            <div
              className={`p-3.5 rounded-xl border text-xs leading-relaxed ${
                selectedSubject.attendance_status === 'critical'
                  ? 'bg-rose-50 border-rose-200 text-rose-800'
                  : 'bg-emerald-50 border-emerald-200 text-emerald-800'
              }`}
            >
              {selectedSubject.attendance_status === 'critical' ? (
                <span>
                  <strong>Attendance Policy Alert:</strong> You are currently below 75%. You must attend the next{' '}
                  <strong>{selectedSubject.classes_needed} consecutive classes</strong> to restore safety.
                </span>
              ) : (
                <span>
                  <strong>Safe Zone:</strong> You can safely miss up to{' '}
                  <strong>{selectedSubject.classes_can_miss} classes</strong> without dropping below the 75% policy threshold.
                </span>
              )}
            </div>

            {/* Marks Breakdown */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-slate-900">Assessments & Marks</h4>
                <button
                  onClick={() => setIsAddMarkOpen(true)}
                  className="text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                >
                  + Add Mark
                </button>
              </div>

              {selectedSubject.marks.length === 0 ? (
                <p className="text-xs text-slate-400 italic py-2">No assessment marks logged yet.</p>
              ) : (
                <div className="divide-y divide-slate-100 border border-slate-100 rounded-xl overflow-hidden">
                  {selectedSubject.marks.map((m: any) => (
                    <div key={m.id} className="p-2.5 flex items-center justify-between text-xs bg-white">
                      <div>
                        <span className="font-semibold text-slate-800 block">{m.name}</span>
                        <span className="text-[11px] text-slate-400">{m.date} • Wt: {m.weight}%</span>
                      </div>
                      <div className="text-right">
                        <span className="font-bold text-slate-900">{m.obtained_marks} / {m.max_marks}</span>
                        <span className="text-[11px] text-indigo-600 block">
                          {Math.round((m.obtained_marks / m.max_marks) * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Add Mark Modal */}
      {isAddMarkOpen && (
        <Modal
          isOpen={isAddMarkOpen}
          onClose={() => setIsAddMarkOpen(false)}
          title="Log Assessment Marks"
          description={`Record assessment results for ${selectedSubject?.code}`}
        >
          <form onSubmit={handleAddMark} className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Assessment Name</label>
              <input
                type="text"
                required
                value={markName}
                onChange={(e) => setMarkName(e.target.value)}
                placeholder="e.g. Midterm 2, Quiz 3"
                className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Type</label>
                <select
                  value={assessmentType}
                  onChange={(e) => setAssessmentType(e.target.value)}
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
                >
                  <option value="quiz">Quiz</option>
                  <option value="assignment">Assignment</option>
                  <option value="midterm">Midterm</option>
                  <option value="lab">Lab Practical</option>
                  <option value="internal">Internal Test</option>
                  <option value="final">Final Exam</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Course Weight (%)</label>
                <input
                  type="number"
                  step="1"
                  required
                  value={weight}
                  onChange={(e) => setWeight(e.target.value)}
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Obtained Marks</label>
                <input
                  type="number"
                  step="0.5"
                  required
                  value={obtainedMarks}
                  onChange={(e) => setObtainedMarks(e.target.value)}
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Max Marks</label>
                <input
                  type="number"
                  step="0.5"
                  required
                  value={maxMarks}
                  onChange={(e) => setMaxMarks(e.target.value)}
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-indigo-600"
                />
              </div>
            </div>

            <div className="pt-3 flex justify-end gap-2 border-t border-slate-100">
              <Button variant="ghost" type="button" onClick={() => setIsAddMarkOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" isLoading={submitting}>
                Save Marks
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
