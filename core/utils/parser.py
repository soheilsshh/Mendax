import sqlglot
from sqlglot import exp
from typing import Dict, Any


def parse_sql_schema(sql_content: str, dialect: str = "mysql") -> Dict[str, Dict[str, Any]]:
    tables = {}

    statements = sqlglot.parse(sql_content, read=dialect)

    for stmt in statements:
        if not stmt or not isinstance(stmt, exp.Create) or stmt.kind != "TABLE":
            continue

        # این خط کلید حل مشکله — table_expr همیشه exp.Table هست
        table_expr: exp.Table = stmt.this

        # استفاده از متدهای () که همیشه وجود دارن و "" برمی‌گردونن اگر خالی باشه
        catalog = table_expr.catalog() or ""
        db = table_expr.db() or ""
        table_name = table_expr.name

        full_table_name = ".".join(filter(None, [catalog, db, table_name]))

        columns = {}
        primary_key = None
        foreign_keys = {}

        for expression in stmt.expression.expressions:

            # 1. ستون معمولی
            if isinstance(expression, exp.ColumnDef):
                col_name = expression.this.name
                col_type = str(expression.kind).upper() if expression.kind else "UNKNOWN"
                columns[col_name] = col_type

                if expression.find(exp.PrimaryKeyColumnConstraint):
                    primary_key = col_name

            # 2. CONSTRAINTها (FOREIGN KEY, PRIMARY KEY)
            elif isinstance(expression, exp.Constraint):
                # FOREIGN KEY
                fk = expression.find(exp.ForeignKey)
                if fk:
                    local_cols = [c.name for c in fk.this.expressions]
                    ref_table_expr: exp.Table = fk.args["reference"].this
                    ref_table = ".".join(filter(None, [
                        ref_table_expr.catalog() or "",
                        ref_table_expr.db() or "",
                        ref_table_expr.name
                    ]))
                    ref_cols = [c.name for c in fk.args["reference"].expressions]

                    for local, ref in zip(local_cols, ref_cols):
                        foreign_keys[local] = {
                            "ref_table": ref_table,
                            "ref_column": ref
                        }

                # PRIMARY KEY داخل CONSTRAINT
                if expression.find(exp.PrimaryKeyColumnConstraint):
                    if expression.this and hasattr(expression.this, "this"):
                        primary_key = expression.this.this.name

            # 3. PRIMARY KEY مستقیم
            elif isinstance(expression, exp.PrimaryKey):
                if expression.this and expression.this:
                    primary_key = expression.this[0].this.name

        # اگر primary key پیدا نشد، اولین ستون رو بذار
        if not primary_key and columns:
            primary_key = next(iter(columns))

        tables[full_table_name] = {
            "columns": columns,
            "primary_key": primary_key,
            "foreign_keys": foreign_keys
        }

    return tables