#this file is used for generating inputs of fiber
#input the "cve_commitelement_"+branch+"_pickle" from patchevolution.py
import helper_zz
import compilekernels
import get_debuginfo
import os,sys
import pickle
from shutil import copyfile

#directory that stores reference kernel source code
refsourcepath = os.getcwd()+'/Fiberinputs/refsources'
#directory that stores reference kernel binary/symbol table/vmlinux/debuginfo
refkernelpath = os.getcwd()+'/Fiberinputs/refkernels'
#the config file name when compiling reference kernel
config='sdm845-perf'
def get_refsources(repo,branch):
    repopath = helper_zz.get_repopath(repo)
    global refsourcepath
    if not os.path.exists(refsourcepath):
        os.makedirs(refsourcepath)
    pickle_in = open("output/cve_commitelement_"+branch+"_pickle",'rb')
    cve_commitelement = pickle.load(pickle_in)
    for cve in cve_commitelement:
        print 'get reference kernel source code for',cve
        cvepath = refsourcepath+'/'+cve
        if not os.path.exists(cvepath):
            os.mkdir(cvepath)
        for afterpatchcommit in cve_commitelement[cve]:
            print afterpatchcommit
            commitpath = cvepath+'/'+afterpatchcommit
            if not os.path.exists(commitpath):
                os.mkdir(commitpath)
            for (filename,funcname) in cve_commitelement[cve][afterpatchcommit]:
                print filename
                directorypath = commitpath+'/'+'/'.join(filename.split('/')[:-1])
                if not os.path.exists(directorypath):
                    os.makedirs(directorypath)
                filepath = commitpath+'/'+filename
                string1= 'cd '+repopath+';git show '+afterpatchcommit+':'+filename+' > '+filepath
                helper_zz.command(string1)

#get binary/symbol table/vmlinux of refkernel
def get_refkernels(repo,branch):
    global refkernelpath,config
    if not os.path.exists(refkernelpath):
        os.makedirs(refkernelpath)
    pickle_in = open("output/cve_commitelement_"+branch+"_pickle",'rb')
    cve_commitelement = pickle.load(pickle_in)
    commitlist = []
    for cve in cve_commitelement:
        for afterpatchcommit in cve_commitelement[cve]:
            commitlist += [afterpatchcommit]
            for element in cve_commitelement[cve][afterpatchcommit]:
                beforecommit = cve_commitelement[cve][afterpatchcommit][element]
                break
            print beforecommit
            commitlist += [beforecommit]
    commitlist = list(set(commitlist))
    compilekernels.compile_kernel(repo,commitlist,config,refkernelpath)

#it will cost much time
def Get_debuginfo():
    global refkernelpath
    get_debuginfo.get_debuginfo(refkernelpath)

def get_patchfile(repopath,prevcommit,filename1,commit,filename2,funcnames):
    string1='cd '+repopath+';git diff '+prevcommit+':'+filename1+' '+commit+':'+filename2
    p_buf=helper_zz.command(string1)
    headstart=0
    head=p_buf[0]
    p_buf2 = []
    for i in range(len(p_buf)):
        line = p_buf[i]
        if '@@' in line:
            head = line
        if 'diff' in head or any(funcname in head for funcname in funcnames):
            p_buf2 += [line]
    return p_buf2

#elementset: set of (filename,funcname)
def generatepatchfile(repo,nopatchcommit,patchcommit,elementset):
    repopath = helper_zz.get_repopath(repo)
    filename_funcnames={}
    totalpatchfile=[]
    for (filename,funcname) in elementset:
        if filename not in filename_funcnames:
            filename_funcnames[filename] = set()
        filename_funcnames[filename].add(funcname)
    for filename in filename_funcnames:
        p_buf2 = get_patchfile(repopath,nopatchcommit,filename,patchcommit,filename,filename_funcnames[filename])
        totalpatchfile += p_buf2
    return totalpatchfile

def get_beforepatchcommits(branch):
    cve_beforecommits={}
    pickle_in = open("output/cve_commitelement_"+branch+"_pickle",'rb')
    cve_commitelement = pickle.load(pickle_in)
    for cve in cve_commitelement:
        for afterpatchcommit in cve_commitelement[cve]:
            for element in cve_commitelement[cve][afterpatchcommit]:
                beforecommit = cve_commitelement[cve][afterpatchcommit][element]
                break
            break
        cve_beforecommits[cve] = beforecommit
    return cve_beforecommits

#we put the patches in the same dir as refsources
def get_patches(repo,branch):
    print 'get_patches:'
    pickle_in = open("output/cve_commitelement_"+branch+"_pickle",'rb')
    cve_commitelement = pickle.load(pickle_in)
    cve_beforecommits = get_beforepatchcommits(branch)
    for cve in cve_commitelement:
        print cve
        cvepath = refsourcepath+'/'+cve
        for afterpatchcommit in cve_commitelement[cve]:
            commitpath = cvepath+'/'+afterpatchcommit
            beforecommit = cve_beforecommits[cve]
            elementset = cve_commitelement[cve][afterpatchcommit].keys()
            patchfile = generatepatchfile(repo,beforecommit,afterpatchcommit,elementset)
            if not patchfile:
                print 'dont get patchfile for',afterpatchcommit,'beforecommit:',beforecommit
                continue
            with open(commitpath+'/'+cve,'w') as f:
                for line in patchfile:
                    f.write(line)

#generate commands used in Fiber pick phase
def generate_pickcommands(branch):
    global refsourcepath,refsourcepath,config
    pickle_in = open("output/cve_commitelement_"+branch+"_pickle",'rb')
    cve_commitelement = pickle.load(pickle_in)
    pickcommands = []
    for cve in cve_commitelement:
        print cve
        for afterpatchcommit in cve_commitelement[cve]:
            localrefsourcepath = refsourcepath+'/'+cve+'/'+afterpatchcommit
            localrefkernelpath = refkernelpath+'/'+afterpatchcommit+'_'+config
            outputpath = localrefsourcepath
            patchlistfile = localrefsourcepath+'/patch_list'
            with open(patchlistfile,'w') as f:
                f.write(localrefsourcepath+'/'+cve)
            pickcommand = 'python pick_sig.py '+patchlistfile+' '+localrefsourcepath+' '+outputpath+' '+localrefkernelpath
            pickcommands += [pickcommand]
    with open('./Fiberinputs/pickcommands','w') as f:
        for line in pickcommands:
            f.write(line+'\n')

#generate commands used in Fiber extract phase
def generate_extcommands(branch):
    global refsourcepath,refsourcepath,config
    pickle_in = open("output/cve_commitelement_"+branch+"_pickle",'rb')
    cve_commitelement = pickle.load(pickle_in)
    extcommands = []
    for cve in cve_commitelement:
        print cve
        for afterpatchcommit in cve_commitelement[cve]:
            localrefkernelpath = refkernelpath+'/'+afterpatchcommit+'_'+config
            localrefsourcepath = refsourcepath+'/'+cve+'/'+afterpatchcommit
            extcommand = 'python ext_sig.py '+localrefkernelpath+' '+localrefsourcepath
            extcommands += [extcommand]
    with open('Fiberinputs/extcommands','w') as f:
        for line in extcommands:
            f.write(line+'\n')

#generate match commands for reference kernels(mode 0 , 2 in Fiber), only need to be executed once (when there are multiple targets)
def generate_matchcommands_ref(branch):
    global refsourcepath,refsourcepath,config
    pickle_in = open("output/cve_commitelement_"+branch+"_pickle",'rb')
    cve_commitelement = pickle.load(pickle_in)
    cve_beforecommits=get_beforepatchcommits(branch)
    matchcommands1 = []
    matchcommands2 = []

    for cve in cve_commitelement:
        print cve
        beforepatchcommit = cve_beforecommits[cve]
        unpatchkernelpath = refkernelpath+'/'+beforepatchcommit+'_'+config
        if not os.path.exists(unpatchkernelpath):
            print 'no compiled beforepatch commit:',beforepatchcommit
            continue
        for afterpatchcommit in cve_commitelement[cve]:
            localrefkernelpath = refkernelpath+'/'+afterpatchcommit+'_'+config
            localrefsourcepath = refsourcepath+'/'+cve+'/'+afterpatchcommit
            sigspath = localrefsourcepath

            kernelpath = sigspath+'/refkernel'
            if not os.path.exists(kernelpath):
                os.mkdir(kernelpath)
            copyfile(localrefkernelpath+'/boot',kernelpath+'/boot')
            copyfile(localrefkernelpath+'/System.map',kernelpath+'/System.map')
            kernelpath = sigspath+'/unpatchkernel'
            if not os.path.exists(kernelpath):
                os.mkdir(kernelpath)
            copyfile(unpatchkernelpath+'/boot',kernelpath+'/boot')
            copyfile(unpatchkernelpath+'/System.map',kernelpath+'/System.map')

            matchcommand = 'python match_sig.py '+sigspath+' 0'
            matchcommands1 += [matchcommand]
            matchcommand = 'python match_sig.py '+sigspath+' 2'
            matchcommands2 += [matchcommand]
    matchcommands = matchcommands1 + matchcommands2
    with open('Fiberinputs/matchcommands_ref','w') as f:
        for line in matchcommands:
            f.write(line+'\n')

def generate_matchcommands_target(branch,targetkernelpath):
    if not os.path.exists(targetkernelpath+'/boot'):
        print 'no binary image in',targetkernelpath
        return
    symbletable_path=targetkernelpath+"/"+"System.map"
    if not os.path.exists(symbletable_path):
        string1='./ext_sym '+targetkernelpath+'/boot > '+targetkernelpath+'/System.map'
        result=helper_zz.command(string1)

    global refsourcepath,refsourcepath,config
    pickle_in = open("output/cve_commitelement_"+branch+"_pickle",'rb')
    cve_commitelement = pickle.load(pickle_in)

    matchcommands = []
    for cve in cve_commitelement:
        print cve
        for afterpatchcommit in cve_commitelement[cve]:
            sigspath = refsourcepath+'/'+cve+'/'+afterpatchcommit
            matchcommand = 'python match_sig.py '+sigspath+' 1 '+targetkernelpath
            matchcommands += [matchcommand]
    with open('Fiberinputs/matchcommands_target','w') as f:
        for line in matchcommands:
            f.write(line+'\n')


if __name__ == '__main__':
    repo = sys.argv[1]
    branch = sys.argv[2]
    #get_refsources(repo,branch)
    get_refkernels(repo,branch)
    
    Get_debuginfo()
    #get_patches(repo,branch)
    
    #generate_pickcommands(branch)
    #generate_extcommands(branch)
    #generate_matchcommands_ref(branch)
    #generate_matchcommands_target(branch,sys.argv[3])
