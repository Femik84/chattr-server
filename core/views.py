from django.http import JsonResponse
from django.db import connection
from django_redis import get_redis_connection


def health_check(request):
    # -------------------
    # PostgreSQL ping
    # -------------------
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
        db_status = "ok" if row else "fail"
    except Exception:
        db_status = "fail"

    # -------------------
    # Redis ping
    # -------------------
    try:
        redis_conn = get_redis_connection("default")
        redis_conn.ping()
        redis_status = "ok"
    except Exception:
        redis_status = "fail"

    return JsonResponse({
        "status": "ok",
        "db": db_status,
        "redis": redis_status
    })