#!/bin/bash

source setup_lcg.sh

python plot.py -i shapes.root --variables "m_vis" --channels "mt"
