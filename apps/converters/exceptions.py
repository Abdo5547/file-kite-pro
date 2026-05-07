class ConverterError(Exception):
    """
    Erreur métier générique pour les conversions FileKit Pro.
    """


class InvalidFileError(ConverterError):
    """
    Fichier invalide, corrompu, vide ou non supporté.
    """


class UnsupportedConversionError(ConverterError):
    """
    Conversion non supportée.
    """


class ProtectedFileError(ConverterError):
    """
    Fichier protégé par mot de passe ou verrouillé.
    """


class ProcessingLimitError(ConverterError):
    """
    Limite utilisateur ou plan dépassée.
    """