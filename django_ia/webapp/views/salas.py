from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q, Max
from django.utils import timezone
import datetime
from webapp.models import Sala, SimulacaoAtendimento, Personagem, MensagemSimulacao, AuditoriaSimulacao
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


@login_required
def dashboard(request):
    if request.user.profile.role != 'administrador':
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('bem_vindo')

    salas = Sala.objects.filter(administrador=request.user).annotate(
        num_simulacoes=Count('simulacoes', distinct=True),
        num_participantes=Count('participantes', distinct=True),
        num_mensagens=Count('simulacoes__mensagens', distinct=True),
        ultima_atividade=Max('simulacoes__start_time'),
        sims_concluidas=Count('simulacoes', filter=Q(simulacoes__end_time__isnull=False), distinct=True),
    )

    uma_semana_atras = timezone.now() - datetime.timedelta(days=7)
    trinta_dias_atras = timezone.now() - datetime.timedelta(days=30)

    total_salas = salas.count()
    total_participantes = sum(s.num_participantes for s in salas)
    total_simulacoes = SimulacaoAtendimento.objects.filter(sala__administrador=request.user).count()
    simulacoes_semana = SimulacaoAtendimento.objects.filter(sala__administrador=request.user, start_time__gte=uma_semana_atras).count()
    simulacoes_concluidas = SimulacaoAtendimento.objects.filter(sala__administrador=request.user, end_time__isnull=False).count()
    total_mensagens = MensagemSimulacao.objects.filter(simulacao__sala__administrador=request.user).count()

    taxa_conclusao = round((simulacoes_concluidas / total_simulacoes * 100) if total_simulacoes else 0)

    # Simulacoes por dia (últimos 7 dias) para sparkline
    atividade_diaria = []
    for i in range(6, -1, -1):
        dia = timezone.now().date() - datetime.timedelta(days=i)
        count = SimulacaoAtendimento.objects.filter(
            sala__administrador=request.user,
            start_time__date=dia,
        ).count()
        atividade_diaria.append({'dia': dia.strftime('%d/%m'), 'count': count})

    # Top 5 salas por atividade
    top_salas = salas.order_by('-num_simulacoes')[:5]

    # Distribuição DISC
    disc_counts = {
        'dominante': 0, 'influente': 0, 'estavel': 0, 'analitico': 0
    }
    for sala in salas:
        for p in sala.personagens_disponiveis.all():
            if p.perfil_disc in disc_counts:
                disc_counts[p.perfil_disc] += 1

    # Simulações recentes
    simulacoes_recentes = SimulacaoAtendimento.objects.filter(
        sala__administrador=request.user
    ).select_related('user', 'sala').order_by('-start_time')[:8]

    context = {
        'views': {'id': 'dashboard', 'titulo': 'Dashboard'},
        'total_salas': total_salas,
        'total_participantes': total_participantes,
        'total_simulacoes': total_simulacoes,
        'simulacoes_semana': simulacoes_semana,
        'simulacoes_concluidas': simulacoes_concluidas,
        'total_mensagens': total_mensagens,
        'taxa_conclusao': taxa_conclusao,
        'atividade_diaria': atividade_diaria,
        'top_salas': top_salas,
        'disc_counts': disc_counts,
        'simulacoes_recentes': simulacoes_recentes,
        'salas': salas,
    }
    return render(request, 'dashboard.html', context)


@login_required
def dashboard_sala(request, sala_id):
    if request.user.profile.role != 'administrador':
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('bem_vindo')

    sala = get_object_or_404(Sala, id=sala_id, administrador=request.user)

    simulacoes = SimulacaoAtendimento.objects.filter(sala=sala).select_related('user')
    total_sims = simulacoes.count()
    sims_concluidas = simulacoes.filter(end_time__isnull=False).count()
    taxa_conclusao = round((sims_concluidas / total_sims * 100) if total_sims else 0)
    total_mensagens = MensagemSimulacao.objects.filter(simulacao__sala=sala).count()

    uma_semana_atras = timezone.now() - datetime.timedelta(days=7)
    sims_semana = simulacoes.filter(start_time__gte=uma_semana_atras).count()

    # Atividade diária (7 dias)
    atividade_diaria = []
    for i in range(6, -1, -1):
        dia = timezone.now().date() - datetime.timedelta(days=i)
        count = simulacoes.filter(start_time__date=dia).count()
        atividade_diaria.append({'dia': dia.strftime('%d/%m'), 'count': count})

    # Participantes com suas métricas
    participantes = sala.participantes.all().prefetch_related('simulacoes_atendimento')
    participantes_stats = []
    for u in participantes:
        sims_u = simulacoes.filter(user=u).order_by('-start_time')
        msgs_u = MensagemSimulacao.objects.filter(
            simulacao__sala=sala, simulacao__user=u, sender='vendedor_usuario'
        ).count()
        concl_u = sims_u.filter(end_time__isnull=False).count()

        # Lista completa de simulações do aluno com auditoria
        sims_lista = []
        for s in sims_u.select_related('auditoria'):
            msgs_sim = MensagemSimulacao.objects.filter(
                simulacao=s, sender='vendedor_usuario'
            ).count()
            try:
                aud = s.auditoria
            except Exception:
                aud = None
            sims_lista.append({
                'sim': s,
                'msgs': msgs_sim,
                'auditoria': aud,
            })

        participantes_stats.append({
            'user': u,
            'total_sims': sims_u.count(),
            'concluidas': concl_u,
            'mensagens': msgs_u,
            'ultima': sims_u.aggregate(u=Max('start_time'))['u'],
            'sims_lista': sims_lista,
        })
    participantes_stats.sort(key=lambda x: x['total_sims'], reverse=True)

    # DISC distribution para esta sala
    disc_counts = {'dominante': 0, 'influente': 0, 'estavel': 0, 'analitico': 0}
    for p in sala.personagens_disponiveis.all():
        if p.perfil_disc in disc_counts:
            disc_counts[p.perfil_disc] += 1
    disc_total = sum(disc_counts.values()) or 1

    # Simulações recentes (com auditoria prefetch)
    simulacoes_recentes = simulacoes.order_by('-start_time').select_related('auditoria')[:10]

    # Nota média por participante + notas individuais
    for ps in participantes_stats:
        audits = [sl['auditoria'] for sl in ps['sims_lista'] if sl['auditoria']]
        notas = [a.nota_total for a in audits]
        ps['media_nota']     = round(sum(notas)/len(notas), 1) if notas else None
        ps['qtd_auditorias'] = len(notas)
        ps['notas_sims']     = [
            {'data': a.simulacao.start_time, 'nota': a.nota_total, 'id': a.simulacao_id}
            for a in audits
        ]

    # Média da turma (todas as auditorias da sala)
    todas_notas = AuditoriaSimulacao.objects.filter(
        simulacao__sala=sala
    ).values_list('nota_total', flat=True)
    todas_notas = list(todas_notas)
    media_turma = round(sum(todas_notas)/len(todas_notas), 1) if todas_notas else None
    total_auditorias = len(todas_notas)

    # Rankings
    ranking_notas = sorted(
        [ps for ps in participantes_stats if ps['media_nota'] is not None],
        key=lambda x: x['media_nota'], reverse=True
    )
    ranking_interacoes = sorted(
        participantes_stats,
        key=lambda x: x['mensagens'], reverse=True
    )

    # Simulações concluídas sem auditoria (pendentes)
    sims_ids_auditadas = set(
        AuditoriaSimulacao.objects.filter(simulacao__sala=sala).values_list('simulacao_id', flat=True)
    )
    sims_pendentes_ids = list(
        simulacoes.filter(end_time__isnull=False)
                  .exclude(id__in=sims_ids_auditadas)
                  .values_list('id', flat=True)
    )

    context = {
        'views': {'id': 'dashboard_sala', 'titulo': f'Dashboard · {sala.nome}'},
        'sala': sala,
        'total_sims': total_sims,
        'sims_concluidas': sims_concluidas,
        'taxa_conclusao': taxa_conclusao,
        'total_mensagens': total_mensagens,
        'sims_semana': sims_semana,
        'atividade_diaria': atividade_diaria,
        'participantes_stats': participantes_stats,
        'disc_counts': disc_counts,
        'disc_total': disc_total,
        'simulacoes_recentes': simulacoes_recentes,
        'personagens': sala.personagens_disponiveis.all(),
        'media_turma': media_turma,
        'total_auditorias': total_auditorias,
        'ranking_notas': ranking_notas,
        'ranking_interacoes': ranking_interacoes,
        'sims_pendentes_ids': sims_pendentes_ids,
    }
    return render(request, 'dashboard_sala.html', context)


import json as _json
import re as _re

@login_required
def imprimir_simulacao(request, sala_id, simulacao_id):
    """Página limpa para impressão/export PDF de uma simulação."""
    if request.user.profile.role != 'administrador':
        messages.error(request, 'Acesso restrito a administradores.')
        return redirect('bem_vindo')

    sala = get_object_or_404(Sala, id=sala_id, administrador=request.user)
    sim  = get_object_or_404(SimulacaoAtendimento, id=simulacao_id, sala=sala)
    msgs = sim.mensagens.order_by('timestamp')

    try:
        auditoria = sim.auditoria
    except Exception:
        auditoria = None

    context = {
        'sala': sala,
        'sim': sim,
        'msgs': msgs,
        'auditoria': auditoria,
    }
    return render(request, 'salas/imprimir_simulacao.html', context)


@login_required
@require_POST
def toggle_notas_liberadas(request, sala_id):
    """Liga/desliga a liberação de notas para os alunos da sala."""
    if request.user.profile.role != 'administrador':
        from django.http import JsonResponse
        return JsonResponse({'error': 'Acesso negado'}, status=403)
    sala = get_object_or_404(Sala, id=sala_id, administrador=request.user)
    sala.notas_liberadas = not sala.notas_liberadas
    sala.save(update_fields=['notas_liberadas'])
    from django.http import JsonResponse
    return JsonResponse({'notas_liberadas': sala.notas_liberadas})

@login_required
def auditar_simulacao(request, sala_id, simulacao_id):
    """Chama o Gemini para auditar uma simulação e salva o resultado."""
    if request.user.profile.role != 'administrador':
        return _json_error('Acesso negado', 403)

    sala = get_object_or_404(Sala, id=sala_id, administrador=request.user)
    sim  = get_object_or_404(SimulacaoAtendimento, id=simulacao_id, sala=sala)

    # Monta transcrição
    msgs = sim.mensagens.order_by('timestamp')
    if not msgs.exists():
        return _json_error('Simulação sem mensagens para auditar.')

    transcript_lines = []
    for m in msgs:
        role = 'CLIENTE' if m.sender == 'cliente_ia' else 'CONSULTOR'
        transcript_lines.append(f'{role}: {m.message_content}')
    transcript = '\n'.join(transcript_lines)

    prompt = f"""Você é um Especialista em Auditoria de Vendas e Qualidade.
Analise a transcrição abaixo e retorne SOMENTE um JSON válido (sem markdown, sem texto extra).

CRITÉRIOS DE AVALIAÇÃO:

1. Método A PONTE (máx 5.0):
   - abordar (máx 0.6): saudação "Seja bem-vindo" (0.3) + apresentação pelo nome (0.3)
   - pesquisar (máx 0.3): identificou o que o cliente procura
   - oferecer (máx 1.2): produto de valor agregado (0.6) + mencionou Crediário/parcelamento (0.6)
   - negociar (máx 2.0): evitou desconto imediato (0.5) + contornou objeções (0.8) + negociou garantia/serviços (0.7)
   - tomar_iniciativa (máx 0.3): conduziu para o fechamento
   - estender (máx 0.6): ofertou cartão ou pediu contato

2. Técnicas EA (máx 4.0):
   - spin (máx 2.0): 0.5 por etapa identificada (Situação, Problema, Implicação, Necessidade)
   - cbv (máx 2.0): 0.67 por técnica (Características, Benefícios, Vantagens)

3. ortografia (inicia em 1.0, -0.25 por erro grave de escrita/concordância)
   - Analise APENAS as falas do CONSULTOR
   - Considere erros de: ortografia, concordância verbal/nominal, pontuação grave, abreviações informais (vc, pq, tb, etc.), gírias inadequadas
   - Liste CADA erro encontrado com o trecho exato, a correção e o tipo de erro

Formato JSON EXATO (sem texto fora do JSON):
{{
  "ponte_abordar": 0.0,
  "ponte_pesquisar": 0.0,
  "ponte_oferecer": 0.0,
  "ponte_negociar": 0.0,
  "ponte_tomar_iniciativa": 0.0,
  "ponte_estender": 0.0,
  "spin": 0.0,
  "cbv": 0.0,
  "ortografia": 1.0,
  "feedback": "Resumo com pontos fortes e oportunidades de melhoria do consultor.",
  "erros_ortografia": [
    {{
      "trecho": "trecho exato da fala do consultor com o erro",
      "correcao": "como deveria ser escrito corretamente",
      "tipo": "ortografia | concordância verbal | concordância nominal | pontuação | abreviação informal | gíria",
      "desconto": 0.25
    }}
  ]
}}

Se não houver erros de ortografia, retorne "erros_ortografia": [].

TRANSCRIÇÃO:
{transcript}
"""

    try:
        import google.generativeai as genai
        from webapp.views.openai import GEMINI_API_KEY
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Remove possível bloco markdown ```json ... ```
        raw = _re.sub(r'^```[a-z]*\n?', '', raw)
        raw = _re.sub(r'\n?```$', '', raw)

        data = _json.loads(raw)
    except Exception as e:
        return _json_error(f'Erro ao chamar Gemini: {e}')

    def clamp(v, max_v):
        try:
            return round(min(max(float(v), 0), max_v), 2)
        except:
            return 0.0

    pa  = clamp(data.get('ponte_abordar', 0),         0.6)
    pp  = clamp(data.get('ponte_pesquisar', 0),        0.3)
    po  = clamp(data.get('ponte_oferecer', 0),         1.2)
    pn  = clamp(data.get('ponte_negociar', 0),         2.0)
    pti = clamp(data.get('ponte_tomar_iniciativa', 0), 0.3)
    pe  = clamp(data.get('ponte_estender', 0),         0.6)
    spin = clamp(data.get('spin', 0),                  2.0)
    cbv  = clamp(data.get('cbv', 0),                   2.0)
    ort  = clamp(data.get('ortografia', 1.0),          1.0)
    feedback = str(data.get('feedback', ''))
    erros = data.get('erros_ortografia', [])
    if not isinstance(erros, list):
        erros = []

    nota_ponte = round(pa + pp + po + pn + pti + pe, 2)
    nota_ea    = round(spin + cbv, 2)
    nota_total = round(nota_ponte + nota_ea + ort, 2)

    auditoria, _ = AuditoriaSimulacao.objects.update_or_create(
        simulacao=sim,
        defaults=dict(
            ponte_abordar=pa, ponte_pesquisar=pp, ponte_oferecer=po,
            ponte_negociar=pn, ponte_tomar_iniciativa=pti, ponte_estender=pe,
            spin_total=spin, cbv_total=cbv, ortografia=ort,
            nota_ponte=nota_ponte, nota_ea=nota_ea, nota_total=nota_total,
            feedback=feedback, erros_ortografia=erros,
        )
    )

    from django.http import JsonResponse
    return JsonResponse({
        'ok': True,
        'nota_total': nota_total,
        'nota_ponte': nota_ponte,
        'nota_ea': nota_ea,
        'ortografia': ort,
        'feedback': feedback,
        'erros_ortografia': erros,
        'detalhe': {
            'abordar': pa, 'pesquisar': pp, 'oferecer': po,
            'negociar': pn, 'tomar_iniciativa': pti, 'estender': pe,
            'spin': spin, 'cbv': cbv,
        }
    })


def _json_error(msg, status=400):
    from django.http import JsonResponse
    return JsonResponse({'ok': False, 'error': msg}, status=status)


