
import os,sys
import pickle
from shutil import copyfile

def get_example_refsourcecode():
    sourcepath = '/data1/zheng/target/samsung/samsungS9/samsungS9_china/sourcecode/20190717/'
    targetpath = './examples/target_kernel_source/'
    
    branch = 'kernel.lnx.4.9.r25-rel'
    pickle_in = open("examples/output/Patch_evolution_"+branch+"_pickle",'rb')
    cve_commit_element_content = pickle.load(pickle_in)
    for cve in cve_commit_element_content:
        for afterpatchcommit in cve_commit_element_content[cve]['aftercommits']:
            for (filename,funcname) in cve_commit_element_content[cve]['aftercommits'][afterpatchcommit]:
                directorypath = targetpath+'/'+'/'.join(filename.split('/')[:-1])
                if not os.path.exists(directorypath):
                    os.makedirs(directorypath)
                print sourcepath+'/'+filename
                if not os.path.exists(targetpath+'/'+filename):
                    if os.path.exists(sourcepath+'/'+filename):
                        copyfile(sourcepath+'/'+filename,targetpath+'/'+filename)
                    else:
                        print sourcepath+'/'+filename,'not exists'
get_example_refsourcecode()

