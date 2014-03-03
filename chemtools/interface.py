import os
import re
from cStringIO import StringIO
import zipfile

import gjfwriter
import utils
import mol_name
import dataparser
import ml


def get_multi_molecule(molecules, keywords, options, form):
    buff = StringIO()
    zfile = zipfile.ZipFile(buff, "w", zipfile.ZIP_DEFLATED)

    generrors = []
    for name in molecules:
        try:
            out = gjfwriter.GJFWriter(name, keywords)
            others = False

            if "image" in options:
                zfile.writestr(out.name + ".png", out.get_png(10))
                others = True
            if "mol2" in options:
                zfile.writestr(name + ".mol2", out.get_mol2())
                others = True
            if "job" in options:
                dnew = form.get_single_data(name)
                zfile.writestr(name + ".job", utils.write_job(**dnew))
                others = True

            if "gjf" in options or not others:
                zfile.writestr(name + ".gjf", out.get_gjf())

        except Exception as e:
            generrors.append("%s - %s" % (name, e))
    if generrors:
        zfile.writestr("errors.txt", '\n'.join(generrors))

    zfile.close()
    buff.flush()

    ret_zip = buff.getvalue()
    buff.close()
    return ret_zip


def get_multi_job(string, form):
    buff = StringIO()
    zfile = zipfile.ZipFile(buff, 'w', zipfile.ZIP_DEFLATED)

    for name in mol_name.name_expansion(string):
        if not name:
            continue
        name, _ = os.path.splitext(name)
        dnew = form.get_single_data(name)
        zfile.writestr("%s.%sjob" % (name, dnew.get("cluster")),
                        utils.write_job(**dnew))

    zfile.close()
    buff.flush()

    ret_zip = buff.getvalue()
    buff.close()
    return ret_zip


def get_property_limits(molecule):
    results = {
                "n": [None, None, None],
                "m": [None, None, None]
                }
    for direction in results:
        try:
            groups = []
            xvals = range(1, 5)
            for j in xvals:
                if direction in molecule:
                    exp = "%s\d+" % direction
                    replace = "%s%d" % (direction, j)
                    temp_name = re.sub(exp, replace, molecule)
                else:
                    temp_name = molecule + "_%s%d" % (direction, j)

                temp_exact = mol_name.get_exact_name(temp_name, spacers=True)
                temp = ml.get_decay_feature_vector(temp_exact)
                groups.append(ml.get_properties_from_decay_with_predictions(
                                                                temp
                                                                ))
            lim_results = dataparser.predict_values(xvals, *zip(*groups))
            properties = ["homo", "lumo", "gap"]
            results[direction] = [lim_results[x][0] for x in properties]
        except Exception as e:
            pass
    return results