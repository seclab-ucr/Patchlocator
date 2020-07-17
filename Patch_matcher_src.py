import sys,os
import helper_zz
import pickle

def compare_sourcecode(branch,targetpath):
    filepath='./output/Patch_evolution_'+branch+'_pickle'
    pickle_in=open(filepath,'rb')
    cve_commit_element_content=pickle.load(pickle_in)
    cvelist=[cve for cve in cve_commit_element_content]
    cvelist.sort()
    cve_result={}
    outputfile=targetpath+'/matchresults'
    countTrue=0
    countFalse=0
    countNone=0
    Falselist=[]
    for cve in cve_commit_element_content:
        result='None'
        for afterpatchcommit in cve_commit_element_content[cve]['aftercommits']:
            for (filename,funcname) in cve_commit_element_content[cve]['aftercommits'][afterpatchcommit]:
                refcontent=cve_commit_element_content[cve]['aftercommits'][afterpatchcommit][(filename,funcname)]
                targetcontents=helper_zz.get_function_content(targetpath,filename,funcname)
                if len(targetcontents)>0:
                    result='N'
                    if refcontent in targetcontents:
                        result='P'
                        break
            if result == 'P':
                break
        cve_result[cve]=result
        if result== 'P':
            countTrue +=1
        elif result=='N':
            countFalse +=1
            Falselist += [cve]
        elif result=='None':
            countNone +=1
    with open(outputfile,'w') as f:
        for cve in cvelist:
            if cve in cve_result:
                f.write(cve+' '+str(cve_result[cve])+'\n')
    print 'countTrue:',countTrue,'countFalse:',countFalse,'countNone:',countNone
    print 'Falselist:',Falselist

def comparewithgroundtruth():
    resultpath=sys.argv[1]
    groundtruthpath=sys.argv[2]
    
    cve_result1={}
    with open(resultpath,'r') as f:
        f_buf=f.readlines()
    for line in f_buf:
        line=line[:-1]
        cve=line.split(' ')[0]
        if cve in cve_discarded:
            continue
        result=line.split(' ')[1]
        if result in ['P','N','None']:
            cve_result1[cve]=result 
        elif result=='True':
            cve_result1[cve]='P'
        elif result=='False' or result=='N':
            cve_result1[cve]='N'
        elif result == 'None':
            cve_result1[cve]='None'
        else:
            print 'invalid result:',line

    cve_result2={}
    with open(groundtruthpath,'r') as f:
        f_buf=f.readlines()
    for line in f_buf:
        line=line[:-1]
        cve=line.split(' ')[0]
        result=line.split(' ')[1]
        if result in ['P','N','None']:
            cve_result2[cve]=result
        if result=='True':
            cve_result2[cve]='P'
        elif result=='False' or result=='N':
            cve_result2[cve]='N'
        elif result == 'None':
            cve_result2[cve]='None'
    
    truepositive=[]
    falsepositive=[]
    truenegative=[]
    falsenegative=[]
    truenone=[]
    falsenone=[]

    for cve in cve_result1:
        result=cve_result1[cve]
        if result=='P':
            if result==cve_result2[cve]:
                truepositive += [cve]
            else:
                falsepositive += [cve]
        elif result=='N':
            if result==cve_result2[cve]:
                truenegative += [cve]
            else:
                falsenegative += [cve]
        elif result=='None':
            if result==cve_result2[cve]:
                truenone += [cve]
            else:
                falsenone += [cve]
    print 'truepositive:',len(truepositive)
    print 'falsepositive:',len(falsepositive)
    print 'truenegative:',len(truenegative)
    print truenegative
    print 'falsenegative:',len(falsenegative)
    print 'accuracy(without none):',(float)(len(truepositive)+len(truenegative))/(len(truepositive)+len(falsepositive)+len(truenegative)+len(falsenegative))
    print 'falsepositivelist:'
    print falsepositive
    print 'falsenegativelist:'
    print falsenegative

#[branch] [target kernel]
if __name__ == '__main__':
    compare_sourcecode(sys.argv[1],sys.argv[2])
