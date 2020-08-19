import parselib as pl
import datetime
import re

def delete_similar_coefs(coefs):
    accuracy = 0.00000000001
    for coef_to in coefs:
        coef_to_float = float(coef_to)
        for coef_from in coefs:
            if(coef_to == coef_from or coefs[coef_to] == None or coefs[coef_from] == None):
                continue
            coef_from_float = float(coef_from)
            if coef_to_float != 0.0:
                res = coef_from_float / coef_to_float
                if(accuracy > abs(1.0 - res)):
                    coefs[coef_to] += coefs[coef_from]
                    coefs[coef_from] = None

    coefs_temp = {}
    for coef in coefs:
        if(coefs[coef] != None):
            coefs_temp[coef] = coefs[coef]
    
    return coefs_temp

def get_datetime_from_file_name(filename):
    days_years = re.search('.{4}(\d{3}).\.(\d{2}).|.{12}(\d{4})(\d{3}).{11}', filename, re.IGNORECASE)

    d = None

    if (days_years and days_years.group(1)):
        days = days_years.group(1)
        year = days_years.group(2)
        d = datetime.datetime.strptime(year + days, '%y%j')
    elif(days_years and days_years.group(3)):
        days = days_years.group(4)
        year = days_years.group(3)
        d = datetime.datetime.strptime(year + days, '%Y%j')
    else:
        raise Exception("Invalid file naming " + filename)

    return d

def parse_ionospheric_cor(cor_string):
    cor_string = cor_string.replace('D', 'E').replace('e', 'E')

    i_cor = re.search('([A-Z]{2,})', cor_string, re.IGNORECASE)
    parsed = {}
    if(i_cor):
        parsed[i_cor.group(1)] = re.findall('(\d\.\d+[E].\d\d)', cor_string)

    return parsed

def get_ionospheric_cor(header):

    t_cor = {}

    if ('ION ALPHA' in header and 'ION BETA' in header):
            ion_alpha = header['ION ALPHA']
            ion_beta = header['ION BETA']
            ion_alpha = ion_alpha.replace('D', 'E').replace('\n', '')
            ion_alpha = ion_alpha.replace('e', 'E')
            ion_beta = ion_beta.replace('D', 'E').replace('\n', '')
            ion_beta = ion_beta.replace('e', 'E')
            ion_alpha = re.findall('[- ]\d+\.\d+E[+-]\d+', ion_alpha, flags=re.IGNORECASE)
            ion_beta = re.findall('[- ]\d+\.\d+E[+-]\d+', ion_beta, flags=re.IGNORECASE)
            ion_alpha = list(map(lambda x: float(x), ion_alpha))
            ion_beta = list(map(lambda x: float(x), ion_beta))
            t_cor = {}
            t_cor['GPSA'] = ion_alpha
            t_cor['GPSB'] = ion_beta


    if 'IONOSPHERIC CORR' in header:
            t_cor = header['IONOSPHERIC CORR']

    if type(t_cor) == type(''):
        t_cor = parse_ionospheric_cor(t_cor)

    return t_cor


def merge_rinexes(files):
    """
    files: list of path strings
    return: dictionary with merged data
    {
        'max_i_q: int,
        'datetimes': [],
        'header': {
            'IONOSPHERIC CORR': {
                'GPSA': [],
                'GPSB': []
            }
        },
        'satellite_name': {
            'datetime': {
                'coef_index': coef,
                ...
            },
            ...
        },
        ...
    }
    """


    rinex_merged_data = {}
    rinex_merged = {}
    rinex_merged['header'] = {}
    rinex_merged['header']['IONOSPHERIC CORR'] = {}
    rinex_merged['datetimes'] = {}
    rinex_merged['max_i_q'] = 0
    ionospheric_corr = {}
    for file in files:
        datetime_from_filename = get_datetime_from_file_name(file)
        if datetime_from_filename in rinex_merged['datetimes']:
            rinex_merged['datetimes'][datetime_from_filename] += 1
        else:
            rinex_merged['datetimes'][datetime_from_filename] = 1

        print(file)
        try:
            current_rinex = pl.rinexnav(file)
        except Exception:
            print('Файл не будет учитываться')
            continue

        ionos_temp = get_ionospheric_cor(current_rinex['header'])

        for gps in ionos_temp:
            if not gps in ionospheric_corr:
                ionospheric_corr[gps] = {}
            for idx, val in enumerate(ionos_temp[gps]):
                if idx in ionospheric_corr[gps]:
                    if val in ionospheric_corr[gps][idx]:
                        ionospheric_corr[gps][idx][val] += 1
                    else:
                        ionospheric_corr[gps][idx][val] = 1
                else:
                    ionospheric_corr[gps][idx] = {}
                    ionospheric_corr[gps][idx][val] = 1
        
        for sv in current_rinex['data']:
            for datetime_k in current_rinex['data'][sv]:

                if not (datetime_k.strftime('%y%j') == datetime_from_filename.strftime('%y%j')):
                    break

                if(not sv in rinex_merged_data):
                    rinex_merged_data[sv] = {}

                if(not datetime_k in rinex_merged_data[sv]):
                    rinex_merged_data[sv][datetime_k] = {}

                coefs = current_rinex['data'][sv][datetime_k]

                if not coefs:
                    raise Exception("Missed coefs")

                for idx, coef in enumerate(coefs):
                    if(idx > rinex_merged['max_i_q']):
                        rinex_merged['max_i_q'] = idx
                    if idx in rinex_merged_data[sv][datetime_k]:
                        try:
                            rinex_merged_data[sv][datetime_k][idx][coef]['count'] += 1
                            rinex_merged_data[sv][datetime_k][idx][coef]['owners'].append(file)
                        except KeyError:
                            rinex_merged_data[sv][datetime_k][idx][coef] = {'count': 1, 'owners': [file] }
                    else:
                        rinex_merged_data[sv][datetime_k][idx] = {}
                        rinex_merged_data[sv][datetime_k][idx][coef] = {'count': 1, 'owners': [file] }

    for gps in ionospheric_corr:
        for idx in ionospheric_corr[gps]:
            coefs = delete_similar_coefs(ionospheric_corr[gps][idx])
            
            right_idx = sorted(coefs, key=lambda x: coefs.get(x), reverse=True)[0]
            
            if not gps in rinex_merged['header']['IONOSPHERIC CORR']:
                rinex_merged['header']['IONOSPHERIC CORR'][gps] = []

            rinex_merged['header']['IONOSPHERIC CORR'][gps].append(right_idx)
    
    rinex_merged['data'] = rinex_merged_data

    return rinex_merged