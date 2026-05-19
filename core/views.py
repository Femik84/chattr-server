from django.http import JsonResponse
from django.db import connection
from channels_redis.core import RedisChannelLayer
import os


def health_check(request):

    # -------------------
    # DB check
    # -------------------
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
        db_status = "ok" if row else "fail"
    except Exception:
        db_status = "fail"

    # -------------------
    # REDIS check (Channels-compatible)
    # -------------------
    try:
        from channels_redis.core import RedisChannelLayer

        channel_layer = RedisChannelLayer(
            {
                "hosts": [os.getenv("REDIS_URL")],
            }
        )

        # simple ping
        conn = channel_layer.connection(False)
        conn.ping()

        redis_status = "ok"
    except Exception:
        redis_status = "fail"

    return JsonResponse({
        "status": "ok",
        "db": db_status,
        "redis": redis_status
    })