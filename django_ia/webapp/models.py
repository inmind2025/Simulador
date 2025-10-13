from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[('cliente', 'Cliente'), ('administrador', 'Administrador')])

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Registros(models.Model):
    choices = [
        ("criacao","criacao"),
        ("correcao","correcao"),
        ("geral","geral"),
    ]
    user = models.ForeignKey(User, related_name="registros", on_delete=models.DO_NOTHING)
    pergunta = models.TextField(max_length=5000)
    resposta = models.TextField(max_length=5000)
    linguagem = models.CharField(max_length=50)
    data = models.DateTimeField(auto_now_add=True, blank=True)
    tipo = models.CharField(max_length=50, choices=choices, null=True)

class SimulacaoAtendimento(models.Model):
    """
    Represents uma sessão completa de simulação de atendimento.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='simulacoes_atendimento')
    sala = models.ForeignKey('Sala', on_delete=models.SET_NULL, null=True, blank=True, related_name='simulacoes')
    
    # Campo para armazenar o prompt inicial ou um resumo da simulação, se desejar.
    # Pode ser útil para entender o contexto de cada simulação.
    initial_prompt_summary = models.CharField(max_length=255, blank=True, null=True) 
    
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True) # Para marcar quando a simulação foi "encerrada" ou reiniciada

    class Meta:
        verbose_name = "Simulação de Atendimento"
        verbose_name_plural = "Simulações de Atendimento"
        ordering = ['-start_time'] # Ordena por data de início, do mais recente para o mais antigo

    def __str__(self):
        return f"Simulação de {self.user.username} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"

class MensagemSimulacao(models.Model):
    """
    Representa uma única mensagem dentro de uma sessão de simulação de atendimento.
    """
    simulacao = models.ForeignKey(SimulacaoAtendimento, on_delete=models.CASCADE, related_name='mensagens')
    
    SENDER_CHOICES = [
        ('cliente_ia', 'Cliente (IA)'),
        ('vendedor_usuario', 'Vendedor (Usuário)'),
    ]
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES, verbose_name="Remetente")
    
    message_content = models.TextField(verbose_name="Conteúdo da Mensagem")
    timestamp = models.DateTimeField(auto_now_add=True) # Registra a data e hora automaticamente

    class Meta:
        verbose_name = "Mensagem da Simulação"
        verbose_name_plural = "Mensagens da Simulação"
        ordering = ['timestamp'] # Ordena as mensagens cronologicamente dentro de cada simulação

    def __str__(self):
        return f"{self.sender} ({self.simulacao.user.username} em {self.timestamp.strftime('%H:%M')}): {self.message_content[:50]}..."


class Personagem(models.Model):
    PERFIL_CHOICES = [
        ('dominante', 'Dominante'),
        ('influente', 'Influente'),
        ('estavel', 'Estável'),
        ('analitico', 'Analítico'),
    ]
    nome_criativo = models.CharField(max_length=100, unique=True)
    perfil_disc = models.CharField(max_length=20, choices=PERFIL_CHOICES)
    descricao = models.TextField()

    def __str__(self):
        return self.nome_criativo

    @property
    def short_name(self):
        return self.nome_criativo.split(',')[0].strip()

class Sala(models.Model):
    nome = models.CharField(max_length=100)
    administrador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='salas_criadas')
    data_criacao = models.DateTimeField(auto_now_add=True)
    codigo_acesso = models.CharField(max_length=10, unique=True, blank=True)
    capacidade_maxima = models.PositiveIntegerField(default=20)
    personagens_disponiveis = models.ManyToManyField(Personagem, related_name='salas')
    participantes = models.ManyToManyField(User, related_name='salas_participando', blank=True)

    def save(self, *args, **kwargs):
        if not self.codigo_acesso:
            # Gera um código único de 6 dígitos/letras
            import string
            import random
            caracteres = string.ascii_uppercase + string.digits
            while True:
                codigo = ''.join(random.choices(caracteres, k=6))
                if not Sala.objects.filter(codigo_acesso=codigo).exists():
                    self.codigo_acesso = codigo
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nome} ({self.administrador.username})'
