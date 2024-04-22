from .models import Pedido, ItensPedido, Cliente, Categoria, Tipo


def carrinho(request):
    qtd_produtos_carrinho = 0
    if request.user.is_authenticated:
        cliente = request.user.cliente
    else:
        if request.COOKIES.get("id_sessao"):
            id_sessao = request.COOKIES.get("id_sessao")
            cliente, criado =Cliente.objects.get_or_create(id_sessao=id_sessao)
        else:
            return {"qtd_produtos_carrinho": qtd_produtos_carrinho}
    
    pedido, criado = Pedido.objects.get_or_create(cliente=cliente, finalizado=False)
    itens_pedido = ItensPedido.objects.filter(pedido=pedido)
    for item in itens_pedido:
        qtd_produtos_carrinho += item.quantidade

    return {"qtd_produtos_carrinho": qtd_produtos_carrinho}

def categorias_tipos(request):
    tipos_navbar = Tipo.objects.all()
    categorias_navbar = Categoria.objects.all
    return {"categorias_navbar": categorias_navbar, "tipos_navbar": tipos_navbar}

def pertence_grupo(request):
    equipe = False
    if request.user.is_authenticated:
        if request.user.groups.filter(name='equipe').exists():
            equipe = True
    return {"equipe": equipe}
