#!/usr/bin/env python

import subprocess
import sys
import os

# search +/- 10% around the chosen intial threshold with combinations of 0-12 pixel hard and soft mask edges

#-----------------------------------------------------------------------------------#
errormsg = "USAGE: rln_opt_pt_mask.py --i <refine 3D final run_class01.mrc> --inithres <n>"

class Arg(object):
    _registry = []
    def __init__(self, flag, value, req):
        self._registry.append(self)
        self.flag = flag
        self.value = value
        self.req = req

def make_arg(flag, value, req):
    Argument = Arg(flag, value, req)
    if Argument.req == True:
        if Argument.flag not in sys.argv:
            print(errormsg)
            sys.exit("ERROR: required argument '{0}' is missing".format(Argument.flag))
    if Argument.value == True:
        try:
            test = sys.argv[sys.argv.index(Argument.flag)+1]
        except ValueError:
            if Argument.req == True:
                print(errormsg)
                sys.exit("ERROR: required argument '{0}' is missing".format(Argument.flag))
            elif Argument.req == False:
                return False
        except IndexError:
                print(errormsg)
                sys.exit("ERROR: argument '{0}' requires a value".format(Argument.flag))
        else:
            if Argument.value == True:
                Argument.value = sys.argv[sys.argv.index(Argument.flag)+1]
        
    if Argument.value == False:
        if Argument.flag in sys.argv:
            Argument.value = True
        else:
            Argument.value = False
    return Argument.value
#-----------------------------------------------------------------------------------#

vers = '0.1'
indata = make_arg('--i',True,True)
thresh = make_arg('--inithresh',True,True)
apix = make_arg('--apix',True,True)
halfmap1 = indata.split('class001')[0]+'half1_class001_unfil.mrc'
halfmap2 = indata.split('class001')[0]+'half2_class001_unfil.mrc'

# error checking for files
if os.path.isfile(indata) == False:
    sys.exit('ERROR input model file: {0} not found'.format(indata))
if os.path.isfile(halfmap1) == False:
    sys.exit('ERROR halfmap file: {0} not found'.format(halmap1))
if os.path.isfile(halfmap2) == False:
    sys.exit('ERROR halfmap file: {0} not found'.format(halfmap2))

def do_mask_PP(indata,thresh,inimask,edge,apix):
    # make mask
    proc = subprocess.Popen(['relion_mask_create','--i',str(indata),'--o','OptPP/mask.mrc','--ini_threshold',str(thresh),'--extend_inimask',str(inimask),'--width_soft_edge',str(edge),'--j','16','--angpix',apix],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    # postprocess
    pp = subprocess.Popen(['relion_postprocess','--mask','OptPP/mask.mrc','--i',indata.split('class001')[0]+'half1_class001_unfil.mrc','--o','OptPP/postprocess','--angpix',apix,'--auto_bfac','--autob_lowres','10'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out, err = pp.communicate()
    outputl=out
    erroutl=err
    return([thresh,inimask,edge,outputl,erroutl])

#setup: check for the OptPP directory
if os.path.isdir('OptPP') == False:
    subprocess.call(['mkdir','OptPP'])

# range for model threshold
prange =[0.01 * x for x in range(-5,6,2)]
threshlist = [ float(thresh)+ (x * float(thresh)) for x in prange]

## make the mask combinations
vals =[]
for k in threshlist:
    for i in range(0,14,3):
        for j in range(0,14,3):
            vals.append([k,i,j])

# user info
print('''
-- Postprocessing mask optimisation v{0} --

input model:    {1}
halfmaps:       {2}
                {3}
threshold min:  {4}
          max:  {5}
pixel size:     {6}
                '''.format(vers,indata,halfmap1,halfmap2,min(threshlist),max(threshlist),apix))
print('0%   |    |    |    | 100%')

# run mask and pp on all combos
results = []
count = 0
bincount = 0
bins = [0.01 * x for x in range(1,101,10)]
bins.append(100.0)
for i in vals:
    result = do_mask_PP(indata,i[0],i[1],i[2],apix)
    for k in result[3].split('\n'):
        if 'FINAL RESOLUTION:' in k:
            finres = k.split()[-1]
        if 'apply b-factor of:' in k:
            bfac = k.split()[-1]
    if 'WARNING' in result[4]:
        errors = True
    else:
        errors = False
    results.append([result[0],result[1],result[2],finres,bfac,errors])
    count +=1
    while float(count)/float(len(vals)) > bins[bincount]:
        sys.stdout.write('==')
        sys.stdout.flush()
        bincount+=1

sys.stdout.write('==\n')
sys.stdout.flush()

# parse final results
results.sort(key=lambda x: float(x[3]))

resresults = []
for i in results:
    if i[5] == False and float(i[3]) != 2*float(apix):
        resresults.append(i[3])

maxres = []
for i in results:
    if i[3] == max(resresults):
        maxres.append(i)
maxres.sort(key=lambda x: float(x[4]),reverse=True)
print('\n-- Highest scoring masks --\n')
print('Thresold\tHM\tSM\tReso\tbFact')
for i in maxres:
    print('{0}\t{1}\t{2}\t{3:.2f}\t{4}'.format(i[0],i[1],i[2],round(float(i[3]),2),i[4])) 