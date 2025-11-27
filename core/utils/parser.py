import sqlglot
from sqlglot import exp
from typing import Dict, Any


def parse_sql_schema(sql_content: str, dialect: str = "mysql") -> Dict[str, Dict[str, Any]]:

    tables = {}

    # همه دستورات CREATE TABLE رو پیدا کن
    for stmt in sqlglot.parse(sql_content, read=dialect):
        if not stmt or not isinstance(stmt, exp.Create) or stmt.kind != "TABLE":
            continue

        # نام جدول رو خیلی ساده و امن بگیر (حتی اگر `users` یا users یا `mydb`.`users`)
        table_name = stmt.this.name if hasattr(stmt.this, "name") else "unknown_table"
        # اگر schema هم داشت (مثل mydb.users) فقط اسم جدول رو نگه دار
        if "." in table_name:
            table_name = table_name.split(".")[-1]
        table_name = table_name.strip('`"\'')  # حذف ` " '

        columns = {}
        primary_key = None
        foreign_keys = {}

        # تمام چیزایی که داخل پرانتز هست
        for expr in stmt.expression.expressions:

            # ستون معمولی: id INT, name VARCHAR(255)
            if isinstance(expr, exp.ColumnDef):
                col_name = expr.this.name
                col_type = str(expr.kind).upper() if expr.kind else "UNKNOWN"
                columns[col_name] = col_type

                # اگر PRIMARY KEY داخل ستون بود
                if expr.find(exp.PrimaryKeyColumnConstraint):
                    primary_key = col_name

            # FOREIGN KEY — مهم‌ترین بخش
            elif isinstance(expr, exp.ForeignKey):
                local_cols = [c.name for c in expr.this.expressions]
                ref_table = expr.args["reference"].this.name
                if "." in ref_table:
                    ref_table = ref_table.split(".")[-1]  # فقط اسم جدول
                ref_table = ref_table.strip('`"\'')
                ref_cols = [c.name for c in expr.args["reference"].expressions]

                for local, ref_col in zip(local_cols, ref_cols):
                    foreign_keys[local] = {
                        "ref_table": ref_table,
                        "ref_column": ref_col
                    }

            # PRIMARY KEY جداگانه: PRIMARY KEY (id)
            elif isinstance(expr, exp.PrimaryKey):
                if expr.this:
                    primary_key = expr.this[0].this.name

        # اگر هیچ PK پیدا نشد، اولین ستون رو PK فرض کن (برای تست)
        if not primary_key and columns:
            primary_key = next(iter(columns))

        tables[table_name] = {
            "columns": columns,
            "primary_key": primary_key,
            "foreign_keys": foreign_keys
        }

    return tables