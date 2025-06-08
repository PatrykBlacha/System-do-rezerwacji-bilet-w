import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets_app', '0004_tickets_functions'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE PROCEDURE reserve_ticket_for_client(p_client_id BIGINT, p_ticket_id BIGINT)
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    v_status TEXT;
                    v_order_id BIGINT;
                BEGIN
                    SELECT status INTO v_status
                    FROM tickets
                    WHERE id = p_ticket_id
                    FOR UPDATE;

                    IF v_status != 'available' THEN
                        RAISE EXCEPTION 'Ticket is not available.';
                    END IF;

                    UPDATE tickets
                    SET status = 'reserved', reserved_until = NOW() + INTERVAL '10 minutes'
                    WHERE id = p_ticket_id;

                    -- Tworzenie zamówienia
                    INSERT INTO orders (user_id, status, created_at, updated_at)
                    VALUES (NULL, 'pending', NOW(), NOW())
                    RETURNING id INTO v_order_id;

                    -- Łączenie klienta z biletem przez szczegóły zamówienia
                    INSERT INTO orders_details (order_id, client_id, ticket_id, ticket_uuid)
                    VALUES (v_order_id, p_client_id, p_ticket_id, gen_random_uuid());
                END;
                $$;
            """,
            reverse_sql="DROP PROCEDURE IF EXISTS reserve_ticket_for_client(BIGINT, BIGINT);"
        ),
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE FUNCTION purchase_ticket(p_client_id BIGINT, p_ticket_id BIGINT)
                RETURNS VOID AS $$
                DECLARE
                    v_order_id BIGINT;
                BEGIN
                    SELECT od.order_id INTO v_order_id
                    FROM orders_details od
                    JOIN orders o ON o.id = od.order_id
                    WHERE od.client_id = p_client_id
                      AND od.ticket_id = p_ticket_id
                      AND o.status = 'pending'
                    FOR UPDATE;

                    IF NOT FOUND THEN
                        RAISE EXCEPTION 'No valid reservation found for client % and ticket %.', p_client_id, p_ticket_id;
                    END IF;

                    UPDATE tickets
                    SET status = 'sold', reserved_until = NULL
                    WHERE id = p_ticket_id;

                    UPDATE orders
                    SET status = 'completed', updated_at = NOW()
                    WHERE id = v_order_id;
                END;
                $$ LANGUAGE plpgsql;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS purchase_ticket(BIGINT, BIGINT);"
        )
    ]
