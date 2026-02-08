from sqlalchemy import event


def test_entities_list_uses_bounded_number_of_queries(client, db_with_casp_data):
    engine = db_with_casp_data.get_bind()
    select_statements = []

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            select_statements.append(statement)

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        response = client.get("/api/entities?register_type=casp&limit=100")
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 3

    # Regression guard: list endpoint should not run per-entity lazy-load SELECTs.
    assert len(select_statements) <= 12, (
        f"Expected <=12 SELECT statements, got {len(select_statements)}"
    )
