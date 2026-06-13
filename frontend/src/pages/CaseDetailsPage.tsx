import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { AuditTimeline } from "../components/AuditTimeline";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { EmptyState } from "../components/EmptyState";
import { EvidencePanel } from "../components/EvidencePanel";
import { LoadingBlock } from "../components/LoadingBlock";
import { StatusBadge } from "../components/StatusBadge";
import {
  formatCaseNumber,
  formatDateTimeAr,
  getHighlightedViolation,
} from "../app/presentation";
import { formatPlateInput, parsePlateInput, splitPlateChars } from "../app/plate";
import type { CaseDetail } from "../app/types";
import { fetchAuditLogs } from "../services/audit";
import {
  applyCaseDecision,
  createCaseViolation,
  deleteCaseViolation,
  fetchCaseDetail,
  fetchCases,
  updateCase,
  updateCaseViolation,
} from "../services/cases";

const VIOLATION_TYPE_OPTIONS = [
  { code: "unfastened_seat_belt", labelAr: "عدم ربط حزام الأمان", labelEn: "Unfastened seat belt" },
  { code: "using_mobile", labelAr: "استخدام الهاتف أثناء القيادة", labelEn: "Using mobile phone" },
  { code: "wrong_way", labelAr: "السير عكس الاتجاه", labelEn: "Wrong way" },
];

function resolveEditableStatus(state: CaseDetail["review_state"]) {
  return state === "no_violation" || state === "rejected" ? "invalid" : "valid";
}

export function CaseDetailsPage() {
  const { caseId = "" } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const [notes, setNotes] = useState("");
  const [plateOverrideAr, setPlateOverrideAr] = useState("");
  const [selectedViolationId, setSelectedViolationId] = useState("");
  const [selectedViolationCodes, setSelectedViolationCodes] = useState<string[]>([]);
  const [caseStatus, setCaseStatus] = useState<"valid" | "invalid">("valid");

  const routeState = (location.state ?? {}) as { from?: string; ids?: string[] };
  const routeIds = Array.isArray(routeState.ids) ? routeState.ids : [];

  const caseQuery = useQuery({ queryKey: ["case", caseId], queryFn: () => fetchCaseDetail(caseId), enabled: Boolean(caseId) });
  const auditQuery = useQuery({
    queryKey: ["audit", "case", caseId],
    queryFn: () => fetchAuditLogs(1, { entity_type: "vehicle_case", entity_id: caseId }),
  });

  const queueQuery = useQuery({
    queryKey: ["cases", "review", ""],
    queryFn: () => fetchCases({ only_supervisor_queue: true }),
    staleTime: 30_000,
    enabled: routeIds.length === 0,
  });

  const detail = caseQuery.data;
  const violations = useMemo(() => (Array.isArray(detail?.violations) ? detail.violations : []), [detail?.violations]);
  const selectedViolation = violations.find((item) => item.id === selectedViolationId) ?? violations[0];
  const plateParts = parsePlateInput(plateOverrideAr || detail?.plate_read?.display_summary_ar);

  useEffect(() => {
    if (!detail) return;
    const firstViolation = detail.violations[0];
    const manualPlate = detail.manual_override_payload?.plate_override_ar;
    setNotes(detail.supervisor_notes ?? "");
    setPlateOverrideAr(formatPlateInput(typeof manualPlate === "string" ? manualPlate : detail.plate_read?.display_summary_ar ?? ""));
    setCaseStatus(resolveEditableStatus(detail.review_state));
    setSelectedViolationId(firstViolation?.id ?? "");
    setSelectedViolationCodes(
      Array.from(new Set(detail.violations.filter((item) => item.actionable).map((item) => item.code))),
    );
  }, [detail]);

  const navIds = routeIds.length > 0 ? routeIds : (queueQuery.data?.items.map((item) => item.id) ?? []);
  const currentIdx = navIds.indexOf(caseId);
  const prevId = currentIdx > 0 ? navIds[currentIdx - 1] : null;
  const nextId = currentIdx >= 0 && currentIdx < navIds.length - 1 ? navIds[currentIdx + 1] : null;
  const navState = routeIds.length > 0 ? routeState : undefined;

  const decisionMutation = useMutation({
    mutationFn: (decision: string) =>
      applyCaseDecision(caseId, { decision, notes, plate_override_ar: plateParts.summary || undefined }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["case", caseId] });
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["reports"] });
      if (nextId) navigate(`/cases/${nextId}`, { replace: true, state: navState });
    },
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      const activeCodes = caseStatus === "valid" ? selectedViolationCodes : [];
      const highlightedCode = activeCodes[0] ?? null;
      await Promise.all(
        violations.map((violation) =>
          updateCaseViolation(caseId, violation.id, {
            actionable: activeCodes.includes(violation.code),
            is_highlighted: violation.code === highlightedCode,
          }),
        ),
      );

      const existingCodes = new Set(violations.map((violation) => violation.code));
      await Promise.all(
        activeCodes
          .filter((code) => !existingCodes.has(code))
          .map((code) => {
            const selectedType = VIOLATION_TYPE_OPTIONS.find((item) => item.code === code);
            if (!selectedType) return Promise.resolve();
            return createCaseViolation(caseId, {
              code,
              display_name_ar: selectedType.labelAr,
              display_name_en: selectedType.labelEn,
              confidence: 1,
              actionable: true,
              is_highlighted: code === highlightedCode,
            });
          }),
      );

      await updateCase(caseId, {
        plate_override_ar: plateParts.summary || undefined,
        status: activeCodes.length ? "ready" : "invalid",
        notes: notes || undefined,
      });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["case", caseId] });
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["reports"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (violationId: string) => deleteCaseViolation(caseId, violationId),
    onSuccess: (_data, violationId) => {
      queryClient.setQueryData<CaseDetail>(["case", caseId], (current) =>
        current
          ? {
              ...current,
              violations: current.violations.filter((item) => item.id !== violationId),
              highlighted_violation_code:
                current.violations.find((item) => item.id === violationId)?.code === current.highlighted_violation_code
                  ? null
                  : current.highlighted_violation_code,
            }
          : current,
      );
      setSelectedViolationId("");
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  if (caseQuery.isLoading) return <LoadingBlock />;
  if (caseQuery.isError) {
    return <EmptyState title="تعذر تحميل الحالة" subtitle="حاولي تحديث الصفحة أو الرجوع للقائمة ثم فتح الحالة مرة أخرى." />;
  }
  if (!detail) return <EmptyState title="الحالة غير موجودة" />;

  const assets = Array.isArray(detail.assets) ? detail.assets : [];
  const originalAsset = assets.find((item) => item.kind === "original");
  const annotatedAsset = assets.find((item) => item.kind === "annotated_case") ?? assets.find((item) => item.kind === "annotated_event");
  const violationsAnnotatedAsset = assets.find((item) => item.kind === "violations_annotated");
  const driverZoomAsset = assets.find((item) => item.kind === "driver_zoom");
  const plateCropAsset = assets.find((item) => item.kind === "plate_crop");

  return (
    <div className="page-grid">
      <div className="case-split">
        <div className="case-split__info">
          <section className="surface">
            <div className="case-nav-bar">
              <div>
                <span className="eyebrow">{formatDateTimeAr(detail.created_at)}</span>
                <h2 style={{ margin: 0, fontSize: "1.15rem" }}>{formatCaseNumber(detail.case_number)}</h2>
              </div>
              <div className="case-nav-actions">
                <button className="ghost-button case-nav-btn" disabled={!prevId} onClick={() => prevId && navigate(`/cases/${prevId}`, { state: navState })}>السابق</button>
                <button className="ghost-button case-nav-btn" disabled={!nextId} onClick={() => nextId && navigate(`/cases/${nextId}`, { state: navState })}>التالي</button>
              </div>
            </div>

            <div className="panel-header case-detail-heading">
              <div>
                <span className="eyebrow">المخالفة الرئيسية</span>
                <h3>
                  {detail.review_state === "no_violation"
                    ? "لا توجد مخالفة"
                    : getHighlightedViolation({ highlighted_violation_code: detail.highlighted_violation_code, violations })}
                </h3>
              </div>
              <StatusBadge state={detail.review_state} />
            </div>

            <div className="plate-table-card">
              <div className="plate-table-card__header">
                <span className="eyebrow">قراءة اللوحة</span>
              </div>
              <table className="plate-preview-table">
                <thead>
                  <tr>
                    <th>الحروف</th>
                    <th>الأرقام</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>
                      <div className="plate-token-row">
                        {splitPlateChars(plateParts.letters).map((char, index) => (
                          <span key={`${char}-${index}`}>{char}</span>
                        ))}
                        {!plateParts.letters ? <span>—</span> : null}
                      </div>
                    </td>
                    <td>
                      <div className="plate-token-row">
                        {splitPlateChars(plateParts.digits).map((char, index) => (
                          <span key={`${char}-${index}`}>{char}</span>
                        ))}
                        {!plateParts.digits ? <span>—</span> : null}
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="edit-grid">
              <label>
                رقم اللوحة
                <input
                  className="plate-edit-input"
                  dir="rtl"
                  inputMode="text"
                  value={plateOverrideAr}
                  onChange={(event) => setPlateOverrideAr(formatPlateInput(event.target.value))}
                  placeholder="مثال: ط س هـ ١ ٢ ٣ ٤"
                />
              </label>
              <label>
                حالة المخالفة
                <select value={caseStatus} onChange={(event) => setCaseStatus(event.target.value as "valid" | "invalid")}>
                  <option value="valid">صالحة</option>
                  <option value="invalid">غير صالحة</option>
                </select>
              </label>
              <label>
                نوع المخالفة
                <div className="checkbox-list violation-checkbox-list">
                  {VIOLATION_TYPE_OPTIONS.map((option) => (
                    <label key={option.code} className="checkbox-row">
                      <input
                        type="checkbox"
                        checked={selectedViolationCodes.includes(option.code)}
                        onChange={(event) => {
                          if (event.target.checked) setCaseStatus("valid");
                          setSelectedViolationCodes((current) =>
                            event.target.checked ? Array.from(new Set([...current, option.code])) : current.filter((code) => code !== option.code),
                          );
                        }}
                      />
                      <span>{option.labelAr}</span>
                    </label>
                  ))}
                </div>
              </label>
              <label>
                ملاحظات المراجعة
                <textarea value={notes} onChange={(event) => setNotes(event.target.value)} rows={2} placeholder="سبب التعديل أو الرفض..." />
              </label>
            </div>

            {selectedViolation ? (
              <div className="selected-violation-summary">
                <div>
                  <span className="eyebrow">الثقة</span>
                  <strong>{selectedViolation.display_name_ar}</strong>
                  <ConfidenceBadge value={selectedViolation.confidence} />
                </div>
                <div>
                  <span className="eyebrow">الكود</span>
                  <strong>{selectedViolation.code}</strong>
                </div>
              </div>
            ) : null}

            <div className="violation-chips">
              {violations.map((violation) => (
                <button
                  key={violation.id}
                  className={`tag-chip violation-chip${violation.id === selectedViolation?.id ? " tag-chip--primary" : ""}`}
                  type="button"
                  onClick={() => setSelectedViolationId(violation.id)}
                >
                  <span>{violation.display_name_ar}</span>
                  <ConfidenceBadge value={violation.confidence} />
                </button>
              ))}
              {!violations.length ? <span className="tag-chip">لا توجد مخالفات مسجلة</span> : null}
            </div>

            <div className="button-row case-action-row">
              <button className="primary-button" onClick={() => saveMutation.mutate()} type="button" disabled={saveMutation.isPending}>
                حفظ التغييرات
              </button>
              <button
                className="ghost-button danger"
                onClick={() => selectedViolation && window.confirm("هل تريد حذف هذه المخالفة نهائيًا؟") && deleteMutation.mutate(selectedViolation.id)}
                type="button"
                disabled={!selectedViolation || deleteMutation.isPending}
              >
                حذف
              </button>
            </div>

            {caseStatus === "valid" && selectedViolationCodes.length > 0 ? (
              <div className="button-row case-action-row">
                <button className="primary-button" onClick={() => decisionMutation.mutate("issue")} type="button" disabled={decisionMutation.isPending}>إصدار</button>
                <button className="ghost-button danger" onClick={() => decisionMutation.mutate("reject")} type="button" disabled={decisionMutation.isPending}>رفض</button>
                <button className="ghost-button" onClick={() => decisionMutation.mutate("send_to_supervisor")} type="button" disabled={decisionMutation.isPending}>تصعيد لمشرف</button>
              </div>
            ) : null}
          </section>
        </div>

        <div className="case-split__evidence">
          <section className="surface">
            <div className="panel-header"><h3>الصور</h3></div>
            <div className="evidence-grid evidence-grid--case-detail">
              <EvidencePanel title="الصورة الأصلية" assetUrl={originalAsset?.url} className="cd-evidence-img" />
              <EvidencePanel title="الصورة المعلّمة" assetUrl={annotatedAsset?.url} className="cd-evidence-img" />
              <EvidencePanel title="المخالفات فقط" assetUrl={violationsAnnotatedAsset?.url} className="cd-evidence-img" />
              <EvidencePanel title="زوم على السائق" assetUrl={driverZoomAsset?.url} className="cd-evidence-img" />
              <EvidencePanel title="صورة اللوحة" assetUrl={plateCropAsset?.url} className="cd-evidence-img cd-plate-img" />
            </div>
          </section>
        </div>
      </div>

      <AuditTimeline items={auditQuery.data?.items ?? []} />
    </div>
  );
}
