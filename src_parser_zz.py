#!/usr/bin/python

import sys
import re
from pygments.lexers import get_lexer_by_name
from pygments.token import Token
import os
import pickle
LINE_BASE = 1

def _trim_lines(buf):
    for i in range(len(buf)):
        if len(buf[i])==0:
            continue
        if buf[i][-1] == '\n':
            buf[i] = buf[i][:-1]
        if len(buf[i])==0:
            continue
        for j in range(len(buf[i])):
            if buf[i][j] != " ":
                break
        buf[i]=buf[i][j:]

def get_function_content(kernel,filename,funcname,funcline=0):
    PATH=kernel+"/"+filename
    if not os.path.exists(PATH):
        return set()
    with open(PATH,"r") as f:
        f_buf=f.readlines()
    return get_function_content_1(f_buf,funcname,funcline) 
def get_function_content_1(f_buf,funcname,funcline=0):
    result=set()
    try:
        (cur_func_inf,cur_func_inf_r)=build_func_map(f_buf)
    except:
        print "build_func_map error"
        #print kernel," ",filename," ",funcname
        return result
    _trim_lines(f_buf)
    list1=[]
    list2=[]
    for element in cur_func_inf:
        #print element
        list1 += [element]
    for element in cur_func_inf_r:
        #print element
        list2 += [element]
    list1.sort()
    #print list1
    list2.sort(key=lambda x:x[1])
    #print list2
    if funcline==0:
        for element in cur_func_inf_r:
            funcname2=element[0]
            #print funcname2
            if funcname2==funcname:
                #print "find ",funcname," in ",filename," in ",kernel
                ((st,ed),arg_cnt)=cur_func_inf_r[element]
                #print funcname2,(st,ed) 
                content='\n'.join(f_buf[st-1:ed])
                result.add(content)
    else:
        for element in cur_func_inf_r:
            funcname2=element[0]
            funcline2=element[1]
            if funcname2==funcname and funcline2==funcline:
                ((st,ed),arg_cnt)=cur_func_inf_r[element]
                content='\n'.join(f_buf[st-1:ed])
                result.add(content)
    return result

    
def get_functions_cve(cve):
    dic_func_content={}
    PATH="/data/zheng/cve2/"+cve+"/diccommit_patchinfo_pickle"
    if not os.path.exists(PATH):
        print "get_functions_cve no patchinfostored for ",cve
        return None
    pickle_in=open(PATH,"rb")
    diccommit_patchinfo=pickle.load(pickle_in)
    for commit in diccommit_patchinfo:
        #print commit
        for element in diccommit_patchinfo[commit]:
            filename=element[0]
            funcname=element[1]
            content='\n'.join(diccommit_patchinfo[commit][element]['content'])
            if (filename,funcname) in dic_func_content:
                dic_func_content[(filename,funcname)].add(content)
            else:
                dic_func_content[(filename,funcname)]=set([content])
    return dic_func_content

def get_functions_commits_cve(cve):
    dic_func_content=get_functions_cve(cve)
    dic_func_commit = {}
    for element in dic_func_content:
        dic_func_commit[element]={}
        for content in dic_func_content[element]:
            dic_func_commit[element][content]=set()

    PATH="/data/zheng/cve2/"+cve+"/diccommit_patchinfo_pickle"
    if not os.path.exists(PATH):
        print "get_functions_cve no patchinfostored for ",cve
        return None
    pickle_in=open(PATH,"rb")
    diccommit_patchinfo=pickle.load(pickle_in)

    for commit in diccommit_patchinfo:
        for element in diccommit_patchinfo[commit]:
            filename=element[0]
            funcname=element[1]
            funcline=element[2]
            content='\n'.join(diccommit_patchinfo[commit][element]['content'])
            dic_func_commit[(filename,funcname)][content].add(commit)
    return dic_func_commit

def funccontent_existinpathchinfo(kernel,cve):
    dic_func_commit=get_functions_commits_cve(cve)
    result={}
    Foundfunction=False
    for (filename,funcname) in dic_func_commit:
        contentset=get_function_content(kernel,filename,funcname)
        if len(contentset) > 0:
            #print "find ",(filename,funcname), " in ",kernel
            Foundfunction=True
            for content in contentset:
                if content in dic_func_commit[(filename,funcname)]:
                    result[(filename,funcname)]={}
                    result[(filename,funcname)]['content']=content
                    result[(filename,funcname)]['commit']=dic_func_commit[(filename,funcname)][content]
                    break
            #else:
            #    print "don't find corresponding content in patchinfo"
    if len(result) >0:
        #print "functionfound: ",Foundfunction
        #print "find correesponding content in patchinfo of ",cve
        return True
    else:
        #print "don't find corresponding content in patchinfo of ",cve 
        #print "functionfound: ",Foundfunction
        return False
        #for element in result:
        #    print element
        

def build_func_map(s_buf):
    cur_func_inf={}
    cur_func_inf_r={}
    cur_func_inf.clear()
    cur_func_inf_r.clear()
    cnt = 0
    prev_pos = (0,0)
    in_str = False
    in_comment = 0
    #print 'length of s_buf'
    #print len(s_buf)
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
