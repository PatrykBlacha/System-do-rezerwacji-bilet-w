from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('tickets_app', '0005_correct_single_ticket_procedures'),
    ]

    operations = [
        # purchase_ticket: osoba; bilet
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE FUNCTION purchase_ticket(p_client_id BIGINT, p_ticket_id BIGINT)
                RETURNS VOID AS $$
                DECLARE
                    v_status TEXT;
                    v_order_id BIGINT;
                BEGIN
                    SELECT status INTO v_status
                    FROM tickets
                    WHERE id = p_ticket_id
                    FOR UPDATE;

                    IF v_status != 'available' THEN
                        RAISE EXCEPTION 'Ticket % is not available.', p_ticket_id;
                    END IF;

                    UPDATE tickets
                    SET status = 'sold'
                    WHERE id = p_ticket_id;

                    -- Tworzenie zamówienia
                    INSERT INTO orders (user_id, status, created_at, updated_at)
                    VALUES (NULL, 'completed', NOW(), NOW())
                    RETURNING id INTO v_order_id;

                    -- Szczegóły zamówienia
                    INSERT INTO orders_details (order_id, client_id, ticket_id, ticket_uuid)
                    VALUES (v_order_id, p_client_id, p_ticket_id, gen_random_uuid());
                END;
                $$ LANGUAGE plpgsql;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS purchase_ticket(BIGINT, BIGINT);"
        ),

        # cancel_order: tylko order_id
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE FUNCTION cancel_order(p_order_id BIGINT)
                RETURNS VOID AS $$
                DECLARE
                    v_ticket_id BIGINT;
                    v_status TEXT;
                BEGIN
                    SELECT o.status, od.ticket_id INTO v_status, v_ticket_id
                    FROM orders o
                    JOIN orders_details od ON o.id = od.order_id
                    WHERE o.id = p_order_id
                    FOR UPDATE;

                    IF v_status != 'completed' THEN
                        RAISE EXCEPTION 'Only completed orders can be canceled.';
                    END IF;

                    UPDATE orders
                    SET status = 'canceled', updated_at = NOW()
                    WHERE id = p_order_id;

                    UPDATE tickets
                    SET status = 'available'
                    WHERE id = v_ticket_id;
                END;
                $$ LANGUAGE plpgsql;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS cancel_order(BIGINT);"
        ),
    ]
