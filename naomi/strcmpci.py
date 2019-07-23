import unicodedata


def strcmpci(str1, str2):
    return unicodedata.normalize(
        "NFKD",
        str1.casefold()
    ) == unicodedata.normalize(
        "NFKD",
        str2.casefold()
    )
