from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('tickets_app', '0007_UUID_view_user_tickets')
    ]

    operations = [
        migrations.RunSQL(
            sql="""
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
            """,
            reverse_sql="""
                DROP VIEW IF EXISTS user_tickets_view;

                CREATE VIEW user_tickets_view AS
                SELECT 
                    od.order_id,
                    od."ticket_UUID",
                    t.event_id,
                    t.seat,
                    o.updated_at,
                    o.user_id
                FROM orders_details od
                JOIN tickets t ON od.ticket_id = t.id
                JOIN orders o ON od.order_id = o.id;
            """
        )
    ]
