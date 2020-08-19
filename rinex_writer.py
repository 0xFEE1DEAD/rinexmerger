def widthAlignCoef(coef):
    add_space = ''
    if(coef >= 0):
        add_space = ' '

    return add_space + '{0:.4E}'.format(coef)

def widthAlignKey(key):
    align = 4
    space = ' ' * (align - len(key))
    return key + space

def add_ods(lst):
    q = 4
    return lst + (['           '] * (q - len(lst)))

def write_rinex(rinex_merged):
    date = sorted(rinex_merged['datetimes'], key=lambda x: rinex_merged['datetimes'].get(x), reverse=True)[0]

    filetype = 'n'

    filename = 'aaaa' + date.strftime("%j") + '0' + '.' + date.strftime("%y") + filetype

    out = open(filename, 'w')

    out.write('     3.03           N: GNSS NAV DATA    G: GPS              RINEX VERSION / TYPE\n')

    i_c = rinex_merged['header']['IONOSPHERIC CORR']
    

    for gps in i_c:
        ionospheric_corr_cefs_l = list(map(lambda x: widthAlignCoef(float(x)), i_c[gps]))
        ionospheric_corr_cefs_l = add_ods(ionospheric_corr_cefs_l)
        
        out.write('{0}  {1} {2} {3} {4}       IONOSPHERIC CORR    \n'.format(widthAlignKey(gps), *ionospheric_corr_cefs_l))
    out.write('                                                            END OF HEADER       \n')

    rinex_merged_data = rinex_merged['data']
    for sv in rinex_merged_data:
        for datetime_k in rinex_merged_data[sv]:
            out.write(sv + ' ')
            out.write(datetime_k.strftime("%Y %m %d %H %M %S"))
            coef_indexes_q = len(rinex_merged_data[sv][datetime_k])
            for coef_idx in rinex_merged_data[sv][datetime_k]:
                coef_val = rinex_merged_data[sv][datetime_k][coef_idx]['rigth_coef']['value']
                out.write(coef_val)
                if(coef_idx == 2 or ((coef_idx - 2) % 4 == 0 and coef_idx != (coef_indexes_q - 1))):
                    out.write('\n    ')

            for i in range(coef_indexes_q - 1, rinex_merged['max_i_q']):
                if((i - 2) % 4 == 0):
                    out.write('\n    ')
                out.write(' 0.000000000000E+00')
                
                
                
            out.write('\n')
    out.close()