import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { translateRole } from "../app/presentation";
import { useAuth } from "../hooks/useAuth";
import { createUser, fetchUsers } from "../services/admin";

export function UsersPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { data, isLoading, isError } = useQuery({ queryKey: ["users"], queryFn: fetchUsers });
  const [form, setForm] = useState({ username: "", full_name: "", role: "supervisor", password: "" });
  const mutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      setForm({ username: "", full_name: "", role: "supervisor", password: "" });
      void queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate(form);
  }

  if (user?.role !== "admin") return <Navigate to="/" replace />;
  return (
    <div className="two-column">
      <form className="surface" onSubmit={submit}>
        <div className="panel-header">
          <h2>إضافة مستخدم</h2>
        </div>
        <label>
          اسم المستخدم
          <input value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} />
        </label>
        <label>
          الاسم الكامل
          <input value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />
        </label>
        <label>
          الدور
          <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}>
            <option value="supervisor">مشرف</option>
            <option value="admin">مدير</option>
          </select>
        </label>
        <label>
          كلمة المرور
          <input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
        </label>
        <button className="primary-button" type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "جارٍ الإنشاء..." : "إنشاء"}
        </button>
      </form>

      <section className="surface">
        <div className="panel-header">
          <h2>المستخدمون الحاليون</h2>
        </div>
        {isLoading ? <LoadingBlock /> : isError ? <EmptyState title="تعذر تحميل المستخدمين" subtitle="حاولي تحديث الصفحة مرة أخرى." /> : !data?.length ? <EmptyState title="لا يوجد مستخدمون" /> : (
          <div className="table-like">
            {data.map((item) => (
              <div key={item.id} className="table-row">
                <strong>{item.full_name}</strong>
                <span>{item.username}</span>
                <span>{translateRole(item.role)}</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
