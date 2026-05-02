from django import forms
from .models import Testimonial, Order


class TestimonialForm(forms.ModelForm):
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Testimonial
        fields = ['name', 'location', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your name', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g. Tsomo', 'class': 'form-control'}),
            'message': forms.Textarea(attrs={
                'rows': 4,
                'maxlength': 300,
                'placeholder': 'Share your experience in 300 characters or less...',
                'class': 'form-control'
            }),
        }

    def clean_honeypot(self):
        value = self.cleaned_data.get('honeypot')
        if value:
            raise forms.ValidationError("Spam detected!")
        return value

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) > 300:
            raise forms.ValidationError("Please keep your message under 300 characters.")
        return message


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['name', 'email', 'phone', 'item', 'date', 'notes', 'reference_image']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Your name',
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'e.g. yourname@example.com (optional)',
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'e.g. 073 123 4567',
                'class': 'form-control'
            }),
            'item': forms.TextInput(attrs={
                'placeholder': 'e.g. Chocolate Cake',
                'class': 'form-control'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Any special instructions?'
            }),
            'reference_image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False  # ✅ Explicitly make email optional
