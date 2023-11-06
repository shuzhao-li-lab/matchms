import logging
import re
from typing import Any, List, Optional
from matchms.typing import SpectrumType
from matchms.utils import filter_none, get_common_keys


logger = logging.getLogger("matchms")


_retention_time_keys = ["retention_time", "retentiontime", "rt", "scan_start_time",
                        "rt_query", "rtinseconds"]
_retention_index_keys = ["retention_index", "retentionindex", "ri"]


def _safe_store_value(metadata: dict, value: Any, target_key: str) -> dict:
    """Helper function to safely store a value in the target key without throwing an exception, but storing 'None' instead.

    Parameters
    ----------
    spectrum
        Spectrum to which to add 'value' in 'target_key'.
    value
        Value to parse into 'target_key'.
    target_key
        Name of the key in which to store the value.

    Returns
    -------
    Spectrum with added key.
    """
    if value is not None:   # one of accepted keys is present
        value = _safe_convert_to_float(value)
    metadata[target_key] = value
    return metadata


def _safe_convert_to_float(value: Any) -> Optional[float]:
    """Safely convert value to float. Return 'None' on failure.

    Parameters
    ----------
    value
        Object to convert to float.

    Returns
    -------
    Converted float value or 'None' if conversion is not possible.
    """
    try:
        if isinstance(value, list):
            if len(value) == 1:
                value = value[0]
            else:
                return None
    
        # logic to read MoNA msp files which specify rt as string with "min" in it
        if isinstance(value, str):
            value = value.strip()
            pattern = r'^[+-]?(\d*\.)?\d+\s*(min|s|h|ms)'
            conversion = {"min": 60, "sec": 1, "s": 1, "h": 3600, "ms": 1e-3, "sec":60}
            match = re.search(pattern, value)
    
            if match and len(match.groups()) == 2:
                val, unit = value.split(' ')
                try:
                    return float(val) * conversion[unit]
                except:
                    return None
        try:
            value = float(value)
            rt = value if value >= 0 else None  # discard negative RT values
        except (ValueError, TypeError):
            logger.warning("%s can't be converted to float.", str(value))
            rt = None
        return rt
    except:
        return None

def _add_retention(metadata: dict, target_key: str, accepted_keys: List[str]) -> dict:
    """Add value from one of accepted keys to target key.

    Parameters
    ----------
    spectrum
        Spectrum from which to read the values.
    target_key
        Key under which to store the value.
    accepted_keys
        List of accepted keys from which a value will be read (in order).

    Returns
    -------
    Spectrum with value from first accepted key stored under target_key.
    """
    common_keys = get_common_keys(metadata.keys(), accepted_keys)
    values_for_keys = filter_none([metadata[key] for key in common_keys])
    values = list(map(_safe_convert_to_float, values_for_keys))
    value = next(filter_none(values), None)

    metadata = _safe_store_value(metadata, value, target_key)
    return metadata


def add_retention_time(spectrum_in: SpectrumType) -> SpectrumType:
    """Add retention time information to the 'retention_time' key as float.
    Negative values and those not convertible to a float result in 'retention_time'
    being 'None'.

    Parameters
    ----------
    spectrum
        Spectrum with retention time information.

    Returns
    -------
    Spectrum with harmonized retention time information.
    """
    if spectrum_in is None:
        return None

    spectrum = spectrum_in.clone()

    target_key = "retention_time"
    spectrum.metadata = _add_retention(spectrum.metadata, target_key, _retention_time_keys)
    return spectrum


def add_retention_index(spectrum_in: SpectrumType) -> SpectrumType:
    """Add retention index into 'retention_index' key if present.


    Parameters
    ----------
    spectrum
        Spectrum with RI information.
    Returns
    -------
    Spectrum with RI info stored under 'retention_index'.
    """
    if spectrum_in is None:
        return None

    spectrum = spectrum_in.clone()

    target_key = "retention_index"
    spectrum.metadata = _add_retention(spectrum.metadata, target_key, _retention_index_keys)
    return spectrum
