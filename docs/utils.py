from django.template.defaultfilters import slugify

def postprocess_toc(text, base):
    usednames = {}
    finaltext = ''
    k = 0
    while True:
        try:
            i = text.index(base + "toc_", k)
            finaltext += text[k:i + len(base)]
            j = text.index(">", i)
            k = text.index("<", j + 1)
            name = text[j + 1:k]
            if name.lower() in usednames:
                newname = name + str(usednames[name.lower()])
            else:
                newname = name
                usednames[name.lower()] = 0
            finaltext += slugify(newname) + text[j - 1:j + 1] + name
            usednames[name.lower()] += 1
        except ValueError:
            break
    finaltext += text[k:]
    return finaltext