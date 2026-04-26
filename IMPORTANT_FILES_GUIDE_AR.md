# دليل أهم الملفات في المشروع

## الجذر

### `docker-compose.yml`
يشغّل النظام كاملًا محليًا: PostgreSQL وRabbitMQ وMinIO وbackend وworker وfrontend.

### `.env`
القيم التشغيلية الافتراضية للديمو المحلي.

### `.env.example`
نسخة مرجعية نظيفة لإعداد البيئة.

### `README.md`
أسرع نقطة دخول لتشغيل المشروع ومعرفة الحسابات والهيكل العام.

### `SYSTEM_EXPLANATION_AR.md`
شرح عربي معماري ووظيفي للنظام بالكامل.

## النماذج

### `Ai_models/violation_detection.pt`
نموذج كشف المركبات/اللوحات/المخالفات داخل الصورة الكاملة.

### `Ai_models/plate_detection.pt`
نموذج كشف توكنات اللوحة مباشرة بدل OCR.

## المجلد `common/`

### `common/constants/plate_mapping.py`
القاموس المركزي لتحويل Franco/classes إلى الحروف والأرقام العربية.

### `common/constants/violation_catalog.py`
تعريف كتالوج المخالفات، أسماء العرض، وما إذا كانت قابلة للإصدار أم لا.

### `common/utils/plate_reading.py`
أهم ملف في مسار قراءة اللوحة:
- ترتيب التوكنات
- دعم الصفوف
- التطبيع
- تكوين النص العربي
- حفظ التفاصيل الدقيقة

### `common/utils/association.py`
منطق ربط المركبة باللوحة والمخالفات مع دعم الحالات الغامضة.

### `common/utils/policy.py`
منطق القرار: هل الحالة جاهزة للإصدار أم تحتاج مشرف؟

## المجلد `backend/app/`

### `backend/app/main.py`
نقطة تشغيل FastAPI والـ middleware وضم الـ routers.

### `backend/app/core/config.py`
إعدادات المشروع من البيئة، مثل قاعدة البيانات وRabbitMQ وMinIO ومسارات النماذج.

### `backend/app/core/security.py`
تجزئة كلمات المرور، توليد رموز الأجهزة، وإنشاء/فك JWT.

### `backend/app/db/session.py`
جلسة SQLAlchemy والاتصال بقاعدة البيانات.

### `backend/app/db/seed.py`
إنشاء المستخدمين الافتراضيين والإعدادات الأولية والأجهزة وملفات النماذج في قاعدة البيانات.

### `backend/app/models/event.py`
جداول:
- الحدث
- الأصول المخزنة
- تشغيلات الاستدلال

### `backend/app/models/case.py`
جداول:
- `vehicle_cases`
- `case_plate_reads`
- `case_violations`

### `backend/app/models/audit.py`
سجل التدقيق المركزي لكل الإجراءات الحساسة.

### `backend/app/models/monitoring.py`
نبضات الخدمات والنماذج الصحية.

### `backend/app/services/event_ingest_service.py`
يستقبل الملف المرفوع، يتحقق منه، يخزّنه، وينشئ الحدث ويرسله للاستدلال.

### `backend/app/services/case_service.py`
إدارة عرض الحالات، تفاصيلها، قرارات المشرف/الإدارة، وإعادة الجدولة.

### `backend/app/services/health_service.py`
يبني صورة الصحة العامة للنظام:
- قاعدة البيانات
- RabbitMQ
- MinIO
- worker
- النماذج

### `backend/app/api/routes/ingest.py`
واجهة رفع الأحداث من الأجهزة.

### `backend/app/api/routes/cases.py`
واجهات قائمة الحالات والتفاصيل والقرارات وإعادة التشغيل.

### `backend/app/api/routes/admin_*`
واجهات الإدارة: المستخدمون، الأجهزة، الإعدادات، النماذج.

## المجلد `worker/app/`

### `worker/app/celery_app.py`
تهيئة Celery وربطه بـ RabbitMQ.

### `worker/app/tasks.py`
القلب التنفيذي الحقيقي لمسار الذكاء الاصطناعي:
- تحميل الحدث
- تشغيل النموذجين
- الربط
- قراءة اللوحة
- إنشاء الحالات
- إنشاء المخالفات
- التحديد النهائي للحالة
- حفظ الأدلة المعلّمة

### `worker/app/inference/model_runtime.py`
تحميل `YOLO` للنموذجين وإدارة النسخة الحالية.

### `worker/app/inference/drawing.py`
قصاصات الصور ورسم الـ overlays والأصول المرئية للديمو والمراجعة.

## المجلد `frontend/src/`

### `frontend/src/app/router.tsx`
تعريف مسارات الواجهة كلها.

### `frontend/src/contexts/AuthContext.tsx`
إدارة جلسة المستخدم وتخزين التوكن.

### `frontend/src/layouts/AppLayout.tsx`
هيكل الواجهة الداخلية بعد تسجيل الدخول.

### `frontend/src/pages/DashboardPage.tsx`
الملخص التشغيلي العام.

### `frontend/src/pages/ReviewQueuePage.tsx`
طابور الحالات التي تحتاج مشرف.

### `frontend/src/pages/CaseDetailsPage.tsx`
أهم شاشة تشغيلية:
- الصور
- اللوحة
- المخالفات
- الأعلام
- القرار
- التدقيق

### `frontend/src/pages/HealthPage.tsx`
شاشة صحة التشغيل.

### `frontend/src/pages/SettingsPage.tsx`
إدارة الإعدادات التشغيلية الحساسة.

### `frontend/src/pages/UsersPage.tsx`
إدارة الحسابات.

### `frontend/src/pages/DevicesPage.tsx`
إدارة الأجهزة وتدوير التوكنات وعرض نسخ النماذج.

### `frontend/src/app/globals.css`
نظام التصميم البصري العربي RTL للواجهة كاملة.

## الاختبارات

### `backend/tests/test_plate_postprocessor.py`
يتأكد من صحة بناء اللوحة العربية من التوكنات.

### `backend/tests/test_association_service.py`
يتأكد من عدم ربط لوحة بمركبة خاطئة بسهولة.

### `backend/tests/test_policy_engine.py`
يتأكد من قرار الإصدار المباشر مقابل التصعيد.

### `backend/tests/test_security.py`
يتحقق من طبقة التجزئة وJWT.
