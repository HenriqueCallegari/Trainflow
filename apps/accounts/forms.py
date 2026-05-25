"""Forms de autenticação, criação de aluno e perfil."""
from __future__ import annotations

import secrets

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import AthleteProfile, Profile


class TrainerRegistrationForm(UserCreationForm):
    """Registro público só para treinador."""

    first_name = forms.CharField(max_length=150, label="Nome")
    last_name = forms.CharField(max_length=150, required=False, label="Sobrenome")
    phone = forms.CharField(max_length=30, required=False, label="Telefone")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=commit)
        if commit:
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.role = Profile.Role.TRAINER
            profile.phone = self.cleaned_data.get("phone", "")
            profile.save()
        return user


class AthleteCreationForm(forms.Form):
    """Treinador cria um atleta: gera login automático e define senha inicial."""

    username = forms.CharField(max_length=150, label="Usuário (login)")
    first_name = forms.CharField(max_length=150, label="Nome")
    last_name = forms.CharField(max_length=150, required=False, label="Sobrenome")
    email = forms.EmailField(required=False, label="E-mail")
    sex = forms.ChoiceField(choices=AthleteProfile.Sex.choices, label="Sexo")
    bodyweight_kg = forms.DecimalField(
        max_digits=5, decimal_places=2, required=False,
        label="Peso corporal (kg)",
    )
    initial_password = forms.CharField(
        min_length=8, max_length=30, label="Senha inicial",
        help_text="Comparta com o(a) atleta. Ele(a) poderá trocar depois.",
        widget=forms.TextInput(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} input".strip()
        if not self.is_bound:
            # Sugere uma senha para facilitar. Treinador pode sobrescrever.
            self.fields["initial_password"].initial = secrets.token_urlsafe(8)

    def clean_username(self) -> str:
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este usuário já existe.")
        return username

    def save(self, trainer: User) -> User:
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data["username"],
            email=data.get("email", ""),
            password=data["initial_password"],
            first_name=data["first_name"],
            last_name=data.get("last_name", ""),
        )
        Profile.objects.create(user=user, role=Profile.Role.ATHLETE)
        AthleteProfile.objects.create(
            user=user,
            trainer=trainer,
            sex=data["sex"],
            bodyweight_kg=data.get("bodyweight_kg") or None,
        )
        return user


class AthleteProfileEditForm(forms.ModelForm):
    """Treinador edita o perfil antropométrico de um atleta."""

    class Meta:
        model = AthleteProfile
        fields = [
            "sex", "birth_date", "bodyweight_kg", "weight_class_kg",
            "equipment", "federation",
            "best_squat_kg", "best_bench_kg", "best_deadlift_kg",
        ]
        widgets = {"birth_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} input".strip()


class MyProfileForm(forms.ModelForm):
    """Usuário edita seus próprios dados básicos."""

    first_name = forms.CharField(max_length=150, label="Nome")
    last_name = forms.CharField(max_length=150, required=False, label="Sobrenome")
    email = forms.EmailField(required=False, label="E-mail")

    class Meta:
        model = Profile
        fields = ["phone", "bio"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].initial = self.instance.user.email
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} input".strip()

    def save(self, commit: bool = True) -> Profile:
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data.get("last_name", "")
        user.email = self.cleaned_data.get("email", "")
        if commit:
            user.save()
            profile.save()
        return profile
