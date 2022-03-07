def replace(text, *params):
    return text.replace(params[0], params[1])


def capitalizeAll(text, *params):
    return text.title()


def capitalize_(text, *params):
    return text[0].upper() + text[1:]


def a(text, *params):
    if len(text) > 0:
        if text[0] in "uU":
            if len(text) > 2:
                if text[2] in "iI":
                    return "a " + text
        if text[0] in "aeiouAEIOU":
            return "an " + text
    return "a " + text


def firstS(text, *params):
    text2 = text.split(" ")
    return " ".join([s(text2[0])] + text2[1:])


def s(text, *params):
    if text[-1] in "shxSHX":
        return text + "es"
    elif text[-1] in "yY":
        if text[-2] not in "aeiouAEIOU":
            return text[:-1] + "ies"
        else:
            return text + "s"
    else:
        return text + "s"


def ed(text, *params):
    if text[-1] in "eE":
        return text + "d"
    elif text[-1] in "yY":
        if text[-2] not in "aeiouAEIOU":
            return text[:-1] + "ied"
    else:
        return text + "ed"


def uppercase(text, *params):
    return text.upper()


def lowercase(text, *params):
    return text.lower()


base_english = {
    'replace': replace,
    'capitalizeAll': capitalizeAll,
    'capitalize': capitalize_,
    'a': a,
    'firstS': firstS,
    's': s,
    'ed': ed,
    'uppercase': uppercase,
    'lowercase': lowercase
}
