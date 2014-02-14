## Troubleshooting Steps ##

1. Check the end of the log file (`tail $FILENAME.log`)
2. Check the $FILENAME.err and $FILENAME.out files (`cat $FILENAME.{out,err}`)
3. Check your email for emails from XSEDE if there are any problems going on with the supercomputer (you might have to check over the course of a few hours).
4. Check your gjf and job files for obvious errors.
    1. Wrong names or paths used in either file
    2. Wrong options used in gjf file
        1. Incorrect path for `%chk` option
        2. Wrong charge/spin specifications
        3. Bad pairings of job options (`td` and `opt`, multiple bases or functionals)
5. Try rerunning the job (This sometimes fixes random errors).
6. If there is a still a problem, triple check all the files involved ($FILENAME.log, $FILENAME.gjf, $FILENAME.err, $FILENAME.job, $FILENAME.out) and look for anything that seems odd.
7. If all else fails, try restarting from the begining (rebuild the molecule, job, etc)

___________________________________________________________


## Errors ##
### Error ###

    qsub: submit filter returned an error code, aborting job submission.
      Running job as user dlwhee93
    Your job will not run
      Invalid project-account number 'ios103' for queue 'normal', valid accounts for user 'dlwhee93' are:
        ung100 on SDSC XSEDE Gordon: all queues (STGGORD)

#### Problem ####

This means that one of two things has happened.
1. Your user account is not on the allocation you put in the job file.
2. All the hours on the allocation you put in the job file have been used up.

#### Fix #####
1. Request to get added to the allocation.
2. Use another allocation that has not been used up.

___________________________________________________________

### Error ###

When submitting a job the following error is returned.

    -l nodes=...:ppn=<procs per node>:... is required
    qsub: submit filter returned an error code, aborting job submission.

#### Problem ####

Sometimes the job files require an added `ppn=16` on with the nodes specification (mainly just Trestles).

#### Fix #####
This problem can be fixed by adding that option to the job file. This can either be done with a text editor, or with `sed`.

    sed -i $JOBFILE -e s/nodes=1/nodes=1:ppn=16/'

___________________________________________________________


### Error ###

he supercomputer sent an email with a status code that

    which: no g09 in (/opt/gaussian/g09:/opt/gnu/bin:/opt/gnu/gcc/bin:/opt/mvapich2/intel/ib/bin:/opt/intel/composer_xe_2013.1.117/bin/intel64:/usr/lib64/qt-3.3/bin:/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/usr/java/latest/bin:/opt/maui/bin:/opt/torque/bin:/opt/torque/sbin:/opt/torque/bin:/opt/torque/sbin:/state/partition1/catalina/bin:/opt/pdsh/bin:/opt/rocks/bin:/opt/rocks/sbin:/home/servers/gordon/bin:/home/dlwhee93/bin:/opt/maui/bin:/opt/torque/bin:/opt/torque/sbin:/opt/torque/bin:/opt/torque/sbin:/state/partition1/catalina/bin:/home/servers/gordon/bin:/home/dlwhee93/bin)

#### Problem ####

Gaussian requires that you accept their terms of service before you will be able to use their software, so for each of the supercomputers you will need to accept their terms of service. Without accepting the terms of service the Gaussian module will not load.

#### Fix ####

You will need to fill out the required forms for that supercomputer to get access. For example, [here](http://www.psc.edu/index.php/gaussian/598) is the link for the Blacklight form.

___________________________________________________________


### Error ###

    %chk=C:\Users\research\Documents\My SugarSync\gjfs\oct_010_2.chk
    ntrex1

#### Problem ####

The `%chk` specification in the gjf is not correct. The path that is specified there must correspond to a path on the supercomputer (in most cases this should just be the name of the file without any folders).

#### Fix ####

Change the `%chk` to be a proper path (remove the `C:\Users\...` part and leave the $FILENAME.chk part)

___________________________________________________________


### Error ###

    Post job file processing error; job 1590474.trestles-fe1.sdsc.edu on host trestles-9-10/15+trestles-9-10/14+trestles-9-10/13+trestles-9-10/12+trestles-9-10/11+trestles-9-10/10+trestles-9-10/9+trestles-9-10/8+trestles-9-10/7+trestles-9-10/6+trestles-9-10/5+trestles-9-10/4+trestles-9-10/3+trestles-9-10/2+trestles-9-10/1+trestles-9-10/0Unknown resource type  REJHOST=trestles-9-10.local MSG=invalid home directory '/home/ccollins' specified, errno=2 (No such file or directory)

#### Problem ####

Generally, this happens when there is a problem with the supercomputer. In this specific case, the File system on Trestles went bad and there was an email sent out from XSEDE within a few hours saying that there was a problem.

This problem can also be caused by a bad job file.

#### Fix ####

Wait and see if XSEDE sends out an email saying that the supercomputer has been fixed. Or if it is the other problem, then check and make sure all the paths/filenames are correct in the job file.

___________________________________________________________


### Error ###

    galloc:  could not allocate memory.

#### Problem ####

The supercomputer was unable to allocate memory for your current job.

#### Fix ####

There are two possible fixes for this problem:
1. Try rerunning the job (this might have to be done multiple times). It seems that sometimes the supercomputer is just unable to allocate memory. This problem can seem to pop up at random.
2. Try lowering the `%mem` option in the gjf file to a lower number.

___________________________________________________________


### Error ###

Empty log file

#### Problem ####

This means that the job had an error before the execution of Gaussian. To get an exact answer to what the problem is you will have to check your email about the job, the `$FILENAME.err` file, and the `$FILENAME.out` file. In one of those places it should give you a clue to where the problem might be.

#### Fix ####

Fixes for these kind of problems will be completely dependent on what is seen in your email, the `$FILENAME.err` file, or the `$FILENAME.out` file.

___________________________________________________________


### Error ###

    Aborted by PBS Server
    Job exceeded its walltime limit. Job was aborted
    See Administrator for help

-

    Initial convergence to 1.0D-05 achieved.  Increase integral accuracy.

-

    Integral accuracy reduced to 1.0D-05 until final iterations.

-

    Calling FoFJK, ICntrl=      2127 FMM=T ISym2X=0 I1Cent= 0 IOpClX= 0 NMat=1 NMatS=1 NMatT=0.

-

    No special actions if energy rises.

#### Problem ####

These sorts of messages are symptomatic of a calculation getting cut off part way through (e.g. reaching the walltime). You will notice that all of these "errors" can be seen inside of a normal log file. This implies that the calculation was cut off while running.

This can also be confirmed by checking your email for for the walltime error message.

#### Fix ####

Move the incomplete log files back to your computer from the supercomputer and load them in Gaussian. Then from there save them as new gjfs and resubmit those on the supercomputer.

___________________________________________________________


### Error ###

    Error termination via Lnk1e in /opt/gaussian/g09/l401.exe

#### Problem ####

If you make the gjf files on windows there is a chance that windows will tack on the windows line endings instead of the ones that are required for unix/linux. This is just a problem of convention differences in the two operating systems. You can see if this is actually the problem if you open one of the gjf files in `vim` on the supercomputer. If the lines end with a `^M` then they will have this problem.

#### Fix ####

Run the dos2unix utility to fix all the line endings.

    dos2unix $FILENAME

___________________________________________________________


### Error ###

    End of file in ZSymb.
    Error termination via Lnk1e in /home/diag/opt/gaussian/g09/l101.exe

#### Problem ####

Gaussian requires that all the gjf files end with a single blank line for whatever reason. If this condition is not met then it will return this error in the log file.

#### Fix ####

Add a newline to the end of the file.

___________________________________________________________


### Error ###

    Route card not found.
    Error termination via Lnk1e in /usr/local/Dist/g09/l1.exe at Thu Dec 19 17:38:29 2013.

#### Problem ####

Gaussian requires that all job files have the route card information line (the line with the #). If that line is not there then it will return an error.

#### Fix ####

Add the route card line with the proper parameters.

___________________________________________________________


### Error ###

    Error termination request processed by link 9999.
    Error termination via Lnk1e in /global/apps/gaussian/g03.e01/g03/l9999.exe

### Problem ###

When running Gaussian, there are two kinds of ways the job can run for too long. The first is a walltime, the second is when Gaussian reaches the max number of iterations. This is the latter case.

### Fix ###

Just like with a walltime error, move the incomplete log files back to your computer from the supercomputer and load them in Gaussian. Then from there save them as new gjfs and resubmit those on the supercomputer.

___________________________________________________________
