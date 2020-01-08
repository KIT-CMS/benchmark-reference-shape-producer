#!/bin/bash

KAPPA_DATABASE=datasets/datasets.json

basedir="/ceph/htautau/deeptau"
ARTUS_OUTPUTS="$basedir/2017/ntuples/"
SVFit_Friends="$basedir/2017/friends/SVFit/"
MELA_Friends="$basedir/2017/friends/MELA/"
FF_Friends="$basedir/2017/friends/FakeFactors/"

ARTUS_FRIENDS_EM="$NNScore_Friends $SVFit_Friends $MELA_Friends"
ARTUS_FRIENDS_ET="$NNScore_Friends $SVFit_Friends $MELA_Friends"
ARTUS_FRIENDS_MT="$NNScore_Friends $SVFit_Friends $MELA_Friends"
ARTUS_FRIENDS_TT="$NNScore_Friends $SVFit_Friends $MELA_Friends"
ARTUS_FRIENDS_FAKE_FACTOR=$FF_Friends

source setup_lcg.sh

python shapes.py \
    --directory $ARTUS_OUTPUTS \
    --et-friend-directory $ARTUS_FRIENDS_ET \
    --em-friend-directory $ARTUS_FRIENDS_EM \
    --mt-friend-directory $ARTUS_FRIENDS_MT \
    --tt-friend-directory $ARTUS_FRIENDS_TT \
    --fake-factor-friend-directory $ARTUS_FRIENDS_FAKE_FACTOR \
    --datasets $KAPPA_DATABASE \
    --binning binning.yaml \
    --tag "reference" \
    --channels "mt" \
    --era 2017 \
    --num-threads 8
