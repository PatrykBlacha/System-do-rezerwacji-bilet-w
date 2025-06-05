from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('tickets_app', '0002_create_views'),
    ]

    operations = [
        #Wywołanie: osoba; bilet
        migrations.RunSQL(
            sql="""
            -- purchase_ticket function
            CREATE OR REPLACE FUNCTION purchase_ticket(p_client_id BIGINT, p_ticket_id BIGINT)
            RETURNS VOID AS $$
            DECLARE
                v_ticket_status TEXT;
            BEGIN
                SELECT status INTO v_ticket_status
                FROM tickets
                WHERE id = p_ticket_id
                FOR UPDATE;

                IF v_ticket_status != 'available' THEN
                    RAISE EXCEPTION 'Ticket % is not available.', p_ticket_id;
                END IF;

                UPDATE tickets
                SET status = 'sold'
                WHERE id = p_ticket_id;

                INSERT INTO orders (client_id, ticket_id, status, created_at, updated_at)
                VALUES (p_client_id, p_ticket_id, 'completed', now(), now());
            END;
            $$ LANGUAGE plpgsql;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS purchase_ticket(BIGINT, BIGINT);"
        ),
        #Wywołanie: tylko order_id
        migrations.RunSQL(
            sql="""
                    CREATE OR REPLACE FUNCTION cancel_order(p_order_id BIGINT)
                    RETURNS VOID AS $$
                    DECLARE
                        v_ticket_id BIGINT;
                        v_status TEXT;
                    BEGIN
                        SELECT status, ticket_id INTO v_status, v_ticket_id
                        FROM orders
                        WHERE id = p_order_id
                        FOR UPDATE;

                        IF v_status != 'completed' THEN
                            RAISE EXCEPTION 'Only completed orders can be canceled.';
                        END IF;

                        UPDATE orders
                        SET status = 'canceled', updated_at = now()
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
