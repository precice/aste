#!/bin/sh
# set -e
BASE=$PWD
cd $BASE
# ---------------------------------------- PARAMETERS --------------------------------------------------------
# 1d tube parameters
N=1000
PROCS=4


# coupling parameters
PPNAME=s-iqn-ils
CP=serial-implicit
PP=IQN-ILS
PRECOND=residual-sum

EXTRAPOLATION=2
REUSED=0

FILTER=QR1
EPS=1e-13

COPY=1

NOW="$(date +'%Y-%m-%d')"

# ------------------------------------------------------------------------------------------------------------
DESCRIPTION=${PPNAME}_N-${N}_p-${PROCS}
#D1=experiments/${PPNAME}/${NOW}_FSI-${N}-${NCOARSE}
D1=experiments/${PPNAME}
DEST_DIR=${D1}/aste_N-${N}
# ------------------------------------------------------------------------------------------------------------


if [ ${CP} = "serial-implicit" ]; then
    cp precice_cpl_S.xml precice_cpl.xml 
else
    cp precice_cpl_V.xml precice_cpl.xml 
fi

FILE=precice_cpl.xml


sed -i s/timesteps-reused\ value=\"[0-9]*\"/timesteps-reused\ value=\"${REUSED}\"/g ${FILE}                # set reuse
sed -i s/extrapolation-order\ value=\"[0-9]*\"/extrapolation-order\ value=\"${EXTRAPOLATION}\"/g ${FILE}   # set extrapolation order
#sed -i s/post-processing:[A-Za-z-]*/post-processing:${PP}/g ${FILE}                                       # set post processing method
sed -i s/coupling-scheme:[A-Za-z-]*/coupling-scheme:${CP}/g ${FILE}                                        # set coupling scheme
#sed -i s/filter\ type=\"[A-Z0-9a-z-]*\"\ limit=\"[0-9e]*\"/filter\ type=\"${FILTER}\"\ limit=\"${EPS}\"/g ${FILE}   # set filter method

echo "Start Simulation run"



for N in 1000 10000
do
    D1=experiments/${PPNAME}
    DEST_DIR=${D1}/aste_N-${N}
    if [ ${COPY} = 1 ]; then
	if [ ! -d ${D1} ]; then
            mkdir ${D1}
	fi
	if [ ! -d ${DEST_DIR} ]; then
            mkdir ${DEST_DIR}
	fi

	cp ${FILE} ${DEST_DIR}/${FILE}
    fi

    for PROCS in 4 8 16 24
    do
	DESCRIPTION=${PPNAME}_N-${N}_p-${PROCS}
        echo "\n ############################### \n"
        echo " run ASTE N="${N}" on p="${PROCS}" processors"
        echo " coupling-scheme: "${CP}
        echo " post-processing: "${PP}
        echo " reuse="${REUSED}
	echo " "${DESCRIPTION}
        echo "\n ###############################"

	mpirun -np ${PROCS} ./aste -x ${FILE} -p A --mesh MeshA --x ${N} --y ${N} --nx ${N} --ny ${N} > log.A 2>&1 &
	mpirun -np ${PROCS} ./aste -x ${FILE} -p B --mesh MeshB --x ${N} --y ${N} --nx ${N} --ny ${N} > log.B 2>&1 

        if [ ${COPY} = 1 ]; then
            cp EventTimings.log ${DEST_DIR}/eventTimings_${DESCRIPTION}.log
	    cp log.A ${DEST_DIR}/log.A_${DESCRIPTION}
	    cp log.B ${DEST_DIR}/log.B_${DESCRIPTION}
        fi
    done
done
