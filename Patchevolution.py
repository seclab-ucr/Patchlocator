import helper_zz
import src_parser
import sys
import pickle
import copy
def get_cveinfos():
    cve_info = {}
    with open('patchdic','r') as f:
        s_buf=f.readlines()
    for line in s_buf:
        if not line.startswith('('):
            continue
        line=line[:-1][1:-1]
        linelist=line.split(", ")
        (month,cve,repo,commit)=(linelist[0][1:-1],linelist[1][1:-1],linelist[2][1:-1],linelist[3][1:-1])
        cve_info[cve]=(month,cve,repo,commit)
    return cve_info

def get_mainfilecommits(repopath,branch,filename):
    string1='cd '+repopath+';git log --oneline --first-parent '+branch+' -- -p '+filename
    resultbuf=helper_zz.command(string1)
    mainfilecommits=[]
    resultbuf.reverse()
    for line in resultbuf:
        commit=line[:12]
        mainfilecommits+= [commit]
    return mainfilecommits

def get_afterpatchcommits(repopath,branch,filename,patchcommit):
    mainfilecommits = get_mainfilecommits(repopath,branch,filename)
    if patchcommit not in mainfilecommits:
        print "strange: patchcommit ",patchcommit,"not in maincommit history of",repopath,branch,filename
        return None
    index = mainfilecommits.index(patchcommit)
    return mainfilecommits[index:]

#input: [repo] [branch] 
#output: dictionary cve-filename-funcname-funccontent
def Patchevolution_tracker():
    repo=sys.argv[1]
    repopath = helper_zz.get_repopath(repo)
    branch = sys.argv[2]

    cve_info=get_cveinfos()
    cve_functioncontent ={}
    patchlocator_result = "upstreamresults/"+repo+"/"+branch
    with open(patchlocator_result,"r") as f:
        s_buf = f.readlines()
    for line in s_buf:
        line=line[:-1]
        if any(ignore in line for ignore in ['#','[]','None','too many candidates','not exist','fail']):
            continue
        cve,commit,maincommit = line.split(" ")[:3]
        #if cve != "CVE-2019-11833":
        #    continue
        print "\n"+cve,commit,maincommit
        (month,cve,original_repo,original_commit)=cve_info[cve]
        original_repopath = helper_zz.get_repopath(original_repo)
        print original_repo,original_commit
        functiondic=helper_zz.get_commit_functions2(original_repopath,original_commit)
        #print functiondic
        cve_functioncontent[cve] ={}
        for filename in functiondic:
            aftercommits = get_afterpatchcommits(repopath,branch,filename,maincommit)
            if not aftercommits:
                #todo file path change
                continue
            for afterpatchcommit in aftercommits:
                for funcname in functiondic[filename]:
                    element = (filename,funcname)
                    if element not in cve_functioncontent[cve]:
                        cve_functioncontent[cve][element] = {}
                    #print f_buf
                    f_buf=helper_zz.get_filecontent(repopath,afterpatchcommit,filename)
                    funccontent=src_parser.get_function_content_1(f_buf,funcname)
                    if len(funccontent)==0:
                        #todo find funcname substitution
                        print cve,repopath,afterpatchcommit,filename,funcname,'not exist'
                        continue
                    funccontent=list(funccontent)[0]
                    if funccontent in cve_functioncontent[cve][element]:
                        continue
                    else:
                        cve_functioncontent[cve][element][funccontent] = set([afterpatchcommit])
        #for element in cve_functioncontent[cve]:
        #    print element
        #    print len(cve_functioncontent[cve][element])
    cve_functioncontent2 = copy.deepcopy(cve_functioncontent)
    for cve in cve_functioncontent:
        for element in cve_functioncontent[cve]:
            if  len(cve_functioncontent[cve][element])==0:
                del cve_functioncontent2[cve][element]
        if len(cve_functioncontent2[cve]) == 0:
            del cve_functioncontent2[cve]
    pickle_out = open("cve_functioncontent_"+branch+"_pickle","wb")
    pickle.dump(cve_functioncontent2,pickle_out)


if __name__ == '__main__':
    Patchevolution_tracker()
