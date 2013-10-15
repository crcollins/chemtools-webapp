#### Error ####

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



#### Error ####
When submitting a job the following error is returned.

    -l nodes=...:ppn=<procs per node>:... is required
    qsub: submit filter returned an error code, aborting job submission.

#### Problem ####

Sometimes the job files require an added `ppn=16` on with the nodes specification (mainly just Trestles).

#### Fix #####
This problem can be fixed by adding that option to the job file. This can either be done with a text editor, or with `sed`.

    sed -i $JOBFILE -e s/nodes=1/nodes=1:ppn=16/'



#### Error ####
The supercomputer sent an email with a status code that

    which: no g09 in (/opt/gaussian/g09:/opt/gnu/bin:/opt/gnu/gcc/bin:/opt/mvapich2/intel/ib/bin:/opt/intel/composer_xe_2013.1.117/bin/intel64:/usr/lib64/qt-3.3/bin:/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/usr/java/latest/bin:/opt/maui/bin:/opt/torque/bin:/opt/torque/sbin:/opt/torque/bin:/opt/torque/sbin:/state/partition1/catalina/bin:/opt/pdsh/bin:/opt/rocks/bin:/opt/rocks/sbin:/home/servers/gordon/bin:/home/dlwhee93/bin:/opt/maui/bin:/opt/torque/bin:/opt/torque/sbin:/opt/torque/bin:/opt/torque/sbin:/state/partition1/catalina/bin:/home/servers/gordon/bin:/home/dlwhee93/bin)

#### Problem ####

Gaussian requires that you accept their terms of service before you will be able to use their software, so for each of the supercomputers you will need to accept their terms of service. Without accepting the terms of service the gaussian module will not load.

#### Fix ####

You will need to fill out the required forms for that supercomputer to get access. For example, [here](http://www.psc.edu/index.php/gaussian/598) is the link for the Blacklight form.



#### Error ####

    %chk=C:\Users\research\Documents\My SugarSync\gjfs\oct_010_2.chk
    ntrex1



#### Error ####

    Post job file processing error; job 1590474.trestles-fe1.sdsc.edu on host trestles-9-10/15+trestles-9-10/14+trestles-9-10/13+trestles-9-10/12+trestles-9-10/11+trestles-9-10/10+trestles-9-10/9+trestles-9-10/8+trestles-9-10/7+trestles-9-10/6+trestles-9-10/5+trestles-9-10/4+trestles-9-10/3+trestles-9-10/2+trestles-9-10/1+trestles-9-10/0Unknown resource type  REJHOST=trestles-9-10.local MSG=invalid home directory '/home/ccollins' specified, errno=2 (No such file or directory)



#### Error ####

    galloc:  could not allocate memory.



#### Error ####

Empty log file



#### Error ####

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

Move the incomplete log files back to your computer from the supercomputer and load them in gaussian. Then from there save them as new gjfs and resubmit those on the supercomputer.


#### Error ####

    Error termination via Lnk1e in /opt/gaussian/g09/l401.exe

#### Fix ####

Run the dos2unix utility to fix all the line endings.

    dos2unix $FILENAME



#### Error ####

    End of file in ZSymb.
    Error termination via Lnk1e in /home/diag/opt/gaussian/g09/l101.exe

#### Fix ####

Add a newline to the end of the file.

