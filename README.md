# Ismail Smart Agent (V2.1 Enterprise Edition)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Enterprise Ready](https://img.shields.io/badge/Status-Enterprise--Ready-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-Proprietary-orange.svg)]()

نظام وكيل ذكاء اصطناعي ذاتي ومتقدم (Enterprise Autonomous AI Agent Framework) مصمم لمشاريع الأتمتة الاحترافية وعقود منصة Upwork، مبني بمعمارية غير متزامنة (Async Architecture) ومحرك تدفق مهام رسومي (DAG Engine) مع واجهة برمجية كاملة عبر FastAPI.

> 📘 **لإرشادات تسليم العميل وتشغيل النظام بنقرة واحدة:** راجع [دليل تسليم العميل (CLIENT_HANDOVER_GUIDE.md)](file:///c:/Users/HP/Documents/AI_Agent/CLIENT_HANDOVER_GUIDE.md).

---

## 🚀 أبرز التحسينات والميزات المعمارية (V2.1 Updates)

### 1. محرك التخطيط الديناميكي الذكي (LLM-First Dynamic Planner)
- **إلغاء المطابقة الثابتة (Zero Hardcoding):** إلغاء تام للاعتماد على الكلمات المفتاحية اليدوية أو القواعد المكتوبة مسبقاً؛ التخطيط واختيار الأدوات يعتمد بنسبة 100% على الـ LLM.
- **تقنية Sparse Tool Loading:**
  - تقسيم الـ 29 أداة إلى **7 فئات وظيفية** (`document`, `data`, `web`, `system`, `vision`, `communication`, `workflow`).
  - حقن الأدوات ذات الصلة فقط في سياق الموجه (Prompt Context) بدلاً من تمرير جميع الأدوات، مما وفر أكثر من **70% من استهلاك الـ Tokens** وحمى تماماً من **Token Overflow**.

### 2. محرك التنفيذ المتطور (Async & Parallel Executor with Self-Healing)
- **معالجة متوازية (Parallel Execution):** دعم تشغيل المهام المتعددة بالتوازي عبر `asyncio.gather` أو تسلسلياً حسب طبيعة الخطة.
- **سجلات تتبع مهيكلة (Structured Logging):** توثيق فوري لطريقة مطابقة الأداة (`structured_dict`, `exact_match`, `prefix_match`, `bridge_match`)، المدخلات، المخرجات، والزمن بالمللي ثانية لتسهيل عملية الـ Debugging.
- **حلقة التصحيح والتعافي الذاتي (Self-Healing Loop):** تصحيح تلقائي للأخطاء الشائعة (مسارات الملفات، امتدادات `.xlsx`/`.pdf`، والروابط) عبر [ReflectionEngine](file:///C:/Users/HP/Documents/AI_Agent/services/reflection_engine.py).
- **بوابات الحوكمة والأمان (Guardrails Gateway):** ثلاثة أوضاع للتحكم في العمليات الحرجة (`auto`, `strict`, `ask`).

### 3. الفحص التشخيصي الشامل (`/health`)
نقطة فحص عميقة تفحص:
- **المحركات الستة (Core Engines):** Planner, Executor, Guardrails, Reflection, DAG Orchestrator, LLM Provider.
- **سلامة الأدوات (Tools Health):** التحقق من قابلية استدعاء جميع الـ 29 أداة والتأكد من خلو النظام من أي أداة معطوبة.
- **البيئة والتخزين (Environment):** مجلد الرفع `uploads`، الصلاحيات، وإصدارات التشغيل.

---

## 📂 هيكلية المشروع (Project Structure)

```text
AI_Agent/
├── api_server.py                 # سيرفر FastAPI الرئيسي مع نقاط /health, /run, /dag, /tools
├── planner.py                    # محرك التخطيط الذكي مع Sparse Tool Loading و Structured Logging
├── executor.py                   # محرك التنفيذ غير المتزامن والمتوازي مع حلقة التعافي الذاتي
├── brain.py                      # نقطة التوجيه المعرفي وسجل الأدوات
├── config.py                     # إعدادات النظام، النماذج، وبوابات الأمان
├── Dockerfile                    # ملف الحاوية الرسمي للإنتاج
├── docker-compose.yml            # تكامل وتشغيل السيرفر مع Ollama
├── .env.example                  # نموذج المتغيرات البيئية
├── requirements.txt              # متطلبات الحزم والمكتبات
├── services/
│   ├── tool_registry_bridge.py   # جسر استخراج مخططات ومعاملات الـ 29 أداة ديناميكياً
│   ├── guardrails.py             # بوابة الحوكمة، السياسات، وسجل التدقيق الأمني
│   └── reflection_engine.py      # محرك التصحيح والتعافي الذاتي
├── orchestrator/
│   ├── dag_engine.py             # محرك الـ DAG الرسومي مع الفرز الطوبولوجي وكشف الدورات
│   ├── node.py                   # عقدة المهمة (TaskNode)
│   ├── context.py                # سياق الحالة المشترك (ExecutionContext)
│   └── workflows.py              # مسارات عمل جاهزة للعملاء (Lead Enrichment, Market Research)
├── tools/                        # حزمة الأدوات الـ 29 المتخصصة (Excel, PDF, DuckDB, Web, OCR...)
├── integrations/
│   └── n8n_orchestrator.py       # تكامل مسارات عمل n8n
└── llm/
    └── manager.py                # مدير الاتصال بمزودات النماذج المحلية (Ollama / LiteLLM)
```

---

## 🛠️ التثبيت والتشغيل المحلي (Local Setup)

### 1. إعداد البيئة الافتراضية
```bash
# إنشاء وتفعيل البيئة الافتراضية
python -m venv venv
# على Windows:
venv\Scripts\activate
# على Linux/macOS:
source venv/bin/activate

# تثبيت الحزم المطلوبة
pip install -r requirements.txt
```

### 2. إعداد المتغيرات البيئية
قم بنسخ ملف الإعدادات:
```bash
cp .env.example .env
```
تأكد من ضبط رابط النموذج المحلي `OLLAMA_URL` واسم النموذج `MODEL_NAME` في ملف `.env`.

### 3. تشغيل السيرفر
```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```
يمكنك تصفح التوثيق التفاعلي للـ API عبر:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 🐳 التشغيل عبر Docker و Docker Compose

### تشغيل النظام بالكامل (الوكيل + Ollama):
```bash
docker-compose up -d --build
```

### تشغيل حاوية الوكيل فقط:
```bash
docker build -t ismail-smart-agent .
docker run -d -p 8000:8000 --name smart-agent --env-file .env ismail-smart-agent
```

---

## 🧪 اختبارات النظام والتحقق (Test Suites)

تم توفير حزم اختبارات شاملة لتأكيد كفاءة واستقرار الـ Framework:

```bash
# 1. الفحص الشامل لجاهزية العميل (Client Readiness Suite)
python test_client_readiness.py

# 2. اختبار ترقيات الـ Framework (Schema Bridge, Guardrails, Reflection, DAG)
python test_framework_enhancements.py

# 3. اختبار التحسينات الأخيرة (Sparse Loading, Structured Logging, Health Endpoint)
python test_system_improvements.py
```

---

## 📡 النقاط البرمجية الرئيسية (API Reference)

| النقطة | النوع | الوصف |
| :--- | :--- | :--- |
| `/health` | `GET` | فحص تشخيصي شامل لصحة المحركات الـ 6، الـ 29 أداة، ومجلدات التخزين |
| `/run` | `POST` | تنفيذ أمر نصي حر باللغة الطبيعية مع التخطيط والتنفيذ المباشر |
| `/plan` | `POST` | توليد خطة العمل المقترحة من الـ LLM دون تنفيذها |
| `/dag` | `POST` | تنفيذ شبكة مخصصة من عقد المهام مع إدارة الاعتماديات ومشاركة السياق |
| `/tools` | `GET` | استعراض كافة الـ 29 أداة المسجلة بمخططاتها ومعاملاتها التفصيلية |
