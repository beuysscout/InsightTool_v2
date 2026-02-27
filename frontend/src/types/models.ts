// --- Project ---
export interface Project {
  project_id: string;
  name: string;
  created_at: string;
  status: string;
  session_count: number;
  participant_count: number;
}

// --- Guide ---
export interface AiFlag {
  flag_type: string;
  message: string;
  suggestion: string | null;
  status: string;
}

export interface Question {
  question_id: string;
  question_text: string;
  mapped_goal: string | null;
  required: boolean;
  probes: string[];
  ai_flags: AiFlag[];
}

export interface GuideSection {
  section_id: string;
  section_name: string;
  time_bracket: string;
  questions: Question[];
}

export interface ResearchGuide {
  project_id: string;
  project_name: string;
  objective: string;
  research_goals: string[];
  sections: GuideSection[];
  review_flags: AiFlag[];
  coverage_gaps: string[];
  estimated_duration_minutes: number | null;
  version: number;
  locked: boolean;
}

export interface GuideReviewResult {
  parsed_guide: ResearchGuide;
  flags: AiFlag[];
  suggested_probes: { question_id: string; probe: string }[];
  coverage_gaps: string[];
  estimated_duration_minutes: number | null;
}

// --- Session ---
export interface Turn {
  turn_index: number;
  speaker: string;
  text: string;
  timestamp: string;
  is_interviewer: boolean;
}

export interface PiiDetection {
  original_text: string;
  replacement_token: string;
  pii_type: string;
  confidence: number;
  start_offset: number;
  end_offset: number;
  turn_index: number;
  status: string;
}

export interface MappedTurn {
  turn_index: number;
  speaker: string;
  text: string;
  timestamp: string;
  mapping_confidence: number;
}

export interface SectionMapping {
  section_id: string;
  section_name: string;
  time_bracket: string;
  coverage_status: string;
  mapped_turns: MappedTurn[];
  coverage_notes: string;
}

export interface OrganisedTranscript {
  session_id: string;
  participant_id: string;
  section_mappings: SectionMapping[];
  off_script_turns: Turn[];
}

export interface Session {
  session_id: string;
  project_id: string;
  participant_id: string;
  transcript: Turn[];
  anonymisation_log: {
    auto_redacted: number;
    researcher_reviewed: number;
    exclusions: number;
    detections: PiiDetection[];
  };
  organised: OrganisedTranscript | null;
  upload_timestamp: string;
  status: string;
}

// --- Themes ---
export interface ThemeEvidence {
  quote: string;
  participant_id: string;
  timestamp: string;
  turn_index: number;
  guide_section: string;
  guide_question_id: string | null;
}

export interface Theme {
  theme_id: string;
  theme_name: string;
  theme_description: string;
  evidence: ThemeEvidence[];
  instance_count: number;
  status: string;
  researcher_notes: string | null;
}

export interface SessionThemes {
  session_id: string;
  participant_id: string;
  themes: Theme[];
}
