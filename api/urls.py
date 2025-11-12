from django.urls import path
from .views import upload_nfe, health_check, exemplo_json, index, redirecionar_menu, consultar_rag
from .gerenciamento_views import (
    menu_principal, gerenciar_cadastros,
    listar_pessoas, atualizar_pessoa, alterar_status_pessoa,
    listar_classificacoes, atualizar_classificacao, alterar_status_classificacao,
    listar_movimentos, listar_parcelas, atualizar_parcela
)

app_name = 'api'

urlpatterns = [
    # Rota raiz redireciona para menu
    path('', redirecionar_menu, name='home'),
    
    # Menu principal e navegação
    path('menu/', menu_principal, name='menu_principal'),
    path('extracao/', index, name='extracao'),  # Alias para extração
    path('gerenciar/', gerenciar_cadastros, name='gerenciar_cadastros'),
    
    # APIs de Pessoas
    path('gerenciar/pessoas/', listar_pessoas, name='listar_pessoas'),
    path('gerenciar/pessoas/<int:pessoa_id>/', atualizar_pessoa, name='atualizar_pessoa'),
    path('gerenciar/pessoas/<int:pessoa_id>/status/', alterar_status_pessoa, name='alterar_status_pessoa'),
    
    # APIs de Classificações
    path('gerenciar/classificacoes/', listar_classificacoes, name='listar_classificacoes'),
    path('gerenciar/classificacoes/<int:classificacao_id>/', atualizar_classificacao, name='atualizar_classificacao'),
    path('gerenciar/classificacoes/<int:classificacao_id>/status/', alterar_status_classificacao, name='alterar_status_classificacao'),
    
    # APIs de Movimentos
    path('gerenciar/movimentos/', listar_movimentos, name='listar_movimentos'),
    
    # APIs de Parcelas
    path('gerenciar/parcelas/', listar_parcelas, name='listar_parcelas'),
    path('gerenciar/parcelas/<int:parcela_id>/', atualizar_parcela, name='atualizar_parcela'),
    
    # Rotas existentes do sistema de extração
    path('upload/', upload_nfe, name='upload_nfe'),
    path('health/', health_check, name='health_check'),
    path('exemplo/', exemplo_json, name='exemplo_json'),
    
    # Rota do Agente 3 - Consulta RAG
    path('consulta-rag/', consultar_rag, name='consultar_rag'),
]