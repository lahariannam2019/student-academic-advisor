export interface StudentProfile {
  id: string;
  user_id: string;
  email?: string;
  name: string;
  college: string;
  program: string;
  department: string;
  current_year: number;
  current_semester: number;
  grading_scale: string; // e.g. "10_point" | "4_point"
  attendance_minimum_pct: number; // e.g. 75
  target_cgpa?: number;
  daily_study_hours?: number;
  onboarding_completed?: boolean;
  created_at?: string;
  updated_at?: string;
}

export type StudentProfileResponse = StudentProfile;

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  profile_id: string;
  student_name: string | null;
  needs_onboarding: boolean;
  is_verified?: boolean;
  verification_sent?: boolean;
  message?: string | null;
}

export interface SubjectOnboardingInput {
  code: string;
  name: string;
  credits: number;
  instructor?: string;
  difficulty?: string;
  topics?: string[];
}

export interface Semester {
  id: string;
  student_id: string;
  semester_number: number;
  academic_year: string;
  is_current: boolean;
  sgpa?: number;
  total_credits?: number;
}

export interface SubjectDetailResponse {
  id: string;
  semester_id: string;
  code: string;
  name: string;
  credits: number;
  instructor?: string;
  difficulty?: 'easy' | 'moderate' | 'challenging';
  topics: string[];
  total_classes: number;
  attended_classes: number;
  attendance_pct: number;
  attendance_status: 'safe' | 'warning' | 'critical';
  classes_needed: number;
  classes_can_miss: number;
  current_marks_pct?: number | null;
  performance_trend?: string;
  assessments_count: number;
  upcoming_exam_date?: string | null;
  pending_assignments_count: number;
  priority_score: number;
  priority_reasons: string[];
  attendance_records: any[];
  marks: any[];
  assignments: any[];
  exams: any[];
}

export interface StudyBlockResponse {
  id: string;
  subject_id?: string | null;
  subject_name: string;
  task_description: string;
  duration_minutes: number;
  study_type: string;
  priority_score: number;
  reason: string;
  status: string;
}

export interface PriorityItem {
  subject_id: string;
  subject_name: string;
  subject_code: string;
  priority_score: number;
  level: string;
  reasons: string[];
  metrics: {
    attendance_pct: number;
    attendance_status: string;
    classes_needed?: number;
    classes_can_miss?: number;
    current_marks_pct?: number | null;
    days_to_exam?: number | null;
    pending_assignments_count?: number;
  };
}

export interface DashboardResponse {
  student_name: string;
  college: string;
  program: string;
  current_year: number;
  current_semester: number;
  cgpa: number;
  target_cgpa?: number;
  overall_attendance_pct: number;
  attendance_minimum_pct: number;
  critical_attendance_subjects_count: number;
  next_exam?: {
    exam_name: string;
    exam_type: string;
    subject_name: string;
    days_until?: number;
  } | null;
  pending_assignments_count: number;
  overdue_assignments_count: number;
  top_priority?: PriorityItem | null;
  study_blocks: StudyBlockResponse[];
  conflict_message?: string | null;
  ai_daily_insight?: {
    headline: string;
    explanation: string;
    actionable_tip: string;
  } | null;
  profile_completeness?: {
    percentage: number;
    checks: Array<{ label: string; done: boolean }>;
    message: string | null;
  } | null;
}

export interface AdvisorChatResponse {
  conversation_id: string;
  message: string;
  suggested_followups: string[];
  context_used: Record<string, any>;
  ai_provider: string;
  action_executed?: {
    action_type: string;
    success: boolean;
    confirmation?: string;
    field?: string;
    old_value?: any;
    new_value?: any;
  } | null;
}
