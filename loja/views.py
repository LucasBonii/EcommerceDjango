from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .models import *
from .utils import *
import uuid
from .api_mercadopago import *
from datetime import datetime


def Homepage(request):
    banners = Banner.objects.filter(ativo=True)
    context = {'banners': banners}
    return render(request, 'homepage.html', context=context)

def Loja(request, filtro=None):
    #Filtra os produtos ativos e conforme os filtros do link da pagina || Cria a variavel produto
    produtos = Produto.objects.filter(ativo=True)
    produtos = filtrar_produtos(produtos, filtro)

    if request.method == "POST":            #Se o formulário for preenchido
        dados = request.POST.dict()

        #Produtos serão os produtos ativos e com filtro de preço
        produtos = produtos.filter(preco__gte=dados.get('preco_minimo'), preco__lte=dados.get('preco_maximo'))
        if "tamanho" in dados:         #Se o usuário selecionar o tamanho, pegará todos os itens do estoque que tem aquele tamanho, e puxará a foreign key pra produtos
            itens= ItemEstoque.objects.filter(tamanho=dados.get('tamanho'), produto__in=produtos)
            ids_produtos = itens.values_list('produto', flat=True).distinct()
            produtos = Produto.objects.filter(id__in=ids_produtos)
        if "tipo" in dados:             #Filtrará o produto de acordo com o tipo selecionado
            produtos = produtos.filter(tipo__slug=dados.get("tipo"))
        if "categoria" in dados:                #Filtrará o produto de acordo com a categoria selecionada
            produtos = produtos.filter(categoria__slug=dados.get("categoria"))

    ids_categorias = produtos.values_list("categoria", flat=True).distinct()
    categorias = Categoria.objects.filter(id__in=ids_categorias)
    itens= ItemEstoque.objects.filter(quantidade__gt=0, produto__in=produtos)
    tamanhos= itens.values_list('tamanho', flat=True).distinct()
    minimo, maximo = preco_min_max(produtos)        #Define o mínimo e o máximo preço dentre os produtos ativos, será utilizado no filtro de preço
    ordem = request.GET.get("ordem", "relevancia")
    produtos = ordenar_produtos(produtos, ordem)

    context = {'produtos': produtos, "minimo": minimo, "maximo": maximo, "tamanhos":tamanhos, "categorias":categorias}
    return render(request, 'loja.html', context=context)

def Ver_produto(request, id_produto, id_cor=None):
    tem_estoque = False
    cores = {}
    tamanhos = {}
    cor_selecionada = None
    produto = Produto.objects.get(id=id_produto)
    itens_estoque = ItemEstoque.objects.filter(produto=produto, quantidade__gt=0)
    if len(itens_estoque)>0:
        tem_estoque = True
        cores = {item.cor for item in itens_estoque}
        if id_cor:
          cor_selecionada = Cor.objects.get(id=id_cor)
          itens_estoque = ItemEstoque.objects.filter(produto=produto, quantidade__gt=0, cor__id = id_cor)  
          tamanhos = {item.tamanho for item in itens_estoque}
    similares = Produto.objects.filter(categoria__id=produto.categoria.id, tipo__id=produto.tipo.id).exclude(id=produto.id)[:4]
    context = {'produto': produto, "tem_estoque": tem_estoque, "cores":cores,
                "tamanhos": tamanhos, "cor_selecionada": cor_selecionada, "similares": similares}
    return render(request, "ver_produto.html", context=context)

def Adicionar_carrinho(request, id_produto):
    if request.method == "POST" and id_produto:
            dados = request.POST.dict()
            tamanho = dados.get("tamanho")
            id_cor = dados.get("cor")
            if not tamanho:
                return redirect(reverse('ver_produto', args=[id_produto]))
            #pegar o cliente
            resposta = redirect('carrinho')
            if request.user.is_authenticated:
                cliente = request.user.cliente
            else:
                if request.COOKIES.get("id_sessao"):
                    id_sessao = request.COOKIES.get("id_sessao")
                else:
                    id_sessao =  str(uuid.uuid4())
                    resposta.set_cookie(key="id_sessao", value=id_sessao, max_age=2_592_000) #max_age = 30 days
                cliente, criado = Cliente.objects.get_or_create(id_sessao=id_sessao)
            
            pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=False)
            item_estoque = ItemEstoque.objects.get(produto__id=id_produto, cor__id =id_cor, tamanho=tamanho)
            item_pedido, criado = ItensPedido.objects.get_or_create(item_estoque=item_estoque, pedido=pedido)
            if item_pedido.quantidade < item_pedido.item_estoque.quantidade:
                item_pedido.quantidade += 1
                item_pedido.save()

            return resposta
    else:
        return redirect('loja')

def Remover_carrinho(request, id_produto):
    if request.method == "POST" and id_produto:
            dados = request.POST.dict()
            tamanho = dados.get("tamanho")
            id_cor = dados.get("cor")
            if not tamanho:
                return redirect(reverse('ver_produto', args=[id_produto]))
            #pegar o cliente
            if request.user.is_authenticated:
                cliente = request.user.cliente
            else:
                if request.COOKIES.get("id_sessao"):
                    id_sessao = request.COOKIES.get("id_sessao")
                    cliente, criado =Cliente.objects.get_or_create(id_sessao=id_sessao)
                else:
                    return redirect('loja')
            pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=False)
            item_estoque = ItemEstoque.objects.get(produto__id=id_produto, cor__id =id_cor, tamanho=tamanho)
            item_pedido, criado = ItensPedido.objects.get_or_create(item_estoque=item_estoque, pedido=pedido)
            item_pedido.quantidade -= 1
            item_pedido.save()
            if item_pedido.quantidade <= 0:
                item_pedido.delete()
            return redirect('carrinho')
    else:
            return redirect('loja')
    
def Carrinho(request):
    if request.user.is_authenticated:
        cliente = request.user.cliente
    else:
        if request.COOKIES.get("id_sessao"):
            id_sessao = request.COOKIES.get("id_sessao")
            cliente, criado =Cliente.objects.get_or_create(id_sessao=id_sessao)
        else:
            context = {"cliente_existente": False, "itens_pedido": None, "pedido": None}
            return render(request, 'carrinho.html', context=context)
    pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=False)
    itens_pedido = ItensPedido.objects.filter(pedido=pedido)
    context = {"itens_pedido": itens_pedido, "pedido": pedido, "cliente_existente": True}
    return render(request, 'carrinho.html', context=context)


def Checkout(request):
    if request.user.is_authenticated:
        cliente = request.user.cliente
    else:
        if request.COOKIES.get("id_sessao"):
            id_sessao = request.COOKIES.get("id_sessao")
            cliente, criado =Cliente.objects.get_or_create(id_sessao=id_sessao)
        else:
            return redirect('loja')
    pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=False)
    enderecos =  Endereco.objects.filter(cliente=cliente)
    context = {"pedido": pedido, "enderecos": enderecos, "erro":None}
    return render(request, 'checkout.html', context=context)

def Finalizar_compra(request, id_pedido):
    if request.method == "POST":
        erro = None
        dados = request.POST.dict()

        total = dados.get("total")
        total = float(total.replace(",", "."))
        pedido = Pedido.objects.get(id = id_pedido)

        if total != float(pedido.preco_total):
            erro = "preco"

        if not "endereco" in dados:
            erro = "endereco"
        else:
            id_endereco = dados.get("endereco")
            endereco = Endereco.objects.get(id=id_endereco)
            pedido.endereco = endereco

        if not request.user.is_authenticated:
            email = dados.get("email")
            try:
                validate_email(email)
            except ValidationError:
                erro = "email"
            if not erro:
                clientes = Cliente.objects.filter(email=email)
                if clientes:
                    pedido.cliente = clientes[0]
                else:
                    pedido.cliente.email = email
                    pedido.cliente.save()

        codigo_transacao = f"{pedido.id}-{datetime.now().timestamp()}"
        pedido.cod_transacao = codigo_transacao
        pedido.save()
        if erro:
            enderecos = Endereco.objects.filter(cliente=pedido.cliente)
            context = {"erro": erro, "pedido": pedido, "enderecos": enderecos}
            return render(request, "checkout.html", context)
        else:
            itens_pedido = ItensPedido.objects.filter(pedido=pedido)
            link = request.build_absolute_uri(reverse('finalizar_pagamento'))
            link_pagamento, id_pagamento = criar_pagamento(itens_pedido, link)
            pagamento = Pagamento.objects.create(id_pagamento=id_pagamento, pedido=pedido)
            pagamento.save()
            return redirect(link_pagamento)
    else:
        return redirect('loja')

def finalizar_pagamento(request):
    dados = request.GET.dict()
    status = dados.get("status")
    id_pagamento = dados.get("preference_id")
    if status == "approved":
        pagamento = Pagamento.objects.get(id_pagamento=id_pagamento)
        pagamento.aprovado = True
        pedido = pagamento.pedido
        pedido.finalizado = True
        pedido.data_finalizacao = datetime.now()
        pagamento.save()
        pedido.save()
        itens_pedido = ItensPedido.objects.filter(pedido=pedido.id)
        for item in itens_pedido:
            item.item_estoque.quantidade -= item.quantidade
            item.item_estoque.save()
        enviar_email(pedido)
        if request.user.is_authenticated:
            return redirect("meus_pedidos")
        else:
            return redirect("pedido_aprovado", pedido.id)
    else:
        return redirect('checkout')
    

def Pedido_aprovado(request, id_pedido):
    pedido = Pedido.objects.get(id=id_pedido)
    context = {"pedido": pedido}
    return render(request, "pedido_aprovado.html", context)

def Adicionar_endereco(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            cliente = request.user.cliente
        else:
            if request.COOKIES.get("id_sessao"):
                id_sessao = request.COOKIES.get("id_sessao")
                cliente, criado =Cliente.objects.get_or_create(id_sessao=id_sessao)

        dados = request.POST.dict()
        endereco = Endereco.objects.create(cliente=cliente, rua=dados.get("rua"), numero=int(dados.get("numero")), estado=dados.get("estado"),
                                           cidade=dados.get("cidade"), complemento=dados.get("complemento"), cep=dados.get("cep"))
        endereco.save()
        return redirect('checkout')
    else:
        pass
    context={}
    return render(request, "adicionar_endereco.html", context)

@login_required
def Minha_conta(request):
    erro = None
    if request.method == "POST":
        dados = request.POST.dict()
        if "senha_atual" in dados:
            senha_atual = dados.get("senha_atual")
            nova_senha = dados.get("nova_senha")
            nova_senha_confirmacao = dados.get("nova_senha_confirmacao")
            if nova_senha == nova_senha_confirmacao:
                usuario = authenticate(request, username=request.user.email, password=senha_atual)
                if usuario:
                    usuario.set_password(nova_senha)
                    usuario.save()
                    messages.success(request, "Senha alterada com sucesso!")
                else:
                    erro = "senha_incorreta"
            else:
                erro = 'senhas_diferentes'
        elif "email" in dados:
            email = dados.get("email")
            nome = dados.get("nome")
            telefone = dados.get("telefone")
            if email != request.user.email:
                usuarios = User.objects.filter(email=email)
                if len(usuarios) > 0:
                    erro = 'email_existente'
            if not erro:
                cliente = request.user.cliente
                cliente.email = email
                request.user.email = email
                request.user.username = email
                cliente.nome = nome
                cliente.telefone = telefone
                cliente.save()
                request.user.save()
                messages.success(request, "Dados alterados com sucesso!")
        else:
            erro = "preenchimento"
    context= {"erro": erro}
    return render(request, 'usuario/minha_conta.html', context)

@login_required
def Meus_pedidos(request):
    cliente = request.user.cliente
    pedidos = Pedido.objects.filter(finalizado=True, cliente=cliente).order_by("-data_finalizacao")
    context = {"pedidos": pedidos}
    return render(request, "usuario/meus_pedidos.html", context)

def Fazer_login(request):
    erro = False
    if request.user.is_authenticated:
        return redirect('loja')
    if request.method == "POST":
        dados = request.POST.dict()
        if "email" in dados and "senha" in dados:
            email = dados.get("email")
            senha = dados.get("senha")
            usuario = authenticate(request, username=email, password=senha)
            if usuario:
                login(request, usuario)
                return redirect('loja')
            else:
                erro = True
        else:
            erro = True
    context = {"erro": erro}
    return render(request, 'usuario/login.html', context)

def Criar_conta(request):
    erro = None
    if request.user.is_authenticated:
        return redirect('loja')
    if request.method == "POST":
        dados = request.POST.dict()
        if "email" in dados and "senha" in dados and "confirmacao_senha" in dados:
            email = dados.get("email")
            senha = dados.get("senha")
            confirmacao_senha = dados.get("confirmacao_senha")
            try:
                validate_email(email)
            except ValidationError:
              erro= "email_invalido"
            if senha == confirmacao_senha:
                usuario, criado = User.objects.get_or_create(username=email, email=email)
                if not criado:
                    erro = "usuario_existente"
                else:
                    usuario.set_password(senha)
                    usuario.save()
                    usuario = authenticate(request, username=email, password=senha)
                    login(request, usuario)

                    if request.COOKIES.get("id_sessao"):
                        id_sessao = request.COOKIES.get("id_sessao")
                        cliente, criado =Cliente.objects.get_or_create(id_sessao=id_sessao)
                    else:
                        cliente, criado = Cliente.objects.get_or_create(email=email)
                    cliente.usuario = usuario
                    cliente.email = email
                    cliente.save()
                    return redirect('loja')
            else:
                erro= "senhas_diferentes"
        else:
            erro = "preenchimento"
    context = {"erro": erro}
    return render(request, 'usuario/criar_conta.html', context)

@login_required
def fazer_logout(request):
    logout(request)
    return redirect("fazer_login")

@login_required
def Gerenciar_loja(request):
    if request.user.groups.filter(name='equipe').exists():
        pedidos_finalizados = Pedido.objects.filter(finalizado = True)
        qtd_pedidos = len(pedidos_finalizados)
        faturamento = sum([pedido.preco_total for pedido in pedidos_finalizados])
        qtd_produtos = sum([pedido.quantidade_total for pedido in pedidos_finalizados])
        context = {"qtd_pedidos": qtd_pedidos, "faturamento": faturamento, "qtd_produtos": qtd_produtos}
        return render(request, 'interno/gerenciar_loja.html', context)
    else:
        return redirect('loja')
    
@login_required
def Exportar_relatorio(request, relatorio):
    if request.user.groups.filter(name='equipe').exists():
        if relatorio == "pedido":
            informacoes = Pedido.objects.filter(finalizado=True)
        elif relatorio == "cliente":
            informacoes = Cliente.objects.all()
        elif relatorio == "endereco":
            informacoes = Endereco.objects.all()
        return exportar_csv(informacoes)
    else:
        return redirect('gerenciar_loja')