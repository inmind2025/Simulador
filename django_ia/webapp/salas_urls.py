from django.urls import path
from .views import salas as salas_views

urlpatterns = [
    path('criar/', salas_views.criar_sala, name='criar_sala'),
    path('', salas_views.lista_salas_admin, name='lista_salas_admin'),
    path('<int:sala_id>/detalhes/', salas_views.detalhe_sala_admin, name='detalhe_sala_admin'),
    path('<int:sala_id>/editar/', salas_views.editar_sala, name='editar_sala'),
    path('<int:sala_id>/excluir/', salas_views.excluir_sala, name='excluir_sala'),

    # URLs do Cliente
    path('entrar/', salas_views.entrar_sala, name='entrar_sala'),
    path('<int:sala_id>/', salas_views.detalhe_sala_cliente, name='detalhe_sala_cliente'),
    path('<int:sala_id>/iniciar-atendimento/', salas_views.iniciar_atendimento_sorteio, name='iniciar_atendimento_sorteio'),
    path('<int:sala_id>/participante/<int:participante_id>/historico/', salas_views.historico_chats_participante, name='historico_chats_participante'),
]
