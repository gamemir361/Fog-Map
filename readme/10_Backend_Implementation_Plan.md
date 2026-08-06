10_Backend_Implementation_Plan.md

```markdown
# 10_Backend_Implementation_Plan.md

## سند برنامه اجرایی توسعه لایه بک‌اند (Comprehensive Backend Implementation Plan)
**پروژه:** پلتفرم جهانی اکتشاف شهری بازی‌وارشده (Gamified Urban Exploration Platform)  
**نسخه:** ۱.۰.۰  
**وضعیت:** نسخه نهایی مصوب (پس از ارزیابی ساختاری مهندس ارشد بک‌اند، معمار ارشد سیستم، مهندس DevOps و CTO)  
**اسناد بالادستی مرجع:** `00_Product_Principles.md` تا `09_AI_And_Game_Intelligence_Architecture.md`

---

## ۱. نمای کلی معماری بک‌اند (Backend Architecture Overview)

در فاز MVP، بک‌اند پلتفرم بر پایه الگوی **مونوپلیت ماژولار (Modular Monolith)** توسعه می‌یابد. انتخاب این الگو برای دوری از پیچیدگی‌های اولیه میکروسرویس‌ها (نظیر Network Latency، Distributed Transactions و سنگینی سربار DevOps) است، در حالی که ساختار پروژه به طور سخت‌گیرانه‌ای مرزهای دامنه‌ای (Bounded Contexts) را در سطح کدهای پایتون ایزوله می‌کند.

### مرزبندی ماژول‌ها و استراتژی هجرت به میکروسرویس‌ها


```

┌────────────────────────────────────────────────────────────────────────┐
│                        MODULE BASE ENCAPSULATION                       │
├────────────────────────────────────────────────────────────────────────┤
│  Each Module Contains:                                                 │
│  [Controller / API] ──> [Internal Service] ──> [Isolated Repository]   │
│                                                                        │
│  Module Invariants:                                                    │
│  - NO Direct Cross-Module Database Queries.                            │
│  - Cross-Module Communication ONLY via Shared Event Bus or Interfaces. │
└────────────────────────────────────────────────────────────────────────┘

```

این مرزبندی ساختاری تضمین می‌کند که در فاز مقیاس (Scale)، هر یک از این ماژول‌ها می‌توانند بدون نیاز به بازنویسی منطق کسب‌وکار، به کانتینرهای مستقل میکروسرویس در کلاستر کوبرنتیز تبدیل شوند.

---

## ۲. پشته فناوری انتخابی و چرایی آن (Tech Stack Selection Strategy)

| لایه زیرساخت | فناوری انتخابی | چرایی انتخاب و مزیت فنی |
| :--- | :--- | :--- |
| **Language & Framework** | **Python 3.11 + FastAPI** | عملکرد فوق‌العاده ناهمگام (Async/Await) بر پایه Starlette و Pydantic، سرعت بی‌پایان در توسعه و اکوسیستم غنی دیتای مکانی. |
| **Main Geospatial DB** | **PostgreSQL 15 + PostGIS** | استاندارد طلایی صنایع مپینگ برای هندلینگ داده‌های توپولوژی، شاخص‌های فضایی و توابع هندسی پیچیده. |
| **Cache & Task Queue** | **Redis + Celery** | ذخیره‌سازی سشن‌های موقت با سرعت زیر میلی‌ثانیه و لودبالانس ناهمگام کارهای سنگین هندسی و هوش مصنوعی. |
| **Map & Routing Engine**| **Valhalla Engine** | انعطاف‌پذیری ۱۰۰ درصدی برای تزریق داینامیک توابع هزینه کیفی در زمان اجرا (Custom Cost Functions). |
| **AI Runtime Integration**| **OpenAI API / LiteLLM** | یکپارچه‌سازی آسان با LLMها به صورت ناهمگام با خروجی Strictly JSON. |

---

## ۳. ساختار درخت پوشه‌ها و ریپازیتوری (Repository Structure)

پروژه بک‌اند در یک مونو-ریپازیتوری با معماری لایه‌ای تمیز (Clean Architecture) به شرح زیر ساختاردهی می‌شود:


```

/backend
├── /app
│     ├── main.py                 # نقطه ورود اصلی برنامه FastAPI
│     ├── /core                   # تنظیمات کلان، امنیت و حاکمیت سیستم
│     │     ├── config.py         # مدیریت متغیرهای محیطی Pydantic Settings
│     │     ├── security.py       # منطق هشینگ و صدور توکن‌های JWT
│     │     └── database.py       # کانکشن پول پایگاه داده SQLAlchemy Session
│     │
│     ├── /modules                # مرزهای ماژولار دامنه‌ای (Bounded Contexts)
│     │     ├── /auth             # ماژول مدیریت نشست و OTP
│     │     ├── /users            # ماژول پروفایل و لیدربورد
│     │     ├── /routes           # ماژول لوپ‌ساز کیفی و متصل به Valhalla
│     │     ├── /exploration      # ماژول سشن زنده پیاده‌روی و وب‌سوکت
│     │     ├── /missions         # ماژول سیستم مأموریت‌ها و ژئوفنسینگ
│     │     └── /game_engine      # ماژول محاسبات XP، مدال‌ها و لول‌آپ
│     │
│     ├── /shared                 # کدهای اشتراکی فاقد منطق کسب‌وکار
│     │     ├── /utils            # توابع جنریک ریاضی و زمانی
│     │     └── /spatial_utils.py # ابزارهای فضایی فرار (Shapely, GeoJSON)
│     │
│     ├── /events                 # لایه مدیریت رویدادهای ناهمگام سیستم
│     │     ├── event_bus.py      # پیاده‌سازی درون‌حافظه‌ای الگوی Pub/Sub
│     │     └── tasks.py          # تعاریف کارهای پس‌زمینه Celery Worker
│     │
│     └── /api_v1                 # لایه کامپوزیشن و روت‌های اصلی APIRouter
│
├── /migrations                   # اسکریپت‌های مهاجرت دیتابیس Alembic
├── Dockerfile                    # مشخصات بیلد کانتینر اپلیکیشن
├── docker-compose.yml            # ارکستریشن محلی وابستگی‌ها (Postgres, Redis, Valhalla)
└── requirements.txt              # لیست پکیج‌های بیلد پروژه

```

*هر ماژول در دایرکتوری `/modules` شامل لایه‌های داخلی مجزا یعنی `router.py`, `service.py`, `models.py` و `repository.py` است.*

---

## ۴. کاتالوگ و مسئولیت ماژول‌های بک‌اند (Service Breakdown)

### ماتریس مالکیت داده و عملکرد ماژول‌ها

| نام ماژول | مسئولیت اصلی | وابستگی مستقیم | مالکیت جداول دیتابیس |
| :--- | :--- | :--- | :--- |
| **Auth Module** | احراز هویت، تایید OTP، نوسازی توکن‌ها | None | `users` |
| **Users Module** | پروفایل، لول، دارایی‌ها، لیدربورد | Auth | `profiles`, `earned_badges` |
| **Routes Module** | بیلد لوپ‌های داینامیک تجربه‌محور | Users, Map Engine | `routes`, `pois` |
| **Exploration Module**| مدیریت وب‌سوکت، پایش لوکیشن لایو | Routes, Game Engine | `exploration_sessions` |
| **Missions Module** | تخصیص مأموریت‌ها، پایش ژئوفنس فضایی | Exploration | `session_missions` |
| **Game Engine** | محاسبات XP، اعطای مدال، لول‌آپ | Users, Exploration | `game_events` |

---

## ۵. معماری لایه‌ای نرم‌افزار (Layered Architecture Flow)

پروژه جهت سادگی در توسعه و جداسازی کامل وظایف (Separation of Concerns)، از الگوی جریان چهار لایه‌ای زیر تبعیت می‌کند:


```

[Client App]
│
▼
[Controller / Router Layer (FastAPI)] : وظیفه: پارس کلاینت، ولیدیشن ساختار با Pydantic، مدیریت HTTP HTTP
│
▼
[Service Layer (Business Logic)]      : وظیفه: حاکمیت بر قوانین کسب‌وکار، مدیریت تراکنش‌ها، انتشار رویدادها
│
▼
[Repository Layer (Data Access)]      : وظیفه: انتزاع لایه ذخیره‌سازی، کوئری‌های خام SQL و هندسی PostGIS
│
▼
[Database / Infrastructure Layer]     : وظیفه: ماندگاری فیزیکی داده‌ها (PostgreSQL / Redis)

```

---

## ۶. پیاده‌سازی گام‌به‌گام جریان‌های اصلی (Core Backend Flows)

### جریان ناوبری زنده، افشای مه و پایش مأموریت (API Level Implementation)

```mermaid
sequenceDiagram
    autonumber
    actor App as کلاینت فلوتر موبایل
    participant WS as Exploration WS Handler
    participant Redis as Redis Buffer List
    participant Worker as Celery Background Worker
    participant PostGIS as PostGIS DB Layer
    participant Game as Game Engine Service
    
    App->{WSS Channel}: ارسال پکت موقعیت زنده (X, Y, Speed, Timestamp)
    {WSS Channel}->>WS: دریافت پکت توسط هندلر ناهمگام FastAPI
    WS->>Redis: دستور LPUSH به لیست موقت سشن (session:trace:id)
    Note over WS, Redis: پاسخ وب‌سوکت معطل پردازش دیتابیس نمی‌ماند (تحت 5ms)
    
    Cron Task (Every 30 Seconds)
    Worker->>Redis: دستور LRANGE & DEL برای تخلیه پکت‌های بافر ۳۰ ثانیه اخیر
    Redis-->>Worker: آرایه‌ای از نقاط پوزیشن عابر
    Worker->>PostGIS: ST_Contains(پوزیشن‌ها، زون‌های مأموریت فعال سشن)
    alt کاربر وارد ژئوفنس مأموریت شد
        PostGIS-->>Worker: تایید ورود فیزیکی به مرز گنج شهری
        Worker->>WS: ارسال سیگنال مستقیم زمان‌واقعی به هندلر وب‌سوکت
        WS-->>App: ارسال پکت زنده { event: "mission_triggered" }
    end
    Worker->>PostGIS: ST_Union(ST_Buffer(Points, 20), user_fog_map)
    PostGIS-->>Worker: بازگرداندن مساحت خالص جدید افشاشده
    Worker->>Game: پردازش رویداد و محاسبه دیسکاوری اسکور و XP جدید
    Game->>PostGIS: به‌روزرسانی تراکنشی جداول profiles و game_events
    Worker->>WS: ارسال سیگنال آپدیت امتیازات به هندلر وب‌سوکت
    WS-->>App: ارسال پکت زنده { event: "fog_cleared" + انیمیشن لایو }

```

---

## ۷. ساختار سیستم رویدادمحور ناهمگام (Event-Driven Backend Design)

* **زیرساخت Event Bus در MVP:** پیاده‌سازی بر پایه کارهای ناهمگام Celery با کانتینر Redis به عنوان پیام‌رسان (Broker).
* **مدل پردازش:** ناشر (Publisher) رویداد را بدون بلاک شدن رشته اصلی، به صف Redis ارسال می‌کند. کارگران Celery (Consumers) به صورت موازی پکت‌ها را برداشته و پردازش می‌کنند.

### نمونه کد امضای تسک‌های پس‌زمینه (Pseudo-code for Celery Workers)

```python
# app/events/tasks.py
from app.core.celery_app import celery_app
from app.modules.game_engine.service import GameEngineService
from app.modules.fog_war.spatial import FogWarProcessor

@celery_app.task(name="tasks.process_live_location_batch")
def process_live_location_batch(session_id: str, coordinates: list):
    """پردازش ناهمگام پکت‌های لوکیشن جهت افشای مه جنگ و پایش مأموریت"""
    # ۱. پردازش لایه هندسی مه جنگ
    unfogged_geojson, new_area = FogWarProcessor.unfog_path(session_id, coordinates)
    
    if new_area > 0:
        # ۲. محاسبه و توزیع پاداش‌ها در صورت کشف معبر جدید
        GameEngineService.distribute_exploration_rewards(session_id, new_area, unfogged_geojson)

@celery_app.task(name="tasks.trigger_llm_storytelling")
def trigger_llm_storytelling(route_id: str, user_id: str):
    """فراخوانی ناهمگام هوش مصنوعی جهت سناریونویسی داستان لوپ مسیر"""
    from app.modules.ai_engine.client import AIEngineClient
    AIEngineClient.generate_route_narrative(route_id, user_id)

```

---

## ۸. زیرساخت لایه ارتباطات زمان‌واقعی (Real-Time System Specification)

* **پروتکل لایه لایو:** WebSockets از طریق ماژول `FastAPI.WebSocket`.
* **مدیریت ارتباطات فعال:** بیلد کلاس `ConnectionManager` در حافظه رم جهت نگهداری دکشنری سشن‌های فعال (`dict[session_id, WebSocket]`).
* **مکانیزم بازگشت ایمن (Fallback):** در صورت قطع ناگهانی کانکشن وب‌سوکت به دلیل ضعف شبکه موبایل عابر، کلاینت فلوتر فوراً به فلو اکشن‌های RESTful (پوینت `/api/v1/exploration/ping-location`) سوییچ می‌کند تا هیچ دیتای موقعیتی Churn نگردد.

---

## ۹. پیاده‌سازی لایه اتصال به موتور مسیریابی (Valhalla Engine Integration)

بک‌اند مستقیماً با کانال HTTP موتور Valhalla که با دیتای لوکال OSM لود شده است، ارتباط برقرار می‌کند.

* **تزریق توابع هزینه داینامیک (Custom Costing Injection):** در زمان درخواست پوینت `/routes/generate`، سرویس بک‌اند متادیتای تگ‌های کیفی معابر را از PostGIS خوانده و به پکت بدنه ریکوئست Valhalla تحت پارامتر `costing_options` تزریق می‌کند تا مسیرها بر پایه کیفیت ($Quality Score$) لوپ شوند، نه زمان فیزیکی.

---

## ۱۰. استراتژی تراکنش‌ها و لایه پایگاه داده (Database Isolation Playbook)

* **قانون طلایی ماژولار مونوپلیت:** هیچ ماژولی حق نوشتن یا خواندن مستقیم از جداول ماژول دیگر را ندارد. ارتباط صرفاً از طریق توابع سرویس (`Service Interfaces`) یا رویدادها مجاز است.
* **مرز تراکنش‌ها (Transaction Boundaries):** تمام کارهای نوشتن لایه سرویس در بدنه بلاک متن مدیریت تراکنش SQLAlchemy تحت دستور `with db.begin():` کپسوله‌سازی می‌شوند تا پایداری داده‌ها (ACID) تضمین شود.

---

## ۱۱. برنامه فازبندی و توسعه نقشه راه MVP (MVP Roadmap Plan)

```
┌────────────────────────────────────────────────────────┐
│ MVP BACKEND IMPLEMENTATION PATH                        │
├────────────────────────────────────────────────────────┤
│ PHASE 1: Core Infra, Auth, Postgres, Valhalla Loop     │
│ PHASE 2: Celery Workers, PostGIS FOW, Game Rewards Core│
│ PHASE 3: WebSocket Streaming, Redis Buffer, Production │
└────────────────────────────────────────────────────────┘

```

### فاز ۱: زیرساخت پایه و روتینگ دایره‌ای (زمان تخمینی: ۲ هفته)

* استقرار دیتابیس PostgreSQL به همراه اکستنشن PostGIS.
* پیاده‌سازی سیستم احراز هویت OTP و صدور توکن‌های JWT.
* اتصال ماژول `routes` به موتور Valhalla جهت رندر لوپ‌های دایره‌ای بر پایه دیتای پایه OSM تهران.

### فاز ۲: گیمیفیکیشن، مأموریت و مه جنگ (زمان تخمینی: ۲ هفته)

* کانفیگ Celery Worker و Redis جهت پردازش کارهای ناهمگام.
* پیاده‌سازی توابع هندسی PostGIS برای محاسبه بافر مسیر و ادغام با پولیگون کلان کاربر (`user_fog_maps`).
* بیلد ماشین وضعیت مأموریت‌ها و منطق قطعی موتور بازی.

### فاز ۳: کانال وب‌سوکت و پایداری زمان‌واقعی (زمان تخمینی: ۱ هفته)

* پیاده‌سازی هندلر وب‌سوکت سشن پیاده‌روی زنده به همراه سیستم بافرینگ Redis.
* لود لایه امنیتی حریم خصوصی لوکیشن و امحای پکت‌های خطی.
* تست نهایی ۱۰۰ سناریوی خطا (Edge Cases) و استقرار کانتینریایز شده.

---

## ۱۲. بهینه‌سازی کارایی و پرفورمنس (Performance Tuning Strategy)

* **ایندکس‌های فضایی فرار:** استفاده الزامی از ایندکس‌های **GiST** بر روی تمام ستون‌های هندسی (`geometry`) جداول PostGIS جهت افزایش سرعت کوئری‌های شعاعی.
* **کاشی‌بندی هندسی (Geometric Tiling):** اعمال تابع `ST_Subdivide` بر روی پولیگون‌های بزرگ مه جنگ کاربران؛ تبدیل پولیگون‌های تو در توی سنگین به پولیگون‌های کوچک شکسته‌شده جهت ممانعت از کند شدن کوئری‌های `ST_Union`.

---

## ۱۳. مانیتورینگ و رویت‌پذیری سیستم (Observability Spec)

* **لایه لاگ‌نویسی (Logging):** استفاده از کتابخانه `Loguru` با فرمت ساختاری خروجی Structured JSON جهت پارس آسان در بسترهای لاگ‌سرور.
* **لایه پایش پرفورمنس (Metrics & Tracing):** ادغام پکیج `Prometheus FastAPI Instrumentator` جهت مانیتورینگ زنده نرخ خطاهای HTTP و زمان پاسخ‌دهی پوینت‌ها (Latency) زیر ۱۰۰ میلی‌ثانیه.

---

## ۱۴. استراتژی استقرار و زیرساخت داکر (Deployment Architecture Specification)

اپلیکیشن بک‌اند به همراه تمام وابستگی‌ها به صورت ۱۰۰٪ کانتینریایز شده بر بستر داکر (Docker) بیلد می‌شود.

### نمونه فایل بیلد رسمی (Production-ready Dockerfile)

```dockerfile
# Dockerfile
FROM python:3.11-slim-buster

WORKDIR /backend

# ۱. نصب پیش‌نیازهای فضایی سیستم‌عامل برای افزونه‌های هندسی پایتون
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# ۲. کانفیگ متغیرهای محیطی برای لایه کامپایل دیتای فضایی
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

```

---

## ۱۵. تحلیل ریسک‌های اجرایی لایه بک‌اند (Implementation Risks)

* **ریسک ۱: پیچیدگی افراطی زیرساخت داده در MVP (Over-engineering Risk)**
* *توضیح:* تلاش برای ورود ابزارهای توزیع‌شده کلان (مانند Kafka یا میکروسرویس‌های خالص) در فازهای اول، تیم را زمین‌گیر کرده و لود توسعه را به شدت بالا می‌برد.
* *راهکار کاهش ریسک (Mitigation):* اتکای مطلق به ساختار **Modular Monolith** و کارهای ناهمگام **Celery/Redis**. این مدل سادگی بی‌پایانی در توسعه ایجاد می‌کند در حالی که به دلیل ایزولاسیون کامل مرز کدهای ماژولار، معماری سیستم آماده هجرت بدون دردسر به کلاسترهای کوبرنتیز در آینده خواهد بود.



---

## بخش‌های ساختاری و متادیتای سند (Metadata)

### Dependencies (وابستگی‌ها)

* این سند برنامه اجرایی کدهای خود را مستقیماً از پوینت‌های واسط کاربری `07_API_Design.md` و ساختار اسکیماهای فیزیکی قفل‌شده در لایه دیتابیس `08_Data_Architecture_and_Database_Design.md` استخراج کرده است.

### Affected Documents (مستندات تحت تأثیر)

تصویب این داک اجرایی، فرآیندهای زیر را وارد فاز پیاده‌سازی می‌کند:

* `11_CI_CD_Pipeline_Configuration.yml` (بیلد اسکریپت‌های اتوماسیون تست و استقرار کانتینرها بر پایه Dockerfile این داک).
* `12_Sprint_Backlog_Tasks.md` (تولید ریز تسک‌های مهندسی جیرا بر پایه بخش ۱۲ نقشه راه MVP).

### Assumptions (فرضیات اساسی)

* فرض اجرایی بر این است که تیم توسعه بک‌اند تسلط کاملی بر کارهای ناهمگام (Async Python) و مفاهیم پایگاه داده‌های فضایی PostGIS داراست.

### Open Questions (سوالات باز)

* آیا در کانتینر داکر پروداکشن، پایش وضعیتWorkers Celery با ابزار Flower به صورت پیش‌فرض فعال باشد یا از سیستم‌های لاگ متمرکز برای خطایابی کارهای پس‌زمینه استفاده شود؟ (پیش‌نهاد فعلی: فعال‌سازی موقت Flower در فاز آلفا).

### Definition of Done (تعریف پایان کار سند)

* این سند زمانی به وضعیت Done می‌رسد که کل ساختار پوشه‌ها، جریان‌های ترتیبی انتقال پکت‌های وب‌سوکت و نقشه توسعه گام‌های MVP به تایید نهایی تیم مهندسی بک‌اند رسیده و پروژه آماده آغاز دستور اولین کامیت (First Commit) در ریپازیتوری گیت باشد.

---

*این مستند برنامه جامع اجرایی لایه بک‌اند پلتفرم با رعایت کامل اصول و قوانین ۱۲گانه همکاری تایید و قفل گردید.*

```

```