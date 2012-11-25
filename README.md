ChemTools-WebApp
================
A Django webapp built around the functionality of chemtools.


_______________________________________________________________________
Build/Run Requirements
----------------------

- Python 2.7+
- Django 1.4
- Python Imaging Library
- Scipy 0.9.0
- Numpy 1.6.1
- Paramiko 1.7.7.1
- PyCrypto 2.26
- South 0.7.6

_______________________________________________________________________
Naming Scheme
------------
There are four main classifications of the parts of the name.

### Cores ###

- CON = Cis Oxygen Nitrogen
- TON = Trans Oxygen Nitrogen
- CSN = Cis Sulfur Nitrogen
- TSN = Trans Sulfur Nitrogen
- CNN = Cis Nitrogen Nitrogen
- TNN = Trans Nitrogen Nitrogen
- CCC = Cis Carbon Carbon
- TCC = Trans Carbon Carbon


### Aryl ###

- 2 = Double Bond
- 3 = Triple Bond
- 4 = Phenyl
- 5 = Thiophene
- 6 = Pyridine
- 7 = Carbazole
- 8 = TZ
- 9 = EDOT
- [DTP]

Within Aryl there are also two minor sub classifications of Aryl groups.
#### Zero Substituent ####
2,3,8,9
#### Two Substituent ####
4,5,6,7


### X-Groups ####

- A = Hydrogen
- B = Chlorine
- C = Bromine
- D = CN
- E = CCH
- F = OH
- G = SH
- H = NH_2
- I = CH_3
- J = Phenyl
- K = TMS
- L = OCH_3


### R-Groups ####

- a = Hydrogen
- b = Chlorine
- c = Bromine
- d = CN
- e = CCH
- f = OH
- g = SH
- h = NH_2
- i = CH_3
- j = Phenyl
- k = TMS
- l = OCH_3


From there the name takes a form similar to this:

    24a_TON_35b_24c

The left part (24a in this case) corresponds to the left side of the cruciform. The next part is the core. The next part goes with the two vertical parts. In an edge case this segment can be substituted to being just an X-group and added to the beginning of the last part.

    24a_TON_B24a

The last part of the name is the right side of the molecule. Beyond the slight option for the middle, there is also the ability to leave off any of the sides and they will be assumed to be just a hydrogen.

    TON_24a_24a
    24a_TON_24a
    24a_TON

Added to the naming scheme are two types of expansion. They are polymer type and stacking type. The former is a direct linking of the parts of the molecule. The latter is, basically, just a copy and paste along the respective axis. In the case of polymer type expansion, one can not have both an "n" (along the horizontal axis) and "m" (along the vertical) expansion due to conflicts in the connection points.

    4a_TON_n2
    4a_TON_B24c_n3
    4a_TON_35_2_m3


For some fun with the naming:

    4a_TON_5555555555_4a
    5_TON_n13

Any errors in the naming scheme will be denoted on the respective molecules page. The error reporting is currently very primitive, but it gives an idea of the problem. If there are errors in the molecule, or if the molecule gives an error when it should work, feel free to submit an error report by clicking the "Report Me" button seen on all of the molecule pages. This button is also listed for each molecule on the multi molecule pages.


The formal grammar definition is roughly as follows:

    digit       = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
    int         = digit, { digit } ;

    core        = "CON" | "TON" | "CSN" | "TSN" | "CNN" | "TNN" | "CCC" | "TCC" ;
    aryl0       = "2" | "3" | "8" | "9" ;
    aryl2       = "4" | "5" | "6" | "7" ;
    aryl        = aryl0 | aryl2 ;
    xgroup      = "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J" | "K" | "L" ;
    rgroup      = "a" | "b" | "c" | "d" | "e" | "f" | "g" | "h" | "i" | "j" | "k" | "l" ;
    full        = aryl2, [rgroup], [rgroup]
    end         = [aryl0, {aryl0}], [full, {full}], [xgroup]
    end2        = "_", end

    extend      = ("n" | "m"), int ;
    stack       = ("x" | "y" | "z"), int ;

    molecule    = [end2], core, ([end2], [end2] | ["_", xgroup, end]), ["_", extend], ["_", stack] {"_", stack}


_______________________________________________________________________
Functionality
-------------

### Molecules ###

All of the following forms of output are possible for all of the molecules generated.

- gjf - a standard Gaussian Cartesian connectivity molecule file
- mol2 - a standard Cartesian-style molecule file format
- png - this is just a very rough rendering of the structure of the molecule.
- Job - there also is a job form on each molecule page that will allow generation of job files for any of the supercomputers given a few parameters.


### Jobs ###
#### Generating Job Files ####

Job files can be made on the respective molecule pages using the Job Form. The job form allows simple replacement for the mechanical task of making new job files for each molecule.

Added with just being able to view the job file there is Alpha functionality to be able to directly upload both jobs and molecules to a supercomputer (just Gordon for now) and run the respective job.


#### Show Currently Running Jobs ####

If you are logged in, and have set up your ssh keys, then under the Jobs page you can see your currently running jobs on Gordon. Along with seeing the currently running jobs, there are also buttons there to allow you to kill running jobs.


### Upload ###
#### Log Parse ####

This takes normal Gaussian log files and will output a text file comma delimited with the values needed from the file (filename, homo, lumo, gap, time taken).


#### Data Parse ####

This takes a file formated like this:

    # 1/n values
    0.09091, 0.04545, 0.0303, 0.02273
    # homo values
    -5.54384, -5.41377, -5.37377, -5.3686
    # lumo values
    -2.17367, -2.45232, -2.55599, -2.59491
    # gap values
    3.1548, 2.61, 2.4482, 2.3972

Where lines starting with "#" are comments. The n values can be given as either n or 1/n. This will return a zipped file with a text file listing the fit parameters as well as two graphs plotting the HOMO/LUMO and the Gap values.


#### Gjf Reset ####

This takes a log file (assumed to be correct) and returns a gjf file with the extracted geometry. This is intended to be used to extract the optimized geometry from the DFT log files to then use as the TDDFT gjf file. WARNING will not work in some cases where the job stopped part way through writing.


#### Homo Orbital ####

This takes multiple log files and returns a page with a list of filenames and the respective Highest occupied molecular orbital number for use in generating HOMO and LUMO cube files. The LUMO will be the value given plus one.


### Users ###
#### Account ####

Chemtools-Webapp has a very simplified view of user accounts. They are mainly used as a shell to persistantly store information like emails and usernames for submitting jobs on the supercomputers. As well as the needed ssh keys.

Registering an account is much like any other site. An email server is not set up yet so it does not do email verification, but that is more of a formality anyways. After registering, click the activation key link to active your account. From there, it is a matter of setting up your directory structure. SSH into all of the different supercomputers and run the following command.

    $ mkdir chemtools chemtools/done

After your directories on the supercomputer are setup, then you need to setup your SSH Keys.


#### SSH Keys ####

SSH keys can be generated for direct access to the supercomputers, or you can provide your own. The ones being used are generated by PyCrypto and are 2048 bit keys.

For the initial setup of the SSH keys, it does require a little bit of foot work. Which amounts to SSH-ing into the supercomputer of choice and running the following command, where <username> is your username.

    $ wget /account/public/<username>/ -O- >> ~/.ssh/authorized_keys

After this key is added nothing else will have to be done.

_______________________________________________________________________
API
---

Right now, the API is very minimal, the current access is just enough to give the basic functionality to the entire site. These features include: dynamic generation of .gjf, .mol, and .png files for any molecule given the name.


### Molecule Specific ###

For all of the molecules there is a basic API access to allow getting the different types of outputs. The first, and most common, being the gjf output. This is the standard gaussian file type and is what should be used for running the calculations. There is also an added possible parameter called "basis" that can be added to add/change the basis/settings of the molecule. If none is given, then "B3LYP/6-31g(d)" is assumed.

    /chem/<NAME>.gjf
    /chem/<NAME>.gjf?basis=B3LYP/6-31g(d)

The next form of output is the mol2 format. This is added because it is a fairly simple interchange format for different software packages.

    /chem/<NAME>.mol2

The last molecule specific access is the png image. It is a very basis rendering over the overall structure of the molecule.

    Single Bond     = single white line
    Aromatic Bond   = single red line
    Double Bond     = single green line
    Triple Bond     = single blue line

    Sulfur          = yellow dot
    Oxygen          = red dot
    Nitrogen        = blue dot
    Chlorine        = green dot
    Carbon          = medium grey dot
    Hydrogen        = off white dot
    Silicon         = green/grey dot

Similar to the gjf file, the images can be parameterized, with their scaling. The default view is a size 10 which means the atoms have a diameter of 10.

    /chem/<NAME>.png
    /chem/<NAME>.png?size=20

The whole thing is very hackish and is just intended to allow a preview of the molecule without having to open it in gaussian. As expected of a 2D Image, Three demensionality is poorly shown. this is especiially apparent in molecules with TMS and Carbazole. (also compounded with the fact that the fragments have a hackish transform to align them)

    /chem/7k_TON_7k_7k.png


### Multi Molecule ###

The multi molecule view works much as you might expect with molecule names comma delimited. This is useful when looking at just a couple of molecules.

    /chem/<NAME1>,<NAME2>,<NAME3>/

Along with comma separated names, there is also an added feature that works much like Unix brace expansion.

Example:

    $ echo test{ing,er,ed,}
    testing tester tested test
    $ echo {a,b,c}{a,b,c}
    aa ab ac ba bb bc ca cb cc

In the case of chemtools-webapp, the usage is much the same.

    /chem/24{a,b,c}_TON/
    # lots of stuff
    /chem/2{4,5}{a,b,c}_TON/
    # lots of stuff

Along with that functionality, there are some added variables that can be accessed the same as shell variables.

Example:

    $ echo $USER
    chris
    $ echo $HOME
    /home/chris

With chemtools-webapp there are six variables each of which correspond to a set of the naming scheme.

- "CORES"   = "CON,TON,CSN,TSN,CNN,TNN,CCC,TCC"
- "RGROUPS" = "a,b,c,d,e,f,g,h,i,j,k,l"
- "XGROUPS" = "A,B,C,D,E,F,G,H,I,J,K,L"
- "ARYL"    = "2,3,4,5,6,7,8,9"
- "ARYL0"   = "2,3,8,9"
- "ARYL2"   = "4,5,6,7"

So, if you wanted to create all of the substituant combinations for 4X_TON, rather than typing all the substituants out, you can just use:

    /chem/4{$RGROUPS}_TON/

    /chem/4{$RGROUPS}_{$CORES}/

Now, that may seem well and good, except in the case where you may have multiple parts that you want the same. Like with 4X_TON_4X_4X. In that case, there are some special variables that correspond to the number of the replacement.

    /chem/4{$RGROUPS}_TON_4{$0}_4{$0}/

    /chem/{$ARYL2}{$RGROUPS}_TON_{$0}{$1}_{$0}{$1}/

Currently, there is no way to simplify the name with heavy repetitions in it. An example being something like the first one below without major changes in the grammar. That being said, this method does make it trivial to make several thousand molecules in the matter of a second or two.

    4X4X4X4X_TON_4X4X4X4X_4X4X4X4X

    /chem/{$ARYL2}{$ARYL2}{$RGROUPS}_{$CORES}_{$0}{$1}{$2}_{$0}{$1}{$2}_n{1,2,3,4}/

This case creating 4 * 4 * 12 * 8 * 4 = 6144 molecules. Due to optimizations, generating the page with all of these molecules is trivial (within a second or so), generating the zip file with all of them in it; however, is not (~5 minutes and ~100 megs of just gjf files). This could be optimized later to at least seem more responsive, but it is not a concern because no one is going to be dealing with more than about 100 molecules at a time. With a reasonable case as follows. Which is completed in a fraction of a second for both the generation and the download.

    /chem/4{$RGROUPS}_TON_4{$0}_4{$0}_n{1,2,3,4},4a_{$CORES}_4a_4a_n{1,2,3,4}/

Added with this main display page is another API type access to allow generating zip files with all the molecules of a given pattern/set.

    /chem/<pattern>.zip


### Generate SSH Key Pair ###
This will return json with with two values. The public key is in the OpenSSH format.

    /account/genkey/

    {
        "public": "ssh-rsa ... chemtools-webapp",

        "private": "-----BEGIN RSA PRIVATE KEY-----
        ...
        ...
        -----END RSA PRIVATE KEY-----"
    }

If the caller is logged in then it will return a public key with <username>@chemtools-webapp.


### Get User's Public Key ###
This is used mainly for getting the user's public key for use on the supercomputers. So instead of having to copy the file to the supercomputer and then append it to the authorized_keys file one can just wget and append.

    /account/public/<username>/

    wget /account/public/<username>/ -O- >> ~/.ssh/authorized_keys