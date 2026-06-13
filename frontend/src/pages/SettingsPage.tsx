import { Navigate } from "react-router-dom";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { useAuth } from "../hooks/useAuth";
import { fetchSettings, updateSetting } from "../services/admin";

const SETTING_LABELS: Record<string, { label: string; description: string; group: string }> = {
  "violation.min_confidence": { label: "الحد الأدنى لثقة المخالفة", description: "أقل مستوى ثقة مقبول لاعتبار المخالفة", group: "إعدادات المخالفات" },
  "violation.review_threshold": { label: "حد المراجعة للمخالفة", description: "أقل من هذا يُعتبر مشكوك فيه", group: "إعدادات المخالفات" },
  "violation.direct_issue_threshold": { label: "حد الإصدار المباشر للمخالفة", description: "فوق هذا يمكن الإصدار مباشرة", group: "إعدادات المخالفات" },
  "plate.min_confidence": { label: "الحد الأدنى لثقة اللوحة", description: "أقل مستوى ثقة مقبول لقراءة اللوحة", group: "إعدادات اللوحات" },
  "plate.direct_issue_threshold": { label: "حد الإصدار المباشر للوحة", description: "فوق هذا تُعتبر القراءة مؤكدة", group: "إعدادات اللوحات" },
  "policy.auto_issue_enabled": { label: "الإصدار التلقائي", description: "هل يتم الإصدار تلقائيًا بدون مشرف", group: "إعدادات السياسة" },
  "policy.escalate_on_missing_plate": { label: "التصعيد عند غياب اللوحة", description: "تصعيد إلى مشرف إذا لم يتم رصد لوحة", group: "إعدادات السياسة" },
  "association.min_plate_score": { label: "حد ربط اللوحة بالمركبة", description: "أقل درجة لربط اللوحة بالمركبة", group: "إعدادات الربط" },
  "association.ambiguity_gap": { label: "فجوة الغموض", description: "الفرق بين أعلى درجتين لاعتبار الربط غامضًا", group: "إعدادات الربط" },
  "ingest.max_upload_size_mb": { label: "أقصى حجم للصورة", description: "أكبر حجم مسموح به لرفع صورة من الجهاز بالميجابايت.", group: "إعدادات الرفع" },
  "policy.direct_issue_default_state": { label: "حالة الإصدار المباشر الافتراضية", description: "الحالة التي يستخدمها النظام للحالات المؤكدة قبل تدخل المشرف.", group: "إعدادات السياسة" },
  "policy.escalate_on_ambiguous_association": { label: "تصعيد حالات الربط غير الواضحة", description: "إرسال الحالة للمراجعة إذا كان ربط اللوحة بالمركبة غير مؤكد.", group: "إعدادات السياسة" },
  "policy.max_detections_per_event": { label: "أقصى عدد اكتشافات لكل حدث", description: "حد أمان لمنع الحالات المزدحمة أو النتائج غير الطبيعية.", group: "إعدادات السياسة" },
};

function getSettingMeta(key: string) {
  return SETTING_LABELS[key] ?? { label: key, description: "", group: "أخرى" };
}

export function SettingsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { data, isLoading, isError } = useQuery({ queryKey: ["settings"], queryFn: fetchSettings });
  const [drafts, setDrafts] = useState<Record<string, string>>({});

  const mutation = useMutation({
    mutationFn: ({ key, value }: { key: string; value: string }) => {
      let parsed: unknown = value;
      try {
        parsed = JSON.parse(value);
      } catch {
        parsed = value;
      }
      return updateSetting(key, parsed);
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["settings"] }),
  });

  if (user?.role !== "admin") return <Navigate to="/" replace />;
  if (isLoading) return <LoadingBlock />;
  if (isError) return <EmptyState title="تعذر تحميل الإعدادات" subtitle="حاولي تحديث الصفحة مرة أخرى." />;
  if (!data?.length) return <EmptyState title="لا توجد إعدادات" />;

  // Group settings by category
  const grouped: Record<string, typeof data> = {};
  for (const item of data) {
    const meta = getSettingMeta(item.key);
    const group = meta.group;
    if (!grouped[group]) grouped[group] = [];
    grouped[group].push(item);
  }

  return (
    <div className="page-grid">
      {Object.entries(grouped).map(([group, items]) => (
        <section key={group} className="surface">
          <div className="panel-header">
            <h2>{group}</h2>
          </div>
          <div className="settings-list">
            {items.map((item) => {
              const meta = getSettingMeta(item.key);
              return (
                <div key={item.key} className="setting-row">
                  <div className="setting-row__label">
                    <strong>{meta.label}</strong>
                    {meta.description && <small>{meta.description}</small>}
                  </div>
                  <div className="setting-row__control">
                    <input
                      value={drafts[item.key] ?? JSON.stringify(item.value_json)}
                      onChange={(event) => setDrafts((current) => ({ ...current, [item.key]: event.target.value }))}
                    />
                    <button
                      className="ghost-button"
                      onClick={() => mutation.mutate({ key: item.key, value: drafts[item.key] ?? JSON.stringify(item.value_json) })}
                      type="button"
                      disabled={mutation.isPending}
                    >
                      حفظ
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
