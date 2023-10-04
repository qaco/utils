#! /usr/bin/python3

import subprocess
import sys
import argparse

KILO=1000
MEGA=1000000
GIGA=1000000000

parser = argparse.ArgumentParser(prog=sys.argv[0], description="Compute FLOPS")
parser.add_argument(
    'command', metavar='CMD', help='The command we reason on.'
)
parser.add_argument(
    "--verbose", action="store_true", help="Print details.",
)
args = parser.parse_args()

COUNTERS = [
    "cpu-cycles",
    "fp_arith_inst_retired.scalar_single",
    "fp_arith_inst_retired.128b_packed_single",
    "fp_arith_inst_retired.256b_packed_single",
    "fp_arith_inst_retired.512b_packed_single"
]

LSCPU_CMD = ["lscpu"]
PERF_CMD = ["perf","stat","-e",','.join(COUNTERS),args.command]

def extract_float(line,target,default,verbose):
    line = line.replace('\n', '')
    line = " ".join(line.split())
    if target in line:
        if verbose:
            print(line)
        line = line.replace(target,'')
        line = line.replace(' ','')
        line = line.encode('ascii', 'ignore')
        return float(line)
    else:
        return default

if args.verbose:
    print(' '.join(LSCPU_CMD))
    
lscpu = subprocess.run(LSCPU_CMD, capture_output=True, text=True)
num_cores = None
freq_hz = None
for l in lscpu.stdout.splitlines():
    if "Processeur(s)" in l:
        num_cores = float(l.split(':')[1])
    if "Vitesse maximale" in l:
        freq_mhz = float(l.split(':')[1].replace(' ','').replace(',','.'))
        freq_hz = freq_mhz * 1000000

assert(num_cores is not None)
assert(freq_hz is not None)

if args.verbose:
    print(' '.join(PERF_CMD))
    
perf = subprocess.run(PERF_CMD,capture_output=True,text=True)
cpu_cycles = None
nflop = 0
for l in perf.stderr.splitlines():
    cpu_cycles = extract_float(
        line=l,target=COUNTERS[0],default=cpu_cycles,verbose=args.verbose
    )
    for c in COUNTERS[1:]:
        nflop += extract_float(
            line=l,target=c,default=0,verbose=args.verbose
        )

assert(cpu_cycles is not None)
assert(nflop > 0)
        
flops = num_cores * freq_hz * (nflop/cpu_cycles)

if flops > GIGA:
    rflops = flops/GIGA
    units = "g"
elif flops > MEGA:
    rflops = flops/MEGA
    units = "m"
elif flops > KILO:
    rflops = flops/KILO
    units = "k"
else:
    rflops = flops
    units = ""
    
print(f"{rflops} {units}flops")

    
