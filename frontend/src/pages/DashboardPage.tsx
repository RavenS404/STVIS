import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { formatCaseNumber, formatDateTimeAr, translateState } from "../app/presentation";
import { fetchDashboardSummary } from "../services/dashboard";

export function DashboardPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["dashboard"], queryFn: fetchDashboardSummary });

  if (isLoading) return <LoadingBlock />;
  if (isError) return <EmptyState title="تعذر تحميل لوحة المتابعة" subtitle="حاولي تحديث الصفحة مرة أخرى." />;
  if (!data) return <EmptyState title="لا توجد بيانات لعرضها" />;

  const casesByState = data.cases_by_state ?? {};
  const violationsByCode = data.violations_by_code ?? {};
  const recentCases = Array.isArray(data.recent_cases) ? data.recent_cases : [];
  const dashboardNavState = { from: "dashboard", ids: recentCases.map((item) => item.id) };

  return (
    <div className="page-grid">
      <section className="stats-grid">
        <StatCard title="حالات تحتاج مشرف" value={data.escalations} />
        <StatCard title="حالات صادرة اليوم" value={data.issued_today} />
        <StatCard title="عمق الطابور" value={data.queue_depth} />
        <StatCard title="أنواع المخالفات المؤكدة" value={Object.keys(violationsByCode).length} />
      </section>

      <section className="surface">
        <div className="panel-header">
          <div>
            <h2>آخر الحالات</h2>
            <p>ملخص سريع لأحدث ما تم التقاطه ومعالجته.</p>
          </div>
        </div>
        <div className="table-like">
          {recentCases.length ? (
            recentCases.map((item) => (
              <Link key={item.id} to={`/cases/${item.id}`} state={dashboardNavState} className="table-row table-row--recent table-row--link">
                <div>
                  <strong>{formatCaseNumber(item.case_number)}</strong>
                  <small>{formatDateTimeAr(item.created_at)}</small>
                </div>
                <StatusBadge state={item.state} />
              </Link>
            ))
          ) : (
            <div className="empty-state compact-empty">لا توجد حالات حديثة بعد.</div>
          )}
        </div>
      </section>

      <section className="two-column">
        <div className="surface">
          <div className="panel-header">
            <div>
              <h2>توزيع الحالات</h2>
              <p>عدد الحالات داخل كل مرحلة تشغيلية.</p>
            </div>
          </div>
          <div className="tag-cloud">
            {Object.entries(casesByState).length ? (
              Object.entries(casesByState).map(([key, value]) => (
                <span key={key} className="tag-chip">
                  {translateState(key)}: {value}
                </span>
              ))
            ) : (
              <span className="tag-chip">لا توجد حالات مسجلة</span>
            )}
          </div>
        </div>

        <div className="surface">
          <div className="panel-header">
            <div>
              <h2>أكثر المخالفات ظهورًا</h2>
              <p>الأسماء المعروضة هنا عربية ومباشرة بدون أكواد داخلية.</p>
            </div>
          </div>
          <div className="tag-cloud">
            {Object.entries(violationsByCode).length ? (
              Object.entries(violationsByCode).map(([key, value]) => (
                <span key={key} className="tag-chip">
                  {key}: {value}
                </span>
              ))
            ) : (
              <span className="tag-chip">لا توجد مخالفات مؤكدة بعد</span>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
