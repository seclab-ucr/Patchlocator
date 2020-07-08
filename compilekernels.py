import os,sys
import helper_zz
from shutil import copyfile

def get_beforecommits(repo,branch):
    filepath = "Patchinfo_"+repo+'_'+branch
    cve_beforepatch = {}
    beforecommitlist = []
    with open(filepath,"r") as f:
        s_buf = f.readlines()
    for line in s_buf:
        line = line[:-1]
        if 'CVE-' in line:
            cve = line
        elif "beforecommit: " in line:
            beforecommit = line.split("beforecommit: ")[1]
            cve_beforepatch[cve]=beforecommit
            beforecommitlist += [beforecommit]
    return cve_beforepatch,beforecommitlist

def move_beforecommits(repo,branch):
    print repo,branch
    repo2= repo[4]+'_'+repo[6:]
    cve_beforepatch,beforecommitlist = get_beforecommits(repo,branch)
    for cve in os.listdir('/data/zheng/patchcommits'+repo2):
        print cve
        nopatchkernelpath = '/data/zheng/patchcommits'+repo2+'/'+cve+'/nopatchkernel'
        if not os.path.exists(nopatchkernelpath):
            os.mkdir(nopatchkernelpath)
        beforecommit = cve_beforepatch[cve]
        beforecommits = os.listdir('/data1/zheng/'+repo+'/')
        beforecommits = [commit for commit in beforecommits if beforecommit in commit]
        for beforecommit in beforecommits:
            print beforecommit
            sourcepath = '/data1/zheng/'+repo+'/'+beforecommit
            targetpath = nopatchkernelpath+'/'+beforecommit
            if not os.path.exists(targetpath):
                os.mkdir(targetpath)
            copyfile(sourcepath+'/boot',targetpath+'/boot')
            copyfile(sourcepath+'/System.map',targetpath+'/System.map')

def compile_kernel(repo,commitlist,config,refkernelpath):
    print len(commitlist)
    kernel=helper_zz.get_repopath(repo)
    for commit in commitlist:
        print commit
        string1='cd '+kernel+';git checkout -f '+commit
        helper_zz.command(string1)
        configdir=kernel+'arch/arm64/configs/'
        string1='cd '+kernel+';python patch_ca_kernel.py;'
        helper_zz.command(string1)
        configfilelist=os.listdir(configdir)
        for configfile in configfilelist:
            if config not in configfile:
                continue
            newpath=refkernelpath+'/'+commit+'_'+configfile[:-10]
            if os.path.exists(newpath+'/boot'):
                print newpath,'already exists'
                continue
            string1='cd '+kernel+';make '+configfile+' O=output;rm output/vmlinux;rm output/arch/arm64/boot/Image;make -j30 O=output >compileresults'
            helper_zz.command(string1)
            if os.path.exists(kernel+'output/vmlinux') and os.path.exists(kernel+'output/arch/arm64/boot/Image'):
                print 'compile success for',commit,configfile
                oldpath=kernel+'/output'
                #newpath='/data/zheng/msm-4.9/'+commit+'_'+configfile[:-10]
                os.mkdir(newpath)
                copyfile(oldpath+'/arch/arm64/boot/Image',newpath+'/boot')
                copyfile(oldpath+'/System.map',newpath+'/System.map')
                copyfile(oldpath+'/vmlinux',newpath+'/vmlinux')
                copyfile(oldpath+'/.config',newpath+'/.config')
            else:
                print 'compile fail for',commit,configfile

#compile_4_4()
#compile_4_9_msm8953()
