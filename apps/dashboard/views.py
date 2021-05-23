from django.shortcuts import render
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import connection

today = datetime.today()

month_dictionary = {
    -1: 'December',
    -2: 'November',
    -3: 'October',
    -4: 'September',
    -5: 'August',
    -6: 'July',
    -7: 'June',
    -8: 'May',
    -9: 'April',
    -10: 'March',
    -11: 'February',
    0: 'January',
    1: 'February',
    2: 'March',
    3: 'April',
    4: 'May',
    5: 'June',
    6: 'July',
    7: 'August',
    8: 'September',
    9: 'October',
    10: 'November',
    11: 'December'		}


@login_required
def dashboard(request):
    """
    Display Analaytics based on Payments and Member Data
    """
    cursor = connection.cursor()

    with connection.cursor() as cursor:
        cursor.execute("SELECT payment_amount, SUM(payment_amount) FROM payments_payments")
        total_revenue_till_date = cursor.fetchall()[0][1]
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT member_id, count(*) FROM members_member WHERE stop=0")
        total_members = cursor.fetchall()[0][1]
    
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT registration_date, COUNT(*) FROM members_member WHERE YEAR(registration_date)={datetime.today().year} AND MONTH(registration_date)={datetime.today().month} AND stop=0")
        members_this_mon = cursor.fetchall()[0][1]
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT fee_status, COUNT(*) FROM members_member WHERE fee_status='pending'")
        pending_payment_members = cursor.fetchall()[0][1]
    
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT fee_status, registration_upto, COUNT(*) FROM members_member WHERE fee_status='pending' AND YEAR(registration_upto)={datetime.today().year} AND MONTH(registration_upto)={datetime.today().month}")
        pending_payment_members_this_month = cursor.fetchall()[0][2]
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT payment_amount, AVG(payment_amount) FROM payments_payments")
        avg_revenue = cursor.fetchall()[0][1]

    context = {
        "members_this_mon": members_this_mon,
        "total_members": total_members,
        "total_revenue_till_date": total_revenue_till_date,
        "pending_payment_members": pending_payment_members,
        "pending_payment_members_this_month": pending_payment_members_this_month,
        "avg_revenue": round(avg_revenue, 2)
    }
    return render(request, "dashboard/board.html", context=context)


@login_required
def member_chart(request):
    # Chart based on Member Data consumed by Chart JS on the frontend
    data = []
    labels = []
    recent_months = [today.month - 3, today.month - 2, today.month -
                     1, today.month]
    for months in recent_months:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT registration_date, COUNT(*) FROM members_member WHERE YEAR(registration_date)={datetime.today().year} AND MONTH(registration_date)={months} AND stop=0")
            count = cursor.fetchall()[0][1]
            print(cursor.fetchall())
        data.append(count)
        labels.append(month_dictionary[months])

    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })


@login_required
def payment_chart(request):
    # Chart based on Payment Data consumed by Chart JS on the frontend 
    data = []
    labels = []
    recent_months = [today.month - 6, today.month - 5, today.month - 4, today.month - 3, today.month - 2, today.month -
                     1, today.month]
    for months in recent_months:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT payment_amount, payment_date, AVG(payment_amount) FROM payments_payments WHERE YEAR(payment_date)={datetime.today().year} AND MONTH(payment_date)={months}")
            count = cursor.fetchall()[0][2]
        data.append(count)
        labels.append(month_dictionary[months])
    return JsonResponse(data={
        'data': data,
        'labels': labels,
    })
