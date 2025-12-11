# Mendax - Smart Dummy Data Generator for Databases

<div dir="rtl">

# منداکس - تولیدکننده هوشمند داده‌های تست برای دیتابیس

</div>

Mendax یک ابزار قدرتمند و هوشمند برای تولید داده‌های تست (dummy data) برای دیتابیس‌های SQL است. این پروژه با استفاده از Django و معماری مدرن، قابلیت پارس کردن اسکیما SQL، تحلیل وابستگی‌های جداول، و تولید داده‌های واقع‌گرا را فراهم می‌کند.

## 📋 فهرست مطالب

- [ویژگی‌ها](#ویژگی‌ها)
- [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
- [استفاده سریع](#استفاده-سریع)
- [مثال‌های استفاده](#مثال‌های-استفاده)
- [معماری پروژه](#معماری-پروژه)
- [API Documentation](#api-documentation)
- [تست‌ها](#تست‌ها)
- [مشارکت](#مشارکت)

## ✨ ویژگی‌ها

### 🔍 پارس هوشمند SQL Schema
- پشتیبانی کامل از دستورات `CREATE TABLE`
- استخراج خودکار ستون‌ها، انواع داده، Primary Keys و Foreign Keys
- پشتیبانی از backticks و نام‌های خاص
- تشخیص و نادیده گرفتن constraint‌ها (KEY, INDEX, UNIQUE, CHECK)

### 🔗 تحلیل وابستگی‌ها
- ساخت گراف وابستگی با استفاده از NetworkX
- محاسبه ترتیب درج صحیح جداول با Topological Sort
- تشخیص وابستگی‌های حلقوی (Circular Dependencies)
- پشتیبانی از Foreign Key های پیچیده و چندگانه

### 🎲 تولید داده‌های واقع‌گرا
- استفاده از **Faker** برای تولید داده‌های واقع‌گرا
- **تشخیص هوشمند نوع فیلد** از نام ستون (email, username, phone, etc.)
- پشتیبانی از انواع مختلف SQL (INT, VARCHAR, TEXT, DATETIME, JSON, etc.)
- مدیریت خودکار Foreign Keys با ارجاع به Primary Keys تولید شده
- پشتیبانی از Auto-increment برای Primary Keys
- امکان تنظیم احتمال NULL برای Foreign Keys قابل null

### 📤 خروجی SQL
- تولید خودکار دستورات `INSERT` آماده برای اجرا
- رعایت ترتیب درج صحیح (مطابق dependency graph)
- Escape کردن صحیح مقادیر string
- پشتیبانی از چندین SQL dialect (MySQL, PostgreSQL)

### 🏗️ معماری مدرن
- **Service Layer Pattern** برای orchestration
- **Strategy Pattern** برای field generators
- **Builder Pattern** برای SQL export
- **Class-based Graph** برای dependency management
- Configuration قابل تنظیم
- Custom Exceptions برای error handling بهتر

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها

- Python 3.8+
- pip
- (اختیاری) Redis برای Celery

### نصب

1. کلون کردن یا دانلود پروژه:
```bash
git clone <repository-url>
cd Mendax
```

2. ایجاد virtual environment (توصیه می‌شود):
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. نصب dependencies:
```bash
pip install -r requirements.txt
```

4. اجرای migrations (برای Django):
```bash
python manage.py migrate
```

5. (اختیاری) راه‌اندازی Redis برای Celery:
```bash
# Windows: دانلود و نصب Redis
# Linux/Mac: 
sudo apt-get install redis-server
redis-server
```

## 💻 استفاده سریع

### مثال 1: استفاده ساده

```python
from core.services.schema_service import SchemaService

# SQL schema شما
sql_content = """
CREATE TABLE countries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  code CHAR(2)
);

CREATE TABLE users (
  id INT PRIMARY KEY,
  username VARCHAR(50),
  email VARCHAR(255),
  country_id INT,
  FOREIGN KEY (country_id) REFERENCES countries(id)
);
"""

# ایجاد service و تولید داده
service = SchemaService()
result = service.process_schema(sql_content, num_records=100, export_sql=True)

# دسترسی به داده‌ها
data = result['data']           # داده‌های تولید شده
sql = result['sql']             # SQL INSERT statements
order = result['insertion_order']  # ترتیب درج جداول
```

### مثال 2: با Configuration سفارشی

```python
from core.services.schema_service import SchemaService
from core.utils.generators.config import GeneratorConfig

# تنظیمات سفارشی
config = GeneratorConfig(
    locale='fa_IR',              # زبان فارسی
    seed=42,                     # Seed برای داده‌های قابل تکرار
    nullable_fk_probability=0.2  # 20% احتمال NULL برای FK
)

service = SchemaService(generator_config=config)
result = service.process_schema(sql_content, num_records=50)
```

### مثال 3: استفاده از Generator به صورت مستقیم

```python
from core.utils.generators.data_generator import DataGenerator
from core.utils.generators.config import GeneratorConfig

config = GeneratorConfig(seed=42)
generator = DataGenerator(config)
data = generator.generate(sql_content, num_records=100)
```

### مثال 4: استفاده از Graph

```python
from core.utils.graph.dependency_graph import DependencyGraph
from core.utils.parser import parse_sql_schema

# Parse schema
schema = parse_sql_schema(sql_content)

# ساخت graph
graph = DependencyGraph(schema)

# دریافت ترتیب درج
order = graph.get_insertion_order()

# بررسی cycles
has_cycles = graph.has_cycles()

# دریافت وابستگی‌های یک جدول
dependencies = graph.get_dependencies('users')
```

## 📚 مثال‌های استفاده

### مثال کامل: از Schema تا SQL

```python
from core.services.schema_service import SchemaService

sql_content = """
CREATE TABLE `countries` (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  code CHAR(2) UNIQUE
);

CREATE TABLE cities (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255),
  country_id INT,
  FOREIGN KEY (country_id) REFERENCES countries(id)
);

CREATE TABLE users (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE,
  email VARCHAR(255),
  city_id BIGINT,
  FOREIGN KEY (city_id) REFERENCES cities(id)
);
"""

service = SchemaService()
result = service.process_schema(sql_content, num_records=1000, export_sql=True)

# ذخیره SQL در فایل
with open('insert_data.sql', 'w', encoding='utf-8') as f:
    f.write(result['sql'])

print(f"Generated {result['metadata']['total_records']} records")
print(f"Insertion order: {result['insertion_order']}")
```

## 🏛️ معماری پروژه

### ساختار دایرکتوری

```
Mendax/
├── core/                       # اپلیکیشن اصلی Django
│   ├── exceptions.py           # Custom exceptions
│   ├── models.py               # Django models
│   ├── services/               # Service Layer
│   │   └── schema_service.py  # Main orchestrator
│   └── utils/                  # Utilities
│       ├── parser.py           # SQL parser
│       ├── generators/         # Data generation
│       │   ├── config.py
│       │   ├── data_generator.py
│       │   └── field_generators.py
│       ├── graph/              # Dependency graph
│       │   └── dependency_graph.py
│       └── exporters/          # SQL export
│           └── sql_exporter.py
├── tests/                      # تست‌ها
│   ├── test_parser_unit.py
│   ├── demo_generator_flow.py
│   └── example_service_usage.py
└── requirements.txt
```

### الگوهای طراحی

1. **Service Layer Pattern**: `SchemaService` تمام workflow را orchestrate می‌کند
2. **Strategy Pattern**: هر نوع فیلد SQL یک generator strategy جداگانه دارد
3. **Builder Pattern**: `SQLInsertBuilder` برای ساخت SQL statements
4. **Factory Pattern**: `FieldGeneratorFactory` استراتژی مناسب را انتخاب می‌کند

## 📖 API Documentation

### SchemaService

کلاس اصلی برای استفاده از Mendax.

```python
class SchemaService:
    def __init__(
        self,
        generator_config: Optional[GeneratorConfig] = None,
        sql_dialect: str = 'mysql'
    )
    
    def process_schema(
        self,
        sql_content: str,
        num_records: int = 100,
        export_sql: bool = False
    ) -> Dict[str, Any]
    
    def parse_only(self, sql_content: str) -> Dict[str, Any]
    def generate_only(self, sql_content: str, num_records: int = 100) -> Dict
    def export_only(self, data, schema, insertion_order) -> str
```

### GeneratorConfig

تنظیمات برای تولید داده.

```python
@dataclass
class GeneratorConfig:
    locale: str = 'en_US'                    # Faker locale
    seed: Optional[int] = None                # Random seed
    nullable_fk_probability: float = 0.3      # احتمال NULL برای FK
```

### DependencyGraph

مدیریت گراف وابستگی جداول.

```python
class DependencyGraph:
    def __init__(self, tables: Dict[str, Dict[str, Any]])
    def get_insertion_order(self) -> List[str]
    def has_cycles(self) -> bool
    def get_dependencies(self, table_name: str) -> List[str]
    def get_dependents(self, table_name: str) -> List[str]
    def get_cycles(self) -> List[List[str]]
```

## 🧪 تست‌ها

اجرای تست‌ها:

```bash
# اجرای همه تست‌ها
python tests/test_parser_unit.py

# با verbose output
python tests/test_parser_unit.py -v

# اجرای demo
python tests/demo_generator_flow.py

# مثال استفاده
python tests/example_service_usage.py
```

## 🔧 پشتیبانی از انواع SQL

### انواع داده پشتیبانی شده

- **Integer**: INT, INTEGER, BIGINT, SMALLINT, TINYINT, MEDIUMINT
- **Decimal**: DECIMAL, NUMERIC, FLOAT, DOUBLE, REAL
- **String**: VARCHAR, CHAR, TEXT, TINYTEXT, MEDIUMTEXT, LONGTEXT
- **Date/Time**: DATE, TIME, DATETIME, TIMESTAMP, YEAR
- **Boolean**: BOOLEAN, BOOL, BIT
- **Other**: JSON, UUID

### تشخیص هوشمند فیلدها

Mendax به صورت خودکار نوع فیلد را از نام ستون تشخیص می‌دهد:

- `email` → آدرس ایمیل
- `username` → نام کاربری
- `phone` → شماره تلفن
- `name` → نام
- `created_at`, `updated_at` → تاریخ/زمان
- `password`, `hash` → رمز عبور
- و غیره...

## 🎯 کاربردها

- **تست نرم‌افزار**: تولید داده‌های تست برای unit tests و integration tests
- **توسعه**: پر کردن دیتابیس با داده‌های نمونه برای توسعه
- **دمو**: ایجاد دیتابیس نمونه برای نمایش به مشتری
- **آموزش**: تولید داده‌های آموزشی برای یادگیری SQL
- **Performance Testing**: تولید حجم زیادی از داده برای تست عملکرد

## 🛠️ تکنولوژی‌های استفاده شده

- **Django 5.2**: Framework اصلی
- **Faker**: تولید داده‌های واقع‌گرا
- **NetworkX**: تحلیل گراف وابستگی
- **sqlparse**: پارس SQL
- **Celery**: پردازش async (برای آینده)
- **Redis**: Message broker برای Celery

## 📝 مثال خروجی

```sql
-- Generated INSERT statements
-- Generated at: 2025-12-11 17:37:00
-- Total tables: 2
-- Total records: 10

INSERT INTO countries (id, name, code) VALUES (1, 'United States', 'US');
INSERT INTO countries (id, name, code) VALUES (2, 'Canada', 'CA');
...

INSERT INTO users (id, username, email, country_id) VALUES (1, 'john_doe', 'john@example.com', 1);
INSERT INTO users (id, username, email, country_id) VALUES (2, 'jane_smith', 'jane@example.com', 2);
...
```

## 🤝 مشارکت

برای مشارکت در پروژه:

1. Fork کنید
2. Branch جدید بسازید (`git checkout -b feature/amazing-feature`)
3. تغییرات را commit کنید (`git commit -m 'Add amazing feature'`)
4. Push کنید (`git push origin feature/amazing-feature`)
5. Pull Request باز کنید

## 📄 لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.

## 👤 نویسنده

Mendax Project

## 🙏 تشکر

- [Faker](https://github.com/joke2k/faker) برای تولید داده‌های واقع‌گرا
- [NetworkX](https://networkx.org/) برای تحلیل گراف
- [sqlparse](https://github.com/andialbrecht/sqlparse) برای پارس SQL
- [Django](https://www.djangoproject.com/) برای framework قدرتمند

---

<div dir="rtl">

**نکته**: این پروژه در حال توسعه است و ممکن است تغییرات زیادی داشته باشد.

</div>

**Note**: This project is under active development and may have breaking changes.

