import dateutil.relativedelta as delta

from datetime import datetime
from django import forms
from .models import Member
from django.db import connection


class AddMemberForm(forms.ModelForm):
    # Add new Member form
    class Meta:
        model = Member
        fields = '__all__'
        exclude = ['registration_upto']

        widgets = {
            'registration_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'cols': 80, 'rows': 3}),
            'medical_history': forms.Textarea(attrs={'cols': 80, 'rows': 3}),
            'dob': forms.DateInput(attrs={'class': 'datepicker', 'type': 'date'}),
            'photo': forms.FileInput(attrs={'accept': 'image/*;capture=camera'})
        }

    def clean_mobile_number(self, *args, **kwargs):
        # Check for mobile number and return Validation Error if incorrect
        mobile_number = self.cleaned_data.get('mobile_number')
        if not mobile_number.isdigit():
            raise forms.ValidationError('Mobile number should be a number')
        if Member.objects.filter(mobile_number=mobile_number).exists():
            raise forms.ValidationError(
                'This mobile number has already been registered.')
        else:
            if len(str(mobile_number)) == 10:
                return mobile_number
            else:
                raise forms.ValidationError(
                    'Mobile number should be 10 digits long.')
        return mobile_number

    def save(self, commit=True):
        """
        Save this form's self.instance object if commit=True. Otherwise, add
        a save_m2m() method to the form which can be called after the instance
        is saved manually at a later time. Return the model instance.
        """
        if self.errors:
            raise ValueError(
                "The %s could not be %s because the data didn't validate." % (
                    self.instance._meta.object_name,
                    'created' if self.instance._state.adding else 'changed',
                )
            )
        if commit:
            # If committing, save the instance and the m2m data immediately.
            if isinstance(self.instance, Member):
                data = self.cleaned_data
                data['photo'] = self.cleaned_data['photo'].name
                data['registration_upto'] = self.cleaned_data['registration_date'] + delta.relativedelta(months=int(self.cleaned_data['subscription_period']))
                data['registration_date'] = self.cleaned_data['registration_date'].strftime('%Y-%m-%d')
                data['dob'] = self.cleaned_data['dob'].strftime('%Y-%m-%d')
                data['admitted_on'] = datetime.now().strftime('%Y-%m-%d')

                names = data.keys()
                values = [f"'{str(value)}'" for value in data.values()]
                
                with connection.cursor() as cursor:
                    sql = "INSERT INTO members_member ({0}) VALUES ({1})".format(", ".join(names), ", ".join(values))
                    cursor.execute(sql)
            else:
                raise ValueError("Exception in save method: self.instance is not a Member instance")
            self._save_m2m()
        else:
            # If not committing, add a method to the form to allow deferred
            # saving of m2m data.
            self.save_m2m = self._save_m2m
        return self.instance

    def clean_amount(self):
        # Clean money amount
        amount = self.cleaned_data.get('amount')
        if not amount.isdigit():
            raise forms.ValidationError('Amount should be a number')
        return amount

    def clean(self):
        # Check for already existing member
        cleaned_data = super().clean()
        dob = cleaned_data.get('dob')
        first_name = cleaned_data.get('first_name').capitalize()
        last_name = cleaned_data.get('last_name').capitalize()
        queryset = Member.objects.filter(
            first_name=first_name,
            last_name=last_name,
            dob=dob
        ).count()
        if queryset > 0:
            raise forms.ValidationError('This member already exists!')


class AddMemberUpdateForm(forms.ModelForm):
    # Update Member form without registration_upto date
    class Meta:
        model = Member
        fields = '__all__'
        exclude = ['registration_upto']

        widgets = {
            'registration_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'cols': 80, 'rows': 3}),
            'medical_history': forms.Textarea(attrs={'cols': 80, 'rows': 3}),
            'dob': forms.DateInput(attrs={'class': 'datepicker', 'type': 'date'}),
            'photo': forms.FileInput(attrs={'accept': 'image/*;capture=camera'})
        }

    def save(self, commit=True):
        """
        Save this form's self.instance object if commit=True. Otherwise, add
        a save_m2m() method to the form which can be called after the instance
        is saved manually at a later time. Return the model instance.
        """
        if self.errors:
            raise ValueError(
                "The %s could not be %s because the data didn't validate." % (
                    self.instance._meta.object_name,
                    'created' if self.instance._state.adding else 'changed',
                )
            )
        if commit:
            # If committing, save the instance and the m2m data immediately.
            if isinstance(self.instance, Member):
                data = self.cleaned_data
                data['photo'] = self.cleaned_data['photo'].name
                data['registration_date'] = self.cleaned_data['registration_date'].strftime('%Y-%m-%d')
                data['dob'] = self.cleaned_data['dob'].strftime('%Y-%m-%d')
   
                values = [f"{name} = '{value}'" for name, value in data.items()]
                
                with connection.cursor() as cursor:
                    sql = "UPDATE members_member SET {0} WHERE member_id = {1}".format(", ".join(values), self.instance.pk)
                    cursor.execute(sql)
            else:
                raise ValueError("Exception in save method: self.instance is not a Member instance")
            self._save_m2m()
        else:
            # If not committing, add a method to the form to allow deferred
            # saving of m2m data.
            self.save_m2m = self._save_m2m
        return self.instance