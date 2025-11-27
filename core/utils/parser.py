import sqlglot
from sqlglot.expressions import Create, ColumnDef, ForeignKey


def parse_sql_schema(sql: str):
    result = {}

    # پارس کل SQL و استخراج AST
    expressions = sqlglot.parse(sql)

    for expr in expressions:
        if isinstance(expr, Create):
            table_name = expr.this.name
            result[table_name] = {
                "columns": {},
                "primary_key": None,
                "foreign_keys": {}
            }

            # پیمایش عناصر داخل CREATE TABLE
            for col in expr.expression.expressions:
                # --- ستون‌ها ---
                if isinstance(col, ColumnDef):
                    col_name = col.name
                    col_type = col.args.get("kind")
                    result[table_name]["columns"][col_name] = col_type.sql()

                    # چک کردن PRIMARY KEY داخل تعریف ستون
                    if col.args.get("constraints"):
                        for c in col.args["constraints"]:
                            if c.__class__.__name__ == "PrimaryKeyColumnConstraint":
                                result[table_name]["primary_key"] = col_name

                # --- FOREIGN KEY ها ---
                if isinstance(col, ForeignKey):
                    fk_column = col.expression.this.name
                    ref_table = col.references.this.name
                    ref_column = col.references.expression.this.name

                    result[table_name]["foreign_keys"][fk_column] = {
                        "ref_table": ref_table,
                        "ref_column": ref_column
                    }

            # اگر Primary Key در ستون‌ها نبود، از table-level constraint پیدا کن
            if not result[table_name]["primary_key"]:
                for c in expr.expression.args.get("constraints", []):
                    if c.__class__.__name__ == "PrimaryKey":
                        result[table_name]["primary_key"] = c.expressions[0].name

    return result