import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { StatusBadge } from "../components/StatusBadge";
import { formatCaseNumber, formatDateTimeAr, formatViolationSummary, summarizeReviewFlags } from "../app/presentation";
import { applyCaseDecision, fetchCases } from "../services/cases";
import { useDebouncedValue } from "../hooks/useDebouncedValue";

const PAGE_SIZE = 20;

export function ReviewQueuePage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const debouncedSearch = useDebouncedValue(search.trim(), 300);
  const queryClient = useQueryClient();

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["cases", "review", debouncedSearch, page],
    queryFn: () => fetchCases({ only_supervisor_queue: true, page, page_size: PAGE_SIZE, search: debouncedSearch || undefined }),
    staleTime: 8_000,
    placeholderData: keepPreviousData,
  });

  const reviewIds = useMemo(() => data?.items.map((item) => item.id) ?? [], [data?.items]);
  const reviewNavState = useMemo(() => ({ from: "review", ids: reviewIds }), [reviewIds]);
  const totalPages = Math.max(1, Math.ceil((data?.meta.total ?? 0) / PAGE_SIZE));
  const pageNumbers = useMemo(() => {
    const start = Math.max(1, page - 2);
    const end = Math.min(totalPages, page + 2);
    return Array.from({ length: end - start + 1 }, (_, index) => start + index);
  }, [page, totalPages]);

  const decisionMutation = useMutation({
    mutationFn: ({ caseId, decision }: { caseId: string; decision: string }) => applyCaseDecision(caseId, { decision }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cases"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  if (isLoading) return <LoadingBlock />;

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
          {data?.items.length ? (
            <span className="tag-chip">{isFetching ? "جاري التحديث..." : `${data.meta.total} حالة`}</span>
          ) : null}
        </div>

        {!data?.items.length ? (
          <EmptyState title="لا توجد حالات تحتاج مراجعة حاليًا" subtitle="جرّب تغيير البحث أو الرجوع لاحقًا." />
        ) : (
          <>
            <div className="table-like">
              {data.items.map((item) => {
                const reasons = summarizeReviewFlags(item.review_flags, item.violations);
                const confidenceItems = item.violations.length
                  ? item.violations
                  : [{ id: `${item.id}-fallback`, display_name_ar: "الثقة العامة", confidence: item.plate_confidence ?? item.vehicle_confidence }];
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
                        <div className="queue-confidence-list">
                          {confidenceItems.map((violation) => (
                            <div key={violation.id} className="queue-confidence-item">
                              <span>{violation.display_name_ar}</span>
                              <ConfidenceBadge value={violation.confidence} />
                            </div>
                          ))}
                        </div>
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

            {totalPages > 1 ? (
              <nav className="pagination-bar" aria-label="Review queue pages">
                <button className="ghost-button" type="button" disabled={page <= 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>
                  السابق
                </button>
                <div className="pagination-bar__pages">
                  {pageNumbers.map((pageNumber) => (
                    <button
                      key={pageNumber}
                      className={`pagination-bar__page${pageNumber === page ? " pagination-bar__page--active" : ""}`}
                      type="button"
                      onClick={() => setPage(pageNumber)}
                      aria-current={pageNumber === page ? "page" : undefined}
                    >
                      {pageNumber}
                    </button>
                  ))}
                </div>
                <button className="ghost-button" type="button" disabled={page >= totalPages} onClick={() => setPage((current) => Math.min(totalPages, current + 1))}>
                  التالي
                </button>
              </nav>
            ) : null}
          </>
        )}
      </section>
    </div>
  );
}
