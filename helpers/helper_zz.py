import sys,os
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
import datetime
import pickle
import subprocess
import re
import time
import src_parser
LINE_BASE = 1

def trim_lines(buf):
    for i in range(len(buf)):
        if len(buf[i])==0:
            continue
        if buf[i][-1] == '\n':
            buf[i] = buf[i][:-1]
#require hard code
def get_repopath(Repo):
    repo_path={}
    with open('repo_path.txt','r') as f:
        s_buf = f.readlines()
    for line in s_buf:
        repo,path=line[:-1].split(' ')
        repo_path[repo]=path
    if Repo in repo_path:
        return repo_path[Repo]
    return None

def checkoutcommit(kernel,commit):
    string1="cd "+kernel+"; git checkout -f "+commit
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p_buf=p.stdout.readlines()
    return

#used for getting renamed files in commits
#return set of (fn,fp)
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

#get files initializated in the commit
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

#used in getting renamed functions    
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

def checkoutfiles_commit(kernel,commit,files):
    string1="cd "+kernel
    updatedfiles=set()
    for filename in files:
        if file_exits_in_commit(kernel,commit,filename):
            string1 += ";git checkout -f "+commit+" "+filename
            updatedfiles.add(filename)
    command(string1)
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

def file_exits_in_commit(kernel,commit,filename):
    if kernel==None or commit == None or filename== None:
        print 'kernel,commit,filename:'
        print kernel,commit,filename
        return False
    commit =commit.strip()
    string1="cd "+kernel+";git cat-file -e "+commit+":"+filename+"&&echo exists"
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
            author=line[12:]
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
    string1="cd "+kernel+";git log --pretty=oneline "+ commitnumber
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    commitlog=p.stdout.readlines()
    return commitlog

def get_candidate_commitnumbers2(repository, file_name):
    candidates=set()
    string1="cd "+repository+";git log --pretty=oneline -- -p -follow "+file_name
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
            string1="cd "+repository+";git log --pretty=oneline -- -p -follow "+newfilename
            p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            candidates_buf=p.stdout.readlines()
        elif len(resultlist) >1:
            print 'multiple substitution'
            newfilename=resultlist[0][:-1]
            string1="cd "+repository+";git log --pretty=oneline -- -p -follow "+newfilename
            p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            candidates_buf=p.stdout.readlines()
        elif len(resultlist)==0:
            string1="cd "+repository+";git log --pretty=oneline -- -p -follow */"+file_name
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
        string1="cd "+repository+";git log --pretty=oneline --first-parent "+branch+' -- -p '+filename
    else:
        string1="cd "+repository+";git log --pretty=oneline --first-parent "+branch
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

def build_func_map(s_buf):
    cur_func_inf={}
    cur_func_inf_r={}
    cur_func_inf.clear()
    cur_func_inf_r.clear()
    cnt = 0
    prev_pos = (0,0)
    in_str = False
    in_comment = 0
    #TODO: Maybe we should utilize lexer to avoid all the mess below.
    ifelse=False
    numberif=0
    for i in range(len(s_buf)):
        #config if else
        #print ifelse
        if s_buf[i].startswith('#else'):
            #print "#else",i
            numberif +=1
            ifelse=True
        if ifelse:
            if s_buf[i].startswith('#if'):
                numberif +=1
            elif s_buf[i].startswith('#endif'):
                numberif -=1
                if numberif==0:
                    ifelse=False
            continue
        for j in range(len(s_buf[i])):
            if s_buf[i][j] == '{':
                #print i
                if in_str or in_comment > 0:
                    continue
                #print cnt
                if cnt == 0:
                    prev_pos = (i,j)
                cnt += 1
            elif s_buf[i][j] == '}':
                if in_str or in_comment > 0:
                    continue
                #print i,cnt
                cnt -= 1
                if cnt == 0:
                    #We have found a out-most {} pair, it *may* be a function.
                    func_head = _detect_func_head(s_buf,prev_pos)
                    #print 'prev_pos:',prev_pos,'func_head:',func_head
                    if func_head:
                        (func,arg_cnt) = func_head
                        #update: head contains 2 lines
                        if func_head[0]+'(' not in s_buf[prev_pos[0]-LINE_BASE]:
                            #update by zz: maybe more than 2lines
                            startline=prev_pos[0]-1
                            funcname=func_head[0]
                            while True:
                                if funcname+'(' in s_buf[startline-1]:
                                    break
                                startline -=1
                            cur_func_inf[(startline,i+1)] = func_head
                            cur_func_inf_r[(func,startline)] = ((startline,i+1),arg_cnt)
                            #cur_func_inf[(prev_pos[0]-1,i+1)] = func_head
                            #cur_func_inf_r[(func,prev_pos[0]-1)] = ((prev_pos[0]-1,i+1),arg_cnt)
                        else:
                            cur_func_inf[(prev_pos[0],i+1)] = func_head
                        #NOTE: Sometimes one file can have multiple functions with same name, due to #if...#else.
                        #So to mark a function we need both name and its location.
                            cur_func_inf_r[(func,prev_pos[0])] = ((prev_pos[0],i+1),arg_cnt)
                elif cnt < 0:
                    print i
                    print '!!! Syntax error: ' + s_buf[i]
                    print 'prev_pos: %d:%d' % adj_lno_tuple(prev_pos)
                    #print '------------Context Dump--------------'
                    l1 = max(i-5,0)
                    l2 = min(i+5,len(s_buf)-1)
                    #print ''.join([s_buf[i] for i in range(l1,l2+1)])
                    return
            elif s_buf[i][j] == '"' and in_comment == 0:
                in_str = not in_str
            elif s_buf[i][j] == '/' and j + 1 < len(s_buf[i]) and s_buf[i][j+1] == '/' and not in_str:
                #Line comment, skip this line
                break
            elif s_buf[i][j] == '/' and j + 1 < len(s_buf[i]) and s_buf[i][j+1] == '*' and not in_str:
                #Block comment start
                in_comment += 1
            elif s_buf[i][j] == '*' and j + 1 < len(s_buf[i]) and s_buf[i][j+1] == '/' and not in_str:
                #Block comment end
                in_comment -= 1

    return (cur_func_inf,cur_func_inf_r)

#pos is the position of leading '{' of a potential function.
def _detect_func_head(s_buf,pos):
    def _back(pos):
        i = pos[0]
        j = pos[1]
        return (i,j-1) if j > 0 else (i-1,len(s_buf[i-1])-1) if i > 0 else None
    #First ensure that there is nothing between the '{' and a ')'
    p = pos
    while True:
        p = _back(p)
        if not p:
            break
        if s_buf[p[0]][p[1]] in ('\n',' ','\t'):
            continue
        elif s_buf[p[0]][p[1]] == ')':
            cnt = 1
            comma_cnt = 0
            any_arg = False
            while True:
                p = _back(p)
                if not p:
                    break
                if s_buf[p[0]][p[1]] == ')':
                    cnt += 1
                elif s_buf[p[0]][p[1]] == '(':
                    cnt -= 1
                elif s_buf[p[0]][p[1]] == ',':
                    comma_cnt += 1
                elif not s_buf[p[0]][p[1]] in ('\n',' ','\t'):
                    any_arg = True
                if cnt == 0:
                    break
            arg_cnt = comma_cnt + 1 if comma_cnt > 0 else 1 if any_arg else 0
            if cnt == 0:
                #It should be a function, extract the func name.
                #First skip the tailing spaces
                while True:
                    p = _back(p)
                    if not p:
                        break
                    if not s_buf[p[0]][p[1]] in ('\n',' ','\t'):
                        break
                if not p:
                    return None
                #Record the function name
                func = [s_buf[p[0]][p[1]]]
                while True:
                    p = _back(p)
                    if not p:
                        break
                    if s_buf[p[0]][p[1]] in ('\n',' ','\t','*'):
                        break
                    func.append(s_buf[p[0]][p[1]])
                func.reverse()
                return (''.join(func),arg_cnt)
            else:
                return None
        else:
            return None
    return None

#It seems that the line number is based on 1 instead of 0 for DWARF, so we need to +1 for each line number.
def adj_lno_tuple(t):
    return tuple(map(lambda x:x+LINE_BASE,t))

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
    (cur_func_inf,cur_func_inf_r)=build_func_map(file_buf1)
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
    (cur_func_inf,cur_func_inf_r)=build_func_map(file_buf2)
    for (funcname,funcline) in cur_func_inf_r:
        if funcline in range(newst,newed+1):
            newfuncname=funcname
            #print 'newfuncname:',newfuncname
            return newfuncname
        #print 'dont find new function'
    return None


#given a commit and a repo branch, try to get the corresponding commit in main branch.
def get_maincommit(repopath,branch,commit,maincommitlog):
    if any(commit in line for line in maincommitlog):
        return commit
    string1='cd '+repopath+';git rev-list '+commit+'..'+branch+' --ancestry-path'
    resultlist1=command(string1)
    string1='cd '+repopath+';git rev-list '+commit+'..'+branch+' --first-parent'
    resultlist2=command(string1)
    commoncommitlist = [commoncommit for commoncommit in resultlist1 if commoncommit in resultlist2]
    return commoncommitlist[-1][:12]

def get_earliest_commits(targetrepopath,targetbranch,commits):
    diclist=[]
    dic={}
    for commit in commits:
        dic['commit'] = commit
        dic['commitdate']=get_commitdate(targetrepopath,commit)
        localdic =  dic.copy()
        diclist += [localdic]
    diclist=sorted(diclist,key=lambda x:x['commitdate'])
    return diclist[0]['commit']

def command(string1):
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result=p.stdout.readlines()
    return result

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
        string1="cd "+kernel+";git log --pretty=oneline "+commit
        p_buf=command(string1)
        prevcommit=p_buf[1][:12]
    return prevcommit

def get_currentcommit(kernel):
    string1="cd "+kernel+";git log -2 --pretty=oneline "
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p_buf=p.stdout.readlines()
    commit1=p_buf[0][:12]
    return commit1

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

#return a dictionary {filename:[functions]} that contains all functions changed in this commit
def get_commit_functions2(kernel,commit):
    p_buf=get_commit_content(kernel,commit)
    changelines=get_commit_changelines(p_buf)
    #checkoutcommit(kernel,commit)
    functiondic={}
    for filename in changelines:
        functiondic[filename]=[]
        string1='cd '+kernel+';git show '+commit+':'+filename
        f_buf=command(string1)
        changeset=changelines[filename]
        try:
            (cur_func_inf,cur_func_inf_r)=build_func_map(f_buf)
        except:
            print "build_func_map fail! in get_commit_functions"
            print commit
            print kernel, " ",filename
            return functiondic
        for (funcname,funcline) in cur_func_inf_r:
            (st,ed)=cur_func_inf_r[(funcname,funcline)][0]
            lineset=set(range(st,ed+1))
            if lineset.intersection(changeset):
                functiondic[filename] += [funcname]
    return functiondic

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
        return (commitcandidate, False)
    return (commitcandidate,True)

def is_patch_commit((commitcandidate,p_buf,repopath)):
    diff_index = [i for i in range(len(p_buf)) if p_buf[i].startswith('diff')] + [len(p_buf)]
    notmatch=0
    strictmatch=0
    fuzzmatch=0
    string1="cd "+repopath+";git show "+commitcandidate
    p=subprocess.Popen(string1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    s_buf=p.stdout.readlines()
    for i in range(len(diff_index)-1):
        (localnotmatch, localstrictmatch, localfuzzmatch) = get_commitnumber_2(p_buf,diff_index[i],diff_index[i+1],s_buf)
        notmatch = notmatch+localnotmatch
        strictmatch = strictmatch+localstrictmatch
        fuzzmatch = fuzzmatch+localfuzzmatch
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
            commitnumber=get_commitnumber_4_fuzz(head,p_buf[t1:t2+1],p_buf[t0:t1],p_buf[t2+1:t3+1],s_buf)
            if commitnumber is None:
                localnotmatch += 1
            else:
                localfuzzmatch +=1
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
