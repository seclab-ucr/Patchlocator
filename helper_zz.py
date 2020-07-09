import datetime
import pickle
import subprocess
import re
import time
import src_parser
import src_parser_zz
def trim_lines(buf):
    for i in range(len(buf)):
        if len(buf[i])==0:
            continue
        if buf[i][-1] == '\n':
            buf[i] = buf[i][:-1]
#require hard code
def get_repopath(repo):
    repo_path = {
            'msm':"/home/zheng/fiberweiteng/msm-3.4",
            'msm-3.4':"/home/zheng/fiberweiteng/msm-3.4",
            'msm-3.10':"/home/zheng/fiberweiteng/msm-3.10",
            'msm-3.18':"/home/zheng/fiberweiteng/msm-3.18",
            'msm-4.4':"/home/zheng/fiberweiteng/msm-4.4",
            'msm-4.9':"/home/zheng/fiberweiteng/msm-4.9",
            'msm-4.14':"/home/zheng/fiberweiteng/msm-4.14",
            'linux':"/home/zheng/fiberweiteng/linux_stable/linux",
            'common':"/home/zheng/fiberweiteng/common",
            'android':"/home/zheng/fiberweiteng/common",
            'androidmsm':"/home/zheng/fiberweiteng/msm",
            'pixel':"/home/zheng/fiberweiteng/msm",
            'oneplus5':"/data1/zheng/opensource/android_kernel_oneplus_msm8998",
            }
    if repo in repo_path:
        return repo_path[repo]
    return None

def checkoutcommit(kernel,commit):
    string1="cd "+kernel+"; git checkout -f "+commit
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p_buf=p.stdout.readlines()
    return

#used for get changed files in initial commits and patch commits
#set of (fn,fp)
def get_filenames_commit(kernel,commit):
    p_buf=get_commit_content(kernel,commit)
    return get_files(p_buf)

def get_files(p_buf):
    filenames=set()
    trim_lines(p_buf)
    diff_index = [i for i in range(len(p_buf)) if p_buf[i].startswith('diff')] + [len(p_buf)]
    for i in range(len(diff_index)-1):
        result=get_filename_diff(p_buf,diff_index[i],diff_index[i+1])
        if result:
            filenames.add(result)
    return filenames

def get_afterfiles(filenames):
    afterfiles=set()
    for (fn,fp) in filenames:
        if fp != None:
            afterfiles.add(fp)
    return afterfiles

def get_beforefiles(filenames):
    beforefiles=set()
    for (fn,fp) in filenames:
        if fn != None:
            afterfiles.add(fn)
    return beforefiles

def get_newfiles(filenames):
    newfiles=set()
    for (fn,fp) in filenames:
        if fn == None:
            newfiles.add(fp)
    return newfiles

def get_deletedfiles(filenames):
    deletedfiles=set()
    for (fn,fp) in filenames:
        if fp == None:
            deletedfiles.add(fn)
    return deletedfiles


def get_filename_diff(p_buf,st,ed):
    fp = None
    fn = None
    for i in range(st,ed):
        if fp is not None and fn is not None:
            break
        if p_buf[i].startswith('---'):
            fn = p_buf[i][6:]
        elif p_buf[i].startswith('+++'):
            fp = p_buf[i][6:]
        elif p_buf[i].startswith('rename from'):
            fn = p_buf[i][12:]
        elif p_buf[i].startswith('rename to'):
            fp = p_buf[i][10:]

    if fp is None or fn is None:
        return None
    elif fp=='ev/null':
        return (fn,None)
    elif fn=='ev/null':
        return (None,fp)
    else:
        return (fn,fp)
    
def get_corresponding_del_adds(filepath):
    with open(filepath,"r") as f:
        p_buf=f.readlines()
    return get_corresponding_del_adds_1(p_buf)
def get_corresponding_del_adds_1(p_buf):
    trim_lines(p_buf)
    del_add_list=[]
    st=0
    ed=len(p_buf)
    at_index = [i for i in range(st,ed) if p_buf[i].startswith('@@')] + [ed]
    for i in range(len(at_index)-1):
        local_list=get_corresponding_del_adds_2(at_index[i],at_index[i+1],p_buf)
        del_add_list += local_list
    return del_add_list

def get_corresponding_del_adds_2(st,ed,p_buf):
    local_list=[]
    head=p_buf[st]
    #print head
    headlist=head.split(",")
    try:
        currentline_B=int(headlist[0].split("-")[1])
        currentline_A=int(headlist[1].split("+")[1])
    except:
        return []
    start=False
    localdel=[]
    localadd=[]
    for i in range(st+1,ed):
        if p_buf[i].startswith("-"):
            start=True
            localdel +=[currentline_B]
            currentline_B +=1
        elif p_buf[i].startswith("+"):
            start=True
            localadd += [currentline_A]
            currentline_A +=1
        else:
            currentline_B +=1
            currentline_A +=1
            if start:
                start=False
                if len(localdel) >0:
                    element1=(localdel[0],localdel[-1])
                else:
                    element1=(None,currentline_B)
                if len(localadd) >0:
                    element2=(localadd[0],localadd[-1])
                else:
                    element2=None
                local_list += [(element1,element2)]
                localdel=[]
                localadd=[]
    return local_list

def lineB_A(del_add_list,linenumber):
    diff=0
    for i in range(len(del_add_list)):
        (element1,element2)=del_add_list[i]
        #print (element1,element2)
        #print diff
        if element1[0] != None:
            (delst,deled)=element1
            if linenumber < delst:
                return (linenumber+diff)
            elif linenumber in range(delst,deled+1):
                if element2 != None:
                    return (element1,element2)
                else:
                    return None
            else:
                diff -= (deled-delst+1)
                if element2 != None:
                    (addst,added)=element2
                    diff += (added-addst+1)
                    #diff=added-deled
                    #print (element1,element2)
                    #print diff
        else:
            #pure add
            delst=element1[1]
            #print delst, diff
            if linenumber<delst:
                return linenumber+diff
            (addst,added)=element2
            diff += (added-addst+1)
    return (linenumber+diff)

initializationcommitlist=['dcd756388a2','408a5ae27d3','e362c2d8e2d','231ea4a2246']
def commit_is_initialization(kernel,commit,patchfiles):
    if commit in initializationcommitlist:
        return True
    string1='cd '+kernel+';git show --oneline '+commit
    result=command(string1)
    if any('Add' in line for line in result) and any('snapshot' in line for line in result):
        return True

    updatedfiles=checkoutfiles_commit(kernel,commit,patchfiles)
    #now we don't consider the cases that it's a initialization patch commit, but the patch file name can't be matched
    if len(updatedfiles)==0:
        return False
    commitfiles=get_filenames_commit(kernel,commit)
    for filename in updatedfiles:
        for (fn,fp) in commitfiles:
            if fp==filename:
                if fn==None:
                    return True
    return False

def get_B_file(kernel,filename,patchinfo):
    filepath=kernel+"/"+filename
    with open(filepath,"r") as f:
        f_buf=f.readlines()
    
    deldic={}
    for element in patchinfo:
        if element[0]==filename:
            if 'add' in patchinfo[element]:
                for (st,ed) in patchinfo[element]['add']:
                    for i in range(st-1,ed):
                        f_buf[i]=None
            if 'del' in patchinfo[element]:
                for (st,ed) in patchinfo[element]['del']:
                    prevline=st-1
                    linelist=patchinfo[element]['del'][(st,ed)]
                    deldic[prevline]=linelist
    f_buf2=[]
    for i in range(len(f_buf)):
        if f_buf[i] != None:
            f_buf2 += [f_buf[i]]
        if (i+1) in deldic:
            for line in deldic[(i+1)]:
                f_buf2 += [line+"\n"]

    return f_buf2



def checkoutfiles_commit(kernel,commit,files):
    string1="cd "+kernel
    updatedfiles=set()
    for filename in files:
        if file_exits_in_commit(kernel,commit,filename):
            string1 += ";git checkout -f "+commit+" "+filename
            updatedfiles.add(filename)
    #try:
    #print string1
    command(string1)
    #print string1
    #except:
    #    print "some errors happens"
    #    print string1
    #    exit()
    return updatedfiles

def get_filecontent(kernel,commit,filename):
    if not file_exits_in_commit(kernel,commit,filename):
        print kernel,commit,filename,'not exist'
        return None
    string1='cd '+kernel+';git show '+commit+':'+filename
    #print string1
    f_buf=command(string1)
    return f_buf

def get_function_content(kernel,filename,funcname,funcline=0):
    return src_parser.get_function_content(kernel,filename,funcname,funcline)

def get_function_content2(kernel,commit,filename,funcname,funcline=0):
    updatedfiles=checkoutfiles_commit(kernel,commit,set([filename]))
    return src_parser.get_function_content(kernel,filename,funcname,funcline)
def get_functionpatchinfo(previous_function_content,function_content):
    previous_function_contentlines=previous_function_content.split('\n')
    with open('tmpfunction1','w') as f:
        for line in previous_function_contentlines:
            f.write(line+'\n')
        #f.write(previous_function_content)
    function_contentlines=function_content.split('\n')
    with open('tmpfunction2','w') as f:
        for line in function_contentlines:
            f.write(line+'\n')
        #f.write(function_content)
    string1='git diff --no-index tmpfunction1 tmpfunction2 >tmpfunctionpatch'
    command(string1)
    functionpatchinfo=src_parser.parse_patch('tmpfunctionpatch','/home/zheng/fiberweiteng/commitresults')
    return functionpatchinfo

def get_bfr_patch_func(src,patch):
    (st,ed) = patch['func_range']
    src_func = src[st-1:ed]
    if patch['type'] == 'aft':
        #The src is aft-patch version, we should add the 'deleted' lines and remove 'added' lines.
        if 'add' in patch:
            for k in patch['add']:
                if k[0]<st:
                    start=0
                else:
                    start=k[0]-st
                if k[1]>ed:
                    end=ed+1-st
                else:
                    end=k[1]+1-st
                src_func[start:end] = ['24K MAGIC'] * (end-start)
        if 'del' in patch:
            dellist=[k for k in patch['del']]
            dellist.sort(key=lambda x:x[0],reverse=True)
            #for k in patch['del']:
            for k in dellist:
                #print k,patch['del'][k]
                src_func = src_func[0:k[0]-st] + patch['del'][k] + src_func[k[0]-st:]
        #Delete previously marked added lines.
        src_func = filter(lambda x:x <> '24K MAGIC',src_func)
    return src_func

def file_exits_in_commit(kernel,commit,filename):
    if kernel==None or commit == None or filename== None:
        print 'kernel,commit,filename:'
        print kernel,commit,filename
        return False
    commit =commit.strip()
    string1="cd "+kernel+";git cat-file -e "+commit+":"+filename+"&&echo exists"
    #print string1
    #print string1
    result=command(string1)[0]
    if "exists" in result:
        return True
    elif "fatal: Not a valid object name" in result:
        return False
    else:
        print "file_exits_in_commit strange return"
        print kernel,commit,filename
        print result
        exit()

def comparecontent(list1,list2):
    if len(list1) != len(list2):
        return False
    for i in range(len(list1)):
        if list1[i].strip() != list2[i].strip():
            return False
    return True

def comparefile(commit1,commit2,filename):
    kernel1="/home/zheng/fiberweiteng/msm"
    currentcommit1=get_currentcommit(kernel1)
    if commit1 != currentcommit1:
        checkoutcommit(kernel1,commit1)

    kernel2="/home/zheng/fiberweiteng/msm3"
    currentcommit2=get_currentcommit(kernel2)
    if commit2 != currentcommit2:
        checkoutcommit(kernel2,commit2)

    string1="diff /home/zheng/fiberweiteng/msm/"+filename+" /home/zheng/fiberweiteng/msm3/"+filename
    result=command(string1)
    if len(result) ==0:
        return True
    else:
        return False

def get_nocontext_patchinfo(patchinfo):
    nocontext_patchinfo={}
    for element in patchinfo:
        #print element
        filename=element[0]
        funcname=element[1]
        funcline=element[2]
        element2=(filename,funcname)
        nocontext_patchinfo[element2]={}
        nocontext_patchinfo[element2]['arg_cnt']=patchinfo[element]['arg_cnt']
        (st,ed)=patchinfo[element]['func_range']
        nocontext_patchinfo[element2]['func_range']=(st-funcline,ed-funcline)
        nocontext_patchinfo[element2]['type']=patchinfo[element]['type']
        nocontext_patchinfo[element2]['content']=patchinfo[element]['content']
        if 'add' in patchinfo[element]:
            nocontext_patchinfo[element2]['add']={}
            for (st,ed) in patchinfo[element]['add']:
                st2=st-funcline
                ed2=ed-funcline
                nocontext_patchinfo[element2]['add'][(st2,ed2)]=patchinfo[element]['add'][(st,ed)]
        if 'del' in patchinfo[element]:
            nocontext_patchinfo[element2]['del']={}
            for (st,ed) in patchinfo[element]['del']:
                st2=st-funcline
                ed2=ed-funcline
                nocontext_patchinfo[element2]['del'][(st2,ed2)]=patchinfo[element]['del'][(st,ed)]
    return nocontext_patchinfo


def get_context_patchinfo(kernel,nocontext_patchinfo):
    patchinfo={}
    for element in nocontext_patchinfo:
        #print element
        if type(element[0])==tuple:
            filename=element[0][0]
            funcname=element[0][1]
            funcline=element[1]
        else:
            filename=element[0]
            funcname=element[1]
            funcline=None
        PATH=kernel+"/"+filename
        #print "PATH: ",PATH
        with open(PATH,"r") as f:
            f_buf=f.readlines()
        try:
            (cur_func_inf,cur_func_inf_r)=src_parser_zz.build_func_map(f_buf)
        except:
            print "build_func_map error"
            print kernel," ",filename," ",funcname
            continue
        diff=None
        for funcinfo in cur_func_inf_r:
            funcname2=funcinfo[0]
            if funcname2==funcname:
                ((st,ed),arg_cnt)=cur_func_inf_r[funcinfo]
                (bst,bed)=nocontext_patchinfo[element]['func_range']
                #print "(st,ed): ",(st,ed)
                #print ed-st
                #print "(bst,bed): ",(bst,bed)
                #print bed-bst
                if funcline:
                    diff=st-funcline
                else:
                    diff=st
                if (ed-st)==(bed-bst):
                    break

        else:
            if not diff:
                print 'strange,dont find',filename,funcname,'in',kernel
                return None
            else:
                print 'length of function not the same'
                print kernel,filename,funcname
                print 'st:',st,'ed:',ed,'bst:',bst,'bed:',bed
        element2=(filename,funcname,st)
        patchinfo[element2]={}
        patchinfo[element2]['arg_cnt']=nocontext_patchinfo[element]['arg_cnt']
        patchinfo[element2]['func_range']=(st,ed)
        patchinfo[element2]['type']=nocontext_patchinfo[element]['type']
        if 'add' in nocontext_patchinfo[element]:
            patchinfo[element2]['add']={}
            for (st,ed) in nocontext_patchinfo[element]['add']:
                (st2,ed2)=(st+diff,ed+diff)
                patchinfo[element2]['add'][(st2,ed2)]=nocontext_patchinfo[element]['add'][(st,ed)]
        if 'del' in nocontext_patchinfo[element]:
            patchinfo[element2]['del']={}
            for (st,ed) in nocontext_patchinfo[element]['del']:
                (st2,ed2)=(st+diff,ed+diff)
                patchinfo[element2]['del'][(st2,ed2)]=nocontext_patchinfo[element]['del'][(st,ed)]
    
    return patchinfo

def get_context_patchinfo2(repo,commit,nocontext_patchinfo):
    patchinfo={}
    kernel = get_repopath(repo)
    for element in nocontext_patchinfo:
        if type(element[0])==tuple:
            filename=element[0][0]
            funcname=element[0][1]
            funcline=element[1]
        else:
            filename=element[0]
            funcname=element[1]
            funcline=None
        updatedfiles=checkoutfiles_commit(kernel,commit,set([filename]))
        if len(updatedfiles)==0:
            print 'updatefile fail for',kernel,commit,filename 
            continue
        PATH=kernel+"/"+filename
        with open(PATH,"r") as f:
            f_buf=f.readlines()
        try:
            (cur_func_inf,cur_func_inf_r)=src_parser_zz.build_func_map(f_buf)
        except:
            print "build_func_map error"
            print kernel," ",filename," ",funcname
            continue
        diff=None
        for funcinfo in cur_func_inf_r:
            funcname2=funcinfo[0]
            if funcname2==funcname:
                ((st,ed),arg_cnt)=cur_func_inf_r[funcinfo]
                (bst,bed)=nocontext_patchinfo[element]['func_range']
                if funcline:
                    diff=st-funcline
                else:
                    diff=st
                if (ed-st)==(bed-bst):
                    break
        else:
            if not diff:
                print 'strange,dont find',filename,funcname,'in',kernel
                return None
            else:
                print 'length of function not the same'
                print kernel,filename,funcname
                print 'st:',st,'ed:',ed,'bst:',bst,'bed:',bed
        element2=(filename,funcname,st)
        patchinfo[element2]={}
        patchinfo[element2]['arg_cnt']=nocontext_patchinfo[element]['arg_cnt']
        patchinfo[element2]['func_range']=(st,ed)
        patchinfo[element2]['type']=nocontext_patchinfo[element]['type']
        if 'add' in nocontext_patchinfo[element]:
            patchinfo[element2]['add']={}
            for (st,ed) in nocontext_patchinfo[element]['add']:
                (st2,ed2)=(st+diff,ed+diff)
                patchinfo[element2]['add'][(st2,ed2)]=nocontext_patchinfo[element]['add'][(st,ed)]
        if 'del' in nocontext_patchinfo[element]:
            patchinfo[element2]['del']={}
            for (st,ed) in nocontext_patchinfo[element]['del']:
                (st2,ed2)=(st+diff,ed+diff)
                patchinfo[element2]['del'][(st2,ed2)]=nocontext_patchinfo[element]['del'][(st,ed)]

    return patchinfo
#used to store file
def get_file(commit,kernel,filename,targetfilepath):
    string1="cd "+kernel+";git show "+commit+":"+filename+" > "+targetfilepath
    command(string1)
def switch_mon(month):
    switcher = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12
    }
    return switcher.get(month, None)

def get_commitDate(c_buf):
    for line in c_buf:
        if line.startswith("CommitDate"):
            #print line
            return line

def get_authorDate(c_buf):
    for line in c_buf:
        if line.startswith("AuthorDate"):
            return line

def get_author(c_buf):
    for line in c_buf:
        if line.startswith("Author:"):
            #linelist=line.split(" ")
            #author=linelist[-2]
            author=line[7:]
            author.strip()
            return author

def get_introduction(c_buf):
    for i in range(len(c_buf)):
        if "CommitDate" in c_buf[i]:
            break
    st=i+1
    for i in range(len(c_buf)):
        if "diff" in c_buf[i]:
            break
    ed=i-1
    content=c_buf[st:ed]
    return content

def get_simpleintroduction(c_buf):
    for i in range(len(c_buf)):
        if "CommitDate" in c_buf[i]:
            break
    st=i+1
    for i in range(st,len(c_buf)):
        if c_buf[i].strip()!="":
            if ":" in c_buf[i].strip() or 'Merge' in c_buf[i]:
                simpleintroduction=c_buf[i].strip()
                break
    else:
        return None
    return simpleintroduction
#Data example: "Date:   Wed Oct 7 10:55:41 2015 -0700\n"
#commitdate example "CommitDate: Mon Aug 8 17:29:06 2016 -0700\n"
#return value example:  datetime.datetime(2015, 10, 7, 10, 55, 41)
def get_time(Date):
    if not Date:
        return None
    Date=Date.split(" ")
    month=switch_mon(Date[2])
    day=int(Date[3])
    hour= int(Date[4].split(":")[0])
    minute=int(Date[4].split(":")[1])
    second=int(Date[4].split(":")[2])
    year=int(Date[5])
    time=datetime.datetime(year,month,day,hour,minute,second)
    return time

def get_date(Date):
    Date=Date.split(" ")
    month=switch_mon(Date[2])
    day=int(Date[3])
    hour= int(Date[4].split(":")[0])
    minute=int(Date[4].split(":")[1])
    second=int(Date[4].split(":")[2])
    year=int(Date[5])
    date=(year,month,day)
    return date

def get_commitversion(kernel,commitnumber):
    string1='cd '+kernel+';git show '+commitnumber+':Makefile'
    s_buf=command(string1)
    version=999
    patchlevel=999
    sublevel=999
    for line in s_buf:
        line=line[:-1]
        if line.startswith('VERSION'):
            version=line.split('= ')[1]
        elif line.startswith('PATCHLEVEL'):
            patchlevel=line.split('= ')[1]
        elif line.startswith('SUBLEVEL'):
            sublevel=line.split('= ')[1]
            break
    else:
        print 'dont find suitable version for',kernel,commitnumber
    return (int(version),int(patchlevel),int(sublevel))

def get_committime(kernel,commitnumber):
    string1="cd "+kernel+";git show --pretty=fuller "+commitnumber
    s_buf=command(string1)
    trim_lines(s_buf)
    commitDate=get_commitDate(s_buf)
    committime=get_time(commitDate)
    return committime
def get_commitdate(kernel,commitnumber):
    string1="cd "+kernel+";git show --pretty=fuller "+commitnumber
    s_buf=command(string1)
    trim_lines(s_buf)
    commitDate=get_commitDate(s_buf)
    #print commitDate
    if commitDate == None:
        print s_buf
    commitdate=get_date(commitDate)
    return commitdate
def get_commit_versionandtime(kernel,commitnumber):
    commitversion=get_commitversion(kernel,commitnumber)
    committime=get_committime(kernel,commitnumber)
    return (commitversion,committime)
    
def get_commitinformation(kernel,commitnumber):
    string1="cd "+kernel+";git show --pretty=fuller "+commitnumber
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    s_buf=p.stdout.readlines()
    trim_lines(s_buf)
    
    dicinfo={}
    commitDate=get_commitDate(s_buf)
    committime=get_time(commitDate)
    if not committime:
        print kernel,commitnumber,"committime is None"
    dicinfo['committime']=committime

    authorDate=get_authorDate(s_buf)
    authortime=get_time(authorDate)
    dicinfo['authortime']=authortime

    author=get_author(s_buf)
    introduction=get_introduction(s_buf)
    simpleintroduction=get_simpleintroduction(s_buf)
    dicinfo['author']=author
    dicinfo['introduction']=introduction
    dicinfo['simpleintroduction']=simpleintroduction
    return dicinfo

def get_commitlog(kernel,commitnumber):
    string1="cd "+kernel+";git log --oneline "+ commitnumber
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    commitlog=p.stdout.readlines()
    return commitlog

def get_candidate_commitnumbers(repository, file_name):
    candidates=set()
    #file may be in different paths
    #file_name="/"+file_name.split("/")[-1]
    #string1="cd "+repository+";git log --oneline --all -- -p -follow *"+file_name
    string1="cd "+repository+";git log --oneline --all -- -p -follow "+file_name
    #print string1
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    candidates_buf=p.stdout.readlines()
    for line in candidates_buf:
        #if line.startswith("commit"):
        #    commitnumber=line.split(" ")[1]
        #    if commitnumber.endswith("\n"):
        #        commitnumber=commitnumber[:-1]
        commitnumber=line[:12]
        candidates.add(commitnumber)
    #print "for file ",file_name," candidates: ",str(candidates)
    return candidates

def get_candidate_commitnumbers2(repository, file_name):
    candidates=set()
    string1="cd "+repository+";git log --oneline -- -p -follow "+file_name
    #print string1
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    candidates_buf=p.stdout.readlines()
    newfilename=file_name
    if len(candidates_buf) ==0:
        #file may be in different paths
        file_name=file_name.split("/")[-1]
        string1="cd "+repository+";find . -name "+file_name
        resultlist=command(string1)
        if len(resultlist)==1:
            newfilename=resultlist[0][:-1]
            string1="cd "+repository+";git log --oneline -- -p -follow "+newfilename
            p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            candidates_buf=p.stdout.readlines()
        elif len(resultlist) >1:
            print 'multiple substitution'
            newfilename=resultlist[0][:-1]
            string1="cd "+repository+";git log --oneline -- -p -follow "+newfilename
            p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            candidates_buf=p.stdout.readlines()
        elif len(resultlist)==0:
            string1="cd "+repository+";git log --oneline -- -p -follow */"+file_name
            p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            candidates_buf=p.stdout.readlines()
            if len(candidates_buf)==0:
                return set([]),file_name
            newfilename=get_newfilename(repository,candidates_buf,file_name)
    for line in candidates_buf:
        commitnumber=line[:12]
        candidates.add(commitnumber)
    #print "for file ",file_name," candidates: ",str(candidates)
    return candidates,newfilename

#main branch commits
def get_candidate_commitnumbers3(repository, branch,filename=None):
    candidates=[]
    if filename:
        string1="cd "+repository+";git log --oneline --first-parent "+branch+' -- -p '+filename
    else:
        string1="cd "+repository+";git log --oneline --first-parent "+branch
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    candidates_buf=p.stdout.readlines()
    candidates_buf.reverse()
    for line in candidates_buf:
        commitnumber=line[:12]
        candidates+= [commitnumber]
    return candidates

#given some commits that an oldname ,find newfilename in the commits
def get_newfilename(repository,candidates_buf,oldfilename):
    print 'oldfilename:',oldfilename
    for line in candidates_buf:
        commitnumber=line[:12]
        print repository,commitnumber
        filenames=get_filenames_commit(repository,commitnumber)
        for (fn,fp) in filenames:
            #print (fn,fp)
            if fp==None:
                continue
            if oldfilename in fp:
                return fp
    print 'in get_newfilename: strange, dont get new function'
    return oldfilename

#in some commits one function is replaced with another function
def get_newfuncname(repopath,commit,filename1,filename2,prevfuncname):
    #print 'get_newfuncname'
    #print repopath,commit,filename1,filename2,prevfuncname
    prevcommit=get_previouscommit(repopath,commit)
    string1='cd '+repopath+';git diff '+prevcommit+':'+filename1+' '+commit+':'+filename2
    p_buf=command(string1)
    string1='cd '+repopath+';git show '+prevcommit+':'+filename1
    file_buf1=command(string1)
    string1='cd '+repopath+';git show '+commit+':'+filename2
    file_buf2=command(string1)
    del_add_list=get_corresponding_del_adds_1(p_buf)
    #print del_add_list
    (cur_func_inf,cur_func_inf_r)=src_parser_zz.build_func_map(file_buf1)
    for (funcname,funcline) in cur_func_inf_r:
        if funcname==prevfuncname:
            prevfuncline=funcline
            #print 'prevfuncline',prevfuncline
            break
    else:
        print 'strange prevfuncname',prevfuncname,' not in prevcommit',prevcommit
        return None
    for ((oldst,olded),newrange) in del_add_list:
        if oldst==None:
            continue
        if prevfuncline in range(oldst,olded+1):
            if newrange==None:
                #print prevfuncname,' is deleted in ',commit
                return None
            else:
                (newst,newed)=newrange
                break
    else:
        print 'strange, deleted function not in del_add_list'
        print commit,filename1,prevfuncname,prevfuncline
        #print del_add_list
        return None
    (cur_func_inf,cur_func_inf_r)=src_parser_zz.build_func_map(file_buf2)
    for (funcname,funcline) in cur_func_inf_r:
        if funcline in range(newst,newed+1):
            newfuncname=funcname
            #print 'newfuncname:',newfuncname
            return newfuncname
        #print 'dont find new function'
    return None


#given a commit and a repo branch, try to get the corresponding commit in main branch.
def get_maincommit(repopath,branch,commit,filename=None):
    candidate_commitnumberslist=get_candidate_commitnumbers3(repopath,branch)
    if commit in candidate_commitnumberslist:
        return commit
    string1='cd '+repopath+';git find-merge '+commit+' '+branch
    result=command(string1)
    maincommit=result[0][:12]
    #print 'maincommit:',maincommit
    return maincommit
    #aftercommits=get_aftercommits(repopath,branch,commit)
    #print 'size of aftercommits:',len(aftercommits)
    #for maincommit in candidate_commitnumberslist:
        #commitlog=get_commitlog(repopath,maincommit)
        #if any(commit in line for line in commitlog):
        #if maincommit in aftercommits:
         #   return maincommit
    print 'strange not find the main commit for ',repopath,commit

def get_earlistmaincommit(targetrepopath,targetbranch,notecandidates):
    if len(notecandidates)==1:
        return notecandidates[0]
    notecandidates=list(set(notecandidates))
    #order is from old to new
    candidate_commitnumberslist=get_candidate_commitnumbers3(targetrepopath,targetbranch)
    for commit in candidate_commitnumberslist:
        if commit in notecandidates:
            return commit

def get_kernelversion(repopath,commit):
    string1='cd '+repopath+';git show '+commit+':Makefile'
    result=command(string1)
    SUBLEVEL=None
    for line in result:
        line=line[:-1]
        if line.startswith('VERSION ='):
            version=int(line.split(' ')[-1])
        elif line.startswith('PATCHLEVEL ='):
            PATCHLEVEL=int(line.split(' ')[-1])
        elif line.startswith('SUBLEVEL'):
            SUBLEVEL=int(line.split(' ')[-1])
        if SUBLEVEL:
            break
    return (version,PATCHLEVEL,SUBLEVEL)

def get_aftercommits(repopath,branch,commit,filename=None):
    aftercommits=[]
    if filename:
        string1='cd '+repopath+';git log --oneline --reverse --ancestry-path '+commit+'^..'+branch+' -- -p '+filename
    else:
        string1='cd '+repopath+';git log --oneline --reverse --ancestry-path '+commit+'^..'+branch
    s_buf=command(string1)
    for line in s_buf:
        commit=line[:12]
        aftercommits += [commit]
    return aftercommits

def command(string1):
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result=p.stdout.readlines()
    return result
#previous commit that contains one commit in totalpatchcommits
def get_prevcommitlist(commit,totalpatchcommits,kernel):
    #kernel="/home/zheng/fiberweiteng/msm"
    commitlog=get_commitlog(kernel,commit)
    commitlist=[]
    for line in commitlog[1:]:
        commitnumber=line[:12]
        if commitnumber in totalpatchcommits:
            commitlist += [commitnumber]
            if len(commitlist) >10:
                break
    if len(commitlist) > 0:
        return commitlist
    return None

def get_previouscommits_formerge(kernel,commit):
    string1="cd "+kernel+";git show -1 "+commit
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p_buf=p.stdout.readlines()
    for line in p_buf:
        if line.startswith("Merge"):
            break
    line=line[:-1]
    linelist=line.split(" ")
    (commit1,commit2)=(linelist[1],linelist[2])
    return (commit1,commit2)
#the nearest previous commit
def get_previouscommit(kernel,commit):
    string1="cd "+kernel+";git show "+commit
    p_buf=command(string1)
    if any(line.startswith('Merge:') for line in p_buf):
        for line in p_buf:
            if line.startswith("Merge:"):
                break
        prevcommit=line.split(" ")[1]
    else:
        string1="cd "+kernel+";git log --oneline "+commit
        p_buf=command(string1)
        prevcommit=p_buf[1][:12]
    return prevcommit

def get_currentcommit(kernel):
    string1="cd "+kernel+";git log -2 --oneline "
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p_buf=p.stdout.readlines()
    commit1=p_buf[0][:12]
    return commit1

def get_diffcommit(prevcommit,commit,kernel):
    #kernel="/home/zheng/fiberweiteng/msm"
    '''
    string1="cd "+kernel+";git branch tmp "+commit+"&&git checkout tmp; git reset --soft "+prevcommit+";git commit -m \'diff\' "
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p_buf=p.stdout.readlines()

    string1="cd "+kernel+";git show "
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    patch_buf=p.stdout.readlines()
    trim_lines(patch_buf)

    string1="cd "+kernel+";git checkout -f "+prevcommit+";git branch -D tmp"
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p_buf=p.stdout.readlines()
    '''
    string1='cd '+kernel+';git diff '+prevcommit+' '+commit
    p_buf=commmand(string1)
    return  p_buf

def get_commit_content(kernel,commit):
    #print 'get_commit_content',kernel,commit
    string1="cd "+kernel+";git show "+commit
    p_buf=command(string1)
    if any(line.startswith('Merge') for line in p_buf):
        for line in p_buf:
            if line.startswith('Merge'):
                oldcommit=line.split(" ")[1]
                break
        string1="cd "+kernel+"; git diff "+oldcommit+" "+commit
        p_buf=command(string1)
    trim_lines(p_buf)
    return p_buf

def get_commit_functions(kernel,commit,targetfunction=None):
    p_buf=get_commit_content(kernel,commit)
    changelines=get_commit_changelines(p_buf)
    #checkoutcommit(kernel,commit)
    functionset=set()
    for filename in changelines:
        if targetfunction:
            if filename!=targetfunction:
                continue
        #print filename
        #filepath=kernel+"/"+filename
        #with open(filepath,"r") as f:
        #    f_buf=f.readlines()
        #print "\n".join(f_buf)
        string1='cd '+kernel+';git show '+commit+':'+filename
        f_buf=command(string1)
        changeset=changelines[filename]
        try:
            (cur_func_inf,cur_func_inf_r)=src_parser_zz.build_func_map(f_buf)
        except:
            print "build_func_map fail! in get_commit_functions"
            print commit
            print kernel, " ",filename
            return functionset
        for (funcname,funcline) in cur_func_inf_r:
            #print (funcname,funcline)
            (st,ed)=cur_func_inf_r[(funcname,funcline)][0]
            #print (st,ed)
            lineset=set(range(st,ed+1))
            #print lineset
            if lineset.intersection(changeset):
                #print "intersection"
                functionset.add(funcname)
    return functionset

#return a dictionary {filename:[functions]} that contains all functions changed in this commit
def get_commit_functions2(kernel,commit):
    p_buf=get_commit_content(kernel,commit)
    changelines=get_commit_changelines(p_buf)
    #checkoutcommit(kernel,commit)
    functiondic={}
    for filename in changelines:
        #print filename
        functiondic[filename]=[]
        #filepath=kernel+"/"+filename
        #with open(filepath,"r") as f:
        #    f_buf=f.readlines()
        #print "\n".join(f_buf)
        string1='cd '+kernel+';git show '+commit+':'+filename
        f_buf=command(string1)
        changeset=changelines[filename]
        try:
            (cur_func_inf,cur_func_inf_r)=src_parser_zz.build_func_map(f_buf)
        except:
            print "build_func_map fail! in get_commit_functions"
            print commit
            print kernel, " ",filename
            return functiondic
        for (funcname,funcline) in cur_func_inf_r:
            #print (funcname,funcline)
            (st,ed)=cur_func_inf_r[(funcname,funcline)][0]
            #print (st,ed)
            lineset=set(range(st,ed+1))
            #print lineset
            if lineset.intersection(changeset):
                #print "intersection"
                functiondic[filename] += [funcname]
    return functiondic

#get all functions in specific file in specific commit
def get_commitfile_functions(kernel,commit,filename):
    functions=set()
    string1='cd '+kernel+';git show '+commit+':'+filename
    f_buf=command(string1)
    try:
        (cur_func_inf,cur_func_inf_r)=src_parser_zz.build_func_map(f_buf)
    except:
        print "build_func_map fail! in get_commitfile_functions"
        print kernel,commit,filename
        return functions
    for (funcname,funcline) in cur_func_inf_r:
        functions.add(funcname)
    return functions

def get_commit_changelines(p_buf):
    changelines={}
    diff_index = [i for i in range(len(p_buf)) if p_buf[i].startswith('diff')] + [len(p_buf)]
    for i in range(len(diff_index)-1):
        get_commit_changelines2(changelines,diff_index[i],diff_index[i+1],p_buf)

    return changelines

def get_commit_changelines2(changelines,st,ed,p_buf):
    fp=None
    fn=None
    for i in range(st,ed):
        if fp is not None and fn is not None:
            break
        if p_buf[i].startswith('---'):
            fn = p_buf[i][6:]
        elif p_buf[i].startswith('+++'):
            fp = p_buf[i][6:]
        elif p_buf[i].startswith('rename from'):
            fn = p_buf[i][12:]
        elif p_buf[i].startswith('rename to'):
            fp = p_buf[i][10:]
    if fp is None or fn is None:
        return
    elif fp=='ev/null':
        return
    filename=fp
    changelines[filename]=set()
    log=False
    for line in p_buf[st:ed]:
        if line.startswith("@@"):
            log=True
            #print line
            try:
                linenumber=int(line.split("+")[1].split(",")[0])-1
            except:
                #print line
                log=False
                continue
        elif line.startswith("-"):
            if log:
                changelines[filename].add((linenumber+1))
        else:
            if log:
                linenumber=linenumber+1
                if line.startswith("+"):
                    changelines[filename].add(linenumber)

    if len(changelines[filename])==0:
        del changelines[filename]

def toolong_filter(commitcandidate):
    string1="cd ../msm2;git show "+commitcandidate
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    s_buf=p.stdout.readlines()
    if len(s_buf) >100000:
        with open('toolongcommits405','a') as f:
            f.write(str(commitcandidate)+"\n")
            return (commitcandidate, False)
    return (commitcandidate,True)


def is_patch_commit((commitcandidate,p_buf,repopath)):
    #print "is_patch_commit starts for ",commitcandidate[:12]
    diff_index = [i for i in range(len(p_buf)) if p_buf[i].startswith('diff')] + [len(p_buf)]
    notmatch=0
    strictmatch=0
    fuzzmatch=0
    string1="cd "+repopath+";git show "+commitcandidate
    #print string1
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    s_buf=p.stdout.readlines()
    for i in range(len(diff_index)-1):
        (localnotmatch, localstrictmatch, localfuzzmatch) = get_commitnumber_2(p_buf,diff_index[i],diff_index[i+1],s_buf)
        notmatch = notmatch+localnotmatch
        strictmatch = strictmatch+localstrictmatch
        fuzzmatch = fuzzmatch+localfuzzmatch
    #print "patch_commit complete for ",commitcandidate
    return (commitcandidate, (notmatch,strictmatch,fuzzmatch))

def get_commitnumber_2(p_buf,st,ed,s_buf):
    at_index = [i for i in range(st,ed) if p_buf[i].startswith('@@')] + [ed]
    notmatch=strictmatch=fuzzmatch=0
    for i in range(len(at_index)-1):
        (localnotmatch,localstrictmatch,localfuzzmatch)=get_commitnumber_3(p_buf,at_index[i],at_index[i+1],s_buf)
        notmatch=notmatch+localnotmatch
        strictmatch=strictmatch+localstrictmatch
        fuzzmatch=fuzzmatch+localfuzzmatch
    return (notmatch,strictmatch,fuzzmatch)

#for each @@
def get_commitnumber_3(p_buf,st,ed,s_buf):
    for i in range(st,ed):
        if p_buf[i].startswith('@@'):
            head = p_buf[i].split('@@')[-1][1:]
            break
    else:
        return
    p_st = i + 1
    c_index = []
    i = p_st
    while i < ed:
        if p_buf[i][0] in ('+','-'):
            j = i + 1
            while j < len(p_buf) and p_buf[j][0] in ('+','-'):
                j += 1
            c_index.append((i,j-1))
            i = j
        else:
            i += 1
    c_index = [(p_st-1,p_st-1)] + c_index + [(ed,ed)]
    prev_line = 0
    localnotmatch=0
    localstrictmatch=0
    localfuzzmatch=0
    for i in range(1,len(c_index)-1):
        t1 = c_index[i][0]
        t2 = c_index[i][1]
        t0 = c_index[i-1][1] + 1
        t3 = c_index[i+1][0] - 1
        if any("Copyright" in line for line in p_buf[t1:t2+1]):
            continue
        #global notmatch, fuzzmatch, strictmatch
        commitnumber=get_commitnumber_4(head,p_buf[t1:t2+1],p_buf[t0:t1],p_buf[t2+1:t3+1],s_buf)
        if commitnumber is None:
            #print 'p_buf[t1:t2+1]:'
            #print p_buf[t1:t2+1]
            commitnumber=get_commitnumber_4_fuzz(head,p_buf[t1:t2+1],p_buf[t0:t1],p_buf[t2+1:t3+1],s_buf)
            if commitnumber is None:
                localnotmatch += 1
            else:
                localfuzzmatch +=1
                #print "fuzzmatch is ", fuzzmatch
                #commitnumbers.add(commitnumber)
        else:
            localstrictmatch +=1

    return (localnotmatch,localstrictmatch,localfuzzmatch)

#locate per "change"
def get_commitnumber_4(head,clines,blines,alines,s_buf):
    i=0
    def _cmp(lines,i):
        if not lines:
            return True
        for j in range(len(lines)):
            re_space = '[\t ]*'
            if i + j > len(s_buf) - 1:
                return False
            re_space = '[\t ]*'
            if re.sub(re_space,' ',lines[j]).strip() <> re.sub(re_space,' ',s_buf[i+j]).strip():
                return False
        return True
    while i < len(s_buf):
        j = i
        if _cmp(blines,i):
            #print "blines match!"
            i += len(blines)
            if _cmp(clines,i):
                #print "clines match!"
                i += len(clines)
                if _cmp(alines,i):
                    #print "alines match! strict matched
                    return True
                    k=i-1
                else:
                    i=j+1
                    continue
            else:
                i=j+1
                continue
        else:
            i += 1
    return None
def get_commitnumber_4_fuzz(head,clines,blines,alines,s_buf):
    def _cmp(lines,i):
        if not lines:
            return True
        for j in range(len(lines)):
            re_space = '[\t ]*'
            if i + j > len(s_buf) - 1:
                return False
            re_space = '[\t ]*'
            if re.sub(re_space,' ',lines[j]).strip() <> re.sub(re_space,' ',s_buf[i+j]).strip():
                return False
        return True
    def _transfer(lines,k):
        result=''
        re_space = '[\t ]*'
        if k>len(lines):
            k=len(lines)
        for i in range(k):
            result=result+re.sub(re_space,' ',lines[i]).strip()
        return result
    count=0
    targetlines=[]
    scores=[]
    commitnumbers=[]
    i=0
    bline=_transfer(blines,len(blines))
    aline=_transfer(alines,len(alines))
    while i < len(s_buf):
        if _cmp(clines,i):
            #print "clines match!"
            return True
        else:
            i +=1
    return None

def get_cve_patchinfo(cve):
    PATH="/data/zheng/patchcommits/"+cve+"/patchinfo_pickle"
    pickle_in=open(PATH,"rb")
    cve_patchinfo=pickle.load(pickle_in)
    return cve_patchinfo

def store_cve_patchinfo(cve,cve_patchinfo):
    PATH="/data/zheng/patchcommits/"+cve+"/patchinfo_pickle"
    pickle_out=open(PATH,"wb")
    pickle.dump(cve_patchinfo,pickle_out)

def print_patchinfo(patchinfo,content=False):
    for element in patchinfo:
        print element
        for key in patchinfo[element]:
            if not content:
                if key=="content":
                    continue
            print key
            print patchinfo[element][key]

def delete_patchinfo_element(cve,commit):
    cve_patchinfo=get_cve_patchinfo(cve)
    del cve_patchinfo[commit]
    store_cve_patchinfo(cve,cve_patchinfo)

def print_patchinfo_cve(cve,commit,content=False):
    cve_patchinfo=get_cve_patchinfo(cve)
    patchinfo=cve_patchinfo[commit]
    print_patchinfo(patchinfo,content)

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

#don't get commit number before strict commit generation methods
#may be before patch or not get the correct commit
patchlist = [
        ("CVE-2017-7308","/home/zheng/fiberweiteng/linux","2b6867c2ce76",["57a3071cfe7e"]),
        ("CVE-2017-0622","/home/zheng/fiberweiteng/msm-3.18","40efa25345003a96db34effbd23ed39530b3ac10",['210d11c9d2ba','cbca5fe1340b']),
        ('CVE-2015-8950','/home/zheng/fiberweiteng/msm-3.10','6e2c437a2d0a85d90d3db85a7471f99764f7bbf8',[]),
        ('CVE-2017-14497','/home/zheng/fiberweiteng/linux','edbd58be15a957f6a760c4a514cd475217eb97fd',[]),
        ('CVE-2016-3858','/home/zheng/fiberweiteng/msm-3.10','0c148b9a9028c566eac680f19e5d664b483cdee3',['fa9b8a9c6fcf']),
        ('CVE-2016-6694','/home/zheng/fiberweiteng/msm-3.18','961e38553aae8ba9b1af77c7a49acfbb7b0b6f62',[]),
        ('CVE-2016-5856','/home/zheng/fiberweiteng/msm-4.4','0c0622914ba53cdcb6e79e85f64bfdf7762c0368',['5bb47425a4a0']),
        ('CVE-2016-7912','/home/zheng/fiberweiteng/linux','38740a5b87d53ceb89eb2c970150f6e94e00373a',['617229a3e940','9d6fd2c3e9fc',]),
        ('CVE-2016-6696','/home/zheng/fiberweiteng/msm-3.18','c3c9341bfdf93606983f893a086cb33a487306e5',[]),
        #CVE-2014-9791:todo
        ('CVE-2014-9791','/home/zheng/msm','9aabfc9e7775abbbcf534cdecccc4f12ee423b27',[]),
        ('CVE-2016-5867','/home/zheng/fiberweiteng/msm-3.18','065360da7147003aed8f59782b7652d565f56be5',[]),
        ('CVE-2016-7917','/home/zheng/fiberweiteng/linux','c58d6c93680f28ac58984af61d0a7ebf4319c241',[]),
        ('CVE-2016-5853','/home/zheng/fiberweiteng/msm-4.4','a8f3b894de319718aecfc2ce9c691514696805be',[]),
        ('CVE-2017-17770','/home/zheng/fiberweiteng/msm-3.18','284f963af0accf7f921ec10e23acafd71c3a724b',[]),
        ('CVE-2017-15115','/home/zheng/fiberweiteng/linux','df80cd9b28b9ebaa284a41df611dbf3a2d05ca74',[]),
        ('CVE-2016-10232','/home/zheng/fiberweiteng/msm-3.10','21e0ead58e47798567d846b84f16f89cf69a57ae',['749544c05f92','2825b5126379']),
        ('CVE-2016-5857','/home/zheng/fiberweiteng/msm-4.4','d9d2c405d46ca27b25ed55a8dbd02bd1e633e2d5',[]),
        ('CVE-2017-8250','/home/zheng/fiberweiteng/msm-3.18','9be5b16de622c2426408425e3df29e945cd21d37',[]),
        ('CVE-2017-9698','/home/zheng/fiberweiteng/msm-4.4','79492490423bc369da4ded113dca7f5a5b38e656',[]),
        #CVE-2016-5855 todo
        ('CVE-2016-5855','/home/zheng/fiberweiteng/msm-4.4','a5edb54e93ba85719091fe2bc426d75fa7059834',[]),
        #CVE-2016-5863 todo
        ('CVE-2016-5863','/home/zheng/fiberweiteng/msm-3.18','daf0acd54a6a80de227baef9a06285e4aa5f8c93',[]),
        ('CVE-2016-5854','/home/zheng/fiberweiteng/msm-4.4','28d23d4d7999f683b27b6e0c489635265b67a4c9',['5bb47425a4a0']),
        ('CVE-2017-6346','/home/zheng/fiberweiteng/linux','d199fab63c11998a602205f7ee7ff7c05c97164b',['e02670164964']),
        ('CVE-2016-8483','/home/zheng/fiberweiteng/msm-3.18','6997dcb7ade1315474855821e64782205cb0b53a',['e8038f7fa640','03c325704806']),
        ('CVE-2016-6693','/home/zheng/fiberweiteng/msm-3.18','ac328eb631fa74a63d5d2583e6bfeeb5a7a2df65',[]),
        ('CVE-2017-7371','/home/zheng/fiberweiteng/msm-4.4','e02e63b8014f7a0a5ea17a5196fb4ef1283fd1fd',[]),
        ('CVE-2017-7495','/home/zheng/fiberweiteng/linux','06bd3c36a733ac27962fea7d6f47168841376824',['f257f11aff21']),
        ('CVE-2016-3906','/home/zheng/fiberweiteng/msm-3.18','b333d32745fec4fb1098ee1a03d4425f3c1b4c2e',[]),
        ('CVE-2016-5345','/home/zheng/fiberweiteng/msm-3.18','67118716a2933f6f30a25ea7e3946569a8b191c6',[]),
        ('CVE-2017-9150','/home/zheng/fiberweiteng/linux','0d0e57697f162da4aa218b5feafe614fb666db07',[]),
        ('CVE-2017-8259','/home/zheng/fiberweiteng/msm-4.4','68020103af00280393da10039b968c95d68e526c',['ec22f61938ea']),
        ('CVE-2016-5858','/home/zheng/fiberweiteng/msm-3.18','3154eb1d263b9c3eab2c9fa8ebe498390bf5d711',[]),
        ('CVE-2017-9716','/home/zheng/fiberweiteng/msm-4.4','aab2cc06db7cb6c7589bef71e65b5acfa58adc33',[]),
        ('CVE-2016-6695','/home/zheng/fiberweiteng/msm-3.18','c319c2b0926d1ea5edb4d0778d88bd3ce37c4b95',[]),
        ('CVE-2017-7372','/home/zheng/fiberweiteng/msm-3.18','1806be003731d6d4be55e5b940d14ab772839e13',['952619c0ff77']),
        ('CVE-2017-11032','/home/zheng/fiberweiteng/msm-3.18','2720294757d0ad5294283c15dc837852f7b2329a',[]),
        ('CVE-2016-5859','/home/zheng/fiberweiteng/msm-3.18','97fdb441a9fb330a76245e473bc1a2155c809ebe',[]),
        ]

#get the commit number before, but be filtered by mistake / not generation successfully
patchlist2=[
        #notpatchinfogeneration due to the different of context(have been solved)
        ('CVE-2016-8655','/home/zheng/fiberweiteng/linux','84ac7260236a49c79eede91617700174c2c19b0c',['5c120b79dd66','f2ce502f8665','1aaa5ced5fc4','4ca2038afc0e','1699d293ac71','6f18029938f7','f9583f47bb99','5fe9e0d31cfb','14670e490ff9','617b89aabca2','6d39cdc06df6','13a77b371ab8']),
        ('CVE-2016-7916','/home/zheng/fiberweiteng/linux','8148a73c9901a8794a50f950083c00ccf97d43b3',['72d52919f2fe','62cb8fcb45f2']),
        ('CVE-2017-15833','/home/zheng/fiberweiteng/msm-3.10','51ce6aec73d80e1f1fcc9c7fa71e9c2fcbdbc0fd',['c4d087edf415','2c32d7aba9fb']),
        ('CVE-2017-6214','/home/zheng/fiberweiteng/linux','ccf7abb93af09ad0868ae9033d1ca8108bdaec82',['5ccd632a9888']),
        ('CVE-2017-8890','/home/zheng/fiberweiteng/linux','657831ffc38e30092a2d5f03d385d710eb88b09a',['c3addaf2dd0a']),
        ('CVE-2015-9004','/home/zheng/fiberweiteng/linux','c3c87e770458aa004bd7ed3f29945ff436fd6511',['7b60bfb86dd4','9226fe04970d',]),
        ('CVE-2017-7308','/home/zheng/fiberweiteng/linux','2b6867c2ce76c596676bec7d2d525af525fdc6e2',['57a3071cfe7e']),
        #unknown(patch commit pass filter before but not generate patchinfo)
        ('CVE-2017-0632','/home/zheng/fiberweiteng/msm-3.10','970d6933e53c1f7ca8c8b67f49147b18505c3b8f',['4272ede58950','b9de234bbbd1']),
        ('CVE-2015-5706','/home/zheng/fiberweiteng/linux','f15133df088ecadd141ea1907f2c96df67c729f0',[]),
        ('CVE-2016-10287','/home/zheng/fiberweiteng/msm-4.4','937bc9e644180e258c68662095861803f7ba4ded',['885cfc7f60d8',]),
        #not pass patch commit filter before
        ('CVE-2017-11016','/home/zheng/fiberweiteng/msm-3.18','6bb0d13bbd9df966a9a2b801e5204937285413fe',[]),
        ('CVE-2016-9754','/home/zheng/fiberweiteng/linux','59643d1535eb220668692a5359de22545af579f6',[]),
        ('CVE-2017-5970','/home/zheng/fiberweiteng/linux','34b2cef20f19c87999fff3da4071e66937db9644',[]),
        ('CVE-2017-11019','/home/zheng/fiberweiteng/msm-3.18','a2e451a1e1d973709ccd062c9aade669cd0daca4',['78d5baecd47a']),
        ('CVE-2016-10230','/home/zheng/fiberweiteng/msm-3.18','bd9a8fc6d7f6bd1a0b936994630006de450df657',[]),
        #CVE-2014-8709 is it kernel cve?
        ('CVE-2014-8709','/home/zheng/fiberweiteng/linux','338f977f4eb441e69bb9a46eaa0ac715c931a67f',[]),
        ('CVE-2016-10229','/home/zheng/fiberweiteng/linux','197c949e7798fbf28cfadc69d9ca0c2abbf93191',['bd80b5e2a8b6','ada5339f7f59','392bc723f354','c89a37dcb4a2','f6432eda149e','e48d11afd27c','a35b0752b537','e93726cc7ec4']),
        ('CVE-2016-9793','/home/zheng/fiberweiteng/linux','b98b0bc8c431e3ceb4b26b0dfc8db509518fb290',[]),
        ('CVE-2016-6725','/home/zheng/fiberweiteng/msm-3.10','cc95d644ee8a043f2883d65dda20e16f95041de3',[]),
        ('CVE-2017-0611','/home/zheng/fiberweiteng/msm-4.4','1aa5df9246557a98181f03e98530ffd509b954c8',[]),
        ]

#don't have the same filename and funcname in AOSP and patchinfos generated before
patchlist3=[
        ('CVE-2014-9789','/home/zheng/msm','5720ed5c3a786e3ba0a2428ac45da5d7ec996b4e',['6c5bff96ab0e',]),
        ('CVE-2016-5864','/home/zheng/fiberweiteng/msm-4.4','cbc21ceb69cb7bca0643423a7ca982abce3ce50a',[]),
        #cve 2014-9322 assembly code patch
        #('CVE-2014-9322','','',[]),
        ('CVE-2017-15820','/home/zheng/fiberweiteng/msm-4.4','7599c5b7d87248b4772d6c4b70ccb922704c8095',[]),
        ('CVE-2016-0723','/home/zheng/fiberweiteng/linux','5c17c861a357e9458001f021a7afa7aab9937439',['e2a8da010698']),
        #CVE-2017-0619: no patch commits
        #('CVE-2017-0619','/home/zheng/fiberweiteng/msm-3.14','72f67b29a9c5e6e8d3c34751600c749c5f5e13e1',[]),
        #todo ('CVE-2014-9777','/home/zheng/msm','17bfaf64ad503d2e6607d2d3e0956f25bf07eb43',['9dd09037eea2']),
        ('CVE-2014-1739','/home/zheng/fiberweiteng/linux','e6a623460e5fc960ac3ee9f946d3106233fd28d8',[]),
        ('CVE-2017-7373','/home/zheng/fiberweiteng/msm-4.4','e5eb0d3aa6fe62ee437a2269a1802b1a72f61b75',[]),
        ('CVE-2017-11075','/home/zheng/fiberweiteng/msm-4.4','7a07165c62926e899b710e1fed31532f31797dd5',[]),
        ('CVE-2017-15537','/home/zheng/fiberweiteng/linux','814fb7bb7db5433757d76f4c4502c96fc53b0b5e',['5e9b07f30d21','d25fea066a8e']),
        ('CVE-2017-15826','/home/zheng/fiberweiteng/msm-4.4','5ac3e9d038a7ee7edf77dde2dffae6f8ba528848',[]),
        ('CVE-2016-10286','/home/zheng/fiberweiteng/msm-4.4','5d30a3d0dc04916ddfb972bfc52f8e636642f999',[]),
        ('CVE-2017-18061','/home/zheng/fiberweiteng/msm-3.18','b65cf2a007e88fe86dbd6d3269682fc585a4130f',[]),
        ('CVE-2017-8277','/home/zheng/fiberweiteng/msm-4.4','c9a6f09f1030cec591df837622cb54bbb2d24ddc',[]),
        #CVE-2017-10996 not a cve in function
        #('CVE-2017-10996','/home/zheng/fiberweiteng/msm-3.18','9f261e5dfe101bbe35043822a89bffa78e080b3b',[]),
        #CVE-2017-15845 not a cve in function
        #('CVE-2017-15845','/home/zheng/fiberweiteng/msm-3.10','d39f7f0663394e1e863090108a80946b90236112',[]),
        #CVE-2017-15829 too many fuzz commits todo
        ('CVE-2017-15829','/home/zheng/fiberweiteng/msm-4.4','c1b60e554e158bfcf6932ed2c543c309236e0f79',[]),
        ('CVE-2016-5862','/home/zheng/fiberweiteng/msm-4.4','4199451e83729a3add781eeafaee32994ff65b04',[]),
        ('CVE-2014-9792','/home/zheng/fiberweiteng/msm-3.10','a3e3dd9fc0a2699ae053ffd3efb52cdc73ad94cd',[]),
        #CVE-2014-9801 no patch commits
        ('CVE-2014-9801','/home/zheng/lk','cf8f5a105bafda906ccb7f149d1a5b8564ce20c0',[]),
        ('CVE-2014-0206','/home/zheng/fiberweiteng/linux','d36db46c2cba973557eb6138d22210c4e0cf17d6',[]),

        ('CVE-2016-10233','/home/zheng/msm','d793c6d91ecba2a1fd206ad47a4fd408d290addf',[]),
        ('CVE-2014-3145','/home/zheng/fiberweiteng/linux','314760e66c35c8ffa51b4c4ca6948d207e783079',[]),
        ('CVE-2016-3855','/home/zheng/fiberweiteng/msm-3.10','ab3f46119ca10de87a11fe966b0723c48f27acd4',[]),
        #not a patch in function ('CVE-2015-8967','/home/zheng/fiberweiteng/linux','c623b33b4e9599c6ac5076f7db7369eb9869aa04',[]),
        ('CVE-2016-8434','/home/zheng/fiberweiteng/msm-3.14','3e3866a5fced40ccf9ca442675cf915961efe4d9',['65da178d9f37','337876c163ad','a5205bde05a9','5103db813f92','a419c79089f4',]),
        ('CVE-2017-7541','/home/zheng/fiberweiteng/linux','8f44c9a41386729fea410e688959ddaa9d51be7c',[]),
        ('CVE-2016-0801','/home/zheng/fiberweiteng/msm','68cdc8df1cb6622980b791ce03e99c255c9888af',['14c4d12de6b3','3386589ec2aa','0334cdac903e','453d319e7733','0c1eb722be85','75a7e7a63ea1']),
        ('CVE-2018-3563','/home/zheng/fiberweiteng/msm-4.4','c643a15d73b3fb6329b002662e72dfa96acfdb8a',['06ec48026b1b','9e91098f9bd6','d92ee1f29ba6','0b63e938e86c','f6214fdc04e8','04478d205743','4bb61c2a112e','8de1c660a302','0bfac4fe818a','ea38cad846de','2c099534570b']),
        ('CVE-2016-5340','/home/zheng/fiberweiteng/msm-3.10','06e51489061e5473b4e2035c79dcf7c27a6f75a6',[]),
        ('CVE-2017-10662','/home/zheng/fiberweiteng/linux','b9dd46188edc2f0d1f37328637860bb65a771124',['4f827eebf2e6']),
        ('CVE-2016-5195','/home/zheng/fiberweiteng/linux',[('/home/zheng/fiberweiteng/linux','9691eac5593f'),('/home/zheng/fiberweiteng/linux','19be0eaffa3a')],['c01894df6ba7']),
        ('CVE-2014-2706','/home/zheng/fiberweiteng/linux','1d147bfa64293b2723c4fec50922168658e613ba',[]),
        ('CVE-2017-11473','/home/zheng/fiberweiteng/linux','dad5ab0db8deac535d03e3fe3d8f2892173fa6a4',[]),
        ('CVE-2014-9778','/home/zheng/msm','af85054aa6a1bcd38be2354921f2f80aef1440e5',['63d243ff9d83']),
        ('CVE-2017-7364','/home/zheng/fiberweiteng/msm-4.4','3ce6c47d2142fcd2c4c1181afe08630aaae5a267',[]),
        ('CVE-2016-5861','/home/zheng/fiberweiteng/msm-4.4','cf3c97b8b6165f13810e530068fbf94b07f1f77d ',[]),
        ('CVE-2016-2502','/home/zheng/fiberweiteng/msm-3.10','0bc45d7712eabe315ce8299a49d16433c3801156',[]),
        #CVE-2017-0583:not patch in function 
        #('CVE-2017-0583','/home/zheng/fiberweiteng/msm-3.18','452d2ad331d20b19e8a0768c4b6e7fe1b65abe8f',[]),
        ('CVE-2017-7374','/home/zheng/fiberweiteng/linux',[('/home/zheng/fiberweiteng/linux','1b53cf9815bb'),('/home/zheng/fiberweiteng/msm','8afa82212a86')],['4f827eebf2e6','a3ccc667a91e',]),
        #CVE-2014-9800: no patchcommits generated
        #('CVE-2014-9800','/home/zheng/lk','6390f200d966dc13cf61bb5abbe3110447ca82b5',[]),
        ('CVE-2014-9802','/home/zheng/lk','222e0ec9bc755bfeaa74f9a0052b7c709a4ad054',['9c548b8c14cd']),
        #2016-3866 no patch on the website
        #('CVE-2016-3866','/home/zheng/lk','222e0ec9bc755bfeaa74f9a0052b7c709a4ad054',[]),
        ('CVE-2015-6640','/home/zheng/common','69bfe2d957d903521d32324190c2754cb073be15',[]),
        #CVE-2014-9779 not a patch in function
        #('CVE-2014-9779','/home/zheng/msm','0b5f49b360afdebf8ef55df1e48ec141b3629621',[]),
        ('CVE-2014-9781','/home/zheng/msm','a2b5237ad265ec634489c8b296d870827b2a1b13',['18cd721872df','4c300ac527ed','b70aba01edb9']),
        #CVE-2017-15848 not a patch in function
        #('CVE-2017-15848','/home/zheng/fiberweiteng/msm-4.4','d24a74a7103cb6b773e1d8136ba51b64fa96b21d',[]),
        ('CVE-2016-10234','/home/zheng/fiberweiteng/msm-3.10','c7d7492c1e329fdeb28a7901c4cd634d41a996b1',['ff2c6dd75b2f','6042185675e2']),
        ('CVE-2015-3636','/home/zheng/fiberweiteng/linux','a134f083e79fb4c3d0a925691e732c56911b4326',[]),
        ('CVE-2017-11024','/home/zheng/fiberweiteng/msm-3.10','f2a482422fefadfa0fa9b4146fc0e2b46ac04922',[]),
        #CVE-2016-3854:no patchcommits generated
        ('CVE-2016-3854','/home/zheng/msm','cc96def76dfd18fba88575065b29f2ae9191fafa',[]),
        ('CVE-2017-9722','/home/zheng/fiberweiteng/msm-4.4','ab0ae43628cff92d10792b762667ddfaf243d796',[]),
        #CVE-2017-6423: not a patch in fucntion
        #('CVE-2017-6423','/home/zheng/fiberweiteng/msm-3.18','0f264f812b61884390b432fdad081a3e995ba768',[]),
        #CVE-2017-11018:no patchcommits generated
        #('CVE-2017-11018','/home/zheng/msm','1d718286c4c482502a2c4356cebef28aef2fb01f',[]),
        ('CVE-2017-11047','/home/zheng/fiberweiteng/msm-4.4','8d0b17fdbea77753ce4388e4b7538f1c32b2b730',[]),
        #many fuzz commits todo
        #('CVE-2016-0802','/home/zheng/fiberweiteng/msm','3fffc78f70dc101add8b82af878d53457713d005',[]),
    ]

patchlist4_1=[
        ('CVE-2017-0576','/home/zheng/fiberweiteng/msm-3.18','2b09507d78b25637df6879cd2ee2031b208b3532',['e78789a497d8']),
        # no link on the website ('CVE-2016-2501','','',[]),
        ('CVE-2016-7910','/home/zheng/fiberweiteng/linux','77da160530dd1dc94f6ae15a981f24e5f0021e84',[]),
        ('CVE-2017-0609','/home/zheng/fiberweiteng/msm-4.4','38a83df036084c00e8c5a4599c8ee7880b4ee567',[]),
        ('CVE-2015-3288','/home/zheng/fiberweiteng/linux','6b7339f4c31ad69c8e9c0b2859276e22cf72176d',['1a87de89f3d8','8250bd666d4e','e84f94bb2389','140625571363','84d142e34270']),
        ('CVE-2016-2184','/home/zheng/fiberweiteng/linux',[('/home/zheng/fiberweiteng/linux','0f886ca12765'),('/home/zheng/fiberweiteng/linux','836b34a935ab')],[]),
        ('CVE-2016-7117','/home/zheng/fiberweiteng/linux','34b88a68f26a75e4fded796f1a49c40f82234b7d',[]),
        ('CVE-2015-8964','/home/zheng/fiberweiteng/linux','dd42bf1197144ede075a9d4793123f7689e164bc',[]),
        ('CVE-2016-5860','/home/zheng/fiberweiteng/msm-4.4','9f91ae0d7203714fc39ae78e1f1c4fd71ed40498',[]),
        ('CVE-2017-8246','/home/zheng/fiberweiteng/msm-3.18','30baaec8afb05abf9f794c631ad944838d498ab8',[]),
        ('CVE-2014-9940','/home/zheng/fiberweiteng/linux','60a2362f769cf549dc466134efe71c8bf9fbaaba',['8f20cf41cd20']),
        ('CVE-2014-9420','/home/zheng/fiberweiteng/linux','f54e18f1b831c92f6512d2eedb224cd63d607d3d',[]),
        ('CVE-2016-5696','/home/zheng/fiberweiteng/linux','75ff39ccc1bd5d3c455b6822ab09e533c551f758',['72d52919f2fe']),
        ('CVE-2016-5343','/home/zheng/fiberweiteng/msm-3.18','6927e2e0af4dcac357be86ba563c9ae12354bb08',[]),
        ('CVE-2016-5868','/home/zheng/fiberweiteng/msm-4.4','fbb765a3f813f5cc85ddab21487fd65f24bf6a8c',[]),
        #CVE-2017-7368 too many fuzzs todo
        ('CVE-2017-7368','/home/zheng/fiberweiteng/msm-3.18','143ef972be1621458930ea3fc1def5ebce7b0c5d',[]),
        ('CVE-2014-9731','/home/zheng/fiberweiteng/linux','0e5cc9a40ada6046e6bc3bdfcd0c0d7e4b706b14',[]),
        ('CVE-2016-3907','/home/zheng/fiberweiteng/msm-3.10','744330f4e5d70dce71c4c9e03c5b6a8b59bb0cda',[]),
        ('CVE-2016-3860','/home/zheng/fiberweiteng/msm-3.18','7e0f77f11613402a621dc2d97155eebd4f4f4716',[]),
        #CVE-2017-0606 deleted on the website
        #('CVE-2017-0606','/home/zheng/fiberweiteng/msm-3.18','7e0f77f11613402a621dc2d97155eebd4f4f4716',[]),
        ('CVE-2017-0626','/home/zheng/fiberweiteng/msm-4.4','64551bccab9b5b933757f6256b58f9ca0544f004',[]),
        ('CVE-2014-4014','/home/zheng/fiberweiteng/linux','23adbe12ef7d3d4195e80800ab36b37bee28cd03',[]),
        ('CVE-2016-7911','/home/zheng/fiberweiteng/linux','8ba8682107ee2ca3347354e018865d8e1967c5f4',[]),
        ('CVE-2016-8450','/home/zheng/fiberweiteng/msm-3.18','e909d159ad1998ada853ed35be27c7b6ba241bdb',['b306efcf9de4','8e4951abcef2','3f68220e56a0']),
        ('CVE-2017-0520','/home/zheng/fiberweiteng/msm-3.18','eb2aad752c43f57e88ab9b0c3c5ee7b976ee31dd',['e78789a497d8']),
        ('CVE-2016-8418','/home/zheng/fiberweiteng/msm-3.18','8f8066581a8e575a7d57d27f36c4db63f91ca48f',[]),
        #too many fuzzs todo
        ('CVE-2017-14892','/home/zheng/fiberweiteng/msm-3.18','a3bed71777c133cfec78b5140877c6ba109961a0',[]),
        ('CVE-2017-15265','/home/zheng/fiberweiteng/linux','71105998845fb012937332fe2e806d443c09e026',[]),
        ('CVE-2017-0614','/home/zheng/fiberweiteng/msm-3.18','fc2ae27eb9721a0ce050c2062734fec545cda604',['20c6b2f5919b']),
        #to many fuzzs
        ('CVE-2016-10285','/home/zheng/fiberweiteng/msm-3.18','67dfd3a65336e0b3f55ee83d6312321dc5f2a6f9',[]),
        ]
patchlist4_2=[
        ('CVE-2017-18066','/home/zheng/fiberweiteng/msm-3.18','ff11f44c0c10c94170f03a8698f73f7e08b74625',[]),
        ('CVE-2015-7872','/home/zheng/fiberweiteng/linux','f05819df10d7b09f6d1eb6f8534a8f68e5a4fe61',[]),
        ('CVE-2017-7369','/home/zheng/fiberweiteng/msm-3.10','75ed08a822cf378ffed0d2f177d06555bd77a006',[]),
        ('CVE-2016-5347','/home/zheng/fiberweiteng/msm-4.4','f14390f13e62460fc6b05fc0acde0e825374fdb6',['3243ae6b89cf']),
        ('CVE-2016-6738','/home/zheng/fiberweiteng/msm-3.18','a829c54236b455885c3e9c7c77ac528b62045e79',[]),
        ('CVE-2017-11600','/home/zheng/fiberweiteng/linux','7bab09631c2a303f87a7eb7e3d69e888673b9b7e',[]),
        #syntax error when parser('CVE-2016-7097','/home/zheng/fiberweiteng/linux','073931017b49d9458aa351605b43a7e34598caef',[]),
        ('CVE-2014-4656','/home/zheng/fiberweiteng/linux','883a1d49f0d77d30012f114b2e19fc141beb3e8e',[]),
        ('CVE-2017-9075','/home/zheng/fiberweiteng/linux','fdcee2cbb8438702ea1b328fb6e0ac5e9a40c7f8',[]),
        #too many fuzzs
        ('CVE-2017-15834','/home/zheng/fiberweiteng/msm-3.18','2e1b54e38f1516e70d9f6581c4f1ee935effb903',[]),
        ('CVE-2016-2059','/home/zheng/fiberweiteng/msm-3.18','9e8bdd63f7011dff5523ea435433834b3702398d',[]),
        #too many fuzzs
        ('CVE-2017-8279','/home/zheng/fiberweiteng/msm-4.4','f09aee50c2ee6b79d94cb42eafc82413968b15cb',[]),
        ('CVE-2015-8966','/home/zheng/fiberweiteng/linux','76cc404bfdc0d419c720de4daaf2584542734f42',[]),

        ('CVE-2016-10290','/home/zheng/fiberweiteng/msm-3.18','a5e46d8635a2e28463b365aacdeab6750abd0d49',[]),
        ('CVE-2016-6136','/home/zheng/fiberweiteng/linux','43761473c254b45883a64441dd0bc85a42f3645c',['495f6dafa300','668b33572e89','4e522566a6c0']),
        ('CVE-2017-0607','/home/zheng/fiberweiteng/msm-4.4','b003c8d5407773d3aa28a48c9841e4c124da453d',[]),
        ('CVE-2016-6828','/home/zheng/fiberweiteng/linux','bb1fceca22492109be12640d49f5ea5a544c6bb4',[]),
        #todo
        #('CVE-2014-9780','/home/zheng/fiberweiteng/msm-3.10',[('/home/zheng/fiberweiteng/msm-3.10','b5bb13e1f738'),('/home/zheng/fiberweiteng/msm','0538065c0814')],[]),
        ('CVE-2017-9724','/home/zheng/fiberweiteng/msm-3.10','5328a92fa26eabe2ba259b1d813f9de488efc9ec',[]),
        ('CVE-2015-8951','/home/zheng/fiberweiteng/msm-3.10','ccff36b07bfc49efc77b9f1b55ed2bf0900b1d5b',[]),
        ('CVE-2017-11033','/home/zheng/fiberweiteng/msm-3.18','b54141365805ae1a5254bff5442e1a103d3701d0',[]),
        ('CVE-2017-9705','/home/zheng/fiberweiteng/msm-3.10','00515286cf52145f2979026b8641cfb15c8e7644',['f6f22bd54e58','f996be0e6ff7','5d797a8aec3c']),
        #too many fuzzs
        ('CVE-2017-11023','/home/zheng/fiberweiteng/msm-4.4','c36e61af0f770125d0061a8d988d0987cc8d116a',[]),
        #too many fuzzs
        ('CVE-2017-1000380','/home/zheng/fiberweiteng/linux','d11662f4f798b50d8c8743f433842c3e40fe3378',[]),
        ('CVE-2014-9788','/home/zheng/fiberweiteng/msm-3.10','73bfc22aa70cc0b7e6709381125a0a42aa72a4f2',[]),
        ('CVE-2018-3599','/home/zheng/fiberweiteng/msm-3.18','cf2702c1a77d2a164a3be03597eff7e6fe5f967e',[]),
        #too many fuzzs
        #some problems todo ('CVE-2016-4998','/home/zheng/fiberweiteng/linux','6e94e0cfb0887e4013b3b930fa6ab1fe6bb6ba91',[]),
        ('CVE-2017-0620','/home/zheng/fiberweiteng/msm-4.4','01b2c9a5d728ff6f2f1f28a5d4e927aaeabf56ed',['a862b13b82bf','84e4cb59f55a','6ed34dddf902','5758181969b8','21821a073e5d']),
        ('CVE-2017-9719','/home/zheng/fiberweiteng/msm-3.18','a491499c3490999555b7ccf8ad1a7d6455625807',[]),
        ('CVE-2015-8961','/home/zheng/fiberweiteng/linux','6934da9238da947628be83635e365df41064b09b',[]),
        ('CVE-2017-0454','/home/zheng/fiberweiteng/msm-3.18','cb0701a2f99fa19f01fbd4249bda9a8eadb0241f',[]),
        ('CVE-2016-7913','/home/zheng/fiberweiteng/linux','8dfbcc4351a0b6d2f2d77f367552f48ffefafe18',[]),
        ('CVE-2015-8962','/home/zheng/fiberweiteng/linux','f3951a3709ff50990bf3e188c27d346792103432',[]),
        ('CVE-2017-8266','/home/zheng/fiberweiteng/msm-3.18','42627c94cf8c189332a6f5bfdd465ea662777911',[]),
        ]
patchlist4_3=[
        ('CVE-2016-10293','/home/zheng/fiberweiteng/msm-3.10','2469d5374745a2228f774adbca6fb95a79b9047f',[]),
        ('CVE-2017-7184','/home/zheng/fiberweiteng/linux','677e806da4d916052585301785d847c3b3e6186a',[]),
        ('CVE-2016-6692','/home/zheng/fiberweiteng/msm-3.18','0f0e7047d39f9fb3a1a7f389918ff79cdb4a50b3',[]),
        ('CVE-2017-0604','/home/zheng/fiberweiteng/msm-3.18','6975e2dd5f37de965093ba3a8a08635a77a960f7',[]),
        ('CVE-2016-2068','/home/zheng/fiberweiteng/msm-3.10','01ee86da5a0cd788f134e360e2be517ef52b6b00',[]),
        ('CVE-2017-0533','/home/zheng/fiberweiteng/msm-3.18',[('/home/zheng/fiberweiteng/msm-3.18','e3af5e89426f'),('/home/zheng/fiberweiteng/msm','651d7e5a492f')],[]),
        ('CVE-2017-10661','/home/zheng/fiberweiteng/linux','1e38da300e1e395a15048b0af1e5305bd91402f6',[]),
        ('CVE-2016-10200','/home/zheng/fiberweiteng/linux','32c231164b762dddefa13af5a0101032c70b50ef',[]),
        ('CVE-2016-8463','/home/zheng/fiberweiteng/msm-3.10','cd0fa86de6ca1d40c0a93d86d1c0f7846e8a9a10',[]),
        ('CVE-2017-7533','/home/zheng/fiberweiteng/linux','49d31c2f389acfe83417083e1208422b4091cd9e',[]),
        ('CVE-2015-8944','/home/zheng/fiberweiteng/msm-3.10','e758417e7c31b975c862aa55d0ceef28f3cc9104',[]),
        ('CVE-2014-9922','/home/zheng/fiberweiteng/linux','69c433ed2ecd2d3264efd7afec4439524b319121',['9fa43b57438e']),
        #too many fuzzs
        ('CVE-2016-6786','/home/zheng/fiberweiteng/linux','f63a8daa5812afef4f06c962351687e1ff9ccb2b',[]),
        ('CVE-2016-9120','/home/zheng/fiberweiteng/linux','9590232bb4f4cc824f3425a6e1349afbe6d6d2b7',[]),
        ('CVE-2017-0531','/home/zheng/fiberweiteng/msm-3.18','530f3a0fd837ed105eddaf99810bc13d97dc4302',[]),
        ('CVE-2016-7914','/home/zheng/fiberweiteng/linux','8d4a2ec1e0b41b0cf9a0c5cd4511da7f8e4f3de2',[]),
        #too many fuzzs
        ('CVE-2017-8242','/home/zheng/fiberweiteng/msm-3.18','6a3b8afdf97e77c0b64005b23fa6d32025d922e5',['20c6b2f5919b']),
        ('CVE-2016-4794','/home/zheng/fiberweiteng/linux','6710e594f71ccaad8101bc64321152af7cd9ea28',[]),
        ('CVE-2017-0463','/home/zheng/fiberweiteng/msm-3.18','955bd7e7ac097bdffbadafab90e5378038fefeb2',[]),
        ('CVE-2017-14891','/home/zheng/fiberweiteng/msm-3.18','736667bf08b03fdca824e88b901c2dbdd6703a0c',[]),
        ('CVE-2017-14140','/home/zheng/fiberweiteng/linux','197e7e521384a23b9e585178f3f11c9fa08274b9',['823383c919f7','569a56200c1a']),
        #not on website
        ('CVE-2014-9790','/home/zheng/msm','6ed921bda8cbb505e8654dfc1095185b0bccc38e',[]),
        ('CVE-2017-7487','/home/zheng/fiberweiteng/linux','ee0d8d8482345ff97a75a7d747efc309f13b0d80',[]),
        ('CVE-2017-13215','/home/zheng/fiberweiteng/linux',[('/home/zheng/fiberweiteng/linux','36c84b22ac8a'),('/home/zheng/fiberweiteng/msm','fec8beab6328')],[]),
        ('CVE-2017-11025','/home/zheng/fiberweiteng/msm-3.10','95e72ae9281b77abc3ed0cc6a33c17b989241efa ',[]),
        ('CVE-2016-10231','/home/zheng/fiberweiteng/msm-3.18','3bfe5a89916f7d29492e9f6d941d108b688cb804',[]),
        ('CVE-2016-9794','/home/zheng/fiberweiteng/linux','a27178e05b7c332522df40904f27674e36ee3757',[]),
        #('CVE-2016-2067','/home/zheng/fiberweiteng/linux','3aa02cb664c5fb1042958c8d1aa8c35055a2ebc4',[]),
        ('CVE-2016-5344','/home/zheng/fiberweiteng/msm-3.18','1d2297267c24f2c44bd0ecb244ddb8bc880a29b7',['f8e87aa19937','3588840641b3','307dcd06e43f']),
        ('CVE-2017-6074','/home/zheng/fiberweiteng/linux','5edabca9d4cff7f1f2b68f0bac55ef99d9798ba4',[]),
        ('CVE-2016-10294','/home/zheng/fiberweiteng/msm-3.18','9e9bc51ffb8a298f0be5befe346762cdb6e1d49c',[]),
        ('CVE-2016-10289','/home/zheng/fiberweiteng/msm-3.18','a604e6f3889ccc343857532b63dea27603381816',[]),
        ('CVE-2016-3938','/home/zheng/fiberweiteng/msm-3.18','467c81f9736b1ebc8d4ba70f9221bba02425ca10',[]),
        ('CVE-2015-0572','/home/zheng/fiberweiteng/msm-3.10','34ad3d34fbff11b8e1210b9da0dac937fb956b61',[]),
        ('CVE-2016-9806','/home/zheng/fiberweiteng/linux','92964c79b357efd980812c4de5c1fd2ec8bb5520',[]),
        ('CVE-2017-7616','/home/zheng/fiberweiteng/linux','cf01fb9985e8deb25ccf0ea54d916b8871ae0e62',[]),
        ('CVE-2016-7915','/home/zheng/fiberweiteng/linux','50220dead1650609206efe91f0cc116132d59b3f',[]),
        #too many fuzzs
        ('CVE-2017-11044','/home/zheng/fiberweiteng/msm-3.18','704512a933415f38c190d21e28bcd2dd122dc4b8',[]),
        ]
patchlist4_4=[
        ('CVE-2016-6750','/home/zheng/fiberweiteng/msm-3.18','34bda711a1c7bc7f9fd7bea3a5be439ed00577e5',[]),
        ('CVE-2017-9697','/home/zheng/fiberweiteng/msm-3.18','34bda711a1c7bc7f9fd7bea3a5be439ed00577e5',[]),
        ('CVE-2016-7042','/home/zheng/fiberweiteng/linux','03dab869b7b239c4e013ec82aea22e181e441cfc',[]),
        ('CVE-2017-10998','/home/zheng/fiberweiteng/msm-3.18','208e72e59c8411e75d4118b48648a5b7d42b1682',[]),
        ('CVE-2017-0610','/home/zheng/fiberweiteng/msm-4.4','65009746a6e649779f73d665934561ea983892fe',[]),
        ('CVE-2014-9785','/home/zheng/fiberweiteng/msm-3.10','b4338420db61f029ca6713a89c41b3a5852b20ce',[]),
        ('CVE-2016-8414','/home/zheng/fiberweiteng/msm-3.10','320970d3da9b091e96746424c44649a91852a846',[]),
        ('CVE-2017-6425','/home/zheng/fiberweiteng/msm-3.18',[('/home/zheng/fiberweiteng/msm-3.18','ef86560a21fe'),('/home/zheng/fiberweiteng/msm','1add68c2877e')],[]),
        ('CVE-2017-11049','/home/zheng/fiberweiteng/msm-3.18','430f3805c82634a3cb969d83acc4fc4c0ee6af27',[]),
        ('CVE-2016-2469','/home/zheng/fiberweiteng/msm-3.18','430f3805c82634a3cb969d83acc4fc4c0ee6af27',[]),
        ('CVE-2017-9700','/home/zheng/fiberweiteng/msm-4.4','c2e5af21d3d3bb856ff3b5783aa2a6147a4c9089',[]),
        ('CVE-2017-5897','/home/zheng/fiberweiteng/linux','7892032cfe67f4bde6fc2ee967e45a8fbaf33756',[]),
        ('CVE-2014-9914','/home/zheng/fiberweiteng/linux','9709674e68646cee5a24e3000b3558d25412203a',[]),
        #too many fuzzs
        ('CVE-2016-3931','/home/zheng/fiberweiteng/msm-3.18','e80b88323f9ff0bb0e545f209eec08ec56fca816',['20c6b2f5919b']),
        ('CVE-2016-1583','/home/zheng/fiberweiteng/linux','e54ad7f1ee263ffa5a2de9c609d58dfa27b21cd9',[]),
        ('CVE-2016-2066','/home/zheng/fiberweiteng/msm-3.18','775fca8289eff931f91ff6e8c36cf2034ba59e88',['dce0f8189f75']),
        ('CVE-2017-11030','/home/zheng/fiberweiteng/msm-3.18','89e6c2d38405cdeefaa278cbf6d18791f255ee5e',[]),
        ('CVE-2016-8480','/home/zheng/fiberweiteng/msm-3.10','0ed0f061bcd71940ed65de2ba46e37e709e31471',['20c6b2f5919b']),
        ('CVE-2017-0451','/home/zheng/fiberweiteng/msm-3.10','59f55cd40b5f44941afc78b78e5bf81ad3dd723e',[]),
        ('CVE-2017-17712','/home/zheng/fiberweiteng/linux','8f659a03a0ba9289b9aeb9b4470e6fb263d6f483',[]),
        ('CVE-2017-8240','/home/zheng/fiberweiteng/msm-3.18','22b8b6608174c1308208d5bc6c143f4998744547',[]),
        ('CVE-2016-3939','/home/zheng/fiberweiteng/msm-3.18','e0bb18771d6ca71db2c2a61226827059be3fa424',[]),
        ('CVE-2017-14897','/home/zheng/fiberweiteng/msm-3.18','11e7de77bd5ab0a7706a013598f845ad0c4a8b4c',[]),
        #too many fuzzs
        ('CVE-2016-2546','/home/zheng/fiberweiteng/linux','af368027a49a751d6ff4ee9e3f9961f35bb4fede',[]),
        #('CVE-2014-9803','/home/zheng/fiberweiteng/linux','af368027a49a751d6ff4ee9e3f9961f35bb4fede',[]),
        ('CVE-2016-6681','/home/zheng/fiberweiteng/msm-3.18','0950fbd39ff189497f1b6115825c210e3eeaf395 ',[]),
        #too many fuzzs
        ('CVE-2017-0613','/home/zheng/fiberweiteng/msm-4.4','b108c651cae9913da1ab163cb4e5f7f2db87b747',['20c6b2f5919b']),
        ('CVE-2017-7187','/home/zheng/fiberweiteng/linux','bf33f87dd04c371ea33feb821b60d63d754e3124',[]),
        ('CVE-2016-5342','/home/zheng/fiberweiteng/msm-3.18','579e796cb089324c55e0e689a180575ba81b23d9',['54cf38854f78','5935a691c689']),
        ]
patchlist4_5=[
        ('CVE-2016-3893','/home/zheng/fiberweiteng/msm-3.10','a7a6ddc91cce7ad5ad55c9709b24bfc80f5ac873',[]),
        ('CVE-2015-8955','/home/zheng/fiberweiteng/linux','8fff105e13041e49b82f92eef034f363a6b1c071',[]),
        ('CVE-2017-9725','/home/zheng/fiberweiteng/msm-4.4','1f8f9b566e8446c13b954220c226c58d22076f88',[]),
        ('CVE-2016-8650','/home/zheng/fiberweiteng/linux','f5527fffff3f002b0a6b376163613b82f69de073',[]),
        ('CVE-2017-0608','/home/zheng/fiberweiteng/msm-4.4','b66f442dd97c781e873e8f7b248e197f86fd2980',[]),
        ('CVE-2017-9076','/home/zheng/fiberweiteng/linux','83eaddab4378db256d00d295bda6ca997cd13a52',[]),
        ('CVE-2016-6791','/home/zheng/fiberweiteng/msm-3.10','62580295210b6c0bd809cde7088b45ebb65ace79',[]),
        #no link on the website
        #('CVE-2016-2489','/home/zheng/fiberweiteng/msm-3.10','62580295210b6c0bd809cde7088b45ebb65ace79',[]),
        ('CVE-2016-3901','/home/zheng/fiberweiteng/msm-3.18','5f69ccf3b011c1d14a1b1b00dbaacf74307c9132',[]),
        ('CVE-2017-7370','/home/zheng/fiberweiteng/msm-3.18','970edf007fbe64b094437541a42477d653802d85',[]),
        ('CVE-2017-8281','/home/zheng/fiberweiteng/msm-3.18','7e0f77f11613402a621dc2d97155eebd4f4f4716',[]),
        ('CVE-2017-14873','/home/zheng/fiberweiteng/msm-3.18','57377acfed328757da280f4adf1c300f0b032422',[]),
        ('CVE-2016-6752','/home/zheng/fiberweiteng/msm-3.18','0de2c7600c8f1f0152a2f421c6593f931186400a',[]),
        #too many fuzzs
        ('CVE-2017-7366','/home/zheng/fiberweiteng/msm-3.18','f4c9ffd6cd7960265f38e285ac43cbecf2459e45',['1f40833fed37','a419c79089f4',]),
        #('CVE-2014-9787','/home/zheng/fiberweiteng/msm-3.18','f4c9ffd6cd7960265f38e285ac43cbecf2459e45',[]),
        ('CVE-2016-10236','/home/zheng/fiberweiteng/msm-3.18','b8199c2b852f1e23c988e10b8fbb8d34c98b4a1c',[]),
        ('CVE-2017-0612','/home/zheng/fiberweiteng/msm-3.18','05efafc998dc86c3b75af9803ca71255ddd7a8eb',['20c6b2f5919b']),
        ('CVE-2017-8262','/home/zheng/fiberweiteng/msm-4.4','9ef4ee8e3dfaf4e796bda781826851deebbd89bd',[]),
        ('CVE-2017-0465','/home/zheng/fiberweiteng/msm-4.4','3823f0f8d0bbbbd675a42a54691f4051b3c7e544',[]),
        ('CVE-2016-0758','/home/zheng/fiberweiteng/linux','23c8a812dc3c621009e4f0e5342aa4e2ede1ceaa',[]),
        ('CVE-2016-6698','/home/zheng/fiberweiteng/msm-3.10','de90beb76ad0b80da821c3b857dd30cd36319e61',[]),
        ('CVE-2017-14902','/home/zheng/fiberweiteng/msm-3.18','8c4901802968b8c8356860ee689b1ef9cd2cbfe4',[]),
        #too many fuzzs
        ('CVE-2015-8963','/home/zheng/fiberweiteng/linux','12ca6ad2e3a896256f086497a7c7406a547ee373',['acdbf3db0928','18088fea40d1','465f59e72b0b','498772e2c7a1']),
        ]

patchlist_new=[
        ('CVE-2017-6001','/home/zheng/fiberweiteng/common','14ac5291d640b0ec3184886bd753babac3615c55',[]),
        ]
extraelementlist= [
        ['CVE-2014-9781',('drivers/video/fbdev/core/fbcmap.c','fb_cmap_to_user')],
        ['CVE-2015-8955',('./drivers/perf/arm_pmu.c','validate_event'),('arch/arm64/kernel/perf_event.c', 'validate_group')],
        ['CVE-2016-0801',('./drivers/huawei_platform/connectivity/bcm/wifi/driver/bcmdhd/wl_cfg80211.c','wl_notify_sched_scan_results'),('./drivers/huawei_platform/connectivity/bcm/wifi/driver/bcmdhd/wl_cfg80211.c','wl_validate_wps_ie')],
        ]
        
        
