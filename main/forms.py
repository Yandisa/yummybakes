from django import forms
from .models import Testimonial


class TestimonialForm(forms.ModelForm):
    # Hidden field to trap bots (should stay empty)
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Testimonial
        fields = ['name', 'location', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Your name',
                'class': 'form-control',
            }),
            'location': forms.TextInput(attrs={
                'placeholder': 'e.g. Cape Town',
                'class': 'form-control',
            }),
            'message': forms.Textarea(attrs={
                'rows': 4,
                'maxlength': 300,
                'placeholder': (
                    'Share your experience in 300 characters or less...'
                ),
                'class': 'form-control',
            }),
        }

    def clean_honeypot(self):
        """Reject spam submissions from bots filling hidden field"""
        if self.cleaned_data.get('honeypot'):
            raise forms.ValidationError("Spam detected!")
        return self.cleaned_data['honeypot']

    def clean_message(self):
        """Ensure testimonial is concise"""
        message = self.cleaned_data.get('message')
        if len(message) > 300:
            raise forms.ValidationError(
                "Please keep your message under 300 characters."
            )
        return message
