#!/usr/bin/env python3.7.4

try:
    import UsrIntel.R1 # Intel specific import to get the standard libraries
except:
    pass

import sys
from sim_seed import sim_seed
import itertools
import markov2p
import mpmath
from  mpmath import mpf
import shlex
import subprocess
from subprocess import PIPE

mpmath.dp = 1024

seed = "a_seed_for_this_test_part3"
seed_index = 0
iterations = 200
#iterations = 3

entropy_divisions = 40
bitwidth = 512 # Length of input width to conditioner

print_case_info = False

# List to return a test name from and index
test_name_list =[ "Most Common Value Estimate",
               "Collision Test Estimate",
               "Markov Test Estimate",
               "tCompression Test Estimate",
               "T-Tuple Test Estimate",
               "LRS Test Estimate",
               "Multi Most Common in Window (MultiMCW) Prediction Test Estimate",
               "Lag Prediction Test Estimate",
               "Multi Markov Model with Counting (MultiMMC) Prediction Test Estimate",
               "LZ78Y Prediction Test Estimate"]

# Dict to return an index from a test name
test_name_dict = dict()
for i,name in enumerate(test_name_list):
    test_name_dict[name]=i

def unwrap_case(case):
    entropy, iteration = case
    case_seed = sim_seed(seed+str(entropy), iteration)
    point = markov2p.pick_point(entropy,2.0**-10,bitwidth,case_seed,quiet=True)
    bias,scc = markov2p.p_2_biasscc(point)
    (p01,p10) = point
    return case_seed, iteration, entropy, p01, p10, bias, scc

# Entropy points from 0 to 1, 1000 divisions
entropy_levels = [float(x)/entropy_divisions for x in range(1,entropy_divisions)]

# At each entropy level, get a number of markov points.
# Compute the mean,scc for those points
iterations = range(1,iterations+1)

# Make all the test cases with a cartesian product rather than a deeply nested loop
caselist = list()
cases = itertools.product(entropy_levels, iterations)
if print_case_info:
    print("case_seed, iteration, entropy, p01, p10, bias, scc")
for case in cases:
    entropy, iteration = case
    case_seed, iteration, entropy, p01, p10, bias, scc = unwrap_case(case)
    caselist.append((case_seed, iteration, entropy, p01, p10, bias, scc))
    if print_case_info:
        print("%s, %d, %f, %f, %f, %f, %f" % (case_seed,iteration,entropy,p01,p10,bias,scc))

# Run the tests
# ea output : H_original: 0.326133

print("case_seed, iteration, entropy, p01, p10, bias, scc, noxor_h_orig, err, percent_err, alg_idx, algorithm")
for case in caselist:
    case_seed, iteration, entropy, p01, p10, bias, scc = case
    ea_non_iid_noxor_command = "ea_non_iid -i -v -t -l 0,1000000 entropyfile.nob 1"
    djenrandom_noxor_command = "djenrandom -m markov_2_param --entropy=%f --detseed=%s -b -k 125 --bpb=1 -o entropyfile.nob" % (entropy, case_seed)
    subprocess.run(shlex.split(djenrandom_noxor_command))

    #noxor_process = subprocess.run(shlex.split(ea_non_iid_noxor_command),text=True,capture_output=True)
    noxor_process = subprocess.run(ea_non_iid_noxor_command,encoding='UTF-8',shell=True,capture_output=True)
    blamed_list=list()
    for line in noxor_process.stdout.split('\n'):
        x =str(line)
        #print("HIT ",x[-10:])
        if x[-10:] == "/ 1 bit(s)":
            y = x.split()
            entstr = y[-4]
            blamed_alg = " ".join(y[0:-5])
            blamed_list.append((entstr,blamed_alg))

        if str(line)[:11] == "H_original:":
            noxor_h = float(line[11:])
            noxor_h_str = line[11:]
            #print("NOXOR_H_STR")
            #print(noxor_h_str)
            #print("BLAMED_LIST")
            #print(blamed_list)
            #print()

    for (entstr,blamed_alg) in blamed_list:
        #print("BLAMED LIST SEARCH")
        #print("  ",entstr ,"  == ",noxor_h_str,"?")
        if noxor_h_str.strip() == entstr.strip():
            actual_blamed_alg = blamed_alg
            #print("  YES")
            actual_blamed_alg_idx = test_name_dict[actual_blamed_alg]

    error_percentage = float(noxor_h)/(float(entropy)/100.0)
    error_dist = 100.0 - error_percentage
    abs_dist = float(noxor_h)-(float(entropy))
    print("%s, %d, %f, %f, %f, %f, %f, %f, %f, %f, %d, %s" % (case_seed,iteration,entropy,p01,p10,bias,scc, noxor_h, abs_dist, error_dist, actual_blamed_alg_idx, actual_blamed_alg))
    sys.stdout.flush() 
    
