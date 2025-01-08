import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font
from textblob import TextBlob
from playwright.sync_api import sync_playwright

# Função para ler os nomes de um arquivo txt
def read_names_from_txt(file_path):
    # Abre o arquivo .txt e lê os nomes, retornando-os como uma lista
    # O método strip() remove espaços em branco no início e no fim de cada linha
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip()]

# Função para determinar a relevância do título
def determine_relevance(conte):
    # Palavras-chave que indicam alta, média e baixa relevância no título
    high_keywords = ['Aumento Salarial', 'Reajuste Salarial', 'aumento salarial', 'reajuste salarial']
    medium_keywords = ['Aumento', 'Reajuste', 'reajuste', 'aumento']
    low_keywords = [
        'Transporte público', 'Tarifa dos ônibus', 'Tarifa de metrô', 'Combustível',
        'Gasolina', 'Diesel', 'Alimentação', 'Supermercado', 'Restaurantes',
        'Preço da comida', 'Inflação', 'Economia doméstica', 'Preços de produtos',
        'Taxas de juros', 'Custos de vida', 'Transporte de carga', 'Pedágios',
        'Passagens aéreas', 'Gastos domésticos', 'Despesas familiares'
    ]
    # Verifica se o título contém palavras-chave de alta relevância
    if any(keyword in conte for keyword in high_keywords):
        return 3
    # Verifica se o título contém palavras-chave de relevância média
    elif any(keyword in conte for keyword in medium_keywords):
        return 2
    # Caso contrário, retorna baixa relevância
    else:
        return 1

# Função para converter uma data relativa em uma data absoluta
def parse_relative_date(relative_str):
    today = datetime.now()  # Obtém a data de hoje
    # Se a string contiver "minuto" ou "hora", retorna a data atual
    if "minuto" in relative_str or "hora" in relative_str:
        return today.strftime("%d/%m/%y")
    elif "dia" in relative_str:
        # Extrai o número de dias e subtrai da data de hoje
        days_ago = int(relative_str.split()[0])
        date = today - timedelta(days=days_ago)
        return date.strftime("%d/%m/%y")
    else:
        # Se a data não for reconhecida, retorna a data de um ano atrás
        return (today - timedelta(days=365)).strftime("%d/%m/%y")

# Função para converter uma string de data em uma data no formato dd/mm/yy
def parse_date(date_str):
    # Dicionário com os meses abreviados e seus nomes completos
    months = {
        "jan.": "janeiro", "fev.": "fevereiro", "mar.": "março", "abr.": "abril", "mai.": "maio", "jun.": "junho",
        "jul.": "julho", "ago.": "agosto", "set.": "setembro", "out.": "outubro", "nov.": "novembro", "dez.": "dezembro"
    }
    current_year = datetime.now().year  # Obtém o ano atual
    try:
        # Se a data estiver vazia, retorna a data de um ano atrás
        if not date_str:
            return (datetime.now() - timedelta(days=365)).strftime("%d/%m/%y")

        # Substitui as abreviações dos meses pelos seus nomes completos
        for abbr, full in months.items():
            date_str = date_str.replace(abbr, full)
        # Se a data tiver o formato "dia de mês", adiciona o ano atual
        if len(date_str.split()) == 3:
            date_str += f" de {current_year}"
        # Converte a data para o formato desejado
        date_obj = datetime.strptime(date_str, "%d de %B de %Y")
        return date_obj.strftime("%d/%m/%y")
    except ValueError:
        # Se ocorrer erro na conversão, tenta a conversão da data relativa
        return parse_relative_date(date_str)

# Função para verificar se a data está dentro do intervalo de uma semana
def is_date_within_range(date_str):
    date_obj = datetime.strptime(date_str, "%d/%m/%y")
    one_week_ago = datetime.now() - timedelta(days=7)  # Obtém a data de uma semana atrás
    # Verifica se a data está dentro do intervalo de uma semana
    return one_week_ago <= date_obj <= datetime.now()

# Função para verificar se o nome pesquisado está no título
def verify_research(name, title):
    # Dicionário com os estados e suas siglas
    estados = {
        'Acre': 'AC', 'Alagoas': 'AL', 'Amapá': 'AP', 'Amazonas': 'AM', 'Bahia': 'BA', 'Ceará': 'CE', 
        'Distrito Federal': 'DF', 'Espírito Santo': 'ES', 'Goiás': 'GO', 'Maranhão': 'MA', 
        'Mato Grosso': 'MT', 'Mato Grosso do Sul': 'MS', 'Minas Gerais': 'MG', 'Pará': 'PA', 
        'Paraíba': 'PB', 'Paraná': 'PR', 'Pernambuco': 'PE', 'Piauí': 'PI', 'Rio de Janeiro': 'RJ', 
        'Rio Grande do Norte': 'RN', 'Rio Grande do Sul': 'RS', 'Rondônia': 'RO', 'Roraima': 'RR', 
        'Santa Catarina': 'SC', 'São Paulo': 'SP', 'Sergipe': 'SE', 'Tocantins': 'TO'
    }

    name_lower = name.lower()  # Converte o nome para minúsculas
    title_lower = title.lower()  # Converte o título para minúsculas

    # Verifica se o nome está no título
    if name_lower in title_lower:
        return 1
    # Verifica se o nome do estado ou sua sigla está no título
    for estado, sigla in estados.items():
        if estado.lower() in name_lower and (estado.lower() in title_lower or sigla.lower() in title_lower):
            return 1
    return 0

# Função para analisar o sentimento e verificar a probabilidade de reajuste
def analyze_sentiment_and_adjustment(title):
    # Palavras-chave que indicam alta e baixa probabilidade de reajuste
    high_probability_keywords = ['confirmado', 'anunciado', 'aprovado', 'definido', 'decidido']
    low_probability_keywords = ['possível', 'planejado', 'estudado', 'considerado']
    analysis = TextBlob(title)  # Análise de sentimento usando o TextBlob
    sentiment = analysis.sentiment.polarity  # Obtém a polaridade do sentimento

    # Determina a probabilidade de reajuste com base nas palavras-chave
    if any(keyword in title for keyword in high_probability_keywords):
        adjustment_probability = "Alta"
    elif any(keyword in title for keyword in low_probability_keywords):
        adjustment_probability = "Baixa"
    else:
        adjustment_probability = "Indefinida"

    # Classifica o sentimento como positivo, negativo ou neutro
    if sentiment > 0:
        sentiment_analysis = "Positivo"
    elif sentiment < 0:
        sentiment_analysis = "Negativo"
    else:
        sentiment_analysis = "Neutro"
    return sentiment_analysis, adjustment_probability

# Função para capturar conteúdo dinâmico usando Playwright
def get_dynamic_content(url):
    try:
        # Usando Playwright para acessar conteúdo dinâmico da página
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            article_content = " ".join(p.get_text(strip=True) for p in soup.find_all('p'))
            browser.close()
            return article_content if article_content else "Conteúdo não encontrado ou bloqueado."
    except Exception as e:
        return f"Erro ao acessar o conteúdo dinâmico: {e}"

# Função principal para extrair notícias do Google News e salvar em XLSX
def scrape_google_news(base_url, search_query, names, output_file):
    wb = Workbook()  # Cria uma nova planilha
    ws = wb.active  # Ativa a planilha
    ws.append(['Nome', 'Título', 'Link', 'Data', 'Relevância', 'Veracidade da pesquisa', 'Sentimento', 'Probabilidade de Reajuste', 'Conteúdo'])

    # Itera sobre os nomes para buscar as notícias
    for name in names:
        url = f"{base_url}&q={search_query}+{name}"  # Monta a URL de busca
        try:
            # Faz a requisição para o Google News
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('article')

            for article in articles:
                # Extrai os detalhes da notícia
                title = article.find('h3').get_text() if article.find('h3') else ''
                link = article.find('a')['href'] if article.find('a') else ''
                date = article.find('time')['datetime'] if article.find('time') else ''
                date = parse_date(date)
                if not is_date_within_range(date):  # Se a data não estiver dentro do intervalo de uma semana, ignora
                    continue

                relevance = determine_relevance(title)  # Determina a relevância do título
                search_verification = verify_research(name, title)  # Verifica a relevância da pesquisa
                sentiment, adjustment = analyze_sentiment_and_adjustment(title)  # Analisa o sentimento e probabilidade de reajuste

                # Obtém o conteúdo dinâmico da notícia
                content = get_dynamic_content(link)
                
                # Adiciona os dados à planilha
                ws.append([name, title, link, date, relevance, search_verification, sentiment, adjustment, content])
        except Exception as e:
            print(f"Erro ao processar a busca para {name}: {e}")
    
    # Salva o arquivo Excel com os dados coletados
    wb.save(output_file)

# Caminhos dos arquivos
names_file = 'nomes.txt'  # Caminho para o arquivo de nomes
output_file = 'noticias_reajuste.xlsx'  # Caminho para o arquivo de saída

# Lê os nomes do arquivo txt
names = read_names_from_txt(names_file)

# Base URL do Google News
base_url = 'https://news.google.com/search'

# Termo de pesquisa para filtrar as notícias
search_query = 'reajuste salarial'

# Chama a função para começar a raspagem e salvar os dados
scrape_google_news(base_url, search_query, names, output_file)

