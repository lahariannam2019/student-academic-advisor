import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { 
  Check, 
  ChevronRight, 
  ChevronLeft, 
  GraduationCap, 
  Sparkles, 
  Plus, 
  Trash2,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import type { StudentProfileResponse, SubjectOnboardingInput } from '../types';

interface OnboardingPageProps {
  onComplete: (studentName: string) => void;
}

export const OnboardingPage: React.FC<OnboardingPageProps> = ({ onComplete }) => {
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Step 1: Personal Info
  const [name, setName] = useState('');

  // Step 2: Institution
  const [college, setCollege] = useState('');

  // Step 3: Academic Details
  const [program, setProgram] = useState('');
  const [department, setDepartment] = useState('');
  const [currentYear, setCurrentYear] = useState(1);
  const [currentSemester, setCurrentSemester] = useState(1);

  // Step 4: Academic System & Policies
  const [gradingScale, setGradingScale] = useState('10_point');
  const [attendanceMin, setAttendanceMin] = useState(75);

  // Step 5: Academic Goals
  const [targetCgpa, setTargetCgpa] = useState('');

  // Step 6: Study Availability
  const [studyHours, setStudyHours] = useState('2.0');

  // Step 7: Enrolled Subjects
  const [subjectsList, setSubjectsList] = useState<SubjectOnboardingInput[]>([]);
  const [newSubCode, setNewSubCode] = useState('');
  const [newSubName, setNewSubName] = useState('');
  const [newSubCredits, setNewSubCredits] = useState('3.0');
  const [newSubInstructor, setNewSubInstructor] = useState('');
  const [newSubDifficulty, setNewSubDifficulty] = useState('moderate');

  const steps = [
    { num: 1, label: 'Name' },
    { num: 2, label: 'College' },
    { num: 3, label: 'Academic' },
    { num: 4, label: 'Policies' },
    { num: 5, label: 'Goals' },
    { num: 6, label: 'Study Hours' },
    { num: 7, label: 'Subjects' },
  ];

  const handleAddSubject = () => {
    if (!newSubName.trim() || !newSubCode.trim()) {
      alert('Please provide both subject name and subject code.');
      return;
    }
    const newSubject: SubjectOnboardingInput = {
      code: newSubCode.trim().toUpperCase(),
      name: newSubName.trim(),
      credits: parseFloat(newSubCredits) || 3.0,
      instructor: newSubInstructor.trim() || undefined,
      difficulty: newSubDifficulty,
      topics: [],
    };
    setSubjectsList((prev) => [...prev, newSubject]);
    setNewSubCode('');
    setNewSubName('');
    setNewSubInstructor('');
    setNewSubCredits('3.0');
  };

  const handleRemoveSubject = (index: number) => {
    setSubjectsList((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleNext = () => {
    setError(null);
    if (step === 1 && !name.trim()) {
      setError('Please enter your full name.');
      return;
    }
    if (step === 2 && !college.trim()) {
      setError('Please enter your college or university name.');
      return;
    }
    if (step === 3 && (!program.trim() || !department.trim())) {
      setError('Please enter your degree program and department.');
      return;
    }

    if (step < 7) {
      setStep(step + 1);
    } else {
      handleSubmitOnboarding();
    }
  };

  const handleBack = () => {
    setError(null);
    if (step > 1) setStep(step - 1);
  };

  const handleSubmitOnboarding = async () => {
    try {
      setSubmitting(true);
      setError(null);

      // Auto-add subject if filled in the input boxes but user forgot to click "+ Add"
      const finalSubjects = [...subjectsList];
      if (newSubName.trim() && newSubCode.trim()) {
        finalSubjects.push({
          code: newSubCode.trim().toUpperCase(),
          name: newSubName.trim(),
          credits: parseFloat(newSubCredits) || 3.0,
          instructor: newSubInstructor.trim() || undefined,
          difficulty: newSubDifficulty,
          topics: [],
        });
      }

      const payload = {
        name: name.trim(),
        college: college.trim(),
        program: program.trim(),
        department: department.trim(),
        current_year: currentYear,
        current_semester: currentSemester,
        grading_scale: gradingScale,
        attendance_minimum_pct: attendanceMin,
        target_cgpa: targetCgpa ? parseFloat(targetCgpa) : undefined,
        daily_study_hours: parseFloat(studyHours) || 2.0,
        subjects: finalSubjects,
      };

      const res = await api.post<StudentProfileResponse>('/api/auth/onboarding', payload);
      localStorage.setItem('student_name', res.name || name.trim());
      localStorage.setItem('onboarding_completed', 'true');
      onComplete(res.name || name.trim());
    } catch (err: any) {
      console.error('Onboarding submission error:', err);
      setError(err.message || 'Failed to complete profile setup. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="max-w-xl w-full space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-indigo-600 text-white items-center justify-center shadow-lg shadow-indigo-100">
            <GraduationCap className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Set Up Your Academic Profile</h2>
          <p className="text-xs text-slate-500">
            Step {step} of 7: {steps[step - 1].label}
          </p>
        </div>

        {/* Stepper Progress Bar */}
        <div className="flex items-center justify-between px-2 overflow-x-auto pb-2">
          {steps.map((s, idx) => (
            <React.Fragment key={s.num}>
              <div className="flex flex-col items-center gap-1 shrink-0">
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                    step > s.num
                      ? 'bg-emerald-500 text-white'
                      : step === s.num
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-200'
                      : 'bg-slate-200 text-slate-500'
                  }`}
                >
                  {step > s.num ? <Check className="w-3.5 h-3.5" /> : s.num}
                </div>
                <span className={`text-[10px] font-semibold ${step === s.num ? 'text-indigo-600' : 'text-slate-400'}`}>
                  {s.label}
                </span>
              </div>
              {idx < steps.length - 1 && (
                <div className={`flex-1 h-0.5 mx-1.5 min-w-[8px] ${step > s.num ? 'bg-emerald-400' : 'bg-slate-200'}`} />
              )}
            </React.Fragment>
          ))}
        </div>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200/80 rounded-xl text-xs text-rose-700 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <Card>
          {/* Step 1: Personal Info */}
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-2">What is your name?</h3>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  autoFocus
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Lahari Sharma"
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 outline-none focus:border-indigo-600 focus:bg-white"
                />
              </div>
            </div>
          )}

          {/* Step 2: Institution */}
          {step === 2 && (
            <div className="space-y-4">
              <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-2">Where do you study?</h3>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">College / University Name</label>
                <input
                  type="text"
                  required
                  autoFocus
                  value={college}
                  onChange={(e) => setCollege(e.target.value)}
                  placeholder="e.g. BVRIT Hyderabad / IIT Delhi"
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 outline-none focus:border-indigo-600 focus:bg-white"
                />
              </div>
            </div>
          )}

          {/* Step 3: Academic Information */}
          {step === 3 && (
            <div className="space-y-4">
              <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-2">Academic Program & Year</h3>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Degree / Program</label>
                  <input
                    type="text"
                    required
                    value={program}
                    onChange={(e) => setProgram(e.target.value)}
                    placeholder="e.g. B.Tech, B.S., B.E."
                    className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 outline-none focus:border-indigo-600"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Department / Branch</label>
                  <input
                    type="text"
                    required
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    placeholder="e.g. CSE, AIML, Mechanical"
                    className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 outline-none focus:border-indigo-600"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Current Year</label>
                  <select
                    value={currentYear}
                    onChange={(e) => setCurrentYear(Number(e.target.value))}
                    className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 outline-none focus:border-indigo-600"
                  >
                    {[1, 2, 3, 4, 5].map((y) => (
                      <option key={y} value={y}>Year {y}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Current Semester</label>
                  <select
                    value={currentSemester}
                    onChange={(e) => setCurrentSemester(Number(e.target.value))}
                    className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 outline-none focus:border-indigo-600"
                  >
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((s) => (
                      <option key={s} value={s}>Semester {s}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Academic Policies */}
          {step === 4 && (
            <div className="space-y-4">
              <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-2">Grading System & Policy</h3>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Grading Scale</label>
                <select
                  value={gradingScale}
                  onChange={(e) => setGradingScale(e.target.value)}
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 outline-none focus:border-indigo-600"
                >
                  <option value="10_point">10-Point Scale (O, A+, A, B+, B, C, P, F)</option>
                  <option value="4_point">4.0 Scale (A, A-, B+, B, B-, C+, C, D, F)</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Minimum Attendance Policy Requirement (%)
                </label>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="50"
                    max="90"
                    step="5"
                    value={attendanceMin}
                    onChange={(e) => setAttendanceMin(Number(e.target.value))}
                    className="flex-1 accent-indigo-600"
                  />
                  <span className="text-sm font-bold text-slate-900 w-12 text-right">{attendanceMin}%</span>
                </div>
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Threshold used to calculate safe buffer vs recovery classes needed.
                </span>
              </div>
            </div>
          )}

          {/* Step 5: Academic Goals */}
          {step === 5 && (
            <div className="space-y-4">
              <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-2">Target Academic Goals</h3>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Target CGPA (Optional)</label>
                <input
                  type="number"
                  step="0.05"
                  value={targetCgpa}
                  onChange={(e) => setTargetCgpa(e.target.value)}
                  placeholder="e.g. 9.00 or 8.50"
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 outline-none focus:border-indigo-600"
                />
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Leave blank if not set. The advisor calculates mathematical feasibility across your remaining credits.
                </span>
              </div>
            </div>
          )}

          {/* Step 6: Study Availability */}
          {step === 6 && (
            <div className="space-y-4">
              <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-2">Daily Study Availability</h3>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  How many hours can you realistically study per day?
                </label>
                <select
                  value={studyHours}
                  onChange={(e) => setStudyHours(e.target.value)}
                  className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 outline-none focus:border-indigo-600"
                >
                  <option value="1.0">1.0 Hour / Day (Light)</option>
                  <option value="1.5">1.5 Hours / Day</option>
                  <option value="2.0">2.0 Hours / Day (Recommended)</option>
                  <option value="3.0">3.0 Hours / Day (Focused)</option>
                  <option value="4.0">4.0+ Hours / Day (Intensive)</option>
                </select>
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Used by the daily study planner to prevent schedule overload.
                </span>
              </div>
            </div>
          )}

          {/* Step 7: Enrolled Subjects */}
          {step === 7 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <h3 className="text-base font-bold text-slate-900">Add Enrolled Subjects</h3>
                <span className="text-xs text-indigo-600 font-bold">{subjectsList.length} Added</span>
              </div>

              {/* Already Added Subjects List */}
              {subjectsList.length > 0 && (
                <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                  {subjectsList.map((sub, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-xl border border-slate-100 text-xs">
                      <div>
                        <span className="font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded mr-2">{sub.code}</span>
                        <span className="font-semibold text-slate-800">{sub.name}</span>
                        <span className="text-slate-400 ml-2">({sub.credits} cr)</span>
                      </div>
                      <button
                        onClick={() => handleRemoveSubject(idx)}
                        className="p-1 text-slate-400 hover:text-rose-600 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* New Subject Input Form */}
              <div className="p-3 bg-indigo-50/50 rounded-2xl border border-indigo-100/80 space-y-3">
                <span className="text-xs font-bold text-indigo-900 block">Add a Subject:</span>
                <div className="grid grid-cols-3 gap-2">
                  <div className="col-span-1">
                    <input
                      type="text"
                      placeholder="Code (e.g. CS501)"
                      value={newSubCode}
                      onChange={(e) => setNewSubCode(e.target.value)}
                      className="w-full text-xs bg-white border border-slate-200 rounded-xl px-2.5 py-2 outline-none focus:border-indigo-600"
                    />
                  </div>
                  <div className="col-span-2">
                    <input
                      type="text"
                      placeholder="Subject Name (e.g. Machine Learning)"
                      value={newSubName}
                      onChange={(e) => setNewSubName(e.target.value)}
                      className="w-full text-xs bg-white border border-slate-200 rounded-xl px-2.5 py-2 outline-none focus:border-indigo-600"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-2">
                  <div className="col-span-1">
                    <input
                      type="number"
                      step="0.5"
                      placeholder="Credits"
                      value={newSubCredits}
                      onChange={(e) => setNewSubCredits(e.target.value)}
                      className="w-full text-xs bg-white border border-slate-200 rounded-xl px-2.5 py-2 outline-none focus:border-indigo-600"
                    />
                  </div>
                  <div className="col-span-2">
                    <input
                      type="text"
                      placeholder="Faculty (Optional)"
                      value={newSubInstructor}
                      onChange={(e) => setNewSubInstructor(e.target.value)}
                      className="w-full text-xs bg-white border border-slate-200 rounded-xl px-2.5 py-2 outline-none focus:border-indigo-600"
                    />
                  </div>
                  <div className="col-span-1">
                    <select
                      value={newSubDifficulty}
                      onChange={(e) => setNewSubDifficulty(e.target.value)}
                      className="w-full text-xs bg-white border border-slate-200 rounded-xl px-2 py-2 outline-none focus:border-indigo-600 text-slate-700"
                    >
                      <option value="easy">Easy</option>
                      <option value="moderate">Moderate</option>
                      <option value="hard">Hard</option>
                    </select>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleAddSubject}
                  className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Subject to List</span>
                </button>
              </div>
              <p className="text-[11px] text-slate-400 italic">
                You can add more subjects or update them anytime from the Subjects tab.
              </p>
            </div>
          )}

          {/* Stepper Buttons */}
          <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-100">
            {step > 1 ? (
              <Button variant="outline" size="sm" onClick={handleBack} leftIcon={<ChevronLeft className="w-4 h-4" />}>
                Back
              </Button>
            ) : <div />}

            <Button
              size="sm"
              isLoading={submitting}
              onClick={handleNext}
              rightIcon={step === 7 ? <Sparkles className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            >
              {step === 7 ? 'Complete Setup & Launch' : 'Continue'}
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};
