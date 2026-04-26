import { useMutation, useQuery } from "@tanstack/react-query";

import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { StatCard } from "../components/StatCard";
import { BRAND_SHORT } from "../app/presentation";
import { exportCasesCsv, fetchReportSummary } from "../services/reports";

export function ReportsPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["reports"], queryFn: fetchReportSummary });
  const exportMutation = useMutation({
    mutationFn: exportCasesCsv,
    onSuccess(blob) {
      // Prepend UTF-8 BOM so Excel correctly recognises Arabic text
      const bom = new Uint8Array([0xef, 0xbb, 0xbf]);
      const bomBlob = new Blob([bom, blob], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(bomBlob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${BRAND_SHORT.toLowerCase()}_cases.csv`;
      anchor.click();
      URL.revokeObjectURL(url);
    },
  });

  if (isLoading) return <LoadingBlock />;
  if (isError) return <EmptyState title="تعذر تحميل التقارير" subtitle="حاولي تحديث الصفحة ثم المحاولة مرة أخرى." />;
  if (!data) return <EmptyState title="تعذر تحميل التقارير" />;

  const violationBreakdown = data.violation_breakdown ?? {};

  return (
    <div className="page-grid">
      <section className="stats-grid">
        <StatCard title="إجمالي الحالات" value={data.total_cases} />
        <StatCard title="الحالات الصادرة" value={data.issued_cases} />
        <StatCard title="الحالات المرفوضة" value={data.rejected_cases} />
        <StatCard title="الحالات المفتوحة للمراجعة" value={data.supervisor_cases} />
      </section>

      <section className="surface">
        <div className="panel-header">
          <div>
            <h2>تفكيك المخالفات</h2>
            <p>اللوحة تعرض أسماء المخالفات بصياغة عربية مفهومة فقط.</p>
          </div>
          <button className="primary-button" type="button" onClick={() => exportMutation.mutate()}>
            تصدير CSV
          </button>
        </div>
        <div className="tag-cloud">
          {Object.entries(violationBreakdown).length ? (
            Object.entries(violationBreakdown).map(([key, value]) => (
              <span key={key} className="tag-chip">
                {key}: {value}
              </span>
            ))
          ) : (
            <span className="tag-chip">لا توجد بيانات مخالفة للتقرير الحالي</span>
          )}
        </div>
      </section>
    </div>
  );
}
