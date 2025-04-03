import json
import pandas as pd
import requests
import io
import certifi
import os
from typing import Optional, Tuple, Dict
from io import StringIO


def formt_text(text):
    # Dictionary to map accented characters to non-accented counterparts
    accents = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'â': 'a', 'ê': 'e', 'ô': 'o', 'à': 'a', 'ã': 'a', 'õ': 'o', 'ç': 'c',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'Â': 'A', 'Ê': 'E', 'Ô': 'O', 'À': 'A', 'Ã': 'A', 'Õ': 'O', 'Ç': 'C'
    }
    if isinstance(text, bytes):
        text.encode('latin-1', errors='replace').decode('utf-8')
    else:
        pass
    #text.encode('latin-1', errors='replace').decode('utf-8')
    # Replace accented characters
    #print(text)
    new_text = ''.join(accents.get(char, char) for char in text)

    # Remove special characters and numbers
    new_text = ''.join(char for char in new_text if char.isalpha() or char.isspace())

    convenio = ''
    if 'S' in new_text[-1]:
        #print('sul america')
        convenio = 'S'
        new_text = new_text.replace('S', '')
    elif 'B' in new_text[-1]:
        #print('bradesco')
        convenio = 'B'
        new_text = new_text.replace('B', '')
    elif 'M' in new_text[-1]:
        #print('mediservice')
        convenio = 'M'
        new_text = new_text.replace('M', '')
    elif 'P' in new_text[-1]:
        #print('particular')
        convenio = 'P'
        new_text = new_text.replace('P', '')
    else:
        pass

    #print(new_text)
    return new_text.upper(), convenio



class Url_Sheets:
    def __init__(self):
        self.conexao = False
        self.verif_conect()
        self.url = 'https://docs.google.com/spreadsheets/d/1wgzO2nbzYRhCJBa501t1RxDMKdaEdjxj/'       #'https://docs.google.com/spreadsheets/d/1PBwyM79jZS7b4GxSr1ayocGleWT48k9V/'  #export?gid={id}&range=A:F&format=csv'
        self.session = requests.Session()

    def verif_conect(self, url:str="http://www.google.com", timeout:int=5) -> bool:
        #print('verificando a internet')
        try:
            requests.get(url, timeout=timeout)
            self.conexao = True
            #print('conectado')
            return True
        except requests.RequestException:
            self.conexao = False
            #print('desconectado')
            return False

    def fetch_csv(self, url:str) -> Optional[requests.Response]:
        #print('tentando conexão')
        # if not self.verif_conect():
        #     self.conexao = False
        #     return False
        try:

            response = self.session.get(url, verify=certifi.where(), timeout=10)
            response.raise_for_status()
            self.conexao = True
            return response

        except requests.RequestException as e:
            self.conexao = False
            return None

    def nomes_ids(self) -> Tuple[Optional[Dict], Optional[Dict]]:
        # response = requests.get(self.url + 'export?gid=268641735&range=A:C&format=csv', verify=certifi.where())
        # response.raise_for_status()  # Lança exceção para erros HTTP
        # df = pd.read_csv(io.StringIO(response.text))
        url = self.url + 'export?gid=1538723142&range=A:C&format=csv'
        #print('extraindo nomes e ids')
        response = self.fetch_csv(url)
        if not response:
            self.conexao = False
            return None, None
        #print('nomes e ids encontrados')
        df = pd.read_csv(io.StringIO(response.text))
        self.conexao = True
        return (dict(zip(df['NOME'], df['ID'])),
                dict(zip(df['NOME'], df['TELE'])))

    def ids_teles(self) -> Optional[Dict]:
        #print('extraindo ids telegram')
        _, dic_teles = self.nomes_ids()

        if not dic_teles:
            return None

        self.conexao = bool(dic_teles)

        if os.path.exists('ids_teleg.json'):
            if dic_teles == json.load(open('ids_teleg.json', encoding='utf-8')):
                return json.load(open('ids_teleg.json', encoding='utf-8'))
            else:
                os.remove('ids_teleg.json')

        with open('ids_teleg.json', 'w', encoding='utf-8') as arq:
            json.dump(dic_teles, arq, indent=4, ensure_ascii=False)

        return dic_teles

    def titulos(self) -> Optional[list]:
        #print('extraindo nomes psis')
        dic_nomes, _ = self.nomes_ids()

        if not dic_nomes:
            self.conexao = False
            return None

        self.conexao = True

        if os.path.exists('nomes_psicos.json'):
            if dic_nomes == json.load(open('nomes_psicos.json', encoding='utf-8')):
                return list(json.load(open('nomes_psicos.json', encoding='utf-8')).keys())
            else:
                os.remove('nomes_psicos.json')

        with open('nomes_psicos.json', 'w', encoding='utf-8') as arq:
            json.dump(dic_nomes, arq, indent=4, ensure_ascii=False)

        return list(dic_nomes.keys())

    def planilha(self, id:str, psico:str) -> Optional[pd.DataFrame]:
        #print('entrando na extração de planilha')

        dic, _ = self.nomes_ids()

        if not dic:
            self.conexao = False
            #print('entrando na extração de planilha S/ INTERNET')
            return None

        #print('extair')
        url = self.url + f'export?gid={id}&range=A:F&&format=csv'
        self.df_resultado = None
        response = self.fetch_csv(url)

        if not response:
            return None

        df = pd.read_csv(io.StringIO(response.text), header=None)
        #print('planilha extraida, tratá-la')

        # Define cabeçalho de forma dinâmica
        header_row = 1 if df.iloc[0].isnull().all() else 0
        df.columns = df.iloc[header_row]
        df = df[header_row + 1:].reset_index(drop=True)

        # novos_nomes = list(df.columns)  # Cria uma cópia da lista de nomes
        # novos_nomes[2] = 'TERCA-FEIRA'  # Substitui o nome da segunda coluna
        # df.columns = novos_nomes

        df.columns = [col if i != 2 else 'TERCA-FEIRA' for i, col in enumerate(df.columns)]

        #df = pd.read_csv(self.url + f'export?gid={id}&range=A:F&format=csv')

        df.fillna(value=pd.NA, inplace=True)
        pasta = os.path.join('agendas', f'agenda_{psico}.csv')
        df.to_csv(pasta, sep=';', decimal=',', index=False, header=True, encoding='utf-8')

        self.conexao = True
        #print('finalizar o tratamento da planilha')

        return df


