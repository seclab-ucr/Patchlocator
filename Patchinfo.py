import helper_zz
import sys,os
import pickle
from Patchevolution import get_cveinfos
def get_mainpatchcommit(patchlocator_result):
    cve_mainpatchcommit= {}
    with open(patchlocator_result,"r") as f:
        s_buf = f.readlines()
    for line in s_buf:
        line=line[:-1]
        if any(ignore in line for ignore in ['#','[]','None','too many candidates','not exist','fail']):
            continue
        cve,commit,maincommit = line.split(" ")[:3]
        cve_mainpatchcommit[cve] = maincommit
    return cve_mainpatchcommit

def get_compiledkernel_versionandtimes():
    repo = sys.argv[1]
    dirpath='/data1/zheng/'+repo+"/"
    repopath = helper_zz.get_repopath(repo)
    commits=os.listdir(dirpath)
    resultlist=[]
    for commit in commits:
        if not os.path.isdir(dirpath+commit):
            continue
        commitnumber=commit[:12]
        (commitversion,committime)=helper_zz.get_commit_versionandtime(repopath,commitnumber)
        resultlist += [(commit,commitversion,committime)]
    resultlist.sort(key=lambda x:(x[2],len(x[0])))
    with open("compiledkernel_versionandtimes_"+repo,"w") as f:
        for element in resultlist:
            f.write(str(element[0])+" "+str(element[1])+" "+str(element[2])+"\n")

def find_compiledkernels():
    repo=sys.argv[1]
    branch = sys.argv[2]
    pickle_in=open('cve_functioncontent_'+branch+'_pickle','rb')
    cve_functioncontent=pickle.load(pickle_in)

    cve_functioncontent_compiledkernels={}
    #cve_debuginfo = {}
    for cve in cve_functioncontent:
        print cve
        new_functioncontent,info = find_compiledkernels_2(cve,repo,cve_functioncontent[cve])
        cve_functioncontent_compiledkernels[cve]=new_functioncontent
        #cve_debuginfo[cve]=info
        with open('find_compiledkernels_'+branch+'_debuginfo','a') as f:
            for line in info:
                f.write(str(line)+'\n')
    pickle_out=open('cve_functioncompiledkernel_'+branch+'_pickle','wb')
    pickle.dump(cve_functioncontent_compiledkernels,pickle_out)

def find_compiledkernels_2(cve,repo,functioncontent):
    info=[]
    info += [cve]
    for element in functioncontent:
        info += [(element,len(functioncontent[element]))]
        for function_content in functioncontent[element]:
            compiledkernel = find_compiledkernel(repo,element[0],element[1],function_content)
            if compiledkernel==None:
                commit = functioncontent[element][function_content]
                info += [str(commit)+' should be compiled']
            #matched in source code but the function is not compiled in binary
            elif type(compiledkernel) == list:
                info += [str(compiledkernel)+' not in binary']
                compiledkernel=None
            else:
                info += [compiledkernel]
            functioncontent[element][function_content]=compiledkernel
    return functioncontent,info

def find_compiledkernel(repo,filename,funcname,function_content):
    kernelpaths = '/data1/zheng/'+repo+"/"
    kernellist= "compiledkernel_versionandtimes_"+repo
    repopath = helper_zz.get_repopath(repo)
    with open(kernellist,'r') as f:
        f_buf=f.readlines()
    sourcekernellist=[]
    if 'CALL' in funcname:
        truefuncname=function_content.split('\n')[0].split('(')[1].split(',')[0]
        print 'truefuncname:',truefuncname,"for",funcname
    else:
        truefuncname=funcname
    for line in f_buf:
        commit=line.split(' ')[0]
        kernelpath=kernelpaths+commit
        commitnumber = commit[:12]
        localfunction_content = helper_zz.get_function_content2(repopath,commitnumber,filename,funcname)
        if function_content in localfunction_content:
            sourcekernellist+=[commit]
            if funcname_indebuginfo(truefuncname,kernelpath):
                return commit
            if len(sourcekernellist) > 10:
                break
    if len(sourcekernellist)==0:
        return None
    else:
        #in source code but not in the binary
        return sourcekernellist

def funcname_indebuginfo(funcname,kernelpath):
    #tmp_o file is generated with get_debuginfo.py
    with open(kernelpath+'/tmp_o','r') as f:
        s_buf=f.readlines()
    #example SyS_perf_event_open for CVE-2016-6786
    if any(funcname in line for line in s_buf):
        return True
    else:
        return False

def get_functionpatchinfo(repo,branch,mainpatchcommit,functioncontent):
    repopath = helper_zz.get_repopath(repo)
    beforecommit=helper_zz.get_previouscommit(repopath,mainpatchcommit)
    print repo,branch,'mainpatchcommit',mainpatchcommit,'beforecommit:',beforecommit
    cve_functionpatchinfo={}    
    for element in functioncontent:
        print 'element:',element
        cve_functionpatchinfo[element]={}
        previous_function_content = helper_zz.get_function_content2(repopath,beforecommit,element[0],element[1])
        if len(previous_function_content)==0:
            print element,'not exist in beforecommit'
            continue
        previous_function_content=list(previous_function_content)[0]
        if previous_function_content in functioncontent[element]:
            print element,"already patched before mainpatchcommit",mainpatchcommit
            continue
        for function_content in functioncontent[element]:
            functionpatchinfo=helper_zz.get_functionpatchinfo(previous_function_content,function_content)
            if len(functionpatchinfo)==0:
                print 'No useful patchinfo',element
                continue

            #length should be one
            for ele in functionpatchinfo:
                patchinfocontent=functionpatchinfo[ele]
            functionpatchinfo={}
            functionpatchinfo[(element[0],element[1]),ele[2]]=patchinfocontent
            cve_functionpatchinfo[element][function_content]=functionpatchinfo
        print len(cve_functionpatchinfo[element])
    return cve_functionpatchinfo

def get_functionpatchinfos():
    repo=sys.argv[1]
    branch=sys.argv[2]
    patchlocator_result = "upstreamresults/"+repo+"/"+branch
    cve_mainpatchcommit = get_mainpatchcommit(patchlocator_result)

    patchevolution_result = "cve_functioncontent_"+branch+"_pickle"
    cve_functioncontent = pickle.load(open(patchevolution_result,'rb'))
    cve_info=get_cveinfos()
    
    cve_functionpatchinfo= {}
    for cve in cve_functioncontent:
        print cve
        mainpatchcommit = cve_mainpatchcommit[cve]
        functioncontentpatchinfo=get_functionpatchinfo(repo,branch,mainpatchcommit,cve_functioncontent[cve])
        cve_functionpatchinfo[cve]=functioncontentpatchinfo
    pickle_out=open('cve_functionpatchinfo'+branch+'_pickle','wb')
    pickle.dump(cve_functionpatchinfo,pickle_out)

def group_cvefunctionpatchinfos(repo,branch):
    pickle_in = open('cve_functionpatchinfo_'+branch+'_pickle','rb')
    cve_functionpatchinfo = pickle.load(pickle_in)

    pickle_in = open('cve_functioncompiledkernel_'+branch+'_pickle','rb')
    cve_functioncontent_compiledkernels = pickle.load(pickle_in)
    
    cvecommitfunctionpatchinfo={}
    deletecves = []
    for cve in cve_functioncontent_compiledkernels:
        print cve
        cvecommitfunctionpatchinfo[cve]={}
        for element in cve_functioncontent_compiledkernels[cve]:
            for functioncontent in cve_functioncontent_compiledkernels[cve][element]:
                commit=cve_functioncontent_compiledkernels[cve][element][functioncontent]
                #ususally due to not compiled in binary
                if commit ==None:
                    continue
                if type(commit) ==list:
                    continue

                if functioncontent not in cve_functionpatchinfo[cve][element]:
                    continue
                #print element,commit
                patchinfo=cve_functionpatchinfo[cve][element][functioncontent]
                #no corresponding patchinfo ,ex, this function is initialization in the patch
                if type(patchinfo) == str:
                    continue
                kernel='/data1/zheng/'+repo+'/'+commit[:12]
                #contextpatchinfo=helper_zz.get_context_patchinfo(kernel,patchinfo)
                contextpatchinfo=helper_zz.get_context_patchinfo2(repo,commit[:12],patchinfo)
                #print patchinfo
                #print contextpatchinfo
                if not contextpatchinfo:
                    continue
                if commit not in cvecommitfunctionpatchinfo[cve]:
                    #print commit
                    cvecommitfunctionpatchinfo[cve][commit]={}
                cvecommitfunctionpatchinfo[cve][commit].update(contextpatchinfo)
        if len(cvecommitfunctionpatchinfo[cve])==0:
            print 'no any patchinfo with compiledkernel for ',cve
            deletecves += [cve]
        for commit in cvecommitfunctionpatchinfo[cve]:
            print commit
            print [element for element in cvecommitfunctionpatchinfo[cve][commit]]
            #for element in cvecommitfunctionpatchinfo[cve][commit]:
            #    print element
            #    print cvecommitfunctionpatchinfo[cve][commit][element]
    print len(deletecves)
    for cve in deletecves:
        del cvecommitfunctionpatchinfo[cve]
    pickle_out=open('cvecommitfunctionpatchinfo'+branch+'_pickle','wb')
    pickle.dump(cvecommitfunctionpatchinfo,pickle_out)

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
    with open('patchfile','w') as f:
        for line in totalpatchfile:
            f.write(line)

def test():
    repo='msm-4.9'
    nopatchcommit='d5d55ba074e6'
    patchcommit = '1fb9158725c8'
    elementset = set([('drivers/staging/android/ion/msm/msm_ion.c', 'msm_ion_custom_ioctl')])
    generatepatchfile(repo,nopatchcommit,patchcommit,elementset)

if __name__ == '__main__':
    #get_functionpatchinfos()
    #get_compiledkernel_versionandtimes()
    #find_compiledkernels()
    #group_cvefunctionpatchinfos('msm-4.9','kernel.lnx.4.9.r25-rel')
    test()

