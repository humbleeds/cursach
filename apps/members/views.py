from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView, DeleteView, ListView
from .models import Member
from .forms import AddMemberForm, AddMemberUpdateForm
from django.contrib.auth.mixins import LoginRequiredMixin
import dateutil.relativedelta as delta
from django.urls import reverse
from apps.wallpaper.models import Wallpaper
from apps.payments.models import Payments
from django.db import connection


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


class LandingPage(TemplateView):
    # Landing Page - CRUD wallpaper model
    template_name = "landing_page.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        with connection.cursor() as cursor:
            cursor.execute("SELECT photo FROM wallpaper_wallpaper LIMIT 0, 1000;")
            if cursor.rowcount > 0:
                wallpaper = cursor.fetchone()[0]
        
                context.update({
                    'wallpaper': {
                        "photo": wallpaper
                    }
                })
        return context


class MemberListView(LoginRequiredMixin, ListView):
    """ Login Required -  List Member by first_name
        Also show stopped members to undo changes
    """
    template_name = 'members/view_members.html'
    context_object_name = 'data'
    paginate_by = 8

    def get_queryset(self):
        #members = Member.objects.filter(stop=0).order_by('first_name')
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM members_member WHERE stop=0 ORDER BY (first_name) LIMIT 0, 1000;")
            members = dictfetchall(cursor)
            for member in members:
                member.update({
                    'pk': member['member_id']
                })
            return members

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        with connection.cursor() as cursor:
            stopped_members = cursor.execute("SELECT * FROM members_member WHERE stop=1 ORDER BY (first_name) LIMIT 0, 1000;")
            members = dictfetchall(cursor)
            for member in members:
                member.update({
                    'pk': member['member_id']
                })
            context.update({
                'stopped_member_data': stopped_members
            })
        return context


class AddMemberView(LoginRequiredMixin, CreateView):
    """ Login Required - Add new member view with 'AddMemberForm' form class
        form_valid method extract relative date form subscription_period and extends registration_upto data accordingly
        Generates a Payment Model Object if status is set to paid
    """
    template_name = 'members/add_member.html'
    form_class = AddMemberForm

    def get_success_url(self) -> str:
        return reverse("members:member-list")

    def form_valid(self, form):
        form.instance.registration_upto = form.cleaned_data['registration_date'] + delta.relativedelta(
            months=int(form.cleaned_data['subscription_period']))
        self.object = form.save()

        if form.cleaned_data['fee_status'] == 'paid':
            payments = Payments(
                user=self.object,
                payment_date=form.cleaned_data['registration_date'],
                payment_period=form.cleaned_data['subscription_period'],
                payment_amount=form.cleaned_data['amount'])

            with connection.cursor() as cursor:
                cursor.execute(f"INSERT INTO payments_payments VALUES ({payments.user.pk}, {payments.payment_date}, {payments.payment_period}, {payments.payment_amount})")

        return HttpResponseRedirect(self.get_success_url())


class MemberDetailView(LoginRequiredMixin, DetailView):
    """ Login Required - Detail View to show personal and medical information of Member
        Also Displays any payment history if available
    """
    template_name = 'members/member_detail.html'
    context_object_name = 'member'
    queryset = Member.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payments = Payments.objects.filter(user=self.kwargs['pk'])
        if not payments.exists():
            payments = 'No Records'
        context.update({
            'member_payment': payments
        })
        return context


class UpdateMemberView(LoginRequiredMixin, UpdateView):
    """ Login Required - Update Selected Member Data
        Reset relative data accordingly
        Checks for existing payment information with new data and creates if the new data has no record
    """
    template_name = 'members/update_member.html'
    form_class = AddMemberUpdateForm
    queryset = Member.objects.all()

    def get_success_url(self) -> str:
        return reverse("members:member-list")

    def form_valid(self, form):
        form.instance.registration_upto = form.cleaned_data['registration_date'] + delta.relativedelta(
            months=int(form.cleaned_data['subscription_period']))
        self.object = form.save()

        if form.cleaned_data['fee_status'] == 'paid':
            check = Payments.objects.filter(
                payment_date=form.cleaned_data['registration_date'], user=self.object).count()
            if check == 0:
                payments = Payments(
                    user=self.object,
                    payment_date=form.cleaned_data['registration_date'],
                    payment_period=form.cleaned_data['subscription_period'],
                    payment_amount=form.cleaned_data['amount'])
                payments.save()

        return HttpResponseRedirect(self.get_success_url())


class DeleteMemberView(LoginRequiredMixin, DeleteView):
    """ Delete Member Data """
    template_name = 'members/member_delete.html'
    queryset = Member.objects.all()

    def get_success_url(self) -> str:
        return reverse("members:member-list")
