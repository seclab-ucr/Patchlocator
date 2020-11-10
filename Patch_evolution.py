import helpers.helper_zz as helper_zz
import helpers.src_parser as src_parser
import sys
import pickle
import copy
def get_cveinfos(patches_info):
    cve_info = {}
    with open(patches_info,'r') as f:
        s_buf=f.readlines()
    for line in s_buf:
        if line.startswith("#"):
            continue
        cve,repo,commit=line[:-1].split(" ")
        cve_info[cve]=(cve,repo,commit)
    return cve_info

def get_mainfilecommits(repopath,branch,filename):
    string1='cd '+repopath+';git log --pretty=oneline --first-parent '+branch+' -- -p '+filename
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

#input: [repo] [branch] [patches info file]
#input: patchlocator_result 
#output: dictionary cve-filename-funcname-funccontent
def Patchevolution_tracker(repo,branch,patches_info):
    repopath = helper_zz.get_repopath(repo)

    cve_info=get_cveinfos(patches_info)
    cve_functioncontent = {}
    cve_commit_element_content = {}
    patchlocator_result = "output/upstreamresults/"+repo+"/"+branch
    with open(patchlocator_result,"r") as f:
        s_buf = f.readlines()
    for line in s_buf:
        line=line[:-1]
        if any(ignore in line for ignore in ['#','[','None','too many candidates','not exist','initcommit','fail']):
            continue
        cve,maincommit = line.split(" ")[:2]
        print 'Patch evolution tracking for',cve
        beforecommit=helper_zz.get_previouscommit(repopath,maincommit)
        (cve,original_repo,original_commit)=cve_info[cve]
        original_repopath = helper_zz.get_repopath(original_repo)
        functiondic=helper_zz.get_commit_functions2(original_repopath,original_commit)
        cve_functioncontent[cve] ={}
        cve_commit_element_content[cve]={}
        cve_commit_element_content[cve]['beforecommit']=beforecommit
        cve_commit_element_content[cve]['aftercommits']={}
        for filename in functiondic:
            aftercommits = get_afterpatchcommits(repopath,branch,filename,maincommit)
            if not aftercommits:
                #todo file path change
                continue
            for afterpatchcommit in aftercommits:
                if afterpatchcommit not in cve_commit_element_content[cve]['aftercommits']:
                    cve_commit_element_content[cve]['aftercommits'][afterpatchcommit]={}
                for funcname in functiondic[filename]:
                    element = (filename,funcname)
                    if element not in cve_functioncontent[cve]:
                        cve_functioncontent[cve][element]=set()
                    f_buf=helper_zz.get_filecontent(repopath,afterpatchcommit,filename)
                    funccontent=src_parser.get_function_content_1(f_buf,funcname)
                    if len(funccontent)==0:
                        #todo find funcname substitution
                        #print cve,repopath,afterpatchcommit,filename,funcname,'not exist'
                        continue
                    funccontent=list(funccontent)[0]
                    if funccontent in cve_functioncontent[cve][element]:
                        continue
                    else:
                        cve_commit_element_content[cve]['aftercommits'][afterpatchcommit][element] = funccontent
                        cve_functioncontent[cve][element].add(funccontent)
    
    cve_commit_element_content2 = copy.deepcopy(cve_commit_element_content)
    for cve in cve_commit_element_content:
        if 'aftercommits' not in cve_commit_element_content[cve]:
            del cve_commit_element_content2[cve]
            continue
        for afterpatchcommit in cve_commit_element_content[cve]['aftercommits']:
            if len(cve_commit_element_content[cve]['aftercommits'][afterpatchcommit])==0:
                del cve_commit_element_content2[cve]['aftercommits'][afterpatchcommit]
        if len(cve_commit_element_content2[cve]['aftercommits'])==0:
            del cve_commit_element_content2[cve]

    pickle_out = open("output/Patch_evolution_"+branch+"_pickle","wb")
    pickle.dump(cve_commit_element_content2,pickle_out)


if __name__ == '__main__':
    repo=sys.argv[1]
    branch=sys.argv[2]
    patches_info=sys.argv[3]
    Patchevolution_tracker(repo,branch,patches_info)
