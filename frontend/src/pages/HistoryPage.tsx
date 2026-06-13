import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { StatusBadge } from "../components/StatusBadge";
import { formatCaseNumber, formatDateTimeAr, formatViolationSummary } from "../app/presentation";
import { parsePlateInput, splitPlateChars } from "../app/plate";
import type { CaseListItem } from "../app/types";
import { fetchCases } from "../services/cases";
import { useDebouncedValue } from "../hooks/useDebouncedValue";

const STATE_OPTIONS = [
  { value: "", label: "الكل" },
  { value: "issued", label: "تم الإصدار" },
  { value: "supervisor_review_required", label: "تحتاج مراجعة" },
  { value: "rejected", label: "مرفوضة" },
  { value: "no_violation", label: "لا توجد مخالفة" },
  { value: "direct_issue_ready", label: "جاهزة للإصدار" },
];

const PAGE_SIZE = 20;

function getPlateParts(item: CaseListItem) {
  const fallback = parsePlateInput(item.plate_text_ar);
  return {
    letters: item.plate_letters_ar || fallback.letters,
    digits: item.plate_digits_ar || fallback.digits,
  };
}

export function HistoryPage() {
  const [search, setSearch] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [page, setPage] = useState(1);
  const debouncedSearch = useDebouncedValue(search.trim(), 300);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, stateFilter]);

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["cases", "history", debouncedSearch, stateFilter, page],
    queryFn: () =>
      fetchCases({
        page,
        page_size: PAGE_SIZE,
        search: debouncedSearch || undefined,
        state: stateFilter || undefined,
      }),
    staleTime: 8_000,
    placeholderData: keepPreviousData,
  });

  const historyIds = useMemo(() => data?.items.map((item) => item.id) ?? [], [data?.items]);
  const historyNavState = useMemo(() => ({ from: "history", ids: historyIds }), [historyIds]);
  const totalPages = Math.max(1, Math.ceil((data?.meta.total ?? 0) / PAGE_SIZE));
  const pageNumbers = useMemo(() => {
    const start = Math.max(1, page - 2);
    const end = Math.min(totalPages, page + 2);
    return Array.from({ length: end - start + 1 }, (_, index) => start + index);
  }, [page, totalPages]);

  if (isLoading) return <LoadingBlock />;

  return (
    <section className="page-grid">
      <div className="surface filter-bar" >
        <input
          placeholder="بحث برقم الحالة أو اللوحة"
          style={{ height: '3.2rem' }}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <select style={{ height: '3.2rem' }} value={stateFilter} onChange={(event) => setStateFilter(event.target.value)}>
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
          {data?.items.length ? (
            <span className="tag-chip">{isFetching ? "جاري التحديث..." : `${data.meta.total} حالة`}</span>
          ) : null}
        </div>

        {!data?.items.length ? (
          <EmptyState title="لا توجد حالات مطابقة" subtitle="جرّب تغيير الفلاتر أو البحث." />
        ) : (
          <>
          <div className="table-like">
            {data.items.map((item) => {
              const plateParts = getPlateParts(item);
              return (
                <div key={item.id} className="table-row table-row--history">
                  <div>
                    <Link
                      to={`/cases/${item.id}`}
                      state={historyNavState}
                      className="table-link"
                    >
                      {formatCaseNumber(item.case_number)}
                    </Link>
                    <small>{formatDateTimeAr(item.created_at)}</small>
                  </div>
                  <div className="history-plate-cell">
                    <span className="eyebrow">اللوحة</span>
                    <table className="history-plate-table" aria-label="تفاصيل اللوحة">
                      <thead>
                        <tr>
                          <th>الحروف</th>
                          <th>الأرقام</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>
                            <span className="history-plate-table__tokens">
                              {splitPlateChars(plateParts.letters).map((char, index) => (
                                <span key={`${char}-${index}`}>{char}</span>
                              ))}
                              {!plateParts.letters ? <span>—</span> : null}
                            </span>
                          </td>
                          <td>
                            <span className="history-plate-table__tokens history-plate-table__tokens--digits">
                              {splitPlateChars(plateParts.digits).map((char, index) => (
                                <span key={`${char}-${index}`}>{char}</span>
                              ))}
                              {!plateParts.digits ? <span>—</span> : null}
                            </span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div>
                    <span className="eyebrow">المخالفة</span>
                    <strong>{formatViolationSummary(item)}</strong>
                    {item.violations.length ? (
                      <div className="violation-confidence-list">
                        {item.violations.map((violation) => (
                          <span key={violation.id} className="violation-confidence-chip">
                            {violation.display_name_ar}
                            <ConfidenceBadge value={violation.confidence} />
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                  <StatusBadge state={item.review_state} />
                </div>
              );
            })}
          </div>

          {totalPages > 1 ? (
            <nav className="pagination-bar" aria-label="History pages">
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
      </div>
    </section>
  );
}
