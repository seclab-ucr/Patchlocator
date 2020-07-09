#this file is used for generating inputs of fiber
#input the "cve_commitelement_"+branch+"_pickle" from patchevolution.py
import helper_zz
import compilekernels
import get_debuginfo

#directory that stores reference kernel source code
refsourcepath = os.getcwd()+'/refsources'
#directory that stores reference kernel binary/symbol table/vmlinux/debuginfo
refkernelpath = '/data1/zheng/msm-4.9'
#the config file name when compiling reference kernel
config='sdm845-perf'
def get_refsources(repo,branch):
    global refsourcepath
    if not os.path.exists(refsourcepath):
        os.mkdir(refsourcepath)
    pickle_in = open("cve_commitelement_"+branch+"_pickle",'rb')
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
                directorypath = commitpath+'/'.join(filename.split('/')[:-1])
                if not os.path.exists(directorypath):
                    os.mkdirs(directorypath)
                filepath = commitpath+'/'+filename
                string1= 'cd '+repopath+';git show '+afterpatchcommit+':'+filename+' > '+filepath
                helper_zz.command(string1)

#get binary/symbol table/vmlinux of refkernel
def get_refkernels(repo,branch):
    global refkernelpath,config
    if not os.path.exists(refkernelpath):
        os.mkdir(refsourcepath)
    pickle_in = open("cve_commitelement_"+branch+"_pickle",'rb')
    cve_commitelement = pickle.load(pickle_in)
    commitlist = []
    for cve in cve_commitelement:
        for afterpatchcommit in cve_commitelement[cve]:
            commitlist += [afterpatchcommit]
            for element in cve_commitelement[cve]:
                beforecommit = cve_commitelement[cve][element]
                break
    commitlist = list(set(commitlist))
    compilekernels.compile_kernel(repo,commitlist,config,refkernelpath)

#it will cost much time
def get_debuginfo():
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

def get_beforepatchcommits(repo,branch):
    cve_beforecommits={}
    pickle_in = open("cve_commitelement_"+branch+"_pickle",'rb')
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
    pickle_in = open("cve_commitelement_"+branch+"_pickle",'rb')
    cve_commitelement = pickle.load(pickle_in)
    cve_beforecommits = get_beforepatchcommits(repo,branch)
    for cve in cve_commitelement:
        print cve
        cvepath = refsourcepath+'/'+cve
        for afterpatchcommit in cve_commitelement[cve]:
            commitpath = cvepath+'/'+afterpatchcommit
            beforecommit = cve_beforecommits[cve]
            elementset = cve_commitelement[cve][afterpatchcommit].keys()
            patchfile = generatepatchfile(repo,beforecommit,afterpatchcommit,elementset)
            with open(commitpath+'/'+cve,'w') as f:
                for line in patchfile:
                    f.write(line)


if __name__ == '__main__':
    repo = sys.argv[1]
    branch = sys.argv[2]
    get_refsources(repo,branch)
    get_refkernels(repo,branch)
    get_debuginfo()
    get_patches(repo,branch)
