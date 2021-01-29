from ..constants import PROTON_MASS
from ..importing import load_adducts_table
from ..typing import SpectrumType


def add_parent_mass(spectrum_in: SpectrumType, estimate_from_adduct: bool = True) -> SpectrumType:
    """Add estimated parent mass to metadata (if not present yet).

    Method to calculate the parent mass from given precursor m/z together
    with charge and/or adduct. Will take precursor m/z from either "precursor_mz"
    or "pepmass" field.
    For estimate_from_adduct=True this function will estimate the parent mass based on
    the mass and charge of known adducts. The table of known adduct properties can be
    found under :download:`matchms/data/known_adducts_table.csv </../matchms/data/known_adducts_table.csv>`.

    Parameters
    ----------
    spectrum_in
        Input spectrum.
    estimate_from_adduct
        When set to True, use adduct to estimate actual molecular mass ("parent mass").
        Default is True. Still switches back to charge-based estimate if adduct does not match
        known adduct.
    """
    if spectrum_in is None:
        return None

    spectrum = spectrum_in.clone()
    adducts_table = load_adducts_table()

    if spectrum.get("parent_mass", None) is None:
        parent_mass = None
        charge = spectrum.get("charge")
        adduct = spectrum.get("adduct")
        # Get precursor m/z
        try:
            precursor_mz = spectrum.get("precursor_mz", None)
            if precursor_mz is None:
                precursor_mz = spectrum.get("pepmass")[0]
        except KeyError:
            print("Not sufficient spectrum metadata to derive parent mass.")

        spectrum = spectrum_in.clone()
        if estimate_from_adduct and adduct in adducts_table.adduct.to_list():
            adduct_data = adducts_table[adducts_table.adduct == adduct]
            multiplier = adduct_data.mass_multiplier.values
            correction_mass = adduct_data.correction_mass.values
            parent_mass = precursor_mz * multiplier - correction_mass

        if parent_mass is None:
            # Otherwise assume adduct of shape [M+xH] or [M-xH]
            protons_mass = PROTON_MASS * charge
            precursor_mass = precursor_mz * abs(charge)
            parent_mass = precursor_mass - protons_mass

        if parent_mass is not None:
            spectrum.set("parent_mass", parent_mass)
    return spectrum
