from django import forms
from .models import *

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

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
    class Meta:
        model = Order
        fields = ['payment_message', 'payment_image']

    payment_message = forms.CharField(widget=forms.Textarea(attrs={'placeholder': '*165*S*12400 RWF transferred to ELIE......'}), required=False)
    payment_image = forms.ImageField(required=False)
