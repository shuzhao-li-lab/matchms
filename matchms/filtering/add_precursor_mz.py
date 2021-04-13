from typing import Iterable
from typing import TypeVar
from ..typing import SpectrumType


_T = TypeVar('_T')
_accepted_keys = ["precursor_mz", "precursormz", "precursor_mass"]


def get_first_common_element(first: Iterable[_T], second: Iterable[_T]) -> _T:
    """ Get first common element from two lists.
    Returns 'None' if there are no common elements.
    """
    return next((item for item in first if item in second), None)


def add_precursor_mz(spectrum_in: SpectrumType) -> SpectrumType:
    """Add precursor_mz to correct field and make it a float.

    For missing precursor_mz field: check if there is "pepmass"" entry instead.
    For string parsed as precursor_mz: convert to float.
    """
    if spectrum_in is None:
        return None

    spectrum = spectrum_in.clone()

    precursor_mz_key = get_first_common_element(spectrum.metadata.keys(), _accepted_keys)
    precursor_mz = spectrum.get(precursor_mz_key)

    if isinstance(precursor_mz, str):
        precursor_mz = float(precursor_mz.strip())
        spectrum.set("precursor_mz", precursor_mz)
    elif isinstance(precursor_mz, float):
        spectrum.set("precursor_mz", precursor_mz)
    elif precursor_mz is None:
        pepmass = spectrum.get("pepmass")
        if pepmass is not None and isinstance(pepmass[0], float):
            spectrum.set("precursor_mz", pepmass[0])
        else:
            print("No precursor_mz found in metadata.")

    return spectrum
