# Erros são comuns devido a instabilidades no portal da B3.

# IMPORTANTE 1: REALIZAR DOWNLOAD DO CHROMEDRIVER E INFORMAR O DIRETORIO DE INSTALACAO NA VARIAVEL ABAIXO
# SITE PARA DOWNLOAD CHROMEDRIVER: https://chromedriver.chromium.org/downloads
dir_chromedriver = r'Caminho\\para\\chromedriver\\chromedriver.exe'

# Horário abertura negociocações e delay de atualização 
# Mudar aqui caso ocorram alteracoes no horario da b3
horario = '10:30' # MANTER FORMATO HH:MM
delay = 30 # Delay de atualização das primeiras negociações do dia

# IMPORTANTE 2: REALIZAR A INSTALACAO DAS BIBLIOTECAS ABAIXO NO AMBIENTE A SER UTILIZADO
# pip install scipy
# pip install selenium

from time import sleep
from math import log, pow, sqrt, exp
from datetime import datetime, date, timedelta
from scipy.stats import norm
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
# RETIRAR/INCLUIR COMENTARIO ABAIXO PARA ATIVAR/DESATIVAR MODO HEADLESS
#options.headless = True

def black_scholes(a, t=0):

    """
    -->> Calcula preços de opções do mercado brasileiro pelo método Black and Scholes,
    com base em informações divulgadas pela B3 e considerando valores de volatilidade
    anualizada para 1, 3, 6 e 12 meses (4 preços são informados).
    Os valores, bem como outras informações, são retornados em forma de dicionario python <<--, 

    Arg:
        a (str): Obrigatorio - Codigo da opcao de compra/venda a ser pesquisado,
        deve ser informado entre aspas. Exemplo: 'PETRR271', ou em forma de variável do tipo string
        t (float): Opcional - Taxa livre de risco a ser considerada nos cálculos,
        deve ser informada em formato decimal. Exemplo: para uma taxa de 5%, informar 0.05
        Manter nulo ou 0 para utilizar a taxa DI atualizada informada pela B3

    Retorna dicionario com informacoes gerais da opcao e preços considerando volatilidade
    anualizada de 1, 3, 6 e 12 meses do ativo objeto, conforme divulgação da B3.

    Importante: para pesquisas realizadas antes das 10:30 da manhã, o programa pesquisará
    o último preço do dia anterior para o ativo objeto, devido a delay de atualização
    do site da Bolsa.

    Erros são comuns devido a instabilidades no portal da B3.
    """

    if type(t) != float and t != 0 or t < 0 or t >= 1:
        return (f'Informe a taxa de juro em formato decimal. Mantenha 0 para utilizar o DI atual.\n'
        'Exemplo: para considerar 5% no cálculo, informe 0.05')

    compra = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
    venda = ['M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']

    dados = consolida_infos(a, t)
    if type(dados) is not dict:
        return 'Erro na consolidação de todos os valores. Verifique conexão e código do ativo.'

    chaves = list(dados.keys())
    valores = list(dados.values())
    
    ativo_obj = valores[chaves.index('Papel')]
    opcao = valores[chaves.index('Opção')]
    estilo = valores[chaves.index('Estilo')]
    venc = valores[chaves.index('Venc')]
    periodo = contdiastrab(venc)/252
    preco_strike = valores[chaves.index('Strike')]
    preco_atual = valores[chaves.index('Ultimo_Preco')]
    vol_anual_1 = valores[chaves.index('VolAnual_1_mes')]
    vol_anual_3 = valores[chaves.index('VolAnual_3_meses')]
    vol_anual_6 = valores[chaves.index('VolAnual_6_meses')]
    vol_anual_12 = valores[chaves.index('VolAnual_12_meses')]
    taxa_juro = valores[chaves.index('Taxa')]
    taxa = log(1 + taxa_juro)

    compra_ou_venda = ''

    if opcao[4].upper() in compra:        
        compra_ou_venda = 'Compra'
        preco1 = call(preco_atual, preco_strike, taxa, vol_anual_1, periodo)
        preco2 = call(preco_atual, preco_strike, taxa, vol_anual_3, periodo)
        preco3 = call(preco_atual, preco_strike, taxa, vol_anual_6, periodo)
        preco4 = call(preco_atual, preco_strike, taxa, vol_anual_12, periodo)

    elif opcao[4].upper() in venda:
        compra_ou_venda = 'Venda'
        preco1 = put(preco_atual, preco_strike, taxa, vol_anual_1, periodo)
        preco2 = put(preco_atual, preco_strike, taxa, vol_anual_3, periodo)
        preco3 = put(preco_atual, preco_strike, taxa, vol_anual_6, periodo)
        preco4 = put(preco_atual, preco_strike, taxa, vol_anual_12, periodo)

    elif opcao[4].upper() not in compra and opcao[4].upper() not in venda:
        return (f'ERRO! Não foi possível identificar se a opção {opcao} se referere\n'
        'a compra ou venda. Verifique as informações e tente novamente.')

    print('Consolidando cálculo...\n')
    sleep(2)

    dic = {"Ativo Objeto": ativo_obj,
            "Opção": opcao,
            "Compra/Venda": compra_ou_venda,
            "Estilo": estilo,
            "Data Vencimento": venc,
            "DUs até Vencimento": round(periodo * 252),
            "Preço Alvo": preco_strike,
            "Preço Atual": preco_atual,
            "Preço_Vol1mes": preco1,
            "Preço_Vol3meses": preco2,
            "Preço_Vol6meses": preco3,
            "Preço_Vol12meses": preco4,
            "Taxa Utilizada": '{:.2%}'.format(taxa_juro), 
            }

    return dic


def call(a, s, t, v, p):

    """
    -->> Calcula preço de opções de compra pelo método Black and Scholes,

    Arg:
        a (float): Obrigatorio - Preço atual do ativo objeto
        s (float): Obrigatorio - Preço de exercicio (strike) da opção
        t (float): Obrigatorio - Taxa livre de risco a ser considerada no cálculo,
        Informar em formato decimal. Exemplo: para 5%, informar 0.05
        v (float): Obrigatorio - Volatilidade anualizada, em formato decimal
        p (float): Obrigatorio - Dias para o vencimento
    """

    d1 = (log(a/s) + (t + pow(v, 2)/2) * p) / (v * sqrt(p))
    d2 = d1 - v * sqrt(p)
    c = a * norm.cdf(d1, loc=0, scale=1) - s * exp(-t * p) * norm.cdf(d2, loc=0, scale=1)
    c = float('{:.2f}'.format(c))
    return c


def put(a, s, t, v, p):

    """
    -->> Calcula preço de opções de venda pelo método Black and Scholes,

    Arg:
        a (float): Obrigatorio - Preço atual do ativo objeto
        s (float): Obrigatorio - Preço de exercicio (strike) da opção
        t (float): Obrigatorio - Taxa livre de risco a ser considerada no cálculo,
        Informar em formato decimal. Exemplo: para 5%, informar 0.05
        v (float): Obrigatorio - Volatilidade anualizada, em formato decimal
        p (float): Obrigatorio - Dias para o vencimento
    """

    d1 = (log(a/s) + (t + pow(v, 2)/2) * p) / (v * sqrt(p))
    d2 = d1 - v * sqrt(p)
    p = s * exp(-t * p) * norm.cdf(-d2, loc=0, scale=1) - a * norm.cdf(-d1, loc=0, scale=1)
    p = float('{:.2f}'.format(p))
    return p


def consolida_infos(a, t=0):

    print('\nPesquisando a opção informada...\n')

    dados_op = busca_codigo(a)
    if type(dados_op) == str:
        return dados_op

    chaves_op = list(dados_op.keys())
    valores_op = list(dados_op.values())
    isin = valores_op[chaves_op.index('ISIN')][0]
    objeto = valores_op[chaves_op.index('Objeto')][0]
    venc = valores_op[chaves_op.index('Vencimento')][0]
    estilo = valores_op[chaves_op.index('Estilo')][0]
    strike = valores_op[chaves_op.index('Strike')][0]

    print('Pesquisando pelo ativo alvo...\n')

    papel = isin[2:7]
    ultimo_negocio = ultimo_preco(papel)
    if type(ultimo_negocio) == str:
        return ultimo_negocio

    chaves_ultimo = list(ultimo_negocio.keys())
    valores_ultimo = list(ultimo_negocio.values())
    preco_ultimo = valores_ultimo[chaves_ultimo.index('Preco')][0]

    print('Buscando informações de volatilidade...\n')

    dados_vol = busca_vol(papel)
    if type(dados_vol) == str:
        return dados_vol

    chaves_vol = list(dados_vol.keys())
    valores_vol = list(dados_vol.values())
    vol_1 = valores_vol[chaves_vol.index('VolAnual_1_mes')][0]/100
    vol_3 = valores_vol[chaves_vol.index('VolAnual_3_meses')][0]/100
    vol_6 = valores_vol[chaves_vol.index('VolAnual_6_meses')][0]/100
    vol_12 = valores_vol[chaves_vol.index('VolAnual_12_meses')][0]/100

    if t == 0:
        print('Coletando taxa DI atualizada...\n')
        taxa = busca_di()
    else:
        taxa = float(t)
        
    if type(taxa) == str:
        return type(taxa)

    dic = {"Papel": papel,
            "Opção": objeto,
            "Estilo": estilo,
            "Venc": venc,
            "Strike": strike,
            "Ultimo_Preco": preco_ultimo,
            "VolAnual_1_mes": vol_1,
            "VolAnual_3_meses": vol_3,
            "VolAnual_6_meses": vol_6,
            "VolAnual_12_meses": vol_12,
            "Taxa": taxa, 
            }

    for k, v in dic.items():
        if v == '' or v == ' ' or v == 0:
            return (f'Há valores não encontrados para precificar o ativo {a}.\n'
            f'Informações sem valor: {k}')

    return dic


def busca_codigo(a):

    """
    -->> Captura informacoes da opcao divulgadas pela B3, em forma de dicionario python <<--

    Arg:
        a (str): Obrigatorio - Codigo da opcao de compra/venda a ser pesquisada

    Retorna dicionario com informacoes de codigo, vencimento, preco de exercicio e outros.

    No caso de existir mais de um registro com o codigo pesquisado,
    o programa retornara as informacoes da primeira linha da tabela encontrada.
    
    Retorna mensagem de erro caso o ativo informado nao seja uma opcao de compra/venda, 
    ou se nao for encontrado nenhum registro no portal da B3.
    """
    
    try:

        ativo = str(a).strip().upper().replace(" ", "")

        url = "http://bvmf.bmfbovespa.com.br/cias-listadas/Titulos-Negociaveis/BuscaTitulosNegociaveis.aspx?idioma=pt-br"
        driver = webdriver.Chrome(executable_path=dir_chromedriver, options=options)
        driver.get(url)

        sleep(1)

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((
            By.XPATH, "//*[@id='ctl00_contentPlaceHolderConteudo_Menu_tabItem2']/span/span")))

        driver.find_element_by_xpath("//*[@id='ctl00_contentPlaceHolderConteudo_Menu_tabItem2']/span/span").click()

        sleep(1)

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((
            By.XPATH, "//*[@id='ctl00_contentPlaceHolderConteudo_txtCodigo_txtCodigo_text']")))

        codigo = driver.find_element_by_xpath("//*[@id='ctl00_contentPlaceHolderConteudo_txtCodigo_txtCodigo_text']")
        codigo.send_keys(ativo)

        sleep(1)

        driver.find_element_by_xpath("//*[@id='ctl00_contentPlaceHolderConteudo_btnBuscarCodigo']").click()

        sleep(1)

        try:
            sleep(3)
            erro = driver.find_element_by_xpath("//*[@id='ctl00_contentPlaceHolderConteudo_lblTexto3']").get_attribute('textContent')
            if erro == 'Empresa/Código não encontrado.':
                driver.quit()
                return f'ERRO! O código --{ativo.upper()}-- não foi encontrado. Verifique e tente novamente.'

        except:
            try:
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((
                By.XPATH, "//*[@id='ctl00_contentPlaceHolderConteudo_ctl00_grdDados']")))

                sleep(1)

                confirma_opc = driver.find_element_by_xpath("//*[@id='ctl00_contentPlaceHolderConteudo_ctl00_lblDescricao']").get_attribute('textContent')

                if confirma_opc[:6] != 'Opções':
                    driver.quit()
                    return f'ERRO! O código --{ativo.upper()}-- não é uma opção válida. Verifique e tente novamente.'

                else:
                    dic = {"ISIN": [],
                            "Especif": [],
                            "Objeto": [],
                            "Vencimento": [],
                            "Strike": [],
                            "Moeda": [],
                            "Protegida": [],
                            "Estilo": [], 
                            }

                    # Busca informacoes do ativo informado
                    ISIN = driver.find_element_by_xpath("//*[@id='ctl00_contentPlaceHolderConteudo_ctl00_grdDados_ctl01']/tbody/tr/td[1]").get_attribute('textContent').strip()
                    Especif = driver.find_element_by_xpath("//*[@id='ctl00_contentPlaceHolderConteudo_ctl00_grdDados_ctl01']/tbody/tr/td[2]").get_attribute('textContent').strip()
                    Objeto = driver.find_element_by_xpath("//*[@id='ctl00_contentPlaceHolderConteudo_ctl00_grdDados_ctl01']/tbody/tr/td[3]").get_attribute('textContent').strip()
                    Vencimento = driver.find_element_by_xpath("//*[@id='ctl00_contentPlaceHolderConteudo_ctl00_grdDados_ctl01']/tbody/tr/td[4]").get_attribute('textContent').strip()

                    Strike = driver.find_element_by_xpath("//*[@id='ctl00_contentPlaceHolderConteudo_ctl00_grdDados_ctl01']/tbody/tr/td[5]").get_attribute('textContent').strip()
                    Strike = Strike.replace(',', '.')
                    Strike = '{:.2f}'.format(float(Strike))
                    Strike = float(Strike)

                    Moeda = driver.find_element_by_xpath("//*[@id='ctl00_contentPlaceHolderConteudo_ctl00_grdDados_ctl01']/tbody/tr/td[6]").get_attribute('textContent').strip()
                    Protegida = driver.find_element_by_xpath("//*[@id='ctl00_contentPlaceHolderConteudo_ctl00_grdDados_ctl01']/tbody/tr/td[7]").get_attribute('textContent').strip()
                    Estilo = driver.find_element_by_xpath("//*[@id='ctl00_contentPlaceHolderConteudo_ctl00_grdDados_ctl01']/tbody/tr/td[8]").get_attribute('textContent').strip()

                    dic["ISIN"].append(ISIN)
                    dic["Especif"].append(Especif)
                    dic["Objeto"].append(Objeto)
                    dic["Vencimento"].append(Vencimento)
                    dic["Strike"].append(Strike)
                    dic["Moeda"].append(Moeda)
                    dic["Protegida"].append(Protegida)
                    dic["Estilo"].append(Estilo)

                    driver.quit()
                    return dic

            except:
                driver.quit()
                return f'ERRO! Informações de --{ativo.upper()}-- não encontradas. Verifique e tente novamente.'

    except:
        driver.quit()
        return 'ERRO! Opção não encontrada. Verifique a conexao, o codigo do ativo e tente novamente.'


def ultimo_preco(a, d=0, p=0):

    """
    -->> Coleta preco da ultima negociacao da acao desejada conforme
    data informada e de acordo com informacoes divulgadas pela B3 <<--

    a (str): Obrigatorio - Codigo do ativo a ser pesquisado
    d (str): Opcional - data a ser pesquisada, em formato string DD/MM/AAAA.
    Manter nulo ou 0 para data atual ou ultima data util.
    p (int): Opcional - dias uteis anteriores a data-base.
    Manter nulo ou 0 para data atual ou ultima data util.

    Retorna dicionario com informacoes do ultimo negocio realizado na data informada.
    Delay de aprox 15 minutos quando o mercado estiver aberto.
    """

    try:

        ativo = str(a).strip().upper().replace(" ", "")

        if p > 0: p = p * -1

        # DEVIDO AO DELAY DE ATUALIZACAO DO SITE DA B3, AS PRIMEIRAS OPERACOES DO DIA
        # PODEM DEMORAR A APARECER, CAUSANDO ERRO NO CÓDIGO. PARA TRATAR ISSO, O ROBO
        # BUSCARA INFORMACOES DO DIA ANTERIOR SE A PESQUISA OCORRER ANTES DAS 10:30
        hora_pregao = int(horario[0:2])
        minutos_pregao = int(horario[4:6])
        hora_agora = datetime.now().hour
        minutos_agora = datetime.now().minute

        if hora_agora <= hora_pregao and minutos_agora < minutos_pregao + delay:
            d1 = datetime.now().date() - timedelta (days=1)
            data_preco = diatrabalho(p, d1) 
        else:
            data_preco = diatrabalho(p, d)

        url = "https://arquivos.b3.com.br/negocios/?lang=pt"
        driver = webdriver.Chrome(executable_path=dir_chromedriver, options=options)
        driver.get(url)

        sleep(1)

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((
            By.XPATH, "//*[@id='root']/div/div/div[1]/div/div/div[1]")))

        sleep(1)

        codigo = driver.find_element_by_xpath("//*[@id='root']/div/div/div[1]/div/div/div[1]")

        ActionChains(driver).move_to_element(codigo).click().send_keys(ativo).perform()

        sleep(1)

        driver.find_element_by_xpath("//*[@id='root']/div/div/div[1]/div/div/div[2]/div").click()
        dia = driver.find_element_by_xpath("//*[@id='root']/div/div/div[1]/div/div/div[2]/div")

        ActionChains(driver).move_to_element(dia).key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
        sleep(1)
        ActionChains(driver).send_keys(Keys.BACKSPACE).perform()
        sleep(1)
        ActionChains(driver).send_keys(data_preco).perform()
        sleep(1)

        driver.find_element_by_xpath("//*[@id='root']/div/div/div[1]/div/div/div[3]").click()

        sleep(1)

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((
            By.XPATH, "//*[@id='root']/div/div/div[2]/div[1]/table/tbody/tr[1]/td[1]")))

        dic = {
        "Papel": [],
        "Quantidade": [],
        "Preco": [],
        "Num Neg": [],
        "Data Ref": [],
        "Hora": [],
        }

        Papel = driver.find_element_by_xpath("//*[@id='root']/div/div/div[2]/div[1]/table/tbody/tr[1]/td[1]").get_attribute('textContent').strip()
        Quantidade = driver.find_element_by_xpath("//*[@id='root']/div/div/div[2]/div[1]/table/tbody/tr[1]/td[2]").get_attribute('textContent').strip()
        Quantidade = str(Quantidade)
        Quantidade = Quantidade.replace('.', '')
        Quantidade = '{:.0f}'.format(float(Quantidade))
        Quantidade = float(Quantidade)

        Preco = driver.find_element_by_xpath("//*[@id='root']/div/div/div[2]/div[1]/table/tbody/tr[1]/td[3]").get_attribute('textContent').strip()
        Preco = Preco.replace(',', '.')
        Preco = '{:.2f}'.format(float(Preco))
        Preco = float(Preco)

        Num_Neg = driver.find_element_by_xpath("//*[@id='root']/div/div/div[2]/div[1]/table/tbody/tr[1]/td[4]").get_attribute('textContent').strip()
        Num_Neg = Num_Neg.replace('.', '')
        Num_Neg = str(Num_Neg)

        Data_Ref = driver.find_element_by_xpath("//*[@id='root']/div/div/div[2]/div[1]/table/tbody/tr[1]/td[5]").get_attribute('textContent').strip()
        Hora = driver.find_element_by_xpath("//*[@id='root']/div/div/div[2]/div[1]/table/tbody/tr[1]/td[6]").get_attribute('textContent').strip()

        dic["Papel"].append(Papel)
        dic["Quantidade"].append(Quantidade)
        dic["Preco"].append(Preco)
        dic["Num Neg"].append(Num_Neg)
        dic["Data Ref"].append(Data_Ref)
        dic["Hora"].append(Hora)

        driver.quit()
        return dic

    except:
        driver.quit()
        return f'ERRO! Ação --{ativo.upper()}-- não encontrada. Verifique conexao, data e codigo do ativo.'


def busca_vol(a):

    """
    -->> Captura volatilidade do ativo informado de acordo com informacoes divulgadas pela B3 <<--

    Arg:
        a (str): Obrigatorio - Codigo do ativo a ser pesquisado

    Retorna dicionario com Desvio e Volatilidade de 1, 3, 6 e 12 meses.
    
    Erros sao comuns devido a instabilidades no portal da B3. Caso o programa
    nao conclua a captura, basta roda-lo novamente apos alguns instantes.
    """

    try:

        ativo = str(a).strip().upper().replace(" ", "")

        url = "https://sistemaswebb3-listados.b3.com.br/securitiesVolatilityPage/standard-deviation/false?language=pt-br"
        driver = webdriver.Chrome(executable_path=dir_chromedriver, options=options)
        driver.get(url)

        sleep(1)

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((
            By.XPATH, "//*[@id='divContainerIframeB3']/standard-deviation/form/div/div/div[2]/table")))

        sleep(1)

        codigo = driver.find_element_by_xpath("//*[@id='nameOrCode']")
        codigo.send_keys(ativo)

        sleep(1)

        driver.find_element_by_xpath("//*[@id='divContainerIframeB3']/standard-deviation/form/div/div/div[1]/div[3]/button").click()

        sleep(1)

        WebDriverWait(driver, 3).until(EC.presence_of_element_located((
            By.XPATH, "//*[@id='divContainerIframeB3']/standard-deviation/form/div/div/div[2]/table")))

        dic = {"Codigo": [],
                "Nome": [],
                "Especif": [],
                "DesvPad_1_mes": [],
                "VolAnual_1_mes": [],
                "DesvPad_3_meses": [],
                "VolAnual_3_meses": [],
                "DesvPad_6_meses": [],
                "VolAnual_6_meses": [],
                "DesvPad_12_meses": [],
                "VolAnual_12_meses": [], 
                }

        codigo = driver.find_element_by_xpath("//*[@id='divContainerIframeB3']/standard-deviation/form/div/div/div[2]/table/tbody/tr[1]/td[1]").get_attribute('textContent')
        nome = driver.find_element_by_xpath("//*[@id='divContainerIframeB3']/standard-deviation/form/div/div/div[2]/table/tbody/tr[1]/td[2]").get_attribute('textContent')
        espec = driver.find_element_by_xpath("//*[@id='divContainerIframeB3']/standard-deviation/form/div/div/div[2]/table/tbody/tr[1]/td[3]").get_attribute('textContent')

        desv1 = driver.find_element_by_xpath("//*[@id='divContainerIframeB3']/standard-deviation/form/div/div/div[2]/table/tbody/tr[1]/td[4]").get_attribute('textContent')
        desv1 = desv1.replace(',', '.')
        desv1 = round(float(desv1), 4)

        vol1 = driver.find_element_by_xpath("//*[@id='divContainerIframeB3']/standard-deviation/form/div/div/div[2]/table/tbody/tr[1]/td[5]").get_attribute('textContent')
        vol1 = vol1.replace(',', '.')
        vol1 = round(float(vol1), 2)

        desv3 = driver.find_element_by_xpath("//*[@id='divContainerIframeB3']/standard-deviation/form/div/div/div[2]/table/tbody/tr[1]/td[6]").get_attribute('textContent')
        desv3 = desv3.replace(',', '.')
        desv3 = round(float(desv3), 4)

        vol3 = driver.find_element_by_xpath("//*[@id='divContainerIframeB3']/standard-deviation/form/div/div/div[2]/table/tbody/tr[1]/td[7]").get_attribute('textContent')
        vol3 = vol3.replace(',', '.')
        vol3 = round(float(vol3), 2)

        desv6 = driver.find_element_by_xpath("//*[@id='divContainerIframeB3']/standard-deviation/form/div/div/div[2]/table/tbody/tr[1]/td[8]").get_attribute('textContent')
        desv6 = desv6.replace(',', '.')
        desv6 = round(float(desv6), 4)

        vol6 = driver.find_element_by_xpath("//*[@id='divContainerIframeB3']/standard-deviation/form/div/div/div[2]/table/tbody/tr[1]/td[9]").get_attribute('textContent')
        vol6 = vol6.replace(',', '.')
        vol6 = round(float(vol6), 2)

        desv12 = driver.find_element_by_xpath("//*[@id='divContainerIframeB3']/standard-deviation/form/div/div/div[2]/table/tbody/tr[1]/td[10]").get_attribute('textContent')
        desv12 = desv12.replace(',', '.')
        desv12 = round(float(desv12), 4)

        vol12 = driver.find_element_by_xpath("//*[@id='divContainerIframeB3']/standard-deviation/form/div/div/div[2]/table/tbody/tr[1]/td[11]").get_attribute('textContent')
        vol12 = vol12.replace(',', '.')
        vol12 = round(float(vol12), 2)

        dic["Codigo"].append(codigo)
        dic["Nome"].append(nome)
        dic["Especif"].append(espec)
        dic["DesvPad_1_mes"].append(desv1)
        dic["VolAnual_1_mes"].append(vol1)
        dic["DesvPad_3_meses"].append(desv3)
        dic["VolAnual_3_meses"].append(vol3)
        dic["DesvPad_6_meses"].append(desv6)
        dic["VolAnual_6_meses"].append(vol6)
        dic["DesvPad_12_meses"].append(desv12)
        dic["VolAnual_12_meses"].append(vol12)

        driver.quit()
        return dic

    except:

        driver.quit()
        return (f'ERRO! Informações de volatidade do ativo --{ativo}-- não encontradas.\n'
        'Verifique a conexao, o codigo do ativo e tente novamente.')


def busca_di():

    """
    -->> Busca taxa DI anual divulgada pela B3, em formato decimal <<--

    """
    url = "http://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/mercado-de-derivativos/indicadores/indicadores-financeiros/"

    try:

        driver = webdriver.Chrome(executable_path=dir_chromedriver, options=options)
        driver.get(url)

        sleep(1)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((
            By.XPATH, "//*[@id='conteudo-principal']/div[4]/div/div/div[2]/div[1]/table/tbody/tr/td")))
        sleep(1)

        di_ano = driver.find_element_by_xpath("//*[@id='conteudo-principal']/div[4]/div/div/div[2]/div[1]/table/tbody/tr/td").get_attribute('textContent')

        di_ano = di_ano.split('%', 1)[0]
        di_ano = di_ano.replace(',', '.')
        di_ano = '{:.4f}'.format((float(di_ano))/100)
        di_ano = float(di_ano)

        driver.quit()
        return di_ano

    except:
        driver.quit()
        return 'ERRO! Não foi possível encontrar informações de taxa DI. Verifique conexão.'


def diatrabalho(p=0, d=0):

    """
    -->> Retorna data util de acordo com relacao de feriados ANBIMA (ja disponibilizada pela
         funcao feriados_lista), periodo e data-base informados pelo usuario (opcionais);
         A relacao de feriados utilizada por essa funcao pode ser
         encontrada em: https://www.anbima.com.br/feriados/feriados.asp 
         Qualquer edicao dessas datas devera ser realizada dentro da funcao feriados_lista() <<--

    Args:
        p (int, optional): Intervalo desejado em DIAS UTEIS (numero inteiro)
        d (str, optional): Data-Base desejada; Manter nulo para data atual

    # IMPORTANTE: se a data-base (seja a informada ou a atual) for um dia nao-util,
        a funcao iniciara a contagem a partir do primeiro dia util anterior a esta

    Returns:
        [date]
    """
    
    try:
        if d == 0:
            d = datetime.now().date()
            
        if type(d) == str:
            d = datetime.strptime(d, '%d/%m/%Y').date()
            
        if type(d) == datetime:
            d = d.date()
            
        if type(p) != int or p % 1 != 0:
            print('[ERRO!] Informe um período em número INTEIRO. Mantenha os campos nulos para\n'
            'data atual e período = 0. Variáveis são aceitas desde que no formato adequado.')
            return False
    
        feriados = feriados_lista()

        while d.strftime('%d/%m/%Y') in feriados or datetime.weekday(d) > 4:
            d = d + timedelta(days=-1)
        
        while p != 0:
            a = p/abs(p)
            d = d + timedelta(days=a)
    
            if d.strftime('%d/%m/%Y') in feriados or datetime.weekday(d) > 4:
                p += 0
            else:
                p -= a
                
    except (ValueError, TypeError, AttributeError):
        print('ERRO! Informações de data.')
    
    return d.strftime('%d/%m/%Y')


def contdiastrab(f=0, i=0, u=0):

    """
    -->> Retorna quantidade de dias-uteis entre duas datas de acordo com relacao de feriados 
         ANBIMA (ja disponibilizada pela funcao feriados_lista), data final informada pelo
         usuario (obrigatoria) e data-base (opcional, igual a data atual se ausente);
         A relacao de feriados utilizada por essa funcao pode ser
         encontrada em: https://www.anbima.com.br/feriados/feriados.asp 
         Qualquer edicao dessas datas devera ser realizada dentro da funcao feriados_lista() <<--

    Args:
        f (data dd/mm/aaaa): data-final, obrigatoria
        i (data dd/mm/aaaa, opcional): Data-Base desejada; Manter nulo para data atual
        u (int, 0 ou 1): incluir ultima dia no calculo

    # IMPORTANTE: se a data-base (seja a informada ou a atual) for um dia nao-util,
        a funcao iniciara a contagem a partir do primeiro dia util anterior a esta;
        O mesmo vale para a data-final

    Returns:
        Numero de dias uteis entre as duas datas, int
    """
    
    try:
        if f == '' or f == 0:
            print('[ERRO] INFORME PELO MENOS UMA DATA! UTILIZAR FORMATO DD/MM/AAAA ENTRE ASPAS SIMPLES')
            return False

        if type(f) == str:
            f = datetime.strptime(f, '%d/%m/%Y').date()

        if type(f) == datetime:
            f = f.date()

        if i == '' or i == 0:
            i = datetime.now().date()
    
        if type(i) == str:
            i = datetime.strptime(i, '%d/%m/%Y').date()

        if type(i) == datetime:
            i = i.date()
        
        if u not in [0, 1]:
            print('[ERRO] Utilize 1 para considerar o último dia-útil no cálculo, ou mantenha nulo.')
            return False
    
        feriados = feriados_lista()

        if i.strftime('%d/%m/%Y') in feriados or datetime.weekday(i) > 4:
            i = i + timedelta(days=-1)

        if f.strftime('%d/%m/%Y') in feriados or datetime.weekday(f) > 4:
            f = f + timedelta(days=-1)

        if f > i:
            freal = f
            ireal = i
        else:
            freal = i
            ireal = f

        cont = 0

        while ireal != freal:
            ireal = ireal + timedelta(days=1)
            if ireal.strftime('%d/%m/%Y') in feriados or datetime.weekday(ireal) > 4:
                cont += 0
            else:
                cont += 1

    except (ValueError, TypeError, AttributeError):
        print('ERRO! Insira a data no formato DD/MM/AAAA (com barras e entre aspas).\n'
        'Mantenha data inicial nula ou 0 para data atual.')

    else:
        return cont + u


def feriados_lista():

    """
    -->> Retorna lista com feriados no formato dd/mm/aaaa (string);
         A relacao de feriados utilizada por essa funcao pode ser
         encontrada em: https://www.anbima.com.br/feriados/feriados.asp 
         Qualquer edicao dessas datas devera ser realizada dentro da funcao <<--
    """

    feriados = [
         '01/01/2001', '26/02/2001', '27/02/2001', '13/04/2001', '21/04/2001', '01/05/2001', '14/06/2001', '07/09/2001',
         '12/10/2001', '02/11/2001', '15/11/2001', '25/12/2001', '01/01/2002', '11/02/2002', '12/02/2002', '29/03/2002',
         '21/04/2002', '01/05/2002', '30/05/2002', '07/09/2002', '12/10/2002', '02/11/2002', '15/11/2002', '25/12/2002',
         '01/01/2003', '03/03/2003', '04/03/2003', '18/04/2003', '21/04/2003', '01/05/2003', '19/06/2003', '07/09/2003',
         '12/10/2003', '02/11/2003', '15/11/2003', '25/12/2003', '01/01/2004', '23/02/2004', '24/02/2004', '09/04/2004',
         '21/04/2004', '01/05/2004', '10/06/2004', '07/09/2004', '12/10/2004', '02/11/2004', '15/11/2004', '25/12/2004',
         '01/01/2005', '07/02/2005', '08/02/2005', '25/03/2005', '21/04/2005', '01/05/2005', '26/05/2005', '07/09/2005',
         '12/10/2005', '02/11/2005', '15/11/2005', '25/12/2005', '01/01/2006', '27/02/2006', '28/02/2006', '14/04/2006',
         '21/04/2006', '01/05/2006', '15/06/2006', '07/09/2006', '12/10/2006', '02/11/2006', '15/11/2006', '25/12/2006',
         '01/01/2007', '19/02/2007', '20/02/2007', '06/04/2007', '21/04/2007', '01/05/2007', '07/06/2007', '07/09/2007',
         '12/10/2007', '02/11/2007', '15/11/2007', '25/12/2007', '01/01/2008', '04/02/2008', '05/02/2008', '21/03/2008',
         '21/04/2008', '01/05/2008', '22/05/2008', '07/09/2008', '12/10/2008', '02/11/2008', '15/11/2008', '25/12/2008',
         '01/01/2009', '23/02/2009', '24/02/2009', '10/04/2009', '21/04/2009', '01/05/2009', '11/06/2009', '07/09/2009',
         '12/10/2009', '02/11/2009', '15/11/2009', '25/12/2009', '01/01/2010', '15/02/2010', '16/02/2010', '02/04/2010',
         '21/04/2010', '01/05/2010', '03/06/2010', '07/09/2010', '12/10/2010', '02/11/2010', '15/11/2010', '25/12/2010',
         '01/01/2011', '07/03/2011', '08/03/2011', '21/04/2011', '22/04/2011', '01/05/2011', '23/06/2011', '07/09/2011',
         '12/10/2011', '02/11/2011', '15/11/2011', '25/12/2011', '01/01/2012', '20/02/2012', '21/02/2012', '06/04/2012',
         '21/04/2012', '01/05/2012', '07/06/2012', '07/09/2012', '12/10/2012', '02/11/2012', '15/11/2012', '25/12/2012',
         '01/01/2013', '11/02/2013', '12/02/2013', '29/03/2013', '21/04/2013', '01/05/2013', '30/05/2013', '07/09/2013',
         '12/10/2013', '02/11/2013', '15/11/2013', '25/12/2013', '01/01/2014', '03/03/2014', '04/03/2014', '18/04/2014',
         '21/04/2014', '01/05/2014', '19/06/2014', '07/09/2014', '12/10/2014', '02/11/2014', '15/11/2014', '25/12/2014',
         '01/01/2015', '16/02/2015', '17/02/2015', '03/04/2015', '21/04/2015', '01/05/2015', '04/06/2015', '07/09/2015',
         '12/10/2015', '02/11/2015', '15/11/2015', '25/12/2015', '01/01/2016', '08/02/2016', '09/02/2016', '25/03/2016',
         '21/04/2016', '01/05/2016', '26/05/2016', '07/09/2016', '12/10/2016', '02/11/2016', '15/11/2016', '25/12/2016',
         '01/01/2017', '27/02/2017', '28/02/2017', '14/04/2017', '21/04/2017', '01/05/2017', '15/06/2017', '07/09/2017',
         '12/10/2017', '02/11/2017', '15/11/2017', '25/12/2017', '01/01/2018', '12/02/2018', '13/02/2018', '30/03/2018',
         '21/04/2018', '01/05/2018', '31/05/2018', '07/09/2018', '12/10/2018', '02/11/2018', '15/11/2018', '25/12/2018',
         '01/01/2019', '04/03/2019', '05/03/2019', '19/04/2019', '21/04/2019', '01/05/2019', '20/06/2019', '07/09/2019',
         '12/10/2019', '02/11/2019', '15/11/2019', '25/12/2019', '01/01/2020', '24/02/2020', '25/02/2020', '10/04/2020',
         '21/04/2020', '01/05/2020', '11/06/2020', '07/09/2020', '12/10/2020', '02/11/2020', '15/11/2020', '25/12/2020',
         '01/01/2021', '15/02/2021', '16/02/2021', '02/04/2021', '21/04/2021', '01/05/2021', '03/06/2021', '07/09/2021',
         '12/10/2021', '02/11/2021', '15/11/2021', '25/12/2021', '01/01/2022', '28/02/2022', '01/03/2022', '15/04/2022',
         '21/04/2022', '01/05/2022', '16/06/2022', '07/09/2022', '12/10/2022', '02/11/2022', '15/11/2022', '25/12/2022',
         '01/01/2023', '20/02/2023', '21/02/2023', '07/04/2023', '21/04/2023', '01/05/2023', '08/06/2023', '07/09/2023',
         '12/10/2023', '02/11/2023', '15/11/2023', '25/12/2023', '01/01/2024', '12/02/2024', '13/02/2024', '29/03/2024',
         '21/04/2024', '01/05/2024', '30/05/2024', '07/09/2024', '12/10/2024', '02/11/2024', '15/11/2024', '25/12/2024',
         '01/01/2025', '03/03/2025', '04/03/2025', '18/04/2025', '21/04/2025', '01/05/2025', '19/06/2025', '07/09/2025',
         '12/10/2025', '02/11/2025', '15/11/2025', '25/12/2025', '01/01/2026', '16/02/2026', '17/02/2026', '03/04/2026',
         '21/04/2026', '01/05/2026', '04/06/2026', '07/09/2026', '12/10/2026', '02/11/2026', '15/11/2026', '25/12/2026',
         '01/01/2027', '08/02/2027', '09/02/2027', '26/03/2027', '21/04/2027', '01/05/2027', '27/05/2027', '07/09/2027',
         '12/10/2027', '02/11/2027', '15/11/2027', '25/12/2027', '01/01/2028', '28/02/2028', '29/02/2028', '14/04/2028',
         '21/04/2028', '01/05/2028', '15/06/2028', '07/09/2028', '12/10/2028', '02/11/2028', '15/11/2028', '25/12/2028',
         '01/01/2029', '12/02/2029', '13/02/2029', '30/03/2029', '21/04/2029', '01/05/2029', '31/05/2029', '07/09/2029',
         '12/10/2029', '02/11/2029', '15/11/2029', '25/12/2029', '01/01/2030', '04/03/2030', '05/03/2030', '19/04/2030',
         '21/04/2030', '01/05/2030', '20/06/2030', '07/09/2030', '12/10/2030', '02/11/2030', '15/11/2030', '25/12/2030',
         '01/01/2031', '24/02/2031', '25/02/2031', '11/04/2031', '21/04/2031', '01/05/2031', '12/06/2031', '07/09/2031',
         '12/10/2031', '02/11/2031', '15/11/2031', '25/12/2031', '01/01/2032', '09/02/2032', '10/02/2032', '26/03/2032',
         '21/04/2032', '01/05/2032', '27/05/2032', '07/09/2032', '12/10/2032', '02/11/2032', '15/11/2032', '25/12/2032',
         '01/01/2033', '28/02/2033', '01/03/2033', '15/04/2033', '21/04/2033', '01/05/2033', '16/06/2033', '07/09/2033',
         '12/10/2033', '02/11/2033', '15/11/2033', '25/12/2033', '01/01/2034', '20/02/2034', '21/02/2034', '07/04/2034',
         '21/04/2034', '01/05/2034', '08/06/2034', '07/09/2034', '12/10/2034', '02/11/2034', '15/11/2034', '25/12/2034',
         '01/01/2035', '05/02/2035', '06/02/2035', '23/03/2035', '21/04/2035', '01/05/2035', '24/05/2035', '07/09/2035',
         '12/10/2035', '02/11/2035', '15/11/2035', '25/12/2035', '01/01/2036', '25/02/2036', '26/02/2036', '11/04/2036',
         '21/04/2036', '01/05/2036', '12/06/2036', '07/09/2036', '12/10/2036', '02/11/2036', '15/11/2036', '25/12/2036',
         '01/01/2037', '16/02/2037', '17/02/2037', '03/04/2037', '21/04/2037', '01/05/2037', '04/06/2037', '07/09/2037',
         '12/10/2037', '02/11/2037', '15/11/2037', '25/12/2037', '01/01/2038', '08/03/2038', '09/03/2038', '21/04/2038',
         '23/04/2038', '01/05/2038', '24/06/2038', '07/09/2038', '12/10/2038', '02/11/2038', '15/11/2038', '25/12/2038',
         '01/01/2039', '21/02/2039', '22/02/2039', '08/04/2039', '21/04/2039', '01/05/2039', '09/06/2039', '07/09/2039',
         '12/10/2039', '02/11/2039', '15/11/2039', '25/12/2039', '01/01/2040', '13/02/2040', '14/02/2040', '30/03/2040',
         '21/04/2040', '01/05/2040', '31/05/2040', '07/09/2040', '12/10/2040', '02/11/2040', '15/11/2040', '25/12/2040',
         '01/01/2041', '04/03/2041', '05/03/2041', '19/04/2041', '21/04/2041', '01/05/2041', '20/06/2041', '07/09/2041',
         '12/10/2041', '02/11/2041', '15/11/2041', '25/12/2041', '01/01/2042', '17/02/2042', '18/02/2042', '04/04/2042',
         '21/04/2042', '01/05/2042', '05/06/2042', '07/09/2042', '12/10/2042', '02/11/2042', '15/11/2042', '25/12/2042',
         '01/01/2043', '09/02/2043', '10/02/2043', '27/03/2043', '21/04/2043', '01/05/2043', '28/05/2043', '07/09/2043',
         '12/10/2043', '02/11/2043', '15/11/2043', '25/12/2043', '01/01/2044', '29/02/2044', '01/03/2044', '15/04/2044',
         '21/04/2044', '01/05/2044', '16/06/2044', '07/09/2044', '12/10/2044', '02/11/2044', '15/11/2044', '25/12/2044',
         '01/01/2045', '20/02/2045', '21/02/2045', '07/04/2045', '21/04/2045', '01/05/2045', '08/06/2045', '07/09/2045',
         '12/10/2045', '02/11/2045', '15/11/2045', '25/12/2045', '01/01/2046', '05/02/2046', '06/02/2046', '23/03/2046',
         '21/04/2046', '01/05/2046', '24/05/2046', '07/09/2046', '12/10/2046', '02/11/2046', '15/11/2046', '25/12/2046',
         '01/01/2047', '25/02/2047', '26/02/2047', '12/04/2047', '21/04/2047', '01/05/2047', '13/06/2047', '07/09/2047',
         '12/10/2047', '02/11/2047', '15/11/2047', '25/12/2047', '01/01/2048', '17/02/2048', '18/02/2048', '03/04/2048',
         '21/04/2048', '01/05/2048', '04/06/2048', '07/09/2048', '12/10/2048', '02/11/2048', '15/11/2048', '25/12/2048',
         '01/01/2049', '01/03/2049', '02/03/2049', '16/04/2049', '21/04/2049', '01/05/2049', '17/06/2049', '07/09/2049',
         '12/10/2049', '02/11/2049', '15/11/2049', '25/12/2049', '01/01/2050', '21/02/2050', '22/02/2050', '08/04/2050',
         '21/04/2050', '01/05/2050', '09/06/2050', '07/09/2050', '12/10/2050', '02/11/2050', '15/11/2050', '25/12/2050',
         '01/01/2051', '13/02/2051', '14/02/2051', '31/03/2051', '21/04/2051', '01/05/2051', '01/06/2051', '07/09/2051',
         '12/10/2051', '02/11/2051', '15/11/2051', '25/12/2051', '01/01/2052', '04/03/2052', '05/03/2052', '19/04/2052',
         '21/04/2052', '01/05/2052', '20/06/2052', '07/09/2052', '12/10/2052', '02/11/2052', '15/11/2052', '25/12/2052',
         '01/01/2053', '17/02/2053', '18/02/2053', '04/04/2053', '21/04/2053', '01/05/2053', '05/06/2053', '07/09/2053',
         '12/10/2053', '02/11/2053', '15/11/2053', '25/12/2053', '01/01/2054', '09/02/2054', '10/02/2054', '27/03/2054',
         '21/04/2054', '01/05/2054', '28/05/2054', '07/09/2054', '12/10/2054', '02/11/2054', '15/11/2054', '25/12/2054',
         '01/01/2055', '01/03/2055', '02/03/2055', '16/04/2055', '21/04/2055', '01/05/2055', '17/06/2055', '07/09/2055',
         '12/10/2055', '02/11/2055', '15/11/2055', '25/12/2055', '01/01/2056', '14/02/2056', '15/02/2056', '31/03/2056',
         '21/04/2056', '01/05/2056', '01/06/2056', '07/09/2056', '12/10/2056', '02/11/2056', '15/11/2056', '25/12/2056',
         '01/01/2057', '05/03/2057', '06/03/2057', '20/04/2057', '21/04/2057', '01/05/2057', '21/06/2057', '07/09/2057',
         '12/10/2057', '02/11/2057', '15/11/2057', '25/12/2057', '01/01/2058', '25/02/2058', '26/02/2058', '12/04/2058',
         '21/04/2058', '01/05/2058', '13/06/2058', '07/09/2058', '12/10/2058', '02/11/2058', '15/11/2058', '25/12/2058',
         '01/01/2059', '10/02/2059', '11/02/2059', '28/03/2059', '21/04/2059', '01/05/2059', '29/05/2059', '07/09/2059',
         '12/10/2059', '02/11/2059', '15/11/2059', '25/12/2059', '01/01/2060', '01/03/2060', '02/03/2060', '16/04/2060',
         '21/04/2060', '01/05/2060', '17/06/2060', '07/09/2060', '12/10/2060', '02/11/2060', '15/11/2060', '25/12/2060',
         '01/01/2061', '21/02/2061', '22/02/2061', '08/04/2061', '21/04/2061', '01/05/2061', '09/06/2061', '07/09/2061',
         '12/10/2061', '02/11/2061', '15/11/2061', '25/12/2061', '01/01/2062', '06/02/2062', '07/02/2062', '24/03/2062',
         '21/04/2062', '01/05/2062', '25/05/2062', '07/09/2062', '12/10/2062', '02/11/2062', '15/11/2062', '25/12/2062',
         '01/01/2063', '26/02/2063', '27/02/2063', '13/04/2063', '21/04/2063', '01/05/2063', '14/06/2063', '07/09/2063',
         '12/10/2063', '02/11/2063', '15/11/2063', '25/12/2063', '01/01/2064', '18/02/2064', '19/02/2064', '04/04/2064',
         '21/04/2064', '01/05/2064', '05/06/2064', '07/09/2064', '12/10/2064', '02/11/2064', '15/11/2064', '25/12/2064',
         '01/01/2065', '09/02/2065', '10/02/2065', '27/03/2065', '21/04/2065', '01/05/2065', '28/05/2065', '07/09/2065',
         '12/10/2065', '02/11/2065', '15/11/2065', '25/12/2065', '01/01/2066', '22/02/2066', '23/02/2066', '09/04/2066',
         '21/04/2066', '01/05/2066', '10/06/2066', '07/09/2066', '12/10/2066', '02/11/2066', '15/11/2066', '25/12/2066',
         '01/01/2067', '14/02/2067', '15/02/2067', '01/04/2067', '21/04/2067', '01/05/2067', '02/06/2067', '07/09/2067',
         '12/10/2067', '02/11/2067', '15/11/2067', '25/12/2067', '01/01/2068', '05/03/2068', '06/03/2068', '20/04/2068',
         '21/04/2068', '01/05/2068', '21/06/2068', '07/09/2068', '12/10/2068', '02/11/2068', '15/11/2068', '25/12/2068',
         '01/01/2069', '25/02/2069', '26/02/2069', '12/04/2069', '21/04/2069', '01/05/2069', '13/06/2069', '07/09/2069',
         '12/10/2069', '02/11/2069', '15/11/2069', '25/12/2069', '01/01/2070', '10/02/2070', '11/02/2070', '28/03/2070',
         '21/04/2070', '01/05/2070', '29/05/2070', '07/09/2070', '12/10/2070', '02/11/2070', '15/11/2070', '25/12/2070',
         '01/01/2071', '02/03/2071', '03/03/2071', '17/04/2071', '21/04/2071', '01/05/2071', '18/06/2071', '07/09/2071',
         '12/10/2071', '02/11/2071', '15/11/2071', '25/12/2071', '01/01/2072', '22/02/2072', '23/02/2072', '08/04/2072',
         '21/04/2072', '01/05/2072', '09/06/2072', '07/09/2072', '12/10/2072', '02/11/2072', '15/11/2072', '25/12/2072',
         '01/01/2073', '06/02/2073', '07/02/2073', '24/03/2073', '21/04/2073', '01/05/2073', '25/05/2073', '07/09/2073',
         '12/10/2073', '02/11/2073', '15/11/2073', '25/12/2073', '01/01/2074', '26/02/2074', '27/02/2074', '13/04/2074',
         '21/04/2074', '01/05/2074', '14/06/2074', '07/09/2074', '12/10/2074', '02/11/2074', '15/11/2074', '25/12/2074',
         '01/01/2075', '18/02/2075', '19/02/2075', '05/04/2075', '21/04/2075', '01/05/2075', '06/06/2075', '07/09/2075',
         '12/10/2075', '02/11/2075', '15/11/2075', '25/12/2075', '01/01/2076', '02/03/2076', '03/03/2076', '17/04/2076',
         '21/04/2076', '01/05/2076', '18/06/2076', '07/09/2076', '12/10/2076', '02/11/2076', '15/11/2076', '25/12/2076',
         '01/01/2077', '22/02/2077', '23/02/2077', '09/04/2077', '21/04/2077', '01/05/2077', '10/06/2077', '07/09/2077',
         '12/10/2077', '02/11/2077', '15/11/2077', '25/12/2077', '01/01/2078', '14/02/2078', '15/02/2078', '01/04/2078',
         '21/04/2078', '01/05/2078', '02/06/2078', '07/09/2078', '12/10/2078', '02/11/2078', '15/11/2078', '25/12/2078'
         ]

    return feriados
