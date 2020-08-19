#!/usr/bin/env python
from pathlib import Path
import xarray
import logging
import numpy as np
import math
from datetime import datetime
from typing import Dict, Union, List, Any, Sequence
from typing.io import TextIO
import re
#
from .rio import opener, rinexinfo
from .common import rinex_string_to_float
# constants
STARTCOL3 = 4  # column where numerical data starts for RINEX 3
Nl = {'C': 7, 'E': 7, 'G': 7, 'J': 7, 'R': 3, 'S': 3, 'I': 7}   # number of additional SV lines
Lf = 19  # string length per field


def rinexnav3(fn: Union[TextIO, str, Path],
              use: Sequence[str] = None,
              tlim: Sequence[datetime] = None) -> xarray.Dataset:
    """
    Reads RINEX 3.x NAV files
    Michael Hirsch, Ph.D.
    SciVision, Inc.
    http://www.gage.es/sites/default/files/gLAB/HTML/SBAS_Navigation_Rinex_v3.01.html

    The "eof" stuff is over detection of files that may or may not have a trailing newline at EOF.
    """
    if isinstance(fn, (str, Path)):
        fn = Path(fn).expanduser()

    rinex_parsed = {}
    rinex_parsed['data'] = {}

    with opener(fn) as f:
        header = navheader3(f)
        rinex_parsed['header'] = header
# %% read data
        for line in f:
            granule = {}
            if line.startswith('\n'):  # EOF
                break

            try:
                time = _time(line)
            except ValueError:  # blank or garbage line
                continue

            if tlim is not None:
                if time < tlim[0] or time > tlim[1]:
                    _skip(f, Nl[line[0]])
                    continue
                # not break due to non-monotonic NAV files

            sv = line[:3]
            if use is not None and not sv[0] in use:
                _skip(f, Nl[sv[0]])
                continue
            
# %% get the data as one big long string per SV, unknown # of lines per SV
            raw = line[23:80]  # NOTE: 80, files put data in the last column!

            for _, ln in zip(range(Nl[sv[0]]), f):
                raw += ln[STARTCOL3:80]
            # one line per SV
            raw = raw.replace('D', 'E').replace('\n', '')
            raw = raw.replace('e', 'E')
            temp_raw = re.findall('[- ]\d+\.\d+E[+-]\d+', raw, flags=re.IGNORECASE)
            if(len(temp_raw) == 0):
                temp_raw = re.findall('[- ]\.\d+E[+-]\d+', raw, flags=re.IGNORECASE)
                temp_raw = list(map(lambda x: x.replace('.', '0.'), temp_raw))

            sv = sv.replace(' ', '0')
            if not sv in rinex_parsed['data']:
                rinex_parsed['data'][sv] = {}
                rinex_parsed['data'][sv][time] = temp_raw
            elif not time in rinex_parsed['data'][sv]:
                rinex_parsed['data'][sv][time] = temp_raw
            
    return rinex_parsed


def _skip(f: TextIO, Nl: int):
    for _, _ in zip(range(Nl), f):
        pass


def _time(ln: str) -> datetime:

    return datetime(year=int(ln[4:8]),
                    month=int(ln[9:11]),
                    day=int(ln[12:14]),
                    hour=int(ln[15:17]),
                    minute=int(ln[18:20]),
                    second=int(ln[21:23]))


def _sparefields(cf: List[str], sys: str, raw: str) -> List[str]:
    """
    check for optional spare fields, or GPS "fit interval" field

    You might find a new way that NAV3 files are irregular--please open a
    GitHub Issue or Pull Request.
    """
    numval = math.ceil(len(raw) / Lf)  # need this for irregularly defined files
# %% patching for Spare entries, some receivers include, and some don't include...
    if sys == 'G':
        if numval == 30:
            cf = cf[:-1]
        elif numval == 29:
            cf = cf[:-2]
    elif sys == 'C':
        if numval == 27:
            cf = cf[:20] + [cf[21]] + cf[23:29]
        elif numval == 28:
            cf = cf[:22] + cf[23:29]
        elif numval == 29:
            cf = cf[:29]
        elif numval == 30:
            cf = cf[:30]
    elif sys == 'J':
        if numval == 29:
            cf = cf[:29]
        elif numval == 30:
            cf = cf[:30]
    elif sys == 'E':
        if numval == 29:  # only one trailing spare fields
            cf = cf[:-2]
        elif numval == 28:  # zero trailing spare fields
            cf = cf[:-3]
        elif numval == 27:  # no middle or trailing spare fields
            cf = cf[:22] + cf[23:-3]
    elif sys == 'I':
        if numval == 28:
            cf = cf[:28]

    if numval != len(cf):
        raise ValueError(f'System {sys} NAV data is not the same length as the number of fields.')

    return cf


def _newnav(ln: str, sv: str) -> List[str]:

    if sv.startswith('G'):
        """
        ftp://igs.org/pub/data/format/rinex303.pdf

        pages:
        G: A23-A24
        E: A25-A28
        R: A29-A30
        J: A31-A32
        C: A33-A34
        S: A35-A36
        I: A37-A39
        """
        fields = ['SVclockBias', 'SVclockDrift', 'SVclockDriftRate',
                  'IODE', 'Crs', 'DeltaN', 'M0',
                  'Cuc', 'Eccentricity', 'Cus', 'sqrtA',
                  'Toe', 'Cic', 'Omega0', 'Cis',
                  'Io', 'Crc', 'omega', 'OmegaDot',
                  'IDOT', 'CodesL2', 'GPSWeek', 'L2Pflag',
                  'SVacc', 'health', 'TGD', 'IODC',
                  'TransTime', 'FitIntvl', 'spare0', 'spare1']
        assert len(fields) == 31
    elif sv.startswith('C'):  # pg A-33  Beidou Compass BDT
        fields = ['SVclockBias', 'SVclockDrift', 'SVclockDriftRate',
                  'AODE', 'Crs', 'DeltaN', 'M0',
                  'Cuc', 'Eccentricity', 'Cus', 'sqrtA',
                  'Toe', 'Cic', 'Omega0', 'Cis',
                  'Io', 'Crc', 'omega', 'OmegaDot',
                  'IDOT', 'spare0', 'BDTWeek', 'spare1',
                  'SVacc', 'SatH1', 'TGD1', 'TGD2',
                  'TransTime', 'AODC', 'spare2', 'spare3']
        assert len(fields) == 31
    elif sv.startswith('R'):  # pg. A-29   GLONASS
        fields = ['SVclockBias', 'SVrelFreqBias', 'MessageFrameTime',
                  'X', 'dX', 'dX2', 'health',
                  'Y', 'dY', 'dY2', 'FreqNum',
                  'Z', 'dZ', 'dZ2', 'AgeOpInfo']
        assert len(fields) == 15
    elif sv.startswith('S'):  # pg. A-35 SBAS
        fields = ['SVclockBias', 'SVrelFreqBias', 'MessageFrameTime',
                  'X', 'dX', 'dX2', 'health',
                  'Y', 'dY', 'dY2', 'URA',
                  'Z', 'dZ', 'dZ2', 'IODN']
        assert len(fields) == 15
    elif sv.startswith('J'):  # pg. A-31  QZSS
        fields = ['SVclockBias', 'SVclockDrift', 'SVclockDriftRate',
                  'IODE', 'Crs', 'DeltaN', 'M0',
                  'Cuc', 'Eccentricity', 'Cus', 'sqrtA',
                  'Toe', 'Cic', 'Omega0', 'Cis',
                  'Io', 'Crc', 'omega', 'OmegaDot',
                  'IDOT', 'CodesL2', 'GPSWeek', 'L2Pflag',
                  'SVacc', 'health', 'TGD', 'IODC',
                  'TransTime', 'FitIntvl', 'spare0', 'spare1']
        assert len(fields) == 31
    elif sv.startswith('E'):  # pg. A-25 Galileo Table A8
        fields = ['SVclockBias', 'SVclockDrift', 'SVclockDriftRate',
                  'IODnav', 'Crs', 'DeltaN', 'M0',
                  'Cuc', 'Eccentricity', 'Cus', 'sqrtA',
                  'Toe', 'Cic', 'Omega0', 'Cis',
                  'Io', 'Crc', 'omega', 'OmegaDot',
                  'IDOT', 'DataSrc', 'GALWeek',
                  'spare0',
                  'SISA', 'health', 'BGDe5a', 'BGDe5b',
                  'TransTime',
                  'spare1', 'spare2', 'spare3']
        assert len(fields) == 31
    elif sv.startswith('I'):
        fields = ['SVclockBias', 'SVclockDrift', 'SVclockDriftRate',
                  'IODEC', 'Crs', 'DeltaN', 'M0',
                  'Cuc', 'Eccentricity', 'Cus', 'sqrtA',
                  'Toe', 'Cic', 'Omega0', 'Cis',
                  'Io', 'Crc', 'omega', 'OmegaDot',
                  'IDOT', 'spare0', 'BDTWeek', 'spare1',
                  'URA', 'health', 'TGD', 'spare2',
                  'TransTime',
                  'spare3', 'spare4', 'spare5']
        assert len(fields) == 31
    else:
        raise ValueError(f'Unknown SV type {sv[0]}')

    return fields


def navheader3(f: TextIO) -> Dict[str, Any]:

    if isinstance(f, (str, Path)):
        with opener(f, header=True) as h:
            return navheader3(h)

    hdr = rinexinfo(f)

    for ln in f:
        if 'END OF HEADER' in ln:
            break

        kind, content = ln[60:].strip(), ln[:60]
        if kind == "IONOSPHERIC CORR":
            if kind not in hdr:
                hdr[kind] = {}

            coeff_kind = content[:4].strip()
            N = 3 if coeff_kind == 'GAL' else 4
            # RINEX 3.04 table A5 page A19
            coeff = [rinex_string_to_float(content[5 + i*12:5 + (i+1)*12]) for i in range(N)]
            hdr[kind][coeff_kind] = coeff
        else:
            hdr[kind] = content

    return hdr


def navtime3(fn: Union[TextIO, Path]) -> np.ndarray:
    """
    return all times in RINEX file
    """
    times = []

    with opener(fn) as f:
        navheader3(f)  # skip header

        for line in f:
            try:
                time = _time(line)
            except ValueError:
                continue

            times.append(time)
            _skip(f, Nl[line[0]])  # different system types skip different line counts

    return np.unique(times)
