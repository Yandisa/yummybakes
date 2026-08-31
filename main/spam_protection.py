import time

from django import forms
from django.conf import settings
from django.core.cache import cache

MIN_FILL_SECONDS = 3
MAX_FORM_AGE_SECONDS = 60 * 60


class SpamProtectionFormMixin(forms.Form):
    """
    Mix into any Form/ModelForm to add a hidden honeypot field, a
    minimum-fill-time check, and (when RECAPTCHA keys are configured)
    an invisible reCAPTCHA v3 field.
    """
    website = forms.CharField(required=False, widget=forms.HiddenInput, label='')
    form_rendered_at = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields['form_rendered_at'].initial = str(time.time())

        if getattr(settings, 'RECAPTCHA_PUBLIC_KEY', '') and getattr(settings, 'RECAPTCHA_PRIVATE_KEY', ''):
            from django_recaptcha.fields import ReCaptchaField
            from django_recaptcha.widgets import ReCaptchaV3
            self.fields['captcha'] = ReCaptchaField(widget=ReCaptchaV3, label='')

    def clean_website(self):
        value = self.cleaned_data.get('website')
        if value:
            raise forms.ValidationError("Spam detected.")
        return value

    def clean_form_rendered_at(self):
        raw = self.cleaned_data.get('form_rendered_at')
        try:
            rendered_at = float(raw)
        except (TypeError, ValueError):
            raise forms.ValidationError("Please reload the page and try again.")
        elapsed = time.time() - rendered_at
        if elapsed < MIN_FILL_SECONDS:
            raise forms.ValidationError("Submitted too quickly — please try again.")
        if elapsed > MAX_FORM_AGE_SECONDS:
            raise forms.ValidationError("This form has expired — please reload the page and try again.")
        return raw


def is_rate_limited(request, key_prefix, limit=5, window_seconds=3600):
    """Simple cache-based per-IP throttle. Returns True if the caller should be blocked."""
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', 'unknown')
    cache_key = f"ratelimit:{key_prefix}:{ip}"
    count = cache.get(cache_key, 0)
    if count >= limit:
        return True
    cache.set(cache_key, count + 1, timeout=window_seconds)
    return False
