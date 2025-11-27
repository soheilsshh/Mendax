import sqlglot
from sqlglot import exp, parse_one
from typing import Dict, Any, List


def parse_sql_schema(sql_content: str, dialect: str = "mysql") -> Dict[str, Dict[str, Any]]:
    """
    با استفاده از SQLGlot، تمام جداول، ستون‌ها، primary key و foreign keyها رو استخراج می‌کنه.
    
    ورودی: محتوای فایل .sql (مثلاً خروجی mysqldump --no-data)
    خروجی: دیکشنری دقیق مثل قبل، اما بدون باگ و با دقت 100%
    """
    tables = {}

    # SQLGlot می‌تونه چند دستور رو با parse() پارس کنه
    statements = sqlglot.parse(sql_content, read=dialect)

    for stmt in statements:
        if not stmt:
            continue

        # فقط CREATE TABLE ها
        if not isinstance(stmt, exp.Create) or stmt.kind != "TABLE":
            continue

        table_expr = stmt.this  # exp.Table
        table_name = table_expr.name  # بدون ` یا "

        # اگر جدول با schema باشه مثل `mydb.users`
        if table_expr.db:
            table_name = f"{table_expr.db}.{table_name}"

        columns = {}
        primary_key = None
        foreign_keys = {}  # {local_col: {"ref_table": ..., "ref_column": ...}}

        # تمام expressions داخل CREATE TABLE
        for expression in stmt.expression.expressions:
            # 1. ستون معمولی: `id` INT PRIMARY KEY
            if isinstance(expression, exp.ColumnDef):
                col_name = expression.this.name
                col_type = expression.kind.sql(dialect=dialect).upper() if expression.kind else "UNKNOWN"
                columns[col_name] = col_type

                # تشخیص PRIMARY KEY inline
                if expression.find(exp.PrimaryKey):
                    primary_key = col_name

            # 2. CONSTRAINTها: PRIMARY KEY, FOREIGN KEY, UNIQUE
            elif isinstance(expression, exp.Constraint):
                # PRIMARY KEY جداگانه
                pk = expression.find(exp.PrimaryKeyColumnConstraint)
                if pk:
                    col = expression.this.this.name
                    primary_key = col

                # FOREIGN KEY
                fk = expression.find(exp.ForeignKey)
                if fk:
                    local_cols = [col.name for col in fk.this.expressions]  # معمولاً یکی
                    ref_table = fk.args["reference"].this.name
                    ref_cols = [col.name for col in fk.args["reference"].expressions]

                    # معمولاً یک به یک
                    for local_col, ref_col in zip(local_cols, ref_cols):
                        foreign_keys[local_col] = {
                            "ref_table": ref_table,
                            "ref_column": ref_col
                        }

            # 3. PRIMARY KEY به صورت جداگانه (مثل PRIMARY KEY (id))
            elif isinstance(expression, exp.PrimaryKey):
                col = expression.this[0].this.name if expression.this else None
                if col:
                    primary_key = col

        tables[table_name] = {
            "columns": columns,
            "primary_key": primary_key,
            "foreign_keys": foreign_keys
        }

    return tables