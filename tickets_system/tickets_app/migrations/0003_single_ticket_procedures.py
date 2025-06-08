import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets_app', '0002_view_user_tickets'),
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

                        INSERT INTO orders (client_id, ticket_id, status, created_at, updated_at)
                        VALUES (p_client_id, p_ticket_id, 'pending', NOW(), NOW());
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
                    SELECT id INTO v_order_id
                    FROM orders
                    WHERE client_id = p_client_id
                      AND ticket_id = p_ticket_id
                      AND status = 'pending'
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
            reverse_sql="DROP PROCEDURE IF EXISTS purchase_ticket(BIGINT, BIGINT);"
        )
    ]