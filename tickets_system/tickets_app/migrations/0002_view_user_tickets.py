import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets_app', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE VIEW user_tickets_view AS
                SELECT
                    o.id AS order_id,
                    o.user_id,
                    o.status AS order_status,
                    o.updated_at,
                    od.ticket_id,
                    t.event_id,
                    t.seat,
                    t.status AS ticket_status
                FROM orders o
                JOIN orders_details od ON o.id = od.order_id
                JOIN tickets t ON od.ticket_id = t.id
                WHERE o.status = 'completed';
            """,
            reverse_sql="DROP VIEW IF EXISTS user_tickets_view;"
        )
    ]