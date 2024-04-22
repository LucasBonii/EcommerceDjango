from django.db.models import Max, Min
from django.core.mail import send_mail
from django.http import HttpResponse
import csv
import math

def filtrar_produtos(produtos, filtro, preco_minimo=0, preco_maximo=1_000_000, tamanho=None):
    if filtro:
        if "-" in filtro:
            categoria, tipo = filtro.split("-")
            produtos = produtos.filter(tipo__slug=tipo, categoria__slug=categoria)
        else:
            produtos = produtos.filter(categoria__slug=filtro)
    return produtos

def preco_min_max(produtos):
    minimo=0
    maximo=0
    if len(produtos) > 0:
        minimo = list(produtos.aggregate(Min('preco')).values())[0]
        minimo=round(minimo, 2)
        maximo = list(produtos.aggregate(Max('preco')).values())[0]
        
        maximo = math.ceil(maximo)

    return minimo, maximo


def ordenar_produtos(produtos, ordem):
    if ordem=="relevancia":
        lista_produtos = []
        for produto in produtos:
            lista_produtos.append((produto.total_vendas(), produto))
        lista_produtos = sorted(lista_produtos, key=lambda x: x[0], reverse=True)
        produtos = [item[1] for item in lista_produtos]
    elif ordem=="maior-preco":
        produtos = produtos.order_by("-preco")
    elif ordem=="menor-preco":
        produtos = produtos.order_by("preco")

    return produtos

def enviar_email(pedido):
    email = pedido.cliente.email
    assunto = "Pedido aprovado!"
    corpo = f"""Parabéns! Seu pedido foi aprovado!
    ID do Pedido: {pedido.id}
    Valor total: {pedido.preco_total}"""
    remetente = "bolordboni6@gmail.com"
    send_mail(assunto, corpo, remetente, [email])

def exportar_csv(informacoes):
    colunas = informacoes.model._meta.fields
    nome_colunas = [coluna.name for coluna in colunas]
    print(nome_colunas)
    resposta = HttpResponse(content_type="text/csv")
    resposta["Content-Disposition"] = f"attachment; filename={informacoes.model._meta.db_table}.csv"

    creator = csv.writer(resposta, delimiter=";")
    creator.writerow(nome_colunas)
    for linha in informacoes.values_list():
        creator.writerow(linha)

    return resposta
