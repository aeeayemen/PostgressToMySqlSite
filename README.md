# PostgreSQL to MySQL Converter

أداة ويب احترافية لتحويل قواعد بيانات PostgreSQL إلى صيغة متوافقة مع MySQL مع واجهة مستخدم عصرية وأداء عالي.

## Description | الوصف

English:
A professional web-based tool designed to convert PostgreSQL SQL dumps to MySQL-compatible format. It automatically fixes syntax incompatibilities, handles reserved keywords, converts boolean values, and preserves JSON data integrity.

العربية:
أداة ويب احترافية لتحويل ملفات وقواعد بيانات PostgreSQL إلى صيغة متوافقة مع MySQL. تقوم الأداة بمعالجة المشاكل الشائعة تلقائياً مثل الكلمات المحجوزة، تحويل القيم المنطقية، وحماية بيانات JSON، مع إمكانية استخراج البيانات فقط في ملف منفصل.

## Key Features | المميزات الرئيسية

- Smart Identifier Backticking: Converts reserved words like "order" to `order`. | معالجة الكلمات المحجوزة تلقائياً.
- Boolean Transformation: Converts TRUE/FALSE to 1/0. | تحويل القيم المنطقية.
- JSON Integrity Protection: Safely preserves double-quotes inside JSON strings. | حماية سلامة بيانات JSON.
- Timezone Cleanup: Removes PostgreSQL specific timezone offsets from timestamps. | تنظيف الطوابع الزمنية.
- Data-Only Extraction: Option to download only INSERT statements as a separate file. | خيار استخراج البيانات فقط في ملف منفصل.
- Zero-Dependency Backend: Built using native Python modules for maximum compatibility. | يعمل السيرفر بدون الحاجة لتركيب مكتبات خارجية.
- Modern UI: React-based frontend with Cairo font and FontAwesome icons. | واجهة مستخدم متطورة بخط كايرو.

## Tech Stack | التقنيات المستخدمة

- Backend: Python 3 (http.server)
- Frontend: React 19 (Vite)
- Styling: Vanilla CSS (Custom Design System)
- Icons: Font Awesome 6
- Fonts: Cairo (Google Fonts)

## How to Use | طريقة الاستخدام

### Prerequisites | المتطلبات
- Python 3.x Installed.

### Steps | الخطوات
1. Clone the repository to your local machine. | قم بتحميل الملفات لجهازك.
2. Run the server using terminal: | قم بتشغيل السيرفر من خلال التيرمينال:
   ```bash
   python backend/app.py
   ```
3. Open your browser and visit: | افتح المتصفح وادخل للرابط:
   http://localhost:5000
4. Upload your .sql file and click "Start Convert". | ارفع الملف واضغط على "بدء التحويل".
5. Download the result files after processing is done. | قم بتحميل الملفات الناتجة بعد الانتهاء.

## Developed By
Antigravity AI
