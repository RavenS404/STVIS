import { useDeferredValue, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { StatusBadge } from "../components/StatusBadge";
import { formatCaseNumber, formatDateTimeAr, formatViolationSummary, summarizeReviewFlags } from "../app/presentation";
import { applyCaseDecision, fetchCases } from "../services/cases";

export function ReviewQueuePage() {
  const [search, setSearch] = useState("");
  const debouncedSearch = useDeferredValue(search);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["cases", "review", debouncedSearch],
    queryFn: () => fetchCases({ only_supervisor_queue: true, search: debouncedSearch || undefined }),
    staleTime: 8_000,
  });

  const reviewIds = useMemo(() => data?.items.map((item) => item.id) ?? [], [data?.items]);
  const reviewNavState = useMemo(() => ({ from: "review", ids: reviewIds }), [reviewIds]);

  const decisionMutation = useMutation({
    mutationFn: ({ caseId, decision }: { caseId: string; decision: string }) => applyCaseDecision(caseId, { decision }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  if (isLoading) return <LoadingBlock />;
  if (!data?.items.length) return <EmptyState title="لا توجد حالات تحتاج مراجعة حاليًا" />;

  return (
    <div className="page-grid">
      <section className="surface filter-bar">
        <input
          placeholder="بحث برقم الحالة أو اللوحة"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
      </section>

      <section className="surface">
        <div className="panel-header">
          <div>
            <h2>طابور المراجعة</h2>
            <p>تظهر هنا فقط الحالات التي تحتاج قرارًا من المشرف.</p>
          </div>
          <span className="tag-chip">{data.meta.total} حالة</span>
        </div>

        <div className="table-like">
          {data.items.map((item) => {
            const reasons = summarizeReviewFlags(item.review_flags, item.violations);
            return (
              <article key={item.id} className="queue-card queue-card--review">
                <div className="queue-card__header">
                  <div>
                    <Link to={`/cases/${item.id}`} state={reviewNavState} className="table-link">{formatCaseNumber(item.case_number)}</Link>
                    <small>{formatDateTimeAr(item.created_at)}</small>
                  </div>
                  <StatusBadge state={item.review_state} />
                </div>

                <div className="queue-card__body">
                  <div className="queue-highlight">
                    <span className="eyebrow">قراءة اللوحة</span>
                    <strong className="plate-text-inline">{item.plate_text_ar ?? "بدون لوحة مؤكدة"}</strong>
                  </div>
                  <div className="queue-highlight">
                    <span className="eyebrow">المخالفة</span>
                    <strong>{formatViolationSummary(item)}</strong>
                  </div>
                  <div className="queue-highlight">
                    <span className="eyebrow">الثقة</span>
                    <ConfidenceBadge value={item.plate_confidence ?? item.vehicle_confidence} />
                  </div>
                </div>

                {reasons.length ? (
                  <div className="queue-card__reasons">
                    {reasons.map((reason) => (
                      <span key={`${item.id}-${reason}`} className="tag-chip">
                        {reason}
                      </span>
                    ))}
                  </div>
                ) : null}

                <div className="queue-card__actions">
                  <button
                    className="primary-button"
                    type="button"
                    disabled={decisionMutation.isPending}
                    onClick={() => decisionMutation.mutate({ caseId: item.id, decision: "issue" })}
                  >
                    اعتماد
                  </button>
                  <button
                    className="ghost-button danger"
                    type="button"
                    disabled={decisionMutation.isPending}
                    onClick={() => decisionMutation.mutate({ caseId: item.id, decision: "reject" })}
                  >
                    رفض
                  </button>
                  <Link to={`/cases/${item.id}`} state={reviewNavState} className="ghost-button queue-card__edit">
                    تعديل
                  </Link>
                </div>
              </article>
            );
          })}
        </div>
      </section>
    </div>
  );
}
