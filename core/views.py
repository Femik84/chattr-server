from django.http import JsonResponse
from django.db import connection
from redis import Redis
import os


def health_check(request):

    # -------------------
    # PostgreSQL check
    # -------------------
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()

        db_status = "ok" if row else "fail"

    except Exception as e:
        print("DB ERROR:", e)
        db_status = "fail"

    # -------------------
    # Redis check
    # -------------------
    try:
        redis_conn = Redis.from_url(
            os.getenv("REDIS_URL"),
            decode_responses=True,
        )

        redis_conn.ping()

        redis_status = "ok"

    except Exception as e:
        print("REDIS ERROR:", e)
        redis_status = "fail"

    return JsonResponse({
        "status": "ok",
        "db": db_status,
        "redis": redis_status
    })