#!/bin/bash
if [[ ! -z $LCG_RELEASE ]]; then
    :
else
    export LCG_RELEASE=95
fi

if uname -a | grep ekpdeepthought -q
then
    if [[ -f /cvmfs/sft.cern.ch/lcg/views/LCG_${LCG_RELEASE}/x86_64-ubuntu1604-gcc54-opt/setup.sh ]]; then
        source /cvmfs/sft.cern.ch/lcg/views/LCG_${LCG_RELEASE}/x86_64-ubuntu1604-gcc54-opt/setup.sh
    else
        source /cvmfs/sft.cern.ch/lcg/views/LCG_95a/x86_64-ubuntu1604-gcc54-opt/setup.sh
    fi
elif uname -a | grep -E 'el7' -q
then
    source /cvmfs/sft.cern.ch/lcg/views/LCG_${LCG_RELEASE}/x86_64-centos7-gcc8-dbg/setup.sh
else
    source /cvmfs/sft.cern.ch/lcg/views/LCG_${LCG_RELEASE}/x86_64-slc6-gcc8-dbg/setup.sh
fi

export PYTHONPATH=$PYTHONPATH:$PWD/shape-producer
export PYTHONPATH=$PYTHONPATH:$PWD/Dumbledraw
