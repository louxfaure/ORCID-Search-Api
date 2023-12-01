#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
import os
import logging
from modules import logs
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry 

SEARCH_CRITERIAS = "affiliation-org-name:(Bordeaux OR Arcachon OR Talence OR Pessac)"
FILE_NAME = "Search_by_affiliation-org-name.json"

# Logs
APP_NAME = "Orcid_Search"
LOGS_LEVEL = 'DEBUG'
LOGS_FILE = "{}/{}".format(os.getenv('LOGS_PATH'),APP_NAME)
ORCID_PUB_KEY = os.getenv('ORCID_PUB_KEY')

#Répertoires de traitement
OUT_FILE_PATH = '/media/sf_LouxBox/ORCID/' #Fichier siganlant les codes manquants avec leur catégorie

#On initialise le logger
logs.setup_logging(name=APP_NAME, level=LOGS_LEVEL,log_dir=LOGS_FILE)
logger = logging.getLogger(__name__)

def search_on_orcid(SEARCH_CRITERIAS,start_row):
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    response = session.request(
        method='GET',
        headers= {
        "Authorization" : "Bearer {}".format(ORCID_PUB_KEY),
        "Content-Type" :'application/json'
            },
        url= "https://pub.orcid.org/v3.0/expanded-search/?q={}&start={}&rows=1000".format(SEARCH_CRITERIAS,start_row)
        )
    try:
        response.raise_for_status()  
    except requests.exceptions.HTTPError:
        logger.error("Alma_Apis :: HTTP Status: {} || Method: {} || URL: {} || Response: {}".format(response.status_code,response.request.method, response.url, response.text))
    except requests.exceptions.ConnectionError:
        return logger.error("Alma_Apis :: Connection Error: {} || Method: {} || URL: {} || Response: {}".format(response.status_code,response.request.method, response.url, response.text))
    except requests.exceptions.RequestException:
        logger.error("Alma_Apis :: Connection Error: {} || Method: {} || URL: {} || Response: {}".format(response.status_code,response.request.method, response.url, response.text))
    return response.json()

# On lance la première recheche 
results = search_on_orcid(SEARCH_CRITERIAS,0)
# On récupère la liste des résultats
results_list = results['expanded-result']
# L'API retourne au maximum 1000 résultats. On regarde combien de résultats sont attendus pour évaluer le nombre de requêtes à lancer 
results_number = results['num-found']
logger.debug("Résultats : {}".format(results_number))
cpteur = results_number // 1000
if cpteur > 0 :
    i = 1
    while i <= cpteur : 
        logger.debug("Requête n° {}".format(i))
        results = search_on_orcid(SEARCH_CRITERIAS,i*1000)
        results_list.extend(results['expanded-result'])
        i += 1
with open('{}{}'.format(OUT_FILE_PATH,FILE_NAME),'w',encoding='utf-8') as f:
    f.write(json.dumps(results_list, indent=4, ensure_ascii=False).encode('utf8').decode())

