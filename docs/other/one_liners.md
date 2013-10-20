### Run on Supercomputer ###

make all formcheck files

    module load gaussian
    for f in `ls *.chk | sed -e 's/.chk//'`; do formchk $f.chk $f.fchk; done


get density and esp

    module load gaussian
    for file in `ls *.fchk | sed -e 's/.fchk//'`; do echo $file'_dens.cube'; cubegen 0 density $file.fchk $file'_dens.cube' 0 h; echo $file'_esp.cube'; cubegen 0 potential $file.fchk $file'_esp.cube' 0 h;  done


Submit all jobs

    for f in `ls *.job`; do qsub $f; done


Make cube files

    for f in `ls *.fchk | sed -e 's/.fchk//'`; do sh newscript $f; done


Convert all line endings to unix (remove ^M characters)

    dos2unix *.gjf


Convert all line endings to dos

    unix2dos *.log


### Run on Computer ###

convert all gjfs in current dir to TD

    for f in `ls *.gjf | sed -e 's/.gjf//'`; do sed $f.gjf -i -e 's/opt/td/' -e 's/\.chk/_TD.chk/' && mv $f.gjf $f'_TD.gjf'; done


Convert 0 charge 1 multiplicity to 1 charge 2 multiplicity assuming "_$charge" naming scheme

    for f in `ls *_0.gjf | sed -e's/_0.gjf//'`; do sed $f'_0.gjf' -e 's/0.chk/1.chk/' -e 's/^0 1/1 2/' > $f'_1.gjf' ; done


Convert 0 charge 1 multiplicity to 2 charge 1 multiplicity

    for f in `ls *_0.gjf | sed -e's/_0.gjf//'`; do sed $f'_0.gjf' -e 's/0.chk/2.chk/' -e 's/^0 1/2 1/' > $f'_2.gjf' ; done


Copy all logs to logs/

    rsync --progress -az $CG:/home/ccollins/done/*.log logs/


Copy all fchk to fchk/

    rsync --progress -az $CG:/home/ccollins/done/*.fchk fchk/


Change allocation number

    for f in `ls *.job`; do sed $f -i -e 's/CHE120042/CHE130042/'; done


Add nprocshared to gjf

    for f in `ls *.gjf`; do sed $f -i -e 's/%mem/%nprocshared=8\n%mem/'; done


Add opt

    for f in `ls *.gjf`; do sed $f -i -e 's/B3LYP/opt B3LYP/I'; done


Get all incomplete logs

    grep -L "Normal termination of Gaussian" *


Change Gordon jobs to work on Trestles (add ppn=16)

    for f in `ls *.job`; do sed $f -i -e 's/node=1^/node=1:ppn=16/'; done
