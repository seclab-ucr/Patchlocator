#from commitnumber import *
import helper_zz
from multiprocessing import Pool
import re
import time
import subprocess
import pickle
import os,sys
import datetime
import src_parser 
import ast

def _trim_lines(buf):
    for i in range(len(buf)):
        if len(buf[i]) != 0:
            if buf[i][-1] == '\n':
                buf[i] = buf[i][:-1]

#given a CVE, locate the patch in a specific branch of specific repository
def get_strict_patchcommits((cve,repo,commit),targetrepopath,targetbranch,commitlog):
    print 'Locating',cve,'in branch',targetbranch,'in repo',targetrepopath
    patchkernel=helper_zz.get_repopath(repo)
    patchinfomation=helper_zz.get_commitinformation(patchkernel,commit)
    Author=patchinfomation['author']
    authortime=patchinfomation['authortime']
    simpleintroduction=patchinfomation['simpleintroduction']
    
    #step1: locate the patch with introduction. If there are multiple patches in the history (it's possible due to merges), choose the earliest one. if this patch is merged into target repository, we also get the merge commit (with function get_maincommit).
    notecandidates=[]
    for line in commitlog:
        if simpleintroduction in line:
            notecandidates +=[line[:12]]
    if len(notecandidates)==1:
        return [notecandidates[0]+' '+helper_zz.get_maincommit(targetrepopath,targetbranch,notecandidates[0])],[]
    elif len(notecandidates)>1:
        maincommit = helper_zz.get_maincommit(targetrepopath,targetbranch,notecandidates[-1])
        return [notecandidates[-1]+' '+maincommit],[]

    #If no results from introduction, we need to use content of patch to locate the patch commit
    helper_zz.checkoutcommit(targetrepopath,targetbranch)
    if not os.path.exists('output/patches'):
        os.mkdir('output/patches')
    patchPath="output/patches/"+cve
    if not os.path.exists(patchPath):
        p_buf=helper_zz.get_commit_content(patchkernel,commit)
        with open(patchPath,"w") as f:
            for line in p_buf:
                f.write(line+"\n")
    with open(patchPath,'r') as p:
        p_buf = p.readlines()
        _trim_lines(p_buf)

    #set of (fn,fp)
    changefiles=helper_zz.get_files(p_buf)
    patchfiles=set([element[1] for element in changefiles])
    #changefiles2 is used to log the difference of file path between original patch and current branch
    changefiles2=set()
    newpatchfiles=set()
    commitcandidates=set()

    strictcommits=set()
    fuzzcommits=set()
    #the patch may contain chanegs in multiple files, we try to locate them separately
    for file_name in patchfiles:
        if file_name.endswith("\r"):
            file_name=file_name[:-1]
        (local_candidates,newfilename)=helper_zz.get_candidate_commitnumbers2(targetrepopath, file_name)
        if newfilename.startswith('./'):
            newfilename=newfilename[2:]
        if len(local_candidates) >0:
            newpatchfiles.add(newfilename)
            #it's possible that the filename is changed in the evolution
            if newfilename != file_name:
                #print file_name,'not exist in this branch log and we find substitution',newfilename
                changefiles2.add((file_name,newfilename))
            commitcandidates=commitcandidates.union(local_candidates)
        #else:
        #    logresult([cve,file_name,'not exist in this branch log and we dont find substitution'])
    
    patchfiles=newpatchfiles
    if len(commitcandidates)==0:
        return (None,None)
    commitcandidateslist = [(commitcandidate,p_buf,targetrepopath) for commitcandidate in commitcandidates]
    if len(commitcandidateslist)> 120:
        logresult([cve,"too many candidates:",len(commitcandidateslist)])
        return [],[]
    p=Pool(24)
    resultlist=p.map(helper_zz.is_patch_commit,commitcandidateslist)
    p.close()
    
    filterbyfunction=0
    filterbydate=0
    for (commitcandidate, (notmatch,strictmatch,fuzzmatch)) in resultlist:
        commitcandidate=commitcandidate[:12]
        information=helper_zz.get_commitinformation(targetrepopath,commitcandidate)
        if determinebyintro(simpleintroduction,information):
            strictcommits.add(commitcandidate)
            continue
        if strictmatch==0 and fuzzmatch==0:
            continue
        if notmatch==0 and fuzzmatch==0:
            strictcommits.add(commitcandidate)
            continue
        if determinebyauthor(Author,authortime,information):
            strictcommits.add(commitcandidate)
            continue
        if determinebycve(cve,information):
            strictcommits.add(commitcandidate)
            continue
        fuzzcommits.add(commitcandidate)
    
    #this CVE may be patched when initialization
    if len(strictcommits)==0 and len(fuzzcommits)==0:
        #try to check if patched in initial commit'
        initcommit=get_initcommit(targetrepopath,patchfiles)
        if initcommit:
            #checkout the files when initialization
            updatedfiles=helper_zz.checkoutfiles_commit(targetrepopath,initcommit,patchfiles)
            #match the change sites
            inf=src_parser.parse_patch(patchPath,targetrepopath,changefiles2)
            #restore the files of target branch
            updatedfiles=helper_zz.checkoutfiles_commit(targetrepopath,targetbranch,patchfiles)
            if len(inf) >0:
                #logresult([cve,'should be patched in initial commit',initcommit])
                return (['initialization commit '+initcommit],[])
    return (list(strictcommits),list(fuzzcommits))

def get_initcommit(kernel,patchfiles):
    patchfile=list(patchfiles)[0]
    string1='cd '+kernel+';git log --first-parent --oneline -- -p '+patchfile
    #print 'get_initcommit',string1
    result=helper_zz.command(string1)
    if len(result)==0:
        logresult([patchfile,'not exist in',kernel])
        return None
    return result[-1][:12]

def determinebyauthor(Author,authortime,infomation):
    if infomation['authortime'] == authortime and infomation['author']==Author :
        return True
    if infomation['author']==Author:
        return False
    else:
        return False


def determinebycve(cve,infomation):
    if any(cve in line for line in infomation['introduction']):
        return True
    return False

def determinebyintro(simpleintroduction,infomation):
    if infomation['simpleintroduction'] == simpleintroduction:
        return True
    return False

def logresult(infolist):
    repo = sys.argv[1]
    branch = sys.argv[2]
    line = ''
    for info in infolist:
        line += str(info)+' '
    line = line[:-1]+'\n'
    with open('output/upstreamresults/'+repo+'/'+branch,'a') as f:
        f.write(line)

#[target repo] [target branch] [path to patches file]
#[patches file]: for example: ./patches
def patchlocator():
    cve_strictcommit={}

    targetrepo = sys.argv[1]
    outputdir = 'output/upstreamresults/'+targetrepo
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
    targetrepopath=helper_zz.get_repopath(targetrepo)
    targetbranch=sys.argv[2]
    string1='cd '+targetrepopath+';git log --first-parent --oneline '+targetbranch
    mainlog=helper_zz.command(string1)
    mainlogcommits=[line[:12] for line in mainlog]
    string1='cd '+targetrepopath+';git log --oneline '+targetbranch
    commitlog=helper_zz.command(string1)
    patchesinfo = sys.argv[3]
    with open(patchesinfo,'r') as f:
        s_buf=f.readlines()
    for line in s_buf:
        if '#' in line:
            continue
        (cve,repo,commit)=line[:-1].split(' ')
        if targetrepo == "android" or targetrepo == "linux":
            if "linux" not in repo and "common" not in repo:
                continue
        (strictlist,fuzzlist)=get_strict_patchcommits((cve,repo,commit),targetrepopath,targetbranch,commitlog)
        if type(strictlist)==list:
            if len(strictlist) ==1 and len(fuzzlist)==0:
                cve_strictcommit[cve]=strictlist[0]
                logresult([cve,strictlist[0],helper_zz.get_commitdate(targetrepopath,strictlist[0].split(' ')[-1])])
            else:
                logresult([cve,strictlist,fuzzlist])
        elif strictlist==None:
            cve_strictcommit[cve]='None'
            logresult([cve,'None'])

if __name__ == '__main__':
    patchlocator()
