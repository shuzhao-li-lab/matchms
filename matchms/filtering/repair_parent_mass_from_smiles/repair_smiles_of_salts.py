import itertools
import logging
from matchms.filtering.filter_utils.get_monoisotopic_neutral_mass import \
    get_monoisotopic_neutral_mass


logger = logging.getLogger("matchms")


def repair_smiles_of_salts(spectrum_in,
                           mass_tolerance):
    """Repairs the smiles of a salt to match the parent mass.
    E.g. C1=NC2=NC=NC(=C2N1)N.Cl is converted to 1=NC2=NC=NC(=C2N1)N if this matches the parent mass
    Checks if parent mass matches one of the ions"""
    if spectrum_in is None:
        return None
    spectrum = spectrum_in.clone()

    smiles = spectrum.get("smiles")
    parent_mass = spectrum.get("parent_mass")
    possible_ion_combinations = create_possible_ions(smiles)
    if possible_ion_combinations == []:
        # It is not a salt
        return spectrum
    for ion, not_used_ions in possible_ion_combinations:
        ion_mass = get_monoisotopic_neutral_mass(ion)
        mass_diff = abs(parent_mass - ion_mass)
        # Check for Repair parent mass is mol wt did only return 1 spectrum. So not added as option for simplicity.
        if mass_diff < mass_tolerance:
            spectrum_with_ions = spectrum.clone()
            spectrum_with_ions.set("smiles", ion)
            spectrum_with_ions.set("salt_ions", not_used_ions)
            logger.info(f"Removed salt ions: {not_used_ions} from {smiles} to match parent mass")
            return spectrum_with_ions
    logger.warning("None of the parts of the smile %s match the parent mass: %s", smiles, parent_mass)
    return spectrum


def create_possible_ions(smiles):
    """Selects all possible ion combinations of a salt"""

    results = []
    if "." in smiles:
        single_ions = smiles.split(".")
        for r in range(1, len(single_ions) + 1):
            combinations = itertools.combinations(single_ions, r)
            for combination in combinations:
                combined_ion = ".".join(combination)
                removed_ions = single_ions.copy()
                for used_ion in combination:
                    removed_ions.remove(used_ion)
                removed_ions = ".".join(removed_ions)
                results.append((combined_ion, removed_ions))
    return results
