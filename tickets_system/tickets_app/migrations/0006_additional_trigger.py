from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('tickets_app', '0005_create_triggers'),
    ]

    operations = [
        #kontroluje datę wsteczną
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION check_event_date_before_ticket_change()
            RETURNS TRIGGER AS $$
            DECLARE
                v_event_date DATE;
            BEGIN
                SELECT event_date INTO v_event_date FROM events WHERE id = NEW.event_id;

                IF v_event_date < CURRENT_DATE THEN
                    RAISE EXCEPTION 'Cannot add or modify tickets for past events.';
                END IF;

                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER trg_check_event_date_before_ticket_change
            BEFORE INSERT OR UPDATE ON tickets
            FOR EACH ROW
            EXECUTE FUNCTION check_event_date_before_ticket_change();
            """,
            reverse_sql="""
            DROP TRIGGER IF EXISTS trg_check_event_date_before_ticket_change ON tickets;
            DROP FUNCTION IF EXISTS check_event_date_before_ticket_change();
            """
        )
    ]
