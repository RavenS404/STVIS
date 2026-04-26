import { useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { AuditTimeline } from "../components/AuditTimeline";
import { EmptyState } from "../components/EmptyState";
import { EvidencePanel } from "../components/EvidencePanel";
import { LoadingBlock } from "../components/LoadingBlock";
import { StatusBadge } from "../components/StatusBadge";
import {
  formatCaseNumber,
  formatDateTimeAr,
  getHighlightedViolation,
} from "../app/presentation";
import { fetchAuditLogs } from "../services/audit";
import { applyCaseDecision, fetchCaseDetail, fetchCases } from "../services/cases";

export function CaseDetailsPage() {
  const { caseId = "" } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const [notes, setNotes] = useState("");
  const [plateOverrideAr, setPlateOverrideAr] = useState("");

  // History navigation context — HistoryPage passes {from:'history', ids:[...]} in route state
  const routeState = (location.state ?? {}) as { from?: string; ids?: string[] };
  const historyIds: string[] = routeState.from === "history" ? (routeState.ids ?? []) : [];

  const caseQuery = useQuery({ queryKey: ["case", caseId], queryFn: () => fetchCaseDetail(caseId), enabled: Boolean(caseId) });
  const auditQuery = useQuery({
    queryKey: ["audit", "case", caseId],
    queryFn: () => fetchAuditLogs(1, { entity_type: "vehicle_case", entity_id: caseId }),
  });

  // Review queue navigation (only loaded when not coming from history)
  const queueQuery = useQuery({
    queryKey: ["cases", "review", ""],
    queryFn: () => fetchCases({ only_supervisor_queue: true }),
    staleTime: 30_000,
    enabled: historyIds.length === 0,
  });

  // Determine which list to navigate within
  const navIds = historyIds.length > 0 ? historyIds : (queueQuery.data?.items.map((item) => item.id) ?? []);
  const currentIdx = navIds.indexOf(caseId);
  const prevId = currentIdx > 0 ? navIds[currentIdx - 1] : null;
  const nextId = currentIdx >= 0 && currentIdx < navIds.length - 1 ? navIds[currentIdx + 1] : null;
  const navState = historyIds.length > 0 ? routeState : undefined;

  const mutation = useMutation({
    mutationFn: (decision: string) =>
      applyCaseDecision(caseId, { decision, notes, plate_override_ar: plateOverrideAr || undefined }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["case", caseId] });
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["reports"] });
      if (nextId) {
        navigate(`/cases/${nextId}`, { replace: true });
      }
    },
  });

  if (caseQuery.isLoading) return <LoadingBlock />;
  if (caseQuery.isError) {
    return <EmptyState title="تعذر تحميل الحالة" subtitle="حاولي تحديث الصفحة أو الرجوع للقائمة ثم فتح الحالة مرة أخرى." />;
  }
  if (!caseQuery.data) return <EmptyState title="الحالة غير موجودة" />;

  const detail = caseQuery.data;
  const assets = Array.isArray(detail.assets) ? detail.assets : [];
  const violations = Array.isArray(detail.violations) ? detail.violations : [];
  const annotatedAsset = assets.find((item) => item.kind === "annotated_event");
  const plateCropAsset = assets.find((item) => item.kind === "plate_crop");
  const originalAsset = assets.find((item) => item.kind === "original");
  const vehicleCropAsset = assets.find((item) => item.kind === "vehicle_crop");

  const primaryImage = annotatedAsset ?? originalAsset;

  return (
    <div className="page-grid">
      {/* ── Compact 2-column workspace ── */}
      <div className="case-split">
        {/* Column A: Review card */}
        <div className="case-split__info">
          <section className="surface">
            {/* Header row: case number + nav */}
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

            {/* Violation */}
            <div className="panel-header" style={{ marginTop: "0.75rem" }}>
              <div>
                <span className="eyebrow">المخالفة الرئيسية</span>
                <h3 style={{ margin: 0 }}>
                  {detail.review_state === "no_violation"
                    ? "لا توجد مخالفة"
                    : getHighlightedViolation({ highlighted_violation_code: detail.highlighted_violation_code, violations })}
                </h3>
              </div>
              <StatusBadge state={detail.review_state} />
            </div>

            {violations.length > 1 && (
              <div className="violation-chips">
                {violations.map((v) => (
                  <span key={v.id} className={`tag-chip${v.is_highlighted ? " tag-chip--primary" : ""}`}>{v.display_name_ar}</span>
                ))}
              </div>
            )}

            {/* Plate reading — Egyptian style. Slots are in LTR visual order (sorted by x_center in backend). */}
            {(() => {
              const plateRead = detail.plate_read;
              const isUnclear = !plateRead ||
                (plateRead.display_summary_ar?.includes("غير واضحة") || plateRead.display_summary_ar?.includes("غير مؤكدة") || plateRead.display_summary_ar?.includes("مكتملة"));
              // letters_ar and digits_ar are already in left-to-right visual order from backend
              const letterSlots = (plateRead?.letters_ar || "").split("").filter(c => c.trim());
              const digitSlots = (plateRead?.digits_ar || "").split("").filter(c => c.trim());
              return (
                <div className="eg-plate" style={{ marginTop: "0.75rem" }}>
                  <div className="eg-plate__header">مصر</div>
                  <div className="eg-plate__body">
                    <div className="eg-plate__section">
                      <span className="eg-plate__label">الحروف</span>
                      <div className="eg-plate__slots">
                        {letterSlots.length ? letterSlots.map((ch, i) => (
                          <span key={i} className="eg-plate__slot">{ch}</span>
                        )) : <span className="eg-plate__slot eg-plate__slot--empty">—</span>}
                      </div>
                    </div>
                    <div className="eg-plate__divider" />
                    <div className="eg-plate__section">
                      <span className="eg-plate__label">الأرقام</span>
                      <div className="eg-plate__slots">
                        {digitSlots.length ? digitSlots.map((ch, i) => (
                          <span key={i} className="eg-plate__slot">{ch}</span>
                        )) : <span className="eg-plate__slot eg-plate__slot--empty">—</span>}
                      </div>
                    </div>
                  </div>
                  {isUnclear && (
                    <div className="eg-plate__warning">
                      ⚠ {plateRead?.display_summary_ar ?? "لوحة غير متاحة"} — يُرجى التحقق يدوياً
                    </div>
                  )}
                </div>
              );
            })()}

            {/* Correction + notes + actions */}
            <div style={{ display: "grid", gap: "0.6rem", marginTop: "0.75rem" }}>
              <label>
                تصحيح اللوحة (اختياري)
                <input value={plateOverrideAr} onChange={(e) => setPlateOverrideAr(e.target.value)} placeholder="مثال: ط س هـ ١٢٣٤" />
              </label>
              <label>
                ملاحظات المراجعة
                <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} placeholder="سبب الرفض أو الإصدار..." />
              </label>

              {detail.review_state === "no_violation" ? (
                <div className="form-error" style={{ background: "var(--success-soft)", color: "var(--success)" }}>
                  هذه الحالة سليمة ولا تتطلب اتخاذ قرار بإصدار مخالفة.
                </div>
              ) : (
                <div className="button-row">
                  <button className="primary-button" onClick={() => mutation.mutate("issue")} type="button" disabled={mutation.isPending}>إصدار</button>
                  <button className="ghost-button danger" onClick={() => mutation.mutate("reject")} type="button" disabled={mutation.isPending}>رفض</button>
                  <button className="ghost-button" onClick={() => mutation.mutate("send_to_supervisor")} type="button" disabled={mutation.isPending}>تصعيد لمشرف</button>
                </div>
              )}
              {currentIdx === -1 && detail.review_state !== "no_violation" && (
                <p className="eyebrow" style={{ textAlign: "center" }}>لا توجد حالات تالية في الطابور.</p>
              )}
            </div>
          </section>
        </div>

        {/* Column B: Evidence card */}
        <div className="case-split__evidence">
          <section className="surface">
            <div className="panel-header"><h3>الصورة المعلّمة</h3></div>
            <EvidencePanel title="" assetUrl={primaryImage?.url} className="cd-main-img" />
          </section>

          <section className="surface" style={{ marginTop: "0.5rem" }}>
            <div className="panel-header"><h3>صورة اللوحة</h3></div>
            <EvidencePanel title="" assetUrl={plateCropAsset?.url} className="cd-plate-img" />
          </section>
        </div>
      </div>


      <AuditTimeline items={auditQuery.data?.items ?? []} />
    </div>
  );
}
