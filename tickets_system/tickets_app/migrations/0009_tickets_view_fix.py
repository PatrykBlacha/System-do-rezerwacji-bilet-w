from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('tickets_app', '0008_update_view_tickets'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DROP VIEW IF EXISTS user_tickets_view;

                CREATE VIEW user_tickets_view AS
                SELECT DISTINCT ON (od."ticket_UUID")
                    od.order_id,
                    od."ticket_UUID",
                    t.event_id,
                    e.name AS event_name,
                    t.seat,
                    o.updated_at,
                    o.user_id
                FROM orders_details od
                JOIN tickets t ON od.ticket_id = t.id
                JOIN events e ON t.event_id = e.id
                JOIN orders o ON od.order_id = o.id
                ORDER BY od."ticket_UUID", o.updated_at DESC;
            """,
            reverse_sql="""
                DROP VIEW IF EXISTS user_tickets_view;

                CREATE VIEW user_tickets_view AS
                SELECT 
                    od.order_id,
                    od."ticket_UUID",
                    t.event_id,
                    e.name AS event_name,
                    t.seat,
                    o.updated_at,
                    o.user_id
                FROM orders_details od
                JOIN tickets t ON od.ticket_id = t.id
                JOIN events e ON t.event_id = e.id
                JOIN orders o ON od.order_id = o.id;
            """
        )
    ]
