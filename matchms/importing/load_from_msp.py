import re
from typing import Generator, List, Tuple
import numpy as np
from ..Spectrum import Spectrum


def load_from_msp(filename: str,
                  metadata_harmonization: bool = True) -> Generator[Spectrum, None, None]:
    """
    MSP file to a :py:class:`~matchms.Spectrum.Spectrum` objects
    Function that reads a .msp file and converts the info
    in :py:class:`~matchms.Spectrum.Spectrum` objects.

    Parameters
    ----------
    filename:
        Path of the msp file.
    metadata_harmonization : bool, optional
        Set to False if metadata harmonization to default keys is not desired.
        The default is True.

    Yields
    ------
    Yield a spectrum object with the data of the msp file


    Example:

    .. code-block:: python

        from matchms.importing import load_from_msp

        # Download msp file from MassBank of North America repository at https://mona.fiehnlab.ucdavis.edu/
        file_msp = "MoNA-export-GC-MS-first10.msp"
        spectrums = List(load_from_msp(file_msp))
    """

    for spectrum in parse_msp_file(filename):
        metadata = spectrum.get("params", None)
        mz = spectrum["m/z array"]
        intensities = spectrum["intensity array"]
        peak_comments = spectrum["peak comments"]
        if peak_comments != {}:
            metadata["peak_comments"] = peak_comments

        # Sort by mz (if not sorted already)
        if not np.all(mz[:-1] <= mz[1:]):
            idx_sorted = np.argsort(mz)
            mz = mz[idx_sorted]
            intensities = intensities[idx_sorted]
        try:
            yield Spectrum(mz=mz,
                           intensities=intensities,
                           metadata=metadata,
                           metadata_harmonization=metadata_harmonization)
        except:
            yield None


def parse_msp_file(filename: str) -> Generator[dict, None, None]:
    """Read msp file and parse info in List of spectrum dictionaries."""

    # Lists/dicts that will contain all params, masses and intensities of each molecule
    params = {}
    masses = np.array([])
    intensities = np.array([])
    peak_comments = {}

    # Peaks counter. Used to track and count the number of peaks
    peakscount = 0

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            rline = line.rstrip()

            if len(rline) == 0:
                continue

            if contains_metadata(rline):
                parse_metadata(rline, params)
                continue

            mz, ints, comment = _parse_line_with_peaks(rline)

            masses = np.append(masses, mz)
            intensities = np.append(intensities, ints)
            
            if comment is not None:
                peak_comments.update({masses[-1]: comment})

            peakscount += len(mz)


            # Obtaining the masses and intensities
            if int(params['num peaks']) == peakscount:
                peakscount = 0
                yield {
                    'params': (params),
                    'm/z array': masses,
                    'intensity array': intensities,
                    'peak comments': peak_comments
                }

                params = {}
                masses = []
                intensities = []
                peak_comments = {}
            



def _parse_line_with_peaks(rline: str) -> Tuple[List[float], List[float], str]:
    """Parse a line containing peaks consisting of mz and intensity values with optional comments.

    Args:
        rline (str): Line with peaks read from the MSP.

    Returns:
        Tuple[List[float], List[float], str]: mz, intensity and peak comments obtained from the line.
    """
    comment, rline = get_peak_comment(rline)   
    mz, intensities = get_peak_values(rline)
    
    return mz, intensities, comment


def get_peak_values(peak: str) -> Tuple[List[float], List[float]]:
    """ Get the m/z and intensity value from the line containing the peak information. """
    tokens = re.findall(r'(\d+(?:\.\d+)?(?:e[-+]?\d+)?)', peak)
    if len(tokens) % 2 != 0:
        raise RuntimeError("Wrong peak format detected!")
    
    tokens = list(map(float, tokens))
    mz = tokens[0::2]
    intensities = tokens[1::2]
    return mz, intensities


def get_peak_comment(rline: str) -> Tuple[str, str]:
    """ Get the peak comment from the line containing the peak information. """
    try:
        comment = re.findall(r'[\"\'](.*)[\"\']', rline)[0]
        rline = rline[:rline.index("\"")]
    except IndexError:
        comment = None
    return comment, rline


def parse_metadata(rline: str, params: dict):
    """ Reads metadata contained in line into params dict. """
    matches = []
    splitted_line = rline.split(":", 1)
    if splitted_line[0].lower() == 'comments' and "=" in splitted_line[1]:
        pattern = r'(\S+)="([^"]*)"|"(\w+)=([^"]*)"|"([^"]*)=([^"]*)"|(\S+)=(\d+(?:\.\d*)?)'
        matches = re.findall(pattern, splitted_line[1].replace("'", '"'))
        for match in matches:
            try:
                match = [i for i in match if i]
                key = match[0]
                value = match[1]
                if key.lower().strip() in params.keys() and key.lower().strip() == 'smiles':
                    params[key.lower()+"_2"] = value.strip()
                else:
                    params[key.lower().strip()] = value.strip()
            except:
                pass
    if len(matches) == 0:
        params[splitted_line[0].lower()] = splitted_line[1].strip()


def contains_metadata(rline: str) -> bool:
    """ Check if line contains Spectrum metadata."""
    has_colon = ':' in rline
    return has_colon and not _is_golm_peak_format(rline)

def _is_golm_peak_format(rline: str) -> bool:
    """This function detects whether a line is a line containing peaks in the GOLM MSP format.

    The GOLM MSP format encodes peaks as mz:intensity - this resembles a metadata line, but actually contains peaks.
    It is therefore necessary to explicitly check this corner case when determining whether a line is peaks or metadata.

    Args:
        rline (str): Line to check whether it contains peaks from GOLM

    Returns:
        bool: Whether the line is a line with peaks from GOLM or not.
    """
    return re.match(r"(\d+:{1}\d+)", rline) is not None
