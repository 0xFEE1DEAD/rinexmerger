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
                    coefs[coef_to]['count'] += coefs[coef_from]['count']
                    coefs[coef_to]['owners'] += coefs[coef_from]['owners']
                    coefs[coef_from] = None

    coefs_temp = {}
    for coef in coefs:
        if(coefs[coef] != None):
            coefs_temp[coef] = coefs[coef]
    
    return coefs_temp

def search_bad_coefs(rinex_merged_data):
    for sv in rinex_merged_data:
        for datetime_k in rinex_merged_data[sv]:
            for coef_idx in rinex_merged_data[sv][datetime_k]:
                coefs_cleared = delete_similar_coefs(rinex_merged_data[sv][datetime_k][coef_idx])
                coefs_l = sorted(coefs_cleared, key=lambda x: coefs_cleared.get(x)['count'], reverse=True)

                rigth_coef = coefs_cleared[coefs_l[0]]
                rigth_coef['value'] = coefs_l[0]

                error_coefs_l = coefs_l[1:]
                error_coefs = []
                for coef in error_coefs_l:
                    coef_dict = coefs_cleared[coef]
                    coef_dict['value'] = coef
                    error_coefs.append(coef_dict)

                rinex_merged_data[sv][datetime_k][coef_idx] = {}

                rinex_merged_data[sv][datetime_k][coef_idx]['rigth_coef'] = rigth_coef
                rinex_merged_data[sv][datetime_k][coef_idx]['error_coefs'] = error_coefs

    return rinex_merged_data