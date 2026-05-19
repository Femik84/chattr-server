from django.http import JsonResponse
from django.db import connection

def health_check(request):
    # lightweight DB ping
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1;")
        row = cursor.fetchone()

    return JsonResponse({
        "status": "ok",
        "db": "ok" if row else "fail"
    })