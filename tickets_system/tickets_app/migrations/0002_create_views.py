from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('tickets_app', '0001_initial'),
    ]

    operations = [
        # 1. Available Tickets View- dostępne bilety na przyszłe wydarzenia
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE VIEW available_tickets_view AS
                SELECT 
                    t.id AS ticket_id,
                    e.name AS event_name,
                    e.event_date,
                    t.seat,
                    t.price
                FROM tickets t
                JOIN events e ON t.event_id = e.id
                WHERE t.status = 'available'
                  AND e.event_date >= CURRENT_DATE;
            """,
            reverse_sql="DROP VIEW IF EXISTS available_tickets_view;"
        ),

        # 2. Event Ticket Availability- dostępne miejsca na dane wydarzenia
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE VIEW event_ticket_availability AS
                SELECT 
                    e.id AS event_id,
                    e.name AS event_name,
                    COUNT(t.id) FILTER (WHERE t.status = 'available') AS available_tickets,
                    COUNT(t.id) FILTER (WHERE t.status = 'sold') AS sold_tickets,
                    COUNT(t.id) AS total_tickets
                FROM events e
                LEFT JOIN tickets t ON e.id = t.event_id
                GROUP BY e.id, e.name;
            """,
            reverse_sql="DROP VIEW IF EXISTS event_ticket_availability;"
        ),

        # 3. Client Orders View-
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE VIEW client_orders_view AS
                SELECT 
                    o.id AS order_id,
                    CONCAT(c.first_name, ' ', c.last_name) AS client_name,
                    e.name AS event_name,
                    e.event_date,
                    t.seat,
                    t.price,
                    o.status,
                    o.created_at
                FROM orders o
                JOIN clients c ON o.client_id = c.id
                JOIN tickets t ON o.ticket_id = t.id
                JOIN events e ON t.event_id = e.id;
            """,
            reverse_sql="DROP VIEW IF EXISTS client_orders_view;"
        ),

        # 4. Event Revenue View
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE VIEW event_revenue_view AS
                SELECT 
                    e.id AS event_id,
                    e.name AS event_name,
                    SUM(t.price) FILTER (WHERE t.status = 'sold') AS revenue
                FROM events e
                LEFT JOIN tickets t ON e.id = t.event_id
                GROUP BY e.id, e.name;
            """,
            reverse_sql="DROP VIEW IF EXISTS event_revenue_view;"
        ),
    ]
