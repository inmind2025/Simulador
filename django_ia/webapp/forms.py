# webapp/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm # Ainda podemos usar algumas coisas dele, mas não herdaremos diretamente para o formulário principal
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

# Textos de ajuda para os campos (mantidos)
USERNAME_HELP_TEXT = '''
<span class="form-text text-muted">
    <small>
        No máximo 150 caracteres. Letras, números e @/./_/-/ somente
    </small>
</span>
'''

PASSWORD_HELP_TEXT_SINGLE = _( # Novo help_text para UM campo de senha
    "Your password must contain at least 8 characters and can’t be too similar to your other personal information."
)

class SignUpForm(forms.ModelForm): # <<<< MUDANÇA AQUI: Agora herda de forms.ModelForm
    # Campos que você quer no formulário, incluindo a única senha
    username = forms.CharField(
        label="",
        max_length=150,
        help_text=USERNAME_HELP_TEXT,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Usuário"
            }
        )
    )

    email = forms.EmailField(
        label="",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Endereço de E-mail"
            }
        ),
        required=True,
    )

    first_name = forms.CharField(
        label="",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Primeiro Nome"
            }
        ),
        required=True,
    )

    last_name = forms.CharField(
        label="",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Sobrenome"
            }
        ),
        required=True,
    )

    password = forms.CharField( # <<<< APENAS UM CAMPO DE SENHA AQUI
        label=_("Password"), # Deixando em inglês por enquanto, como você pediu
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password" # Placeholder para o campo de senha
            }
        ),
        help_text=PASSWORD_HELP_TEXT_SINGLE, # Usando o novo help text
    )
    
    role = forms.ChoiceField(
        label="",
        choices=[('aluno', 'Aluno'), ('administrador', 'Administrador')],
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        )
    )


    class Meta: # <<<< MUDANÇA AQUI: Sem herdar de UserCreationForm.Meta
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password", # <<<< APENAS 'password' aqui
        )

    # REMOVIDO: O método __init__ personalizado não é mais necessário para modificar os atributos,
    # pois eles foram definidos diretamente na declaração dos campos acima.
    # Se você ainda precisar de lógica no __init__, adicione-a.
    # No entanto, a lógica de password e password2 foi movida para a view.

    def save(self, commit=True): # <<<< SOBRESCRITA DO MÉTODO SAVE PARA HASH DA SENHA
        user = super().save(commit=False) # Salva o usuário sem a senha ainda
        user.set_password(self.cleaned_data["password"]) # Define a senha com hashing
        if commit:
            user.save()
        return user

from .models import Personagem, Sala

class SalaForm(forms.ModelForm):
    personagens_disponiveis = forms.ModelMultipleChoiceField(
        queryset=Personagem.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Personagens Disponíveis para a Sala"
    )

    class Meta:
        model = Sala
        fields = ['nome', 'capacidade_maxima', 'personagens_disponiveis']
        labels = {
            'nome': 'Nome da Sala',
            'capacidade_maxima': 'Nº Máximo de Participantes',
        }