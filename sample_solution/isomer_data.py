import os
import math
from sample_solution.element_info import ElementInfo


class IsomerData:
    '''
    This class retrieves and stores data relevant to a single isomer
    '''
    @classmethod
    def filename_from_nuclear_data(cls, atomic_number: int, atomic_mass: int, energy_state: int = 0):
        '''
        Returns the filename of the ENDF file for the isomer with the given nuclear data
        :param cls: The class
        :param atomic_number: int The atomic number of the isomer
        :param atomic_mass: int The atomic mass of the isomer
        :param energy_state: int The energy state of the isomer
        :return: str The filename of the ENDF file for the isomer with the given nuclear data'''
        filename = "dec-{}_{}_{}".format(str(atomic_number).zfill(3), ElementInfo.get_element_symbol_from_atomic_number(atomic_number), str(atomic_mass).zfill(3))

        if energy_state:
            filename += "m{}".format(energy_state)

        filename += ".endf"

        return filename

    @staticmethod
    def isomer_name_from_nuclear_data(atomic_number: int, atomic_mass: int, energy_state: int = 0):
        '''
        Returns the isomer name of the isomer with the given nuclear data
        :param atomic_number: int The atomic number of the isomer
        :param atomic_mass: int The atomic mass of the isomer
        :param energy_state: int The energy state of the isomer
        :return: str The isomer name of the isomer with the given nuclear data
        '''
        isomer_name = "{}{}".format(ElementInfo.get_element_symbol_from_atomic_number(atomic_number), atomic_mass)

        if energy_state:
            isomer_name += "m{}".format(energy_state)

        return isomer_name

    @classmethod
    def nuclear_data_from_name(cls, isomer_name: str):
        '''
        Returns the nuclear data of the isomer with the given isomer name
        :param cls: The class
        :param isomer_name: str The isomer name of the isomer
        :return: tuple(int, int, int) The nuclear data of the isomer with the given isomer name
        '''
        for i, char in enumerate(isomer_name):
            if char.isnumeric():
                n_char_symbol = i
                break

        symbol = isomer_name[:n_char_symbol]

        atomic_number = ElementInfo.get_atomic_number_from_element_symbol(symbol)

        mass_and_group = isomer_name[n_char_symbol:].split("m")

        atomic_mass = int(mass_and_group[0])

        try:
            energy_state = int(mass_and_group[1])
        except IndexError:
            energy_state = 0

        return atomic_number, atomic_mass, energy_state

    @classmethod
    def filename_from_isomer_name(cls, isomer_name: str):
        '''
        Returns the filename of the ENDF file for the isomer with the given isomer name
        :param cls: The class
        :param isomer_name: str The isomer name of the isomer
        :return: str The filename of the ENDF file for the isomer with the given isomer name
        '''
        nuclear_data = cls.nuclear_data_from_name(isomer_name)

        filename = cls.filename_from_nuclear_data(*nuclear_data)

        return filename

    @staticmethod
    def nuclear_data_from_filename(filename: str):
        '''
        Returns the nuclear data of the isomer with the given filename
        :param filename: str The filename of the ENDF file for the isomer
        :return: tuple(int, int, int) The nuclear data of the isomer with the given filename
        '''
        atomic_number = int(filename[4:7])
        mass_and_group = filename.split("_")[2].split(".")[0]
        atomic_mass = int(mass_and_group.split("m")[0])
        try:
            energy_state = int(mass_and_group.split("m")[1])
        except IndexError:
            energy_state = 0

        return atomic_number, atomic_mass, energy_state

    @classmethod
    def isomer_name_from_filename(cls, filename: str):
        '''
        Returns the isomer name of the isomer with the given filename
        :param filename: str The filename of the ENDF file for the isomer
        :return: str The isomer name of the isomer with the given filename
        '''
        nuclear_data = cls.nuclear_data_from_filename(filename)

        isomer_name = cls.isomer_name_from_nuclear_data(*nuclear_data)

        return isomer_name

    @classmethod
    def instance_from_filename(cls, filename: str, directory_prefix: str = None):
        '''
        Returns an instance of the class representing the isomer with the given filename
        :param filename: str The filename of the ENDF file for the isomer
        :param directory_prefix: str The directory prefix to add to the filename
        :return: IsomerData An instance of the class representing the isomer with the given filename'''
        isomer_name = cls.isomer_name_from_filename(filename)

        return cls(isomer_name, directory_prefix)

    def __init__(self, isomer_name: str, data_directory_prefix: str = None):
        '''
        Initialises the class representing the isomer with the given isomer name
        :param isomer_name: str The isomer name of the isomer
        :param data_directory_prefix: str The directory prefix to add to the filename
        '''
        self._isomer_name = isomer_name
        self._atomic_number, self._atomic_mass, self._energy_state = self.nuclear_data_from_name(isomer_name)

        filename = self.filename_from_isomer_name(isomer_name)

        try:
            filepath = os.path.join(data_directory_prefix, filename)
        except TypeError:
            filepath = filename

        with open(filepath) as f:
            lines = f.readlines()

        # Find the decay rate
        for line in lines:
            if line[:16] == "Parent half-life":
                decay_rate_word = line.split(" ")[2]
                decay_rate_unit = line.split(" ")[3]
                break
        else:
            raise ValueError("No decay rate in this file")

        if decay_rate_word == "STABLE":
            self._stable = True
            self._decay_rate = 0.0
            self._decay_atomic_number_change = 0
            self._decay_atomic_mass_change = 0
            return

        self._stable = False
        self._decay_rate = math.log(2) / float(decay_rate_word)
        match decay_rate_unit:
            case "PS":
                self._decay_rate *= 1e12
            case "NS":
                self._decay_rate *= 1e9
            case "US":
                self._decay_rate *= 1e6
            case "MS":
                self._decay_rate *= 1e3
            case "S":
                pass
            case "M":
                self._decay_rate /= 60
            case "H":
                self._decay_rate /= 3.6e3
            case "D":
                self._decay_rate /= 8.64e4
            case "Y":
                self._decay_rate /= 3.1536e7
            case _:
                raise ValueError("Unknown Half-Life Unit '{}'".format(decay_rate_unit))

        # Find the decay mode
        for line in lines:
            if line[:10] == "Decay Mode":
                decay_mode = line.split()[2]
                break
        else:
            raise ValueError("No decay mode in this file")

        match decay_mode:
            case "A":
                self._decay_atomic_number_change = -2
                self._decay_atomic_mass_change = -4
            case "B-":
                self._decay_atomic_number_change = 1
                self._decay_atomic_mass_change = 0
            case "EC":
                self._decay_atomic_number_change = -1
                self._decay_atomic_mass_change = 0
            case _:
                raise ValueError("Unknown decay mode '{}'".format(decay_mode))

    @property
    def stable(self):
        '''
        Returns whether the isomer is stable
        :return: bool Whether the isomer is stable'''
        return self._stable

    @property
    def decay_rate(self):
        '''
        Returns the decay rate of the isomer
        :return: float The decay rate of the isomer in units of 1/s'''
        return self._decay_rate

    @property
    def decay_atomic_number_change(self):
        '''
        Returns the change in atomic number of the isomer due to decay
        :return: int The change in atomic number of the isomer due to decay
        '''
        return self._decay_atomic_number_change

    @property
    def decay_atomic_mass_change(self):
        '''
        Returns the change in atomic mass of the isomer due to decay
        :return: int The change in atomic mass of the isomer due to decay
        '''
        return self._decay_atomic_mass_change

    @property
    def atomic_number(self):
        '''
        Returns the atomic number of the isomer
        :return: int The atomic number of the isomer'''
        return self._atomic_number

    @property
    def atomic_mass(self):
        '''
        Returns the atomic mass of the isomer
        :return: int The atomic mass of the isomer'''
        return self._atomic_mass

    @property
    def energy_state(self):
        '''
        Returns the energy state of the isomer
        :return: int The energy state of the isomer
        '''
        return self._energy_state

    @property
    def daughter_name(self):
        '''
        Returns the name of the daughter isomer
        :return: str The name of the daughter isomer
        '''
        daughter_atomic_number = self.atomic_number + self.decay_atomic_number_change
        daughter_atomic_mass = self.atomic_mass + self.decay_atomic_mass_change
        daughter_energy_state = 0

        return self.isomer_name_from_nuclear_data(daughter_atomic_number, daughter_atomic_mass, daughter_energy_state)

    def __str__(self):
        '''
        Returns a string representation of the isomer
        :return: str A string representation of the isomer
        '''
        return "Isomer data for {}".format(self.isomer_name)
