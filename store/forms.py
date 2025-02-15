from django import forms
from .models import *


class ProductForm(forms.ModelForm):
    main_image = forms.ModelChoiceField(
        queryset=ProductImage.objects.none(),  # Set dynamically in __init__
        required=False,
        widget=forms.RadioSelect
    )

    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'expected_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['main_image'].queryset = self.instance.product_images.all()
            self.fields['main_image'].initial = self.instance.product_images.filter(main_image=True).first()

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'



class TeamMemberForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = '__all__'
        widgets = {
            'image': forms.FileInput(attrs={'accept': 'image/*'}),
        }



class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['phone_number', 'address', 'profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'accept': 'image/*'}),
        }





class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        # Check if password and confirm_password match
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data

from django.contrib.auth.forms import UserChangeForm

class EditProfileForm(UserChangeForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password", required=False)
    phone_number = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))
    profile_picture = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']  # Excluding password here for now

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        # If password is entered, confirm the match
        if password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # If a new password is provided, set it
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()
        
        # Update customer profile info
        customer = Customer.objects.get(user=user)
        customer.phone_number = self.cleaned_data['phone_number']
        customer.address = self.cleaned_data['address']
        customer.profile_picture = self.cleaned_data.get('profile_picture', customer.profile_picture)
        customer.save()

        return user
    
    


class PaymentForm(forms.ModelForm):
    payment_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Enter the name used in payment'}),
        required=True
    )
    payment_message = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': '*165*S*12400 RWF transferred to ELIE......'}),
        required=False
    )
    payment_image = forms.ImageField(required=False)

    class Meta:
        model = Order
        fields = ['payment_name', 'payment_message', 'payment_image']


class AdvertisementForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = ['title', 'image', 'link', 'start_date', 'end_date', 'active']

    # Optional: Add validation to ensure start_date is before end_date
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError("Start date must be before end date.")
        return cleaned_data


class NotificationForm(forms.ModelForm):
    for_all_customers = forms.BooleanField(required=False, label="Send to All Customers (Non-Staff)")
    for_all_staff = forms.BooleanField(required=False, label="Send to All Staff")
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False,
        label="Select Specific Users"
    )

    class Meta:
        model = Notification
        fields = ['message', 'for_all_customers', 'for_all_staff', 'users']
