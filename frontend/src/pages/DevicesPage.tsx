import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { useAuth } from "../hooks/useAuth";
import { createDevice, fetchDevices, fetchModels, rotateDeviceToken } from "../services/admin";

export function DevicesPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["devices"], queryFn: fetchDevices });
  const modelsQuery = useQuery({ queryKey: ["models"], queryFn: fetchModels });
  const [tokenReveal, setTokenReveal] = useState<string | null>(null);
  const [form, setForm] = useState({ code: "", name: "", location_label: "", notes: "" });
  const createMutation = useMutation({
    mutationFn: createDevice,
    onSuccess: (result) => {
      setTokenReveal(result.plain_token);
      setForm({ code: "", name: "", location_label: "", notes: "" });
      void queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
  });
  const rotateMutation = useMutation({
    mutationFn: rotateDeviceToken,
    onSuccess: (result) => {
      setTokenReveal(result.plain_token);
      void queryClient.invalidateQueries({ queryKey: ["devices"] });
    },
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    createMutation.mutate(form);
  }

  if (user?.role !== "admin") return <Navigate to="/" replace />;
  return (
    <div className="page-grid">
      <form className="surface" onSubmit={submit}>
        <div className="panel-header">
          <h2>إضافة جهاز</h2>
        </div>
        <label>
          الرمز
          <input value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value })} />
        </label>
        <label>
          الاسم
          <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
        </label>
        <label>
          الموقع
          <input value={form.location_label} onChange={(event) => setForm({ ...form, location_label: event.target.value })} />
        </label>
        <label>
          ملاحظات
          <input value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} />
        </label>
        <button className="primary-button" type="submit">إنشاء جهاز</button>
        {tokenReveal ? <pre className="debug-block">رمز الجهاز الجديد: {tokenReveal}</pre> : null}
      </form>

      <section className="surface">
        <div className="panel-header">
          <h2>الأجهزة والنماذج</h2>
        </div>
        {isLoading ? <LoadingBlock /> : !data?.length ? <EmptyState title="لا توجد أجهزة" /> : (
          <div className="table-like">
            {data.map((item) => (
              <div key={item.id} className="table-row table-row--card">
                <div>
                  <strong>{item.name}</strong>
                  <small>{item.code} - {item.location_label}</small>
                </div>
                <button className="ghost-button" type="button" onClick={() => rotateMutation.mutate(item.id)}>
                  تدوير الرمز
                </button>
              </div>
            ))}
          </div>
        )}
        <div className="tag-cloud">
          {modelsQuery.data?.map((model) => (
            <span key={model.id} className="tag-chip">
              {model.display_name}: {model.version}
            </span>
          ))}
        </div>
      </section>
    </div>
  );
}
