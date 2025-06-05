from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('tickets_app', '0004_create_procedure'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            -- Funkcja sprawdzająca czy bilet nie jest już sprzedany
            CREATE OR REPLACE FUNCTION prevent_duplicate_ticket_order()
            RETURNS TRIGGER AS $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM orders
                    WHERE ticket_id = NEW.ticket_id AND status = 'completed'
                ) THEN
                    RAISE EXCEPTION 'This ticket has already been sold.';
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER trg_prevent_duplicate_ticket_order
            BEFORE INSERT ON orders
            FOR EACH ROW
            EXECUTE FUNCTION prevent_duplicate_ticket_order();

            -- Funkcja aktualizująca status biletu po zmianie statusu zamówienia
            CREATE OR REPLACE FUNCTION update_ticket_status_on_order()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.status = 'completed' THEN
                    UPDATE tickets
                    SET status = 'sold'
                    WHERE id = NEW.ticket_id;
                ELSIF NEW.status = 'canceled' THEN
                    UPDATE tickets
                    SET status = 'available'
                    WHERE id = NEW.ticket_id;
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER trg_update_ticket_status_on_order
            AFTER INSERT OR UPDATE ON orders
            FOR EACH ROW
            EXECUTE FUNCTION update_ticket_status_on_order();

            -- Funkcja przywracająca status biletu po usunięciu zamówienia
            CREATE OR REPLACE FUNCTION restore_ticket_on_order_delete()
            RETURNS TRIGGER AS $$
            BEGIN
                UPDATE tickets
                SET status = 'available'
                WHERE id = OLD.ticket_id;
                RETURN OLD;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER trg_restore_ticket_on_order_delete
            AFTER DELETE ON orders
            FOR EACH ROW
            EXECUTE FUNCTION restore_ticket_on_order_delete();
            """,
            reverse_sql="""
            DROP TRIGGER IF EXISTS trg_prevent_duplicate_ticket_order ON orders;
            DROP FUNCTION IF EXISTS prevent_duplicate_ticket_order();

            DROP TRIGGER IF EXISTS trg_update_ticket_status_on_order ON orders;
            DROP FUNCTION IF EXISTS update_ticket_status_on_order();

            DROP TRIGGER IF EXISTS trg_restore_ticket_on_order_delete ON orders;
            DROP FUNCTION IF EXISTS restore_ticket_on_order_delete();
            """
        ),
    ]
