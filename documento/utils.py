from datetime import datetime

# utils.py
def validar_cabecalho_csv(cabecalho):
    # Remove o caractere especial '\ufeff' se presente
    if cabecalho[0].startswith('\ufeff'):
        cabecalho[0] = cabecalho[0].replace('\ufeff', '')

    campos_obrigatorios = ['EMPRESA', 'REGIONAL', 'UNIDADE', 'MATRICULA', 'NOME', 'CARGO', 'ADMISSAO', 'CPF',
                           'STATUS']
    for campo in campos_obrigatorios:
        if campo not in cabecalho:  # Verifica se o campo está presente no cabeçalho
            print(f'Campo obrigatório ausente: {campo}')
            print(f'Cabeçalho do CSV: {cabecalho}')
            return False
    return True


def validar_dados_csv(linha, cabecalho):
    for campo in cabecalho:
        # Verifica se o campo obrigatório está ausente ou vazio apenas se estiver presente no cabeçalho
        if campo in ['EMPRESA', 'REGIONAL', 'UNIDADE', 'MATRICULA', 'NOME', 'CARGO', 'ADMISSAO', 'CPF', 'STATUS'] and (campo not in linha or not linha[campo]):
            print(f'Dado ausente ou vazio para o campo obrigatório: {campo}')
            return False

    # Ajustando o CPF para ter exatamente 11 dígitos, completando com zeros à esquerda se necessário
    if 'CPF' in linha and linha['CPF']:
        linha['CPF'] = linha['CPF'].zfill(11)
        if len(linha['CPF']) != 11 or not linha['CPF'].isdigit():
            print("CPF inválido:", linha['CPF'])
            return False

    # Ajustando a matrícula para ter exatamente 8 dígitos, completando com zeros à esquerda se necessário
    if 'MATRICULA' in linha and linha['MATRICULA']:
        linha['MATRICULA'] = linha['MATRICULA'].zfill(8)
        if len(linha['MATRICULA']) != 8 or not linha['MATRICULA'].isdigit():
            print("MATRICULA inválida:", linha['MATRICULA'])
            return False

    if linha['ADMISSAO']:
        try:
            datetime.strptime(linha['ADMISSAO'], '%d/%m/%Y')
        except ValueError:
            print("Data de admissão inválida:", linha['ADMISSAO'])
            return False

    return True
