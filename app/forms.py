from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Conversation, Message


class MessageForm(forms.ModelForm):
    """Form for user to send messages"""

    class Meta:
        model = Message
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 2,
                    "placeholder": "Ask anything…",
                    "class": "dp-input",
                }
            ),
        }


class ConversationForm(forms.ModelForm):
    """Form to create or edit conversations"""

    class Meta:
        model = Conversation
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Debug failing API endpoint",
                    "class": "field-input",
                    "autofocus": True,
                }
            ),
        }


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "field-input",
                "placeholder": "you@example.com",
            }
        ),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "field-input", "placeholder": "your_username"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "field-input", "placeholder": "Min 8 characters"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "field-input", "placeholder": "Repeat password"}
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "field-input", "placeholder": "Username", "autofocus": True}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "field-input", "placeholder": "Password"}
        )
    )
