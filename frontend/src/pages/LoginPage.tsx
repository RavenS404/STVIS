import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";

import { BRAND_SHORT } from "../app/presentation";
import { useAuth } from "../hooks/useAuth";

export function LoginPage() {
  const { login, user } = useAuth();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("Admin@123456");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      await login(username, password);
    } catch {
      setError("تعذر تسجيل الدخول. تحققي من اسم المستخدم وكلمة المرور.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="surface auth-form" onSubmit={handleSubmit}>
      <div className="panel-header">
        <div>
          <h2>تسجيل الدخول</h2>
          <p>{BRAND_SHORT} Console</p>
        </div>
      </div>
      <label>
        اسم المستخدم
        <input value={username} onChange={(event) => setUsername(event.target.value)} />
      </label>
      <label>
        كلمة المرور
        <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
      </label>
      {error ? <div className="form-error">{error}</div> : null}
      <button className="primary-button" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "جارٍ تسجيل الدخول..." : "دخول"}
      </button>
    </form>
  );
}
