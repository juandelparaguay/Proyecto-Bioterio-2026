"""
Crea/actualiza los grupos de roles después de aplicar migraciones.
- Administrador: todos los permisos de insumos y animales.
- Investigados/Operador: ver todo + agregar/cambiar "movimientos".
"""
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group

class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Correo de contacto")
    first_name = forms.CharField(label="Nombre", required=False)
    last_name = forms.CharField(label="Apellido", required=False)
    # Evitamos consultar DB en import-time:
    role = forms.ModelChoiceField(
        label="Rol (Grupo)",
        queryset=Group.objects.none(),
        required=False,
        help_text="Rol del usuario (Administrador / Investigador)",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = Group.objects.all().order_by("name")
        for name, field in self.fields.items():
            css = "form-select" if name == "role" else "form-control"
            field.widget.attrs.setdefault("class", css)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
            role = self.cleaned_data.get("role")
            if role:
                user.groups.clear()
                user.groups.add(role)
        return user


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label="Nombre", required=False)
    last_name = forms.CharField(label="Apellido", required=False)
    is_active = forms.BooleanField(label="Activo", required=False)
    role = forms.ModelChoiceField(
        label="Rol (Grupo)",
        queryset=Group.objects.none(),
        required=False,
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_active", "role")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = Group.objects.all().order_by("name")
        for name, field in self.fields.items():
            css = "form-select" if name == "role" else "form-control"
            field.widget.attrs.setdefault("class", css)

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            role = self.cleaned_data.get("role")
            if role:
                user.groups.clear()
                user.groups.add(role)
        return user


# usuarios/forms.py
from django import forms
from django.contrib.auth import password_validation

class PasswordChangeCustomForm(forms.Form):
    old_password = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    def __init__(self, user, *args, **kwargs):
        """
        Recibimos el usuario logueado para poder verificar la contraseña actual.
        """
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old = self.cleaned_data.get("old_password")
        if not self.user.check_password(old):
            raise forms.ValidationError("La contraseña actual no es correcta.")
        return old

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")

        if p1 and p2 and p1 != p2:
            self.add_error("new_password2", "Las contraseñas nuevas no coinciden.")
            return cleaned

        # Validar con los validadores de Django (longitud mínima, etc.)
        if p1:
            password_validation.validate_password(p1, self.user)

        return cleaned
