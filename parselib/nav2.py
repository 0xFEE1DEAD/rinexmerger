#!/usr/bin/env python
from pathlib import Path
from datetime import datetime
from typing import Dict, Union, Any, Sequence, Tuple
from typing.io import TextIO
import xarray
import numpy as np
import logging
import re

from .rio import opener, rinexinfo
from .common import rinex_string_to_float
#
STARTCOL2 = 3  # column where numerical data starts for RINEX 2
Nl = {'G': 7, 'R': 3, 'E': 7}   # number of additional SV lines


def rinexnav2(fn: Union[TextIO, str, Path],
              tlim: Sequence[datetime] = None) -> Tuple:
    """
    Reads RINEX 2.x NAV files
    Michael Hirsch, Ph.D.
    SciVision, Inc.

    http://gage14.upc.es/gLAB/HTML/GPS_Navigation_Rinex_v2.11.html
    ftp://igs.org/pub/data/format/rinex211.txt
    """
    if isinstance(fn, (str, Path)):
        fn = Path(fn).expanduser()

    Lf = 19  # string length per field

    rinex_parsed = {}
    rinex_parsed['data'] = {}

    with opener(fn) as f:

        header = navheader2(f)
        rinex_parsed['header'] = header

        if header['filetype'] == 'N':
            svtype = 'G'
        elif header['filetype'] == 'G':
            svtype = 'R'  # GLONASS
        elif header['filetype'] == 'E':
            svtype = 'E'  # Galileo
        else:
            raise NotImplementedError(f'I do not yet handle Rinex 2 NAV {header["sys"]}  {fn}')
# %% read data
        for ln in f:
            granule = {}
            try:
                time = _timenav(ln)
            except ValueError:
                continue

            if tlim is not None:
                if time < tlim[0]:
                    _skip(f, Nl[header['systems']])
                    continue
                elif time > tlim[1]:
                    break
# %% format I2 http://gage.upc.edu/sites/default/files/gLAB/HTML/GPS_Navigation_Rinex_v2.11.html
            sv = f'{svtype}{ln[:2]}'
            sv = sv.replace(' ', '0')
            """
            now get the data as one big long string per SV
            """
            raw = ln[22:79]  # NOTE: MUST be 79, not 80 due to some files that put \n a character early!
            for _ in range(Nl[header['systems']]):
                raw += f.readline()[STARTCOL2:79]
            # one line per SV
            # NOTE: Sebastijan added .replace('  ', ' ').replace(' -', '-')
            # here, I would like to see a file that needs this first, to be sure
            # I'm not needlessly slowing down reading or creating new problems.
            raw = raw.replace('D', 'E').replace('\n', '')
            raw = raw.replace('e', 'E')
            temp_raw = re.findall('[- ]\d+\.\d+E[+-]\d+', raw, flags=re.IGNORECASE)
            if(len(temp_raw) == 0):
                temp_raw = re.findall('[- ]\.\d+E[+-]\d+', raw, flags=re.IGNORECASE)
                temp_raw = list(map(lambda x: x.replace('.', '0.'), temp_raw))

            if not sv in rinex_parsed['data']:
                rinex_parsed['data'][sv] = {}
                rinex_parsed['data'][sv][time] = temp_raw
            elif not time in rinex_parsed['data'][sv]:
                rinex_parsed['data'][sv][time] = temp_raw
            
    return rinex_parsed

def navheader2(f: TextIO) -> Dict[str, Any]:
    """
    For RINEX NAV version 2 only. End users should use rinexheader()
    """
    if isinstance(f, (str, Path)):
        with opener(f, header=True) as h:
            return navheader2(h)

    hdr = rinexinfo(f)

    for ln in f:
        if 'END OF HEADER' in ln:
            break
        kind, content = ln[60:].strip(), ln[:60]
        hdr[kind] = content

    return hdr


def _timenav(ln: str) -> datetime:

    year = int(ln[3:5])
    if 80 <= year <= 99:
        year += 1900
    elif year < 80:  # because we might pass in four-digit year
        year += 2000
    else:
        raise ValueError(f'unknown year format {year}')

    return datetime(year=year,
                    month=int(ln[6:8]),
                    day=int(ln[9:11]),
                    hour=int(ln[12:14]),
                    minute=int(ln[15:17]),
                    second=int(float(ln[17:20])),
                    microsecond=int(float(ln[17:22]) % 1 * 1000000)
                    )


def _skip(f: TextIO, Nl: int):
    for _, _ in zip(range(Nl), f):
        pass

def navtime2(fn: Union[TextIO, Path]) -> np.ndarray:
    """
    read all times in RINEX 2 NAV file
    """
    times = []
    with opener(fn) as f:
        hdr = navheader2(f)

        while True:
            ln = f.readline()
            if not ln:
                break

            try:
                time = _timenav(ln)
            except ValueError:
                continue

            times.append(time)

            _skip(f, Nl[hdr['systems']])

    return np.unique(times)
