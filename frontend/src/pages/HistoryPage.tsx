import { useDeferredValue, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { StatusBadge } from "../components/StatusBadge";
import { formatCaseNumber, formatDateTimeAr, formatViolationSummary, translateState } from "../app/presentation";
import { fetchCases } from "../services/cases";

const STATE_OPTIONS = [
  { value: "", label: "الكل" },
  { value: "issued", label: "تم الإصدار" },
  { value: "supervisor_review_required", label: "تحتاج مراجعة" },
  { value: "rejected", label: "مرفوضة" },
  { value: "no_violation", label: "لا توجد مخالفة" },
  { value: "direct_issue_ready", label: "جاهزة للإصدار" },
];

export function HistoryPage() {
  const [search, setSearch] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const debouncedSearch = useDeferredValue(search);

  const { data, isLoading } = useQuery({
    queryKey: ["cases", "history", debouncedSearch, stateFilter],
    queryFn: () =>
      fetchCases({
        search: debouncedSearch || undefined,
        state: stateFilter || undefined,
      }),
    staleTime: 8_000,
  });

  if (isLoading) return <LoadingBlock />;

  return (
    <section className="page-grid">
      <div className="surface filter-bar">
        <input
          placeholder="بحث برقم الحالة أو اللوحة"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <select value={stateFilter} onChange={(event) => setStateFilter(event.target.value)}>
          {STATE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className="surface">
        <div className="panel-header">
          <div>
            <h2>السجل التشغيلي</h2>
            <p>عرض مبسط للحالات السابقة مع اللوحة والمخالفة والحالة النهائية.</p>
          </div>
          {data?.items.length ? <span className="tag-chip">{data.meta.total} حالة</span> : null}
        </div>

        {!data?.items.length ? (
          <EmptyState title="لا توجد حالات مطابقة" subtitle="جرّب تغيير الفلاتر أو البحث." />
        ) : (
          <div className="table-like">
            {data.items.map((item) => (
              <div key={item.id} className="table-row table-row--history">
                <div>
                  <Link to={`/cases/${item.id}`} className="table-link">
                    {formatCaseNumber(item.case_number)}
                  </Link>
                  <small>{formatDateTimeAr(item.created_at)}</small>
                </div>
                <div>
                  <span className="eyebrow">اللوحة</span>
                  <strong>{item.plate_text_ar ?? "بدون لوحة"}</strong>
                </div>
                <div>
                  <span className="eyebrow">المخالفة</span>
                  <strong>{formatViolationSummary(item)}</strong>
                </div>
                <StatusBadge state={item.review_state} />
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
