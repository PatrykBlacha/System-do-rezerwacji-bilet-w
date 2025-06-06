from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('tickets_app', '0003_create_functions'),
    ]


    operations = [
        # wywołanie: lista ludzi; lista biletów
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE PROCEDURE assign_tickets_group(p_client_ids BIGINT[], p_ticket_ids BIGINT[])
                LANGUAGE plpgsql
                AS $$
                DECLARE
                    idx INT;
                    v_status TEXT;
                BEGIN
                    IF array_length(p_client_ids, 1) != array_length(p_ticket_ids, 1) THEN
                        RAISE EXCEPTION 'client_ids and ticket_ids must have the same length';
                    END IF;

                    -- Sprawdzenie dostępności i blokowanie biletów
                    FOR idx IN 1..array_length(p_ticket_ids, 1)
                    LOOP
                        SELECT status INTO v_status
                        FROM tickets
                        WHERE id = p_ticket_ids[idx]
                        FOR UPDATE;

                        IF v_status != 'available' THEN
                            RAISE EXCEPTION 'Ticket % is not available', p_ticket_ids[idx];
                        END IF;
                    END LOOP;

                    -- Aktualizacja statusów i tworzenie zamówień
                    FOR idx IN 1..array_length(p_ticket_ids, 1)
                    LOOP
                        UPDATE tickets
                        SET status = 'sold'
                        WHERE id = p_ticket_ids[idx];

                        INSERT INTO orders (client_id, ticket_id, status, created_at, updated_at)
                        VALUES (p_client_ids[idx], p_ticket_ids[idx], 'completed', now(), now());
                    END LOOP;
                EXCEPTION
                    WHEN OTHERS THEN
                        RAISE NOTICE 'Rolling back due to error: %', SQLERRM;
                        RAISE;
                END;
                $$;
            """,
            reverse_sql="DROP PROCEDURE IF EXISTS assign_tickets_group(BIGINT[], BIGINT[]);"
        ),
        #wywołanie: lista order id
        migrations.RunSQL(
            sql="""
                    CREATE OR REPLACE PROCEDURE cancel_orders_group(p_order_ids BIGINT[])
                    LANGUAGE plpgsql
                    AS $$
                    DECLARE
                        idx INT;
                        v_ticket_id BIGINT;
                        v_status TEXT;
                    BEGIN
                        FOR idx IN 1..array_length(p_order_ids, 1)
                        LOOP
                            -- Pobranie statusu i ID biletu
                            SELECT status, ticket_id INTO v_status, v_ticket_id
                            FROM orders
                            WHERE id = p_order_ids[idx]
                            FOR UPDATE;

                            IF v_status != 'completed' THEN
                                RAISE EXCEPTION 'Order % is not completed and cannot be canceled.', p_order_ids[idx];
                            END IF;

                            -- Aktualizacja zamówienia
                            UPDATE orders
                            SET status = 'canceled', updated_at = now()
                            WHERE id = p_order_ids[idx];

                            -- Zmiana biletu na dostępny
                            UPDATE tickets
                            SET status = 'available'
                            WHERE id = v_ticket_id;
                        END LOOP;
                    EXCEPTION
                        WHEN OTHERS THEN
                            RAISE NOTICE 'Rollback due to error: %', SQLERRM;
                            RAISE;
                    END;
                    $$;
                """,
            reverse_sql="DROP PROCEDURE IF EXISTS cancel_orders_group(BIGINT[]);"
        )
    ]
