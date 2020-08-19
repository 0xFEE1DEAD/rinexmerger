import glob
import sys
from rinex_merger import merge_rinexes
from bad_coefs_searcher import search_bad_coefs
from rinex_writer import write_rinex
from report_writer import write_report



if __name__ == '__main__':
    files = glob.glob('rintest/*')
    merge_rin = merge_rinexes(files)
    merge_rin['data'] = search_bad_coefs(merge_rin['data'])
    write_rinex(merge_rin)
    write_report(merge_rin['data'])