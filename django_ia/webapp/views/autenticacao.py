# webapp/views/autenticacao.py

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout
from webapp.forms import SignUpForm # Importa o formulário de registro

def signin(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Você logou com sucesso !!")
            if user.profile.role == 'administrador':
                return redirect("lista_salas_admin")
            else:
                return redirect("bem_vindo")
        else:
            messages.error(request, "Falha ao efetuar login !!")
            return redirect("correcao")

    return render(request, "correcao.html")

def signout(request):
    logout(request)
    messages.success(request, "Você efetuou logout")
    return redirect("correcao")

def signup(request):
    contexto = {
        "view_data":{
            "id": "registro",
            "titulo": "Registro de Usuário"
        }
    }

    if request.method =="POST":
        form = SignUpForm(request.POST)
        contexto["form"] = form
        if form.is_valid():
            user = form.save() # <<<< O form.save() AGORA JÁ FAZ O HASH DA SENHA
            user.profile.role = form.cleaned_data.get('role')
            user.profile.save()
            # Não precisamos mais autenticar novamente aqui, pois o usuário já foi criado
            # e a senha já foi definida e hashed.
            login(request, user) # Faz o login do usuário recém-criado e salvo
            messages.success(request, "Você criou uma conta com sucesso !")
            return redirect("bem_vindo")
        # Se o formulário não for válido, ele será renderizado novamente com os erros.
    else: # Requisição GET
        contexto["form"] = SignUpForm()
        
    return render(request, "registro.html", contexto)