import pandas as pd
import time
import re

from parsel import Selector
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument('--headless')  # Sem interface gráfica
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

df = pd.read_csv("species_south_america.csv")

resultados = []

for idx, row in df.iterrows():
    # print(row["scientificName"])
    base_url = "https://powo.science.kew.org/results?q=%s" % row["scientificName"]
    print("base_url %s" % base_url)
    
    try: 
        driver.get(base_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//article'))
        )

        # Obtém o HTML da página
        html = driver.page_source

        # Usa parsel.Selector (igual ao Scrapy)
        response = Selector(text=html)

        # Agora você pode usar response.xpath normalmente!
        articles = response.xpath('//article')
        for a in articles:
            name = a.xpath('.//a/div[1]/p[1]/text()').get(default='').strip()
            href = a.xpath('.//a/@href').get(default='').strip()

            # Garante URL completa
            if href.startswith('/'):
                href = f"https://powo.science.kew.org{href}"

            print(name, "→", href)

            driver.get(href)
            time.sleep(2)  # pequena pausa para garantir carregamento completo

            html_detail = driver.page_source
            detail = Selector(text=html_detail)


            status_species = None
            native_range_text = None

            # Captura o status da espécie (ex.: "This species is accepted")
            # status_species = detail.xpath('//p[contains(text(), "This species is")]/text()').get()
            status_species = detail.xpath('//text()[contains(., "This species is")]').get()
            if status_species:
                status_species = status_species.strip()
                print(f"      Status taxonômico: {status_species}")
            else:
                print("      ⚠️ Status taxonômico não encontrado")

            # Captura a descrição da faixa nativa (ex.: "The native range of this species is ...")
            # native_range_text = detail.xpath('//p[contains(text(), "The native range of this species")]/text()').get()
            native_range_text = detail.xpath('//text()[contains(., "The native range of this species")]').get()
            if native_range_text:
                native_range_text = native_range_text.strip()
                print(f"      Faixa nativa: {native_range_text}")
            else:
                print("      ⚠️ Faixa nativa não encontrada")
            # Campos com verificação de existência

            nome_page = detail.xpath('/html/body/div[3]/main/div[1]/div[1]/div/h1/text()').get()
            if nome_page:
                nome_page = nome_page.strip()
                print(f"      Nome da página: {nome_page}")
            else:
                print("      ⚠️ Nome da espécie não encontrado no XPath /html/body/div[3]/main/div[1]/div[1]/div/h1")


            publicacao = None

            if not publicacao:
                first_pub = detail.xpath('//text()[contains(., "First published in")]').get()
                if first_pub:
                    publicacao = first_pub.strip()
                    print(f"      Publicação (estratégia 2): {publicacao}")
            

            native_countries = []
            try:
                native_text = detail.xpath('//*[@id="distribution-listing"]/p/text()').get()
                
                if native_text:
                    native_text = native_text.strip()
                    # Remove prefixos como "Native to:" ou "Native to"
                    native_text = re.sub(r'(?i)^\s*Native to[:\s\-–—]*', '', native_text).strip()
                    # Remove conteúdo entre parênteses (ex.: notas ou regiões adicionais)
                    native_text = re.sub(r'\(.*?\)', '', native_text).strip()
                    # Divide por vírgulas, ponto e vírgula, barra ou "and"
                    parts = re.split(r',|;|/|\band\b|\s+and\s+', native_text)
                    native_countries = [p.strip() for p in parts if p.strip()]
                    print(f"      Países nativos: {', '.join(native_countries)}")
                else:
                    print("      ⚠️ Países nativos não encontrados no XPath #distribution-listing/p")

            except Exception as e:
                print("      Erro extraindo países nativos:", e)


            # ========== IUCN - MÉTODO ATUALIZADO ==========
            iucn = None
            iucn_code = None
            iucn_full_name = None
            iucn_url = None
            
            print(f"      Buscando informação IUCN...")
            
            # 1. Verificar se existe aba "General Information"
            general_info_link = detail.xpath('//a[contains(@href, "/general-information")]/@href').get()
            
            if general_info_link:
                print(f"      ✅ Aba 'General Information' encontrada")
                
                # Construir URL completa
                if general_info_link.startswith('/'):
                    iucn_url = f"https://powo.science.kew.org{general_info_link}"
                elif general_info_link.startswith('http'):
                    iucn_url = general_info_link
                else:
                    iucn_url = href.rstrip('/') + '/general-information'
                
                print(f"      Acessando: {iucn_url}")
                
                # Acessar a aba General Information
                driver.get(iucn_url)
                time.sleep(3)  # Aguardar carregamento completo
                
                html_general = driver.page_source
                general = Selector(text=html_general)
                
                # ========== EXTRAIR INFORMAÇÃO "According to IUCN Categories" ==========
                
                # ESTRATÉGIA 1: Procurar por "According to IUCN Categories" e pegar próximo elemento
                iucn_section = general.xpath('//h3[contains(., "According to IUCN Categories")]').get()
                
                if iucn_section:
                    print(f"      ✅ Seção 'According to IUCN Categories' encontrada")
                    
                    # Pegar o conteúdo após o h3
                    # Opção A: Próximo elemento irmão
                    iucn_content = general.xpath('//h3[contains(., "According to IUCN Categories")]/following-sibling::*[1]//text()').getall()
                    
                    if iucn_content:
                        iucn_text = ' '.join([t.strip() for t in iucn_content if t.strip()])
                        print(f"      Conteúdo IUCN: {iucn_text}")
                        
                        # Extrair código e nome (ex: "EN - Endangered")
                        # Procurar por padrão: CODE - Name
                        import re
                        match = re.search(r'(EX|EW|CR|EN|VU|NT|LC|DD|NE)\s*-\s*(\w+.*?)(?:\s|$)', iucn_text)
                        
                        if match:
                            iucn_code = match.group(1)  # Ex: "EN"
                            iucn_full_name = match.group(2)  # Ex: "Endangered"
                            iucn = f"{iucn_code} - {iucn_full_name}"
                            print(f"      ✅ IUCN extraído: {iucn}")
                        else:
                            # Se não encontrou padrão, pegar texto completo
                            iucn = iucn_text
                            print(f"      ⚠️  IUCN (texto completo): {iucn}")

            else:
                print(f"      ⚠️  Aba 'General Information' não encontrada")
                
                # Fallback: tentar na página principal
                iucn_xpath_options = [
                    '//h3[contains(., "IUCN")]//button//span/text()',
                    '//button[contains(@class, "conservation")]//span/text()',
                    '//div[contains(@class, "iucn")]//text()',
                    '//section//h3//button//span[1]/text()'
                ]
                
                for xpath in iucn_xpath_options:
                    iucn = detail.xpath(xpath).get()
                    if iucn:
                        iucn = iucn.strip()
                        print(f"      ✅ IUCN encontrado (página principal): {iucn}")
                        break
            
            if not iucn:
                print(f"      ❌ IUCN não encontrado")


            resultados.append({
                'species': row["scientificName"],
                'name': name,
                'url': href,
                'publicacao': publicacao if publicacao else '',
                'native_countries': '; '.join(native_countries) if native_countries else '',
                'native_countries_count': len(native_countries),
                'iucn': iucn if iucn else '',
                'iucn_code': iucn_code if iucn_code else '',
                'iucn_full_name': iucn_full_name if iucn_full_name else '',
                'status_species': status_species if status_species else '',
                'native_range': native_range_text if native_range_text else '',
            })

    except:
        # raise ValueError
        continue
    
driver.quit()

# Salva os resultados em CSV
output = pd.DataFrame(resultados)
output.to_csv("powo_detalhes.csv", sep="|", index=False, encoding="utf-8")