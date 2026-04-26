import { useDeferredValue, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { StatusBadge } from "../components/StatusBadge";
import { formatCaseNumber, formatDateTimeAr, formatViolationSummary, summarizeReviewFlags } from "../app/presentation";
import { fetchCases } from "../services/cases";

export function ReviewQueuePage() {
  const [search, setSearch] = useState("");
  const debouncedSearch = useDeferredValue(search);

  const { data, isLoading } = useQuery({
    queryKey: ["cases", "review", debouncedSearch],
    queryFn: () => fetchCases({ only_supervisor_queue: true, search: debouncedSearch || undefined }),
    staleTime: 8_000,
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
          <span className="tag-chip">{data.items.length} حالة</span>
        </div>

        <div className="table-like">
          {data.items.map((item) => {
            const reasons = summarizeReviewFlags(item.review_flags, item.violations);
            return (
              <Link key={item.id} to={`/cases/${item.id}`} className="queue-card">
                <div className="queue-card__header">
                  <div>
                    <strong className="table-link">{formatCaseNumber(item.case_number)}</strong>
                    <small>{formatDateTimeAr(item.created_at)}</small>
                  </div>
                  <StatusBadge state={item.review_state} />
                </div>

                <div className="queue-card__body">
                  <div>
                    <span className="eyebrow">قراءة اللوحة</span>
                    <strong>{item.plate_text_ar ?? "بدون لوحة مؤكدة"}</strong>
                  </div>
                  <div>
                    <span className="eyebrow">المخالفة</span>
                    <strong>{formatViolationSummary(item)}</strong>
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
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
