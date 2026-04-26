import { Link, isRouteErrorResponse, useRouteError } from "react-router-dom";

import { BRAND_SHORT } from "../app/presentation";

function getErrorMessage(error: unknown): { title: string; subtitle: string } {
  if (isRouteErrorResponse(error)) {
    if (error.status === 404) {
      return {
        title: "الصفحة غير موجودة",
        subtitle: "الرابط المطلوب غير متاح أو تم نقله. يمكنك الرجوع للرئيسية والمتابعة من هناك.",
      };
    }

    return {
      title: "تعذر عرض الصفحة",
      subtitle: error.statusText || "حدث خطأ أثناء تحميل الصفحة. حاولي مرة أخرى بعد ثوانٍ.",
    };
  }

  if (error instanceof Error && error.message) {
    return {
      title: "حدث خطأ غير متوقع",
      subtitle: error.message,
    };
  }

  return {
    title: "حدث خطأ غير متوقع",
    subtitle: "يمكنك الرجوع للرئيسية أو إعادة تحميل الصفحة.",
  };
}

export function RouteErrorPage() {
  const error = useRouteError();
  const message = getErrorMessage(error);

  return (
    <div className="page-grid">
      <section className="surface empty-state">
        <span className="eyebrow">{BRAND_SHORT}</span>
        <h2>{message.title}</h2>
        <p>{message.subtitle}</p>
        <div className="button-row">
          <Link className="primary-button" to="/">
            العودة للرئيسية
          </Link>
          <button className="ghost-button" onClick={() => window.location.reload()} type="button">
            إعادة التحميل
          </button>
        </div>
      </section>
    </div>
  );
}
