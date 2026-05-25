export type UserRole = "admin" | "supervisor";
export type CaseState = "direct_issue_ready" | "supervisor_review_required" | "issued" | "rejected" | "no_violation";

export interface CurrentUser {
  id: string;
  username: string;
  full_name: string;
  role: UserRole;
}

export interface DashboardSummary {
  cases_by_state: Record<string, number>;
  violations_by_code: Record<string, number>;
  queue_depth: number;
  escalations: number;
  issued_today: number;
  recent_cases: Array<{ id: string; case_number: string; state: string; created_at: string }>;
}

export interface CaseViolation {
  id: string;
  code: string;
  display_name_ar: string;
  display_name_en: string;
  confidence: number;
  actionable: boolean;
  review_required: boolean;
  is_highlighted: boolean;
  detection_bbox: Record<string, unknown>;
}

export interface CasePlateRead {
  id: string;
  raw_text_visual: string;
  arabic_text_display: string;
  display_summary_ar: string;
  normalized_search_value: string;
  letters_ar: string;
  digits_ar: string;
  raw_letters: string;
  raw_digits: string;
  plate_confidence: number;
  token_count: number;
  row_count: number;
  token_details: Array<Record<string, unknown>>;
  plate_bbox: Record<string, unknown>;
  model_version: string;
  association_score?: number | null;
  is_confident: boolean;
}

export interface CaseAsset {
  id: string;
  kind: string;
  mime_type: string;
  url: string;
}

export interface CaseListItem {
  id: string;
  case_number: string;
  review_state: CaseState;
  association_status: string;
  highlighted_violation_code?: string | null;
  review_flags: string[];
  issue_ready: boolean;
  requires_supervisor: boolean;
  vehicle_label: string;
  vehicle_confidence: number;
  event_id: string;
  plate_text_ar?: string | null;
  plate_letters_ar?: string | null;
  plate_digits_ar?: string | null;
  plate_confidence?: number | null;
  violation_summary_ar?: string | null;
  created_at: string;
  violations: CaseViolation[];
}

export interface CaseDetail extends CaseListItem {
  vehicle_bbox: Record<string, unknown>;
  supervisor_notes?: string | null;
  manual_override_payload: Record<string, unknown>;
  plate_read?: CasePlateRead | null;
  assets: CaseAsset[];
  model_versions: Record<string, string | null>;
  debug_payload: Record<string, unknown>;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  meta: {
    page: number;
    page_size: number;
    total: number;
  };
}

export interface ReportSummary {
  total_cases: number;
  issued_cases: number;
  rejected_cases: number;
  supervisor_cases: number;
  average_plate_confidence?: number | null;
  violation_breakdown: Record<string, number>;
}

export interface HealthComponent {
  status: string;
  details: Record<string, unknown>;
}

export interface SystemHealth {
  generated_at: string;
  components: Record<string, HealthComponent>;
}

export interface AuditLog {
  id: string;
  action_type: string;
  entity_type: string;
  entity_id: string;
  summary_ar: string;
  summary_en: string;
  actor_role?: string | null;
  occurred_at: string;
  details_json: Record<string, unknown>;
}

export interface SettingEntry {
  key: string;
  value_json: unknown;
  description?: string | null;
  is_secret?: boolean;
}

export interface UserEntry extends CurrentUser {
  is_active: boolean;
  last_login_at?: string | null;
}

export interface DeviceEntry {
  id: string;
  code: string;
  name: string;
  location_label: string;
  is_active: boolean;
  last_seen_at?: string | null;
  notes?: string | null;
  metadata_json: Record<string, unknown>;
}

export interface ModelProfile {
  id: string;
  model_key: string;
  display_name: string;
  artifact_path: string;
  version: string;
  class_map: Record<string, string>;
  metadata_json: Record<string, unknown>;
  is_active: boolean;
}
