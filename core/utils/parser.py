import sqlglot
from sqlglot import exp
from typing import Dict, Any


def parse_sql_schema(sql_content: str, dialect: str = "mysql") -> Dict[str, Dict[str, Any]]:

    tables = {}

    # sqlglot.parse چندین دستور رو قبول می‌کنه
    statements = sqlglot.parse(sql_content, read=dialect)

    for stmt in statements:
        if not stmt:
            continue

        # فقط CREATE TABLE ها
        if not isinstance(stmt, exp.Create) or stmt.kind != "TABLE":
            continue

        table_expr: exp.Table = stmt.this

        # ساخت نام کامل جدول: catalog.db.table یا db.table یا فقط table
        parts = [part for part in [table_expr.catalog, table_expr.db, table_expr.name] if part]
        table_name = ".".join(parts)

        columns = {}
        primary_key = None
        foreign_keys = {}  # {local_column: {"ref_table": ..., "ref_column": ...}}

        # تمام تعاریف داخل پرانتز CREATE TABLE
        for expression in stmt.expression.expressions:

            # 1. تعریف ستون: `id INT PRIMARY KEY, name VARCHAR(255)
            if isinstance(expression, exp.ColumnDef):
                col_name = expression.this.name
                col_type = str(expression.kind).upper() if expression.kind else "UNKNOWN"
                columns[col_name] = col_type

                # اگر PRIMARY KEY داخل تعریف ستون باشه
                if expression.find(exp.PrimaryKeyColumnConstraint):
                    primary_key = col_name

            # 2. CONSTRAINT جداگانه: PRIMARY KEY (id), FOREIGN KEY (...), UNIQUE (...)
            elif isinstance(expression, exp.Constraint):
                # PRIMARY KEY
                pk_constraint = expression.find(exp.PrimaryKeyColumnConstraint)
                if pk_constraint:
                    # معمولاً داخل expression.this.this هست
                    if expression.this and hasattr(expression.this, "this"):
                        primary_key = expression.this.this.name

                # FOREIGN KEY
                fk = expression.find(exp.ForeignKey)
                if fk:
                    # ستون‌های محلی
                    local_cols = [col.name for col in fk.this.expressions]
                    # جدول و ستون مرجع
                    ref_table_expr = fk.args["reference"].this
                    ref_table = ".".join(
                        [p for p in [ref_table_expr.catalog, ref_table_expr.db, ref_table_expr.name] if p]
                    )
                    ref_cols = [col.name for col in fk.args["reference"].expressions]

                    for local_col, ref_col in zip(local_cols, ref_cols):
                        foreign_keys[local_col] = {
                            "ref_table": ref_table,
                            "ref_column": ref_col
                        }

            # 3. PRIMARY KEY به صورت مستقیم: PRIMARY KEY (id)
            elif isinstance(expression, exp.PrimaryKey):
                if expression.this and len(expression.this) > 0:
                    primary_key = expression.this[0].this.name

        # اگر primary key پیدا نشد، اولین ستون رو در نظر گرفته بشه (رایج در تست‌ها)
        if not primary_key and columns:
            primary_key = next(iter(columns))

        tables[table_name] = {
            "columns": columns,
            "primary_key": primary_key,
            "foreign_keys": foreign_keys
        }

    return tables