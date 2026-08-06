# Urban Exploration Game Platform

پلتفرم جهانی اکتشاف شهری بازی‌وارشده (Gamified Urban Exploration Platform). 
این سیستم مقصدهای سنتی را حذف کرده و فضاها و معابر کلان‌شهرها را به یک نقشه بازی جهان‌باز (Open-World Map) تبدیل می‌کند تا با استفاده از الگوریتم‌های تجربه‌محور، حس کاوش و سلامت روان شهری را ارتقا دهد.

## ساختار پروژه (Project Structure)

این مخزن بر اساس معماری مونو-ریپو (Mono-repo) و با استانداردهای سطح Enterprise برای مقیاس‌پذیری بالا سازمان‌دهی شده است.

* `/docs` : اسناد معماری، طراحی دامنه، نقشه‌راه و تصمیمات کلیدی (ADRs).
* `/backend` : هسته Modular Monolith با استفاده از Python، FastAPI، PostGIS و Celery.
* `/mobile` : اپلیکیشن کلاینت با استفاده از Flutter، MapLibre و الگوی Clean Architecture (BLoC).
* `/infrastructure` : کدهای IaC شامل Terraform، مانیفست‌های Kubernetes و تنظیمات Docker.
* `/.github` : خطوط لوله CI/CD (GitHub Actions) برای تست، بیلد و استقرار یکپارچه.
* `/scripts` : اسکریپت‌های اتوماسیون وظایف روزمره، مهاجرت دیتابیس و مدیریت محیط.
* `/configs` : فایل‌های پیکربندی سرویس‌های زیرساختی نظیر Nginx، Valhalla و Redis.
* `/assets` : منابع گرافیکی، آیکون‌ها، فونت‌ها و افکت‌های صوتی سیستم بازی‌وارسازی.

## اسناد مرجع

برای درک کامل اهداف، اصول و معماری این پروژه، لطفاً فایل [14_Master_Blueprint.md](docs/14_Master_Blueprint.md) را به عنوان نقطه ورود (Single Source of Truth) مطالعه نمایید.