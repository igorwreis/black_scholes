Precificação de Opções pelo modelo Black and Scholes, a partir de informações divulgadas pela B3 e taxa de juros desejada pelo usuário.

    -->> Calcula preços de opções do mercado brasileiro pelo método Black and Scholes,
    com base em informações divulgadas pela B3 e considerando valores de volatilidade
    anualizada para 1, 3, 6 e 12 meses (4 preços são informados).
    Os valores, bem como outras informações, são retornados em forma de dicionario python <<--
    
        Arg:
        a (str): Obrigatorio - Codigo da opcao de compra/venda a ser pesquisado,
        deve ser informado entre aspas. Exemplo: 'PETRR271', ou em forma de variável do tipo string
        t (float): Opcional - Taxa livre de risco a ser considerada nos cálculos,
        deve ser informada em formato decimal. Exemplo: para uma taxa de 5%, informar 0.05
        Manter nulo ou 0 para utilizar a taxa DI atualizada informada pela B3

IMPORTANTE: REALIZAR A INSTALACAO DAS BIBLIOTECAS ABAIXO NO AMBIENTE A SER UTILIZADO
pip install scipy
pip install selenium

Erros são comuns devido a instabilidades no portal da B3.
