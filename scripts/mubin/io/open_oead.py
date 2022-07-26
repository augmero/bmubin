from oead import aamp, byml, Sarc, yaz0
from pathlib import Path

class OEADFile:
    """A wrapper class containg easy access to the meta data of an oead file."""

    content = {}
    """Dictionary or list of the OEADFile instances' content in an editable form."""

    file_bytes = []
    """Byte array of the OEADFile instances' file bytes."""

    type = ''
    """Similar to Magic except BYML is one type."""

    sub_type = ''
    """Sub type is the BYML type, e.g. MUBIN, ACTORINFO"""

    endian = True
    """
    The OEADFile instances' endian type as a bool.

    Possible types are True (Big Endian) or False (Little Endian)
    """

    is_yaz0 = False
    """Boolean defining the Yaz0 compression status."""

class OpenOead:
    """Basic in/out funtions for handling oead formats."""

    def from_bytes(data: bytes) -> OEADFile:
        """Opens the read bytes of an oead file and returns an OEADFile."""

        oead_file = OEADFile()
        oead_file.file_bytes = data

        if data[:4] == b'Yaz0':
            oead_file.is_yaz0 = True
            data = yaz0.decompress(data)

        if data[:2] == b'BY' or b'YB':
            # Set type
            oead_file.type = 'BYML'
            oead_file.content = byml.from_binary(data)

            # Set sub type
            if 'Objs' and 'Rails' in oead_file.content:
                oead_file.sub_type = 'MUBIN'
            elif 'Actors' and 'Hashes' in oead_file.content:
                oead_file.sub_type = 'ACTORINFO'

            # Set endianness
            if data[:2] == b'YB':
                oead_file.endian = False

        if data[:4] == b'AAMP':
            # Set type
            oead_file.type = 'AAMP'
            oead_file.content = aamp.ParameterIO.from_binary(data)

        if data[:4] == b'SARC':
            # Set type
            oead_file.type = 'SARC'
            oead_file.content = Sarc(data).get_files()

            # Set endianness
            if Sarc(data).get_endianness() == 'Little':
                oead_file.endian = False

        return oead_file

    def from_path(path) -> OEADFile:
        return OpenOead.from_bytes(Path(path).read_bytes())