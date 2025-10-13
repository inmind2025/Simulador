from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from webapp.models import Sala, SimulacaoAtendimento, Personagem
from webapp.forms import SalaForm

@login_required
def criar_sala(request):
    if request.user.profile.role != 'administrador':
        messages.error(request, "Apenas administradores podem criar salas.")
        return redirect('bem_vindo')

    if request.method == 'POST':
        form = SalaForm(request.POST)
        if form.is_valid():
            sala = form.save(commit=False)
            sala.administrador = request.user
            sala.save()
            # O form.save() não lida com ManyToMany, então salvamos separadamente
            form.save_m2m()
            messages.success(request, f'A sala "{sala.nome}" foi criada com sucesso!')
            return redirect('lista_salas_admin')
    else:
        form = SalaForm()
    
    personagens = Personagem.objects.all()

    context = {
        'form': form,
        'personagens': personagens,
        'views': {'id': 'criar_sala', 'titulo': 'Criar Nova Sala de Treinamento'}
    }
    return render(request, 'salas/criar_sala.html', context)

@login_required
def lista_salas_admin(request):
    if request.user.profile.role != 'administrador':
        messages.error(request, "Acesso não autorizado.")
        return redirect('bem_vindo')

    salas = Sala.objects.filter(administrador=request.user).order_by('-data_criacao')
    context = {
        'salas': salas,
        'views': {'id': 'lista_salas', 'titulo': 'Minhas Salas de Treinamento'}
    }
    return render(request, 'salas/lista_salas_admin.html', context)

@login_required
def detalhe_sala_admin(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)

    # Garante que apenas o admin que criou a sala possa vê-la
    if sala.administrador != request.user:
        messages.error(request, "Você não tem permissão para ver esta sala.")
        return redirect('lista_salas_admin')

    context = {
        'sala': sala,
        'views': {'id': 'detalhe_sala', 'titulo': f'Detalhes da Sala: {sala.nome}'}
    }
    return render(request, 'salas/detalhe_sala_admin.html', context)


# --- Views do Cliente ---

@login_required
def entrar_sala(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo_acesso', '').upper()
        if not codigo:
            messages.error(request, "Por favor, insira um código de acesso.")
            return redirect('bem_vindo')
        
        try:
            sala = Sala.objects.get(codigo_acesso=codigo)
            
            if sala.participantes.count() >= sala.capacidade_maxima:
                messages.error(request, f'A sala "{sala.nome}" está cheia.')
                return redirect('bem_vindo')

            if request.user in sala.participantes.all():
                messages.warning(request, f'Você já está na sala "{sala.nome}".')
            else:
                sala.participantes.add(request.user)
                messages.success(request, f'Você entrou na sala "{sala.nome}" com sucesso!')

        except Sala.DoesNotExist:
            messages.error(request, "Código de acesso inválido.")
    
    return redirect('bem_vindo')

@login_required
def detalhe_sala_cliente(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)

    if request.user not in sala.participantes.all():
        messages.error(request, "Você não tem permissão para ver esta sala.")
        return redirect('bem_vindo')

    context = {
        'sala': sala,
        'views': {'id': 'detalhe_sala_cliente', 'titulo': sala.nome}
    }
    return render(request, 'salas/detalhe_sala_cliente.html', context)

@login_required
def iniciar_atendimento_sorteio(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    if request.user not in sala.participantes.all():
        messages.error(request, "Acesso negado.")
        return redirect('bem_vindo')

    personagens = list(sala.personagens_disponiveis.all())
    if not personagens:
        messages.error(request, "Esta sala não tem personagens disponíveis para simulação.")
        return redirect('detalhe_sala_cliente', sala_id=sala.id)
    
    # Sorteio
    import random
    personagem_sorteado = random.choice(personagens)
    
    # Limpa a sessão de chat anterior para garantir uma nova simulação
    if 'chat_display' in request.session:
        del request.session['chat_display']
    if 'gemini_chat_internal_history' in request.session:
        del request.session['gemini_chat_internal_history']
    
    # Guarda o ID da sala e do personagem na sessão
    request.session['current_sala_id'] = sala.id
    request.session['current_personagem_id'] = personagem_sorteado.id
    request.session.save()  # Força o salvamento da sessão

    # Redireciona para a view do perfil sorteado
    nome_view_perfil = personagem_sorteado.perfil_disc
    return redirect(nome_view_perfil)

@login_required
def historico_chats_participante(request, sala_id, participante_id):
    sala = get_object_or_404(Sala, id=sala_id)
    participante = get_object_or_404(User, id=participante_id)

    # Validações de segurança
    if sala.administrador != request.user:
        messages.error(request, "Acesso não autorizado.")
        return redirect('lista_salas_admin')
    if participante not in sala.participantes.all():
        messages.error(request, "Este usuário não é participante da sala.")
        return redirect('detalhe_sala_admin', sala_id=sala.id)

    simulacoes = SimulacaoAtendimento.objects.filter(sala=sala, user=participante).order_by('-start_time')

    context = {
        'sala': sala,
        'participante': participante,
        'simulacoes': simulacoes,
        'views': {'id': 'historico_participante', 'titulo': f'Histórico de {participante.username} em {sala.nome}'}
    }
    return render(request, 'salas/historico_participante.html', context)

@login_required
def editar_sala(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    if sala.administrador != request.user:
        messages.error(request, "Você não tem permissão para editar esta sala.")
        return redirect('lista_salas_admin')

    if request.method == 'POST':
        form = SalaForm(request.POST, instance=sala)
        if form.is_valid():
            form.save()
            messages.success(request, f'A sala "{sala.nome}" foi atualizada com sucesso!')
            return redirect('lista_salas_admin')
    else:
        form = SalaForm(instance=sala)

    personagens = Personagem.objects.all()

    context = {
        'form': form,
        'sala': sala,
        'personagens': personagens,
        'views': {'id': 'editar_sala', 'titulo': f'Editando Sala: {sala.nome}'}
    }
    return render(request, 'salas/editar_sala.html', context)

@login_required
def excluir_sala(request, sala_id):
    sala = get_object_or_404(Sala, id=sala_id)
    if sala.administrador != request.user:
        messages.error(request, "Você não tem permissão para excluir esta sala.")
        return redirect('lista_salas_admin')

    if request.method == 'POST':
        nome_sala = sala.nome
        sala.delete()
        messages.success(request, f'A sala "{nome_sala}" foi excluída com sucesso.')
        return redirect('lista_salas_admin')
    
    # Se não for POST, apenas redireciona, pois a confirmação é via JS.
    return redirect('lista_salas_admin')
