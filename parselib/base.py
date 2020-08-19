from pathlib import Path
from typing import Union, Tuple, Dict, Sequence
from typing.io import TextIO
from .nav2 import rinexnav2
from datetime import datetime, timedelta
from .nav3 import rinexnav3
from .rio import rinexinfo
from .utils import _tlim


def rinexnav(fn: Union[TextIO, str, Path],
             use: Sequence[str] = None,
             tlim: Tuple[datetime, datetime] = None) -> Tuple:
    """ Read RINEX 2 or 3  NAV files"""

    tlim = _tlim(tlim)

    info = rinexinfo(fn)
    if int(info['version']) == 2:
        raw = rinexnav2(fn, tlim=tlim)
    elif int(info['version']) == 3:
        raw = rinexnav3(fn, use=use, tlim=tlim)
    else:
        raise LookupError(f'unknown RINEX  {info}  {fn}')

    return raw