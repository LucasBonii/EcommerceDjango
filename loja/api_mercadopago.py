import mercadopago

public_key = "TEST-862476eb-d5e8-4a80-87cb-abd964a0cd1a"
token = "TEST-7127635920031469-032922-2905777d2642d4cecfac70354af75f5e-444575516"

def criar_pagamento(itens_pedido, link):
    # Configure as credenciais
    sdk = mercadopago.SDK(token)
    
    # Crie um item na preferência
    itens = []
    for item in itens_pedido:
        quantidade = int(item.quantidade)
        nome_produto = item.item_estoque.produto.nome
        preco_unitario = float(item.item_estoque.produto.preco)
        itens.append({
            "title": nome_produto,
            "quantity": quantidade,
            "unit_price": preco_unitario,
            })

    preference_data = {
        "items": itens,
        "auto_return": "all",
        "back_urls": {
            "success": link,
            "pending": link,
            "failure": link,
        }
        
    }
    resposta = sdk.preference().create(preference_data)
    link_pagamento = resposta["response"]["init_point"]
    id_pagamento = resposta["response"]["id"]
    return link_pagamento, id_pagamento
