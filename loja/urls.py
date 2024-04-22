from django.urls import path
from django.contrib.auth import views
from .views import *

urlpatterns = [
    path('', Homepage, name='homepage'),
    path('loja/', Loja, name='loja'),
    path('loja/<str:filtro>/', Loja, name='loja'),
    path('produto/<int:id_produto>/', Ver_produto, name='ver_produto'),
    path('produto/<int:id_produto>/<int:id_cor>', Ver_produto, name='ver_produto'),
    path('carrinho/', Carrinho, name='carrinho'),
    path('checkout/', Checkout, name='checkout'),
    path('adicionarcarrinho/<int:id_produto>/', Adicionar_carrinho, name='adicionar_carrinho'),
    path('removercarrinho/<int:id_produto>/', Remover_carrinho, name='remover_carrinho'),
    path('adicionar_endereco/', Adicionar_endereco, name='adicionar_endereco'),
    path('minhaconta/', Minha_conta, name='minha_conta'),
    path('meuspedidos/', Meus_pedidos, name='meus_pedidos'),
    path('login/', Fazer_login, name='fazer_login'),
    path('criarconta/', Criar_conta, name='criar_conta'),
    path('logout/', fazer_logout, name='fazer_logout'),
    path('finalizarcompra/<int:id_pedido>/', Finalizar_compra, name='finalizar_compra'),
    path('pedidoaprovado/<int:id_pedido>/', Pedido_aprovado, name='pedido_aprovado'),
    path('finalizarpagamento/', finalizar_pagamento, name='finalizar_pagamento'),

    path('gerenciarloja/', Gerenciar_loja, name="gerenciar_loja"),
    path('exportarrelatorio/<str:relatorio>', Exportar_relatorio, name="exportar_relatorio"),

    path("password_change/", views.PasswordChangeView.as_view(), name="password_change"),
    path("password_change/done/", views.PasswordChangeDoneView.as_view(), name="password_change_done"),

    path("password_reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
