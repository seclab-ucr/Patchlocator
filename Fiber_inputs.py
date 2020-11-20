#this file is used for generating inputs of fiber
#input the "Patch_evolution_"+branch+"_pickle" from patchevolution.py
import helpers.helper_zz as helper_zz
import helpers.compile_kernels as compile_kernels
import helpers.get_debuginfo as get_debuginfo
import os,sys
import pickle
from shutil import copyfile

#directory that stores reference kernel source code
refsourcepath = os.getcwd()+'/output/Fiberinputs/refsources'
#directory that stores reference kernel binary/symbol table/vmlinux/debuginfo
refkernelpath = os.getcwd()+'/output/Fiberinputs/refkernels'

# used for getting patch-related source codes of reference kernel.
def get_refsources(repo,branch):
    repopath = helper_zz.get_repopath(repo)
    global refsourcepath
    if not os.path.exists(refsourcepath):
        os.makedirs(refsourcepath)
    pickle_in = open("output/Patch_evolution_"+branch+"_pickle",'rb')
    cve_commit_element_content = pickle.load(pickle_in)
    for cve in cve_commit_element_content:
        print 'get reference kernel source code for',cve
        cvepath = refsourcepath+'/'+cve
        if not os.path.exists(cvepath):
            os.mkdir(cvepath)
        for afterpatchcommit in cve_commit_element_content[cve]['aftercommits']:
            commitpath = cvepath+'/'+afterpatchcommit
            if not os.path.exists(commitpath):
                os.mkdir(commitpath)
            for (filename,funcname) in cve_commit_element_content[cve]['aftercommits'][afterpatchcommit]:
                directorypath = commitpath+'/'+'/'.join(filename.split('/')[:-1])
                if not os.path.exists(directorypath):
                    os.makedirs(directorypath)
                filepath = commitpath+'/'+filename
                string1= 'cd '+repopath+';git show '+afterpatchcommit+':'+filename+' > '+filepath
                helper_zz.command(string1)

#used for getting binary image/symbol table/vmlinux of reference kernel. We will compile reference kernels here
def get_refkernels(repo,branch,config):
    global refkernelpath
    if not os.path.exists(refkernelpath):
        os.makedirs(refkernelpath)
    pickle_in = open("output/Patch_evolution_"+branch+"_pickle",'rb')
    cve_commit_element_content = pickle.load(pickle_in)
    commitlist = []
    for cve in cve_commit_element_content:
        beforecommit = cve_commit_element_content[cve]['beforecommit']
        commitlist += [beforecommit]
        for afterpatchcommit in cve_commit_element_content[cve]['aftercommits']:
            commitlist += [afterpatchcommit]
    commitlist = list(set(commitlist))
    compile_kernels.compile_kernel(repo,commitlist,config,refkernelpath)

#used for extracting debug info from vmlinux. You can use the provided addr2line in tools directory or download GCC by yourself and set the path in get_debuginfo.py. It will cost much time
def Get_debuginfo():
    global refkernelpath
    get_debuginfo.get_debuginfo(refkernelpath)

def get_patchfile(repopath,prevcommit,filename1,commit,filename2,funcnames):
    string1='cd '+repopath+';git diff '+prevcommit+':'+filename1+' '+commit+':'+filename2
    p_buf=helper_zz.command(string1)
    #revert may results in no difference
    if len(p_buf)==0:
        return []
    headstart=0
    head=p_buf[0]
    p_buf2 = []
    local_pbuf = []
    for i in range(len(p_buf)):
        line = p_buf[i]
        if '@@' in line:
            local_pbuf_str = ''.join(local_pbuf)
            if 'diff' in head or any(funcname in local_pbuf_str for funcname in funcnames):
                p_buf2 += local_pbuf
            local_pbuf = []
            head = line
        local_pbuf += [line]
    local_pbuf_str = ''.join(local_pbuf)
    if 'diff' in head or any(funcname in local_pbuf_str for funcname in funcnames):
        p_buf2 += local_pbuf
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

#used for getting patch file. (for each CVE, each reference kernel, there is a patchfile).
def get_patches(repo,branch):
    print 'get_patches:'
    pickle_in = open("output/Patch_evolution_"+branch+"_pickle",'rb')
    cve_commit_element_content = pickle.load(pickle_in)
    for cve in cve_commit_element_content:
        print cve
        cvepath = refsourcepath+'/'+cve
        beforecommit = cve_commit_element_content[cve]['beforecommit']
        for afterpatchcommit in cve_commit_element_content[cve]['aftercommits']:
            commitpath = cvepath+'/'+afterpatchcommit
            elementset = cve_commit_element_content[cve]['aftercommits'][afterpatchcommit].keys()
            print 'getpatchfile:'
            print 'repo:',repo,'beforecommit:',beforecommit,'afterpatchcommit:',afterpatchcommit,'elementset:',elementset
            patchfile = generatepatchfile(repo,beforecommit,afterpatchcommit,elementset)
            if not patchfile:
                print 'dont get patchfile for',afterpatchcommit,'beforecommit:',beforecommit
                continue
            with open(commitpath+'/'+cve,'w') as f:
                for line in patchfile:
                    f.write(line)

#generate commands used in Fiber pick phase
def generate_pickcommands(branch,config):
    global refsourcepath,refsourcepath
    pickle_in = open("output/Patch_evolution_"+branch+"_pickle",'rb')
    cve_commit_element_content = pickle.load(pickle_in)
    pickcommands = []
    for cve in cve_commit_element_content:
        print 'generate pickcommands of Fiber for',cve
        for afterpatchcommit in cve_commit_element_content[cve]['aftercommits']:
            localrefsourcepath = refsourcepath+'/'+cve+'/'+afterpatchcommit
            localrefkernelpath = refkernelpath+'/'+afterpatchcommit+'_'+config
            outputpath = localrefsourcepath
            patchlistfile = localrefsourcepath+'/patch_list'
            with open(patchlistfile,'w') as f:
                f.write(localrefsourcepath+'/'+cve)
            pickcommand = 'python pick_sig.py '+patchlistfile+' '+localrefsourcepath+' '+outputpath+' '+localrefkernelpath
            pickcommands += [pickcommand]
    with open('./output/Fiberinputs/pickcommands','w') as f:
        for line in pickcommands:
            f.write(line+'\n')

#generate commands used in Fiber extract phase
def generate_extcommands(branch,config):
    global refsourcepath,refsourcepath
    pickle_in = open("output/Patch_evolution_"+branch+"_pickle",'rb')
    cve_commit_element_content = pickle.load(pickle_in)
    extcommands = []
    for cve in cve_commit_element_content:
        print 'generate extcommands of Fiber for',cve
        for afterpatchcommit in cve_commit_element_content[cve]['aftercommits']:
            localrefkernelpath = refkernelpath+'/'+afterpatchcommit+'_'+config
            localrefsourcepath = refsourcepath+'/'+cve+'/'+afterpatchcommit
            extcommand = 'python ext_sig.py '+localrefkernelpath+' '+localrefsourcepath
            extcommands += [extcommand]
    with open('output/Fiberinputs/extcommands','w') as f:
        for line in extcommands:
            f.write(line+'\n')

#generate match commands for reference kernels(mode 0 , 2 in Fiber), only need to be executed once (when there are multiple targets)
def generate_matchcommands_ref(branch,config):
    global refsourcepath,refsourcepath
    pickle_in = open("output/Patch_evolution_"+branch+"_pickle",'rb')
    cve_commit_element_content = pickle.load(pickle_in)
    matchcommands1 = []
    matchcommands2 = []
    
    for cve in cve_commit_element_content:
        print 'generate matchcommands(ref kernels) of Fiber for',cve
        beforepatchcommit = cve_commit_element_content[cve]['beforecommit']
        unpatchkernelpath = refkernelpath+'/'+beforepatchcommit+'_'+config
        if not os.path.exists(unpatchkernelpath):
            print 'no compiled beforepatch commit:',beforepatchcommit
            continue
        for afterpatchcommit in cve_commit_element_content[cve]['aftercommits']:
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

            matchcommand = 'python match_sig.py '+sigspath+' 0 '+ sigspath+'/refkernel'
            matchcommands1 += [matchcommand]
            matchcommand = 'python match_sig.py '+sigspath+' 2 '+sigspath+'/refkernel'+' '+sigspath+'/unpatchkernel'
            matchcommands2 += [matchcommand]
    matchcommands = matchcommands1 + matchcommands2
    with open('output/Fiberinputs/matchcommands_ref','w') as f:
        for line in matchcommands:
            f.write(line+'\n')

def generate_matchcommands_target(branch,targetkernelpath,config):
    if not os.path.exists(targetkernelpath+'/boot'):
        print 'no binary image in',targetkernelpath
        return
    symbletable_path=targetkernelpath+"/"+"System.map"
    if not os.path.exists(symbletable_path):
        string1='./helpers/ext_sym '+targetkernelpath+'/boot > '+targetkernelpath+'/System.map'
        result=helper_zz.command(string1)

    global refsourcepath,refsourcepath
    pickle_in = open("output/Patch_evolution_"+branch+"_pickle",'rb')
    cve_commit_element_content = pickle.load(pickle_in)

    matchcommands = []
    for cve in cve_commit_element_content:
        print 'generate matchcommands(target kernel) for',cve
        for afterpatchcommit in cve_commit_element_content[cve]['aftercommits']:
            sigspath = refsourcepath+'/'+cve+'/'+afterpatchcommit
            refkernel=sigspath+'/refkernel'
            unpatchkernel = sigspath+'/unpatchkernel'
            matchcommand = 'python match_sig.py '+sigspath+' 1 '+refkernel+' '+unpatchkernel+' '+targetkernelpath
            matchcommands += [matchcommand]
    with open('output/Fiberinputs/matchcommands_target','a') as f:
        for line in matchcommands:
            f.write(line+'\n')


if __name__ == '__main__':
    repo = sys.argv[1]
    branch = sys.argv[2]
    config = sys.argv[3]
    get_refsources(repo,branch)
    get_refkernels(repo,branch,config)
    
    Get_debuginfo()
    get_patches(repo,branch)
    
    generate_pickcommands(branch,config)
    generate_extcommands(branch,config)
    generate_matchcommands_ref(branch,config)
    for targetkernel in sys.argv[4:]:
        generate_matchcommands_target(branch,targetkernel)
