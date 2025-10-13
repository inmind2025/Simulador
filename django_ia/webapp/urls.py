from django.urls import path, include
from webapp.views import openai, autenticacao

urlpatterns = [
    path('salas/', include('webapp.salas_urls')),
    path('dominante', openai.dominante, name='dominante'),
    path('influente', openai.influente, name='influente'),
    path('analitico', openai.analitico, name='analitico'),
    path('estavel', openai.estavel, name='estavel'),
    path('bem-vindo', openai.bem_vindo, name='bem_vindo'),
    path('correcao', openai.correcao, name='correcao'),
    path('criacao', openai.criacao, name='criacao'),
    path('geral', openai.geral, name='geral'),
    path('mapa-mental', openai.mapa_mental, name='mapa_mental'),
    path('mapa-mental/download-pdf', openai.download_mapa_pdf, name='download_mapa_pdf'),
    
    path('enviar_resposta/', openai.enviar_resposta_vendedor, name='enviar_resposta_vendedor'),
    path('reiniciar/', openai.reiniciar_simulacao, name='reiniciar_simulacao'),
    path('signin', autenticacao.signin, name='signin'),
    path('signout', autenticacao.signout, name='signout'),
    path('registro/', autenticacao.signup, name='registro'),
    path('historico', openai.historico, name='historico'),
    path('historico/simulacoes/', openai.historico_simulacoes, name='historico_simulacoes'),
    path('historico/simulacao/<int:simulacao_id>/', openai.conversation_detail, name='conversation_detail'),
]
