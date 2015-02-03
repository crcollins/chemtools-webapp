
_______________________________________________________________________
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


_______________________________________________________________________
Functionality
-------------

### Molecules ###

All of the following forms of output are possible for all of the molecules generated.

- gjf - a standard Gaussian Cartesian connectivity molecule file
- mol2 - a standard Cartesian-style molecule file format
- png - this is just a very rough rendering of the structure of the molecule.
- svg - this is the same as the png rendering with the added benefit that it is a vector image
- json - this returns a json object with all of the properties of a molecule.
- Job - there also is a job form on each molecule page that will allow generation of job files for any of the clusters given a few parameters.

In addition to the files, the page for each structure also includes the exact name, the feature vector, and estimates for the HOMO, LUMO, and Band Gap energies. These estimates are calculated using a support vector machines predictor which was trained on about 1100 single core benzobisazole structures with side lengths less than 5 aryl groups.

Currently the system implemented updates the predictors every night if there have been more structures added to the database.


### Jobs ###
#### Generating Job Files ####

Job files can be made on the respective molecule pages using the Job Form. The job form allows simple replacement for the mechanical task of making new job files for each molecule.

Added with just being able to view the job file there is Alpha functionality to be able to directly upload both jobs and molecules to a cluster and run the respective job. Currently, these submit at about a rate of half a molecule per second. The current assumption is that this is more network bound.

Jobs can also be made in bulk using the [Make Jobs](/chem/multi_job/) page.

#### Show Running Jobs ####

If you are logged in, and have set up your credentials, then under the [Running](/chem/jobs/) page you can see all the jobs you currently have running on any cluster you have credentials for. Along with seeing the currently running jobs, there are also buttons that allow you to kill running jobs.


### Upload ###
#### Log Parse ####

This takes normal Gaussian log files and will output a text file comma delimited with various useful values from the log file (Name, HOMO, LUMO, HomoOrbital, Dipole, Energy, Excited, Time).


#### Long Chain Limit ####

To calculate the long chain limit, a file formated like this is needed:

    # 1/n values
    0.09091, 0.04545, 0.0303, 0.02273
    # homo values
    -5.54384, -5.41377, -5.37377, -5.3686
    # lumo values
    -2.17367, -2.45232, -2.55599, -2.59491
    # gap values
    3.1548, 2.61, 2.4482, 2.3972

Where lines starting with "#" are comments. The `n` values can be given as either `n` or `1/n`. This will return a zipped file with a text file listing the fit parameters as well as two graphs plotting the HOMO/LUMO and the Gap values.

The actual reading of information can also be done now using just the log files. If you upload a set of log files with `n1, n2, ... nN` somewhere in the filename these logs will be put together. Once together they will be parsed for the relevant data and the long chain limit will be calculated. This simplifies the process by not requiring the creation of a separate file just for the data.


#### Gjf Reset ####

This takes a log file and returns a gjf file with the extracted geometry. This is intended to be used to extract the optimized geometry from the DFT log files to then use as the TDDFT gjf file. _WARNING: this will not work in some cases where the job stopped part way through writing._ If this does occur, the parser will try to get the geometry from the top of the log file and return the same geometry that was used for the job.

In addition to just being able to write out the gjf with the same parameters that were used to generate the log file, this also allows the creation of TDDFT files. If you are logged in, you can use this same mechanism to then submit the TDDFT calculation on the spot.


### Users ###
#### Account ####

Chemtools-Webapp has a very simplified view of user accounts. They are mainly used as a shell to persistently store information like emails and usernames for submitting jobs on the clusters. They are also used as a way of keeping track of cluster credentials.

Registering an account is much like any other site. An email server is not set up yet so it does not do email verification, but that is more of a formality anyways. After registering, click the activation key link to active your account.

After your directories on the cluster are setup, then you need to setup your SSH Keys.


#### SSH Keys ####

SSH keys can be generated for direct access to the clusters, or you can provide your own. The ones being used are generated by PyCrypto and are 2048 bit keys.

For the initial setup of the SSH keys, it does require a little bit of foot work. Which amounts to SSH-ing into the cluster of choice and running the following command, where $USERNAME is your username.

    $ wget /u/$USERNAME/id_rsa.pub -O- >> ~/.ssh/authorized_keys

After this key is added nothing else will have to be done. If you change your ssh key with chemtools it will auto update all of the clusters that you have credentials for with the new key.


#### Credentials ####

To give chemtools the ability to get and submit files/jobs on the clusters it must have the correct credentials stored so that it can log in. Credentials come in two forms: credentials using passwords, and credentials using ssh keys. The former is less secure due to the fact that the login password must be stored on the chemtools server. In light of this, the passwords are all stored with 128 bit AES encryption. The latter type of credential makes use of the public/private keys that chemtools generates for each user. To use these, you will need to follow the instructions in the [SSH Keys](#ssh-keys) section.

It is _strongly_ recommended to use the SSH key type credential for clusters.

If you are logged in, Credentials can be added in the [account settings pages](/u/username/credentials/).




_______________________________________________________________________
API
---

Right now, the API is very minimal, the current access is just enough to give the basic functionality to the entire site. These features include: dynamic generation of .gjf, .mol2, .svg, and .png files for any molecule given the name.


### Naming ###
OSNPC
For generating the molecules, there is a very rough Finite State Machine that parses through the names given and spits out either the molecule requested or an error. Here is roughly what the context free grammar would look like.

    digit       = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
    int         = digit, { digit } ;

    YY          = "N" | "P" | "C" ;
    XX          = "O" | "S" | YY ;
    type        = "C" | "T" | "E" | "Z" ;
    core        = type, XX, YY ;
    aryl0       = "10" | "11" | "2" | "3" | "8" | "9" ;
    aryl2       = "12" | "13" | "4" | "5" | "6" | "7" ;
    aryl        = aryl0 | aryl2 ;
    xgroup      = "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J" | "K" | "L" | "M" ;
    rgroup      = "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j" | "k" | "l" | "m" ;
    full        = aryl2, ["-"], [rgroup], ["-"], [rgroup], ["-"] ;
    end         = [aryl0, {aryl0}], [full, {full}], [xgroup] ;

    extend      = ("n" | "m"), int ;
    stack       = ("x" | "y" | "z"), int ;

    main        = [end, "_"], core, ["_", end2, "_"], [("_" | "__"), end2] ;
    molecule    = main, {"_", main}, ["_", extend], ["_", stack] {"_", stack} ;


### Molecule Specific ###

For all of the molecules there is a basic API access to allow getting the different types of outputs. The first, and most common, being the gjf output. This is the standard Gaussian file type and is what should be used for running the calculations. There is also an added possible parameter called "keywords" that can be added to add/change the keywords/settings of the molecule. If none is given, then `opt B3LYP/6-31g(d)` is assumed. Another possible parameter is "view". If this is enabled the output will be browser viewable rather than a download.

    /chem/$NAME.gjf
    /chem/$NAME.gjf?keywords=B3LYP/6-31g(d)
    /chem/$NAME.gjf?view=true

The next form of output is the mol2 format. This is added because it is a fairly simple interchange format for different software packages.

    /chem/$NAME.mol2
    /chem/$NAME.mol2?view=true

The last type of molecule specific access is an image of the structure. This comes in two different forms, both of which show the exact same thing. The first is a standard .png image. The second is a vector version in the form of a .svg. It is a very basic rendering over the overall structure of the molecule.

    Single Bond     = single black line
    Aromatic Bond   = two dashed red lines
    Double Bond     = two green lines
    Triple Bond     = three blue lines

    Sulfur          = yellow dot
    Oxygen          = red dot
    Nitrogen        = blue dot
    Chlorine        = green dot
    Carbon          = medium gray dot
    Phosphorus      = orange dot
    Hydrogen        = off white dot
    Silicon         = green/gray dot
    Flourine        = green/blue dot


Similar to the gjf file, the images can be parameterized, with their scaling. The default view is a size 10 which means the atoms have a diameter of 10.

    /chem/$NAME.png
    /chem/$NAME.png?size=20
    /chem/$NAME.svg
    /chem/$NAME.svg?size=20

The whole thing is very hackish and is just intended to allow a preview of the molecule without having to open it in Gaussian. As expected of a 2D Image, three dimensionality is poorly shown. this is especially apparent in molecules with TMS or Carbazole. This is also compounded with the fact that the fragments have a hackish transform to align them)

[/chem/7k\_TON\_7k\_7k.png](/chem/7k_TON_7k_7k.png)

![/chem/7k_TON_7k_7k.png](/chem/7k_TON_7k_7k.png)


#### Molecule JSON Data ####
If you want a simple machine readable collection of the properties of a given name you can use the molecule JSON interface. Many of the values that are returned by this are dependent on the name of the molecule and if the calculated values of the molecule are already in the database. `lumo`, `homo`, and `band_gap` will only be available for names that fit the subset of the naming scheme that the machine learning was done (single core). The `limits` values will be available if the name fits the subset of the naming scheme and if that respective direction can be polymerized (ie, no X-Groups capping expansion in that direction). `datapoint` will only be seen in structures that already have calculated values stored in the database.

[/chem/4a_TON.json](/chem/4a_TON.json)

    {
        "features": [
            [ <NAIVE FEATURE VECTOR> ],
            [ <DECAY FEATURE VECTOR> ],
        ],
        "molecule": "4a_TON",
        "lumo": -1.6922736317511982,
        "homo": -6.0272586106408301,
        "exact_name":"4aaA_TON_A_A_n1_m1_x1_y1_z1",
        "keywords": "opt B3LYP/6-31g(d)",
        "band_gap": 3.9585367995371712,
        "limits": {
            "m": [-5.7452556884445283, -2.29758310520688, 2.8838972872018624],
            "n": [-5.8333558187221861, -2.9287786769624411, 2.457959486049158]
        },
        "known_errors": null,
        "error_message": null,
        "datapoint": {
            "band_gap": 4.0578,
            "name": "4_TON_A_A",
            "energy": -798.2647132,
            "homo_orbital": 61,
            "id": 1882,
            "lumo": -1.68737791307,
            "homo": -5.99983802696,
            "exact_name": "4aaA_TON_A_A_n1_m1_x1_y1_z1",
            "dipole": 1.3283,
            "options": "td B3LYP/6-31g(d)"},
            "exact_name_spacers": "4aaA**_TON_A**_A**_n1_m1_x1_y1_z1"
        }
    }

#### Jobs ####

Jobs have a few required parameters: `name`, `email`, `cluster`, `nodes`, and `walltime`. `name` and `email` are just as they seem. The former being the name of the job/file (this can be used to setup time dependent files). The latter just being the email to send the job updates to. `cluster` corresponds to the single letter at the start of the cluster's name.

    Gordon      = g
    Blacklight  = b
    Trestles    = t
    Hooper      = h
    Carver      = c
    Localhost   = l

`nodes` is the number of nodes to use on the cluster. This value is multiplied by 16 for the clusters that require ncpu numbers instead of nodes. The final value `walltime` is the maximum amount of time, in hours, that the job should run.


When submitting jobs, it returns a bit of information to tell the state of the jobs submission. This comes in the form of a simple json object with two values. `error` and `jobid`. If `error` is not `null` then that means the job submission failed and it will display the error that occurred. Otherwise `jobid` will display the number of the job submitted.

    {
        "jobid": 123,
        "error": null,
    }


### Multi Molecule ###

The multi molecule view works much as you might expect with molecule names comma delimited. This is useful when looking at just a couple of molecules.

    /chem/$NAME1,$NAME2,$NAME3/

This method makes it simple to make a few nonrelated molecules quickly.

[/chem/24a\_TON,35b\_TNN,4g\_CCC\_4g/](/chem/24a_TON,35b_TNN,4g_CCC_4g/)

Just like with single molecules, it is possible to set the keywords to be something other than `B3LYP/6-31g(d)`.

    /chem/$NAME1,$NAME2,$NAME3/?keywords=HF/3-21G

In addition to getting all of the structures given, there is also the ability to randomly sample the structures using the `random` parameter. The following will return two random structures from the three given.

    /chem/$NAME1,$NAME2,$NAME3/?random=2


#### Brace Expansion ####

Along with comma separated names, there is also an added feature that works much like Unix brace expansion.

Example:

    $ echo test{ing,er,ed,}
    testing tester tested test
    $ echo {a,b,c}{a,b,c}
    aa ab ac ba bb bc ca cb cc

In the case of chemtools-webapp, the usage is much the same.

[/chem/24{a,b,c}\_TON/](/chem/24{a,b,c}_TON/)

[/chem/2{4,5}{a,b,c}\_TON/](/chem/2{4,5}{a,b,c}_TON/)


#### Variables ####

Along with that functionality, there are some added variables that can be accessed the same as shell variables.

Example:

    $ echo $USER
    chris
    $ echo $HOME
    /home/chris

With chemtools-webapp there are six variables each of which correspond to a set of the naming scheme.

    CORES   = "{C,T,E,Z}{O,S,N,P,C}{N,P,C}"
    SCORES   = "{E,Z}{O,S,N,P,C}{N,P,C}"
    DCORES   = "{C,T}{O,S,N,P,C}{N,P,C}"
    RGROUPS = "a,b,c,d,e,f,g,h,i,j,k,l"
    XGROUPS = "A,B,C,D,E,F,G,H,I,J,K,L"
    ARYL    = "2,3,4,5,6,7,8,9,10,11,12,13"
    ARYL0   = "2,3,8,9,10,11"
    ARYL2   = "4,5,6,7,12,13"

So, if you wanted to create all of the substituant combinations for `4X_TON`, rather than typing all the substituants out, you can just use:

[/chem/4{$RGROUPS}\_TON/](/chem/4{$RGROUPS}_TON/)

Or if you wanted all the R-groups and all the cores:

[/chem/4{$RGROUPS}\_{$CORES}/](/chem/4{$RGROUPS}_{$CORES}/)


#### Internal Variables ####

Now, that may seem well and good, except in the case where you may have multiple parts that you want the same. Like with `4X_TON_4X_4X`. In that case, there are some special variables that correspond to the number of the replacement.

[/chem/4{$RGROUPS}\_TON\_4{$0}\_4{$0}/](/chem/4{$RGROUPS}_TON_4{$0}_4{$0}/)

[/chem/{$ARYL2}{$RGROUPS}\_TON\_{$0}{$1}\_{$0}{$1}/](/chem/{$ARYL2}{$RGROUPS}_TON_{$0}{$1}_{$0}{$1}/)

Currently, there is no way to simplify the name with heavy repetitions in it. An example being something like the first one below without major changes in the grammar. That being said, this method does make it trivial to make several thousand molecules in the matter of a second or two.

    4X4X4X4X_TON_4X4X4X4X_4X4X4X4X

[/chem/{$ARYL2}{$ARYL2}{$RGROUPS}\_{$CORES}\_{$0}{$1}{$2}\_{$0}{$1}{$2}\_n{1,2,3,4}/](/chem/{$ARYL2}{$ARYL2}{$RGROUPS}_{$CORES}_{$0}{$1}{$2}_{$0}{$1}{$2}_n{1,2,3,4}/)

This case creating `4 * 4 * 12 * 8 * 4 = 6144` molecules. Due to optimizations, generating the page with all of these molecules is trivial (within a second or so), generating the zip file with all of them in it; however, is not (~5 minutes and ~100 megs of just gjf files). Because of this, there is a arbitrary timeout limit when generating molecules of 1 second. This could be optimized later to at least seem more responsive, but it is not a concern because no one is going to be dealing with more than about 100 molecules at a time. With a reasonable case as follows. Which is completed in a fraction of a second for both the generation and the download.

[/chem/4{$RGROUPS}\_TON\_4{$0}\_4{$0}\_n{1,2,3,4},4a\_{$CORES}\_4a\_4a\_n{1,2,3,4}/](/chem/4{$RGROUPS}_TON_4{$0}_4{$0}_n{1,2,3,4},4a_{$CORES}_4a_4a_n{1,2,3,4}/)

In addition to the values of the there are also 2 options that can be applied to the variables to change the case. These are added by adding a .U (for uppercase) or a .L (for lowercase) to the end of the variable number. This is useful when making matching R-Groups and X-Groups.

[/chem/4{$RGROUPS}\_TON\_4{$0}\_{$0.U}/](/chem/4{$RGROUPS}_TON_4{$0}_{$0.U}/)


#### Zip Output ####

Added with this main display page is another API type access to allow generating zip files with all the molecules of a given pattern/set. By default this will include all of the .gjf files for the molecules. The following two examples are equivalent.

    /chem/$PATTERN.zip
    /chem/$PATTERN.zip?gjf=true

In addition to being able to get gjf files this can also be used to download jobs, .mol2, and .png files of the molecules. This can be done by setting `job`, `mol2`, and `image` to `true`, respectively.

    /chem/$PATTERN.zip?mol2=true
    /chem/$PATTERN.zip?gjf=true
    /chem/$PATTERN.zip?image=true&gjf=true

Note that the job option requires the inclusion of all of the job parameters.

    /chem/$PATTERN.zip?job=true&name={{name}}&email=e@t.com&cluster=b&nodes=1&walltime=1

Any errors in the output will be written to a file called `errors.txt`.

[/chem/24{a,ball}_TON.zip](/chem/24{a,ball}_TON.zip)


#### Name Check ####

If you want to check the validity of a name or set of names you can use the name checker. The API call returns a json object with two values: `molecules` and `error`. `error` is used to keep track of problems when doing the entire set. Most time this is just a timeout error due to the query taking longer than an arbitrary limit of 1 second. The second value is a array of arrays. With each array corresponding to a molecule name. Within each one they come in the form `[name, warning, error]`. Errors are actual problems in the name, whereas warnings are user submitted problems.

[/chem/24{a,ball}_TON/check/](/chem/24{a,ball}_TON/check/)

    {
        "molecules": [
            ["24a_TON", true, null],
            ["24ball_TON", null, "no rgroups allowed at start"]
        ],
        "error": null
    }


#### Jobs ####

With multiple molecules this adds a small layer of complexity with respect to naming. This comes in the form of a generic naming variable `{{ name }}`. So for example, if you wanted to create all the time dependent job names. The following two names would be equivalent.

    {{ name }}_TD
    {{name}}_TD

Just like with single molecules, at this time there is Alpha functionality to be able submit jobs to the clusters. When the jobs are submitted a bit of json will be returned to display the status of the jobs. There are two main lists, the first being `failed`. It corresponds to the jobs that failed for some reason. Each item in the list is a list of the name of the job and the reason why it failed. The second list is a list of name and jobid pairs. The last value returned is an overall `error` value that is only non-null if the person trying to submit is not a staff user.

POST
[/chem/24{a,ball}_TON?name={{name}}&email=e@t.com&cluster=b&nodes=1&walltime=1](/chem/24{a,ball}_TON?name={{name}}&email=e@t.com&cluster=b&nodes=1&walltime=1)

    {
        "failed": [
            ["24ball_TON", "no rgroups allowed"],
            ...
            ...
        ],
        "worked" : [
            ["24a_TON", 1000],
            ...
            ...
        ],
        "error" : null,
    }


### Fragments ###

All of the fragments used in generating the molecules can be found here:

    /chem/frag/$NAME/

They use a slightly altered XYZ file format in the form of:

    Element0 x0 y0 z0
    Element1 x1 y1 z1
    ...
    ElementN xN yN zN

    Atom0 Atom1 Connection0
    Atom1 Atom2 Connection1
    ...
    AtomN-1 AtomN ConnectionN

Where x, y, and z are all floats. Element is a String from the set of all the elements plus the addition of a few special characters to signify where to bond to. Atom1 and Atom2 are both Integers corresponding to the location of the atom in the coordinate list. The connection is a string in the set `["1", "2", "3", "Ar"]`, where 1, 2, and 3 are single, double and triple bonds, respectively. Ar is an Aromatic (1.5 bond).

Here is an example of the Triple Bond.

[/chem/frag/3/](/chem/frag/3/)

    C 0.402800 -0.479100 -0.000100
    C 1.209100 0.607700 -0.000300
    ~0 2.383000 2.189800 -0.000700
    ~1 -0.747300 -2.029000 0.000300

    1 2 3
    1 4 Ar
    2 3 Ar

There are 3 added symbols in the character set for the element names and those are "~", "*", and "+". These are used to signify the type of things the element can bond to. After the set of possible things to bond to is a number that indicates the order that the bonds get used. So, in the case of the cores, the correct parts of the molecule are built in the correct order.


### Job Templates ###

Just like with the fragments, the standard job files can be found here:

    /chem/template/$NAME/

Most of the job files are just standard shell scripts with the headers required for the various clusters. The job files can be accessed by either the first letter of the cluster, or the full name (case insensitive).

[/chem/template/Gordon/](/chem/template/Gordon)


### Get User's Public Key ###

This is used mainly for getting the user's public key for use on the clusters. So instead of having to copy the file to the cluster and then append it to the authorized_keys file one can just wget and append.

    /u/$USERNAME/id_rsa.pub

    wget /u/$USERNAME/id_rsa.pub -O- >> ~/.ssh/authorized_keys


### Get Running Jobs ###

This is used to allow viewing the currently running jobs of the logged in user. It returns two values. The first is `is_authenticated` which is used internally to determine whether or not the user is logged in. The second is `clusters`, an array of clusters objects that the user has added credentials for. Each one of those objects contains 3 properties: `name`, `columns`, `jobs`. `name` is the name of the cluster. `columns` is an array of all the column names. `jobs` is a 2D array of jobs from that cluster. The first dimension is all of the jobs themselves. The second is the properties. The properties are the same as what is given by the command `qstat` on the clusters split up based on spaces.

[/chem/jobs/running.json](/chem/jobs/running.json)

    {
      "is_authenticated": true,
      "clusters": [
        {
          "jobs": [
            ["9969", "ccollins", "5b_TON_4c_6d.mjo", "59gb", "48:00:00", "--", "R"],
            ...
          ],
          "name": "Marcy",
          "columns": ["Job ID", "Username", "Jobname", "Req'd Memory", "Req'd Time", "Elap Time", "S"]
        },
        ...
      ]
    }