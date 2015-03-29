Naming Scheme
------------
There are four main classifications of the parts of the name.

### Cores ###

Cores are made up of three parts, the type, the "x" element, and the "y" element. There are 2 options for type. The molecule can either be Cis (C), Trans (T), single sided same side (Z), or single sided opposite side (E). The x element can, in theory, be any element that allows at least 2 bonds (Oxygen, Sulfur, Nitrogen, Phosphorus, Carbon). The x element can be any element that allows at least 3 bonds (Nitrogen, Phosphorus, Carbon).

    CON = Cis Oxygen Nitrogen
    TON = Trans Oxygen Nitrogen
    CSN = Cis Sulfur Nitrogen
    TSN = Trans Sulfur Nitrogen
    CNN = Cis Nitrogen Nitrogen
    TNN = Trans Nitrogen Nitrogen
    CCC = Cis Carbon Carbon
    TCC = Trans Carbon Carbon


### Aryl ###

    2 = Double Bond
    3 = Triple Bond
    4 = Phenyl
    5 = Thiophene
    6 = Pyridine
    7 = Carbazole
    8 = Tetrazine
    9 = EDOT
    10 = DTP
    11 = Acetyl
    12 = Furan
    13 = Pyrrole

Within Aryl there are also two minor sub classifications of Aryl groups.
#### Zero Substituent ####

    2,3,8,9,10,11

#### Two Substituent ####

    4,5,6,7,12,13


### X-Groups ####

    A = Hydrogen
    B = Chlorine
    C = Bromine
    D = Cyano
    E = Alkyne
    F = Hydroxy
    G = Thiol
    H = Amine
    I = Methyl
    J = Phenyl
    K = TMS
    L = Methoxy
    M = Fluorine


### R-Groups ####

    a = Hydrogen
    b = Chlorine
    c = Bromine
    d = Cyano
    e = Alkyne
    f = Hydroxy
    g = Thiol
    h = Amine
    i = Methyl
    j = Phenyl
    k = TMS
    l = Methoxy
    m = Fluorine


### Basic Examples ####

From there the name takes a form similar to this:

    24a_TON_35b_24c

![/chem/24a_TON_35b_24c.png](/chem/24a_TON_35b_24c.png)

The left part (`24a` in this case) corresponds to the left side of the cruciform. The next part is the core. The next part goes with the two vertical parts. In the past, there was an edge case that allowed the first letter in this group to be the middle group. This is no longer allowed.

    24a_TON_B_24a

![/chem/24a_TON_B_24a.png](/chem/24a_TON_B_24a.png)

The last part of the name is the right side of the molecule. Beyond the slight option for the middle, there is also the ability to leave off any of the sides and they will be assumed to be just a hydrogen.

    TON_24a_24a

![/chem/TON_24a_24a](/chem/TON_24a_24a.png)

    24a_TON_24a

![/chem/24a_TON_24a](/chem/24a_TON_24a.png)

    24a_TON

![/chem/24a_TON](/chem/24a_TON.png)


### Polymer ####

Added to the naming scheme are two types of expansion. They are polymer type and stacking type. The former is a direct linking of the parts of the molecule. The latter is, basically, just a copy and paste along the respective axis. In the case of polymer type expansion, one can not have both an `n` (along the horizontal axis) and `m` (along the vertical) expansion due to conflicts in the connection points.

    4a_TON_n2

![/chem/4a_TON_n2](/chem/4a_TON_n2.png)

    4a_TON_24c_n3

![/chem/4a_TON_24c_n3](/chem/4a_TON_24c_n3.png)

    4a_TON_35_2_m3

![/chem/4a_TON_35_2_m3](/chem/4a_TON_35_2_m3.png)


### Multicore ####

In addition to building molecules with a single core, this also allows creating multicore structures. For multicore structures, it attributes all the segments directly to the right (up until the next core) as part of the current core.

    TON_24a_24a_TON

![/chem/TON_24a_24a_TON](/chem/TON_24a_24a_TON.png)

At first glance it might seem like there would be a problem correctly grouping center verses right side groups when dealing with multicore structures. This problem is rectified by removing group that is not present and leaving the separating underscore.

    TON_24a__TON

![/chem/TON_24a__TON](/chem/TON_24a__TON.png)

    TON__24a_TON

![/chem/TON__24a_TON](/chem/TON__24a_TON.png)


### No Core ####

Beyond multicore names, there is also the ability to build chains just from the aryl groups by excluding the cores altogether. When there is no core in the structure name, all underscores are rendered just as spaces in the name that mean nothing. All of the following names are equivalent.

    4444
    4_444
    44_44
    444_4
    4_4_44
    4_44_4
    44_4_4
    4_4_4_4

![/chem/4444](/chem/4444.png)

From this example, you might also notice that there is no distinct direction that the chain goes in. This is due to the fact that each of these structures on their own does not have a defined orientation like they would have if they were being built from a core.


### Rotating/Flipping ####

A little less obvious of a problem that arises from this naming scheme is how to handle rotations (a group can be rotated 180 degrees around the bond axis). This problem has been solved by the addition of a meta character `-`.

    55

![/chem/55](/chem/55.png)

    5-5

![/chem/5-5](/chem/5-5.png)

This character applies to the the Aryl group directly preceding the character. So the following names are all equivalent.

    5-b
    5b-
    5-bb
    5b-b
    5bb-

![/chem/55b-5](/chem/55b-5.png)
![/chem/55b5](/chem/55b5.png)

In addition to being able to flip the Aryl groups 180 degrees, there is also the ability to freeze the dihedral angles between two Aryl groups. This is done by adding `(x)` after the Aryl group that needs to be rotated (where `x` is some angle in degrees). Note that the `-` token is not required with this.

    44

![/chem/44](/chem/44.png)

    44(70)

![/chem/44\(70\)](/chem/44\(70\).png)

The angles between groups are all relative to the previous Aryl group, so creating a spiral affect is simple.

    44(20)4(20)4(20)4(20)4(20)

![/chem/44\(20\)4\(20\)4\(20\)4\(20\)4\(20\)](/chem/44\(20\)4\(20\)4\(20\)4\(20\)4\(20\).png)

In addition to positive angles, negative angles are also supported.

    55(35)

![/chem/55\(35\)](/chem/55\(35\).png)

    55(-35)

![/chem/55\(-35\)](/chem/55\(-35\).png)

### Other Examples ####

For some fun with the naming:

    4a_TON_5555555555_4a
    5_TON_n13
    5ba_TON_5ba55_TON_345495_2_TON_n6


### Errors ####


Any errors in the naming scheme will be denoted on the respective molecules page. The error reporting is currently fairly primitive, but it gives an idea of the problem in the structure name. An example problem being

`no rgroups allowed on aryl0`

[/chem/2a\_TON](/chem/2a_TON)

This is caused because the double bond can not have any R-Group substituants. This can be fixed by using `A` instead of `a` because the former is an X-Group.

Another example of an error is if you try to put a name that contains a part that is not a valid token.

`Bad Substituent Name(s): [u'z']`

[/chem/2za\_TON/](/chem/2za_TON/)

In this example, it tells you the exact value that was invalid.

If there are errors in the molecule, or if the molecule gives an error when it should work, feel free to submit an error report by clicking the "Report Me" button seen on all of the molecule pages. This button is also listed for each molecule on the multi molecule pages.
