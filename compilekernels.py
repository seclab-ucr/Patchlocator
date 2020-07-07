import os,sys
import helper_zz
from shutil import copyfile
def compile_4_14():
    repo='msm-4.14'
    repo2=repo[4]+'_'+repo[6]
    kernel='/home/zheng/fiberweiteng/msm-4.14/'
    
    with open('/home/zheng/fiberweiteng/commitresults/compiledkernels'+repo2,'r') as f:
        s_buf=f.readlines()
    for line in s_buf:
        if len(line.split(' ')[0])==12:
            commitlist += [line[:12]]

    for commit in commitlist:
        #if os.path.exists('/data/zheng/msm-4.14/'+commit):
        #    continue
        print commit
        string1='cd '+kernel+';git checkout -f '+commit
        helper_zz.command(string1)
        string1='cd '+kernel+';python patch_ca_kernel_'+repo2+'.py;'
        result=helper_zz.command(string1)
        configdir=kernel+'arch/arm64/configs/'
        configfilelist=os.listdir(configdir)
        if os.path.exists(configdir+'/vendor'):
            configfilelist += os.listdir(configdir+'/vendor')
        if os.path.exists(configdir+'vendor/sm8150_defconfig'):
            configfile='sm8150_defconfig'
            string1='cd '+kernel+';cp arch/arm64/config/vendor/sm8150_defconfig arch/arm64/config/sm8150_defconfig'
            helper_zz.command(string1)
        elif os.path.exists(configdir+'sm8150_defconfig'):
            configfile='sm8150_defconfig'
        elif os.path.exists(configdir+'sdm855_defconfig'):
            configfile='sdm855_defconfig'
        elif os.path.exists(configdir+'defconfig'):
            configfile='defconfig'
        else:
            print 'no suitable config file for',commit
            continue
        print commit
        print 'config file:',configfile
        string1='cd '+kernel+';python patch_ca_kernel_4_14.py;make '+configfile+';cp .config output/.config;rm .config;rm output/vmlinux;rm output/arch/arm64/boot/Image;make -j32 O=output >compileresults'
        result=helper_zz.command(string1)
        #print result
        if os.path.exists(kernel+'output/vmlinux') and os.path.exists(kernel+'output/arch/arm64/boot/Image'):
            print 'compile success for',commit
            string1='cd '+kernel+';python copy.py'
            helper_zz.command(string1)
            print 'copy done'
        else:
            print 'compile fail for',commit

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


#def get_cveunpatchcommits(repo,branch):
#    cve_unpatchcommits = {}
#    filepath = 'upstreamresults/'+repo+'/'+branch
#    with open(filepath,'r') as f:
#        s_buf = f.readlines()
#    for line in s_buf:
#        line=line[:-1]
#        if "CVE" not in line:
#            continue
#        if "too many candidates" in line:
#            continue
#        if "//" in line:
#            line=line.split("//")[0]
#        if '[]' in line:
#            continue
#        if '(' not in line:
#            continue
        #print line
#        cve=line.split(' ')[0]
#        patchcommit = line.split(' ')[2]
#        repopath = helper_zz.get_repopath(repo)
#        unpatchcommit = helper_zz.get_previouscommit(repopath,patchcommit)
#        cve_unpatchcommits[cve] = unpatchcommit
#        print cve,'patchcommit:',patchcommit,'beforepatchcommit:',unpatchcommit
#    return cve_unpatchcommits

def get_uncompiledcommits(branch):
    commitlist = []
    filepath = "find_compiledkernels_"+branch+"_debuginfo"
    with open(filepath,"r") as f:
        s_buf =f.readlines()
    for line in s_buf:
        line= line[:-1]
        if " should be compiled" in line:
            commit = line[6:18]
            commitlist += [commit]
    return commitlist
def compile_4_9():
    #commitlist=['230f5ef8edc6','74a7eba03f0a','e09a610dd731']
    #commitlist=[]
    #cve_beforepatch,commitlist=get_beforecommits("msm-4.9_kernel.lnx.4.9.r25-rel")
    #commitlist = get_uncompiledcommits("kernel.lnx.4.9.r25-rel")
    #commitlist = ['854975ee1bbf']
    print len(commitlist)
    repo='msm-4.9'
    #repo='msm-4.4'
    repo2=repo[4]+'_'+repo[6]
    kernel='/home/zheng/fiberweiteng/'+repo+'/'
    #with open('/home/zheng/fiberweiteng/commitresults/compiledkernels'+repo2,'r') as f:
    #    s_buf=f.readlines()
    #for line in s_buf:
    #    if len(line.split(' ')[0])==12:
    #        commitlist += [line[:12]]
    #commitlist = list(set(commitlist))
    #commitlist = ['83ca41f3fcc1','78667dedc643','46838cf1ad7f','8f8b5140bd94','230f5ef8edc6','e7da47f2cfe8','ded3533c0e75','d31e7c9af651','98ae89537923','696d37fc99f8','192abd85bbdd','e26d8b2c8093','34c5814e8243','f07a15734ce7','a5bdc9ebe5cf','4077a94c3136','f332617ebb03','c36d54c34fef','de6abb23dc05','6c6aaf4e8330','19a8101c2309','1d7b97667c43','7bb76790999d','d448f2cd9ba6','29d5ef6b97cc','e276e60d848d','6a58381f3569','146de2055790','d6d7f6f8d00c']
    print len(commitlist)
    #commitlist=['406cc39b36ea']
    for commit in commitlist:
        #if os.path.exists('/data/zheng/msm-4.9/'+commit+'_msm8953'):
        #    continue
        print commit
        string1='cd '+kernel+';git checkout -f '+commit
        helper_zz.command(string1)
        configdir=kernel+'arch/arm64/configs/'
        #if not os.path.exists(configdir+'msm8953_defconfig'):
        #    print configdir+'msm8953_defconfig not exists for ',commit 
        #    continue
        #if os.path.exists(configdir+'sdm845_defconfig'):
        #    configfile='sdm845_defconfig'
        #elif os.path.exists(configdir+'msmskunk-perf_defconfig'):
        #    configfile='msmskunk-perf_defconfig'
        #else:
        #    print 'no suitable config file for',commit
        #    continue
        string1='cd '+kernel+';python patch_ca_kernel_'+repo2+'.py;'
        result=helper_zz.command(string1)
        configfilelist=os.listdir(configdir)
        for configfile in configfilelist:
            if configfile not in ['sdm845-perf_defconfig']:
                continue
            #if configfile not in ['msm_defconfig','msm-perf_defconfig','sdm660_defconfig','sdm660-perf_defconfig']:
            #if configfile =='sdm845_defconfig'  or configfile=='defconfig' or configfile=='ranchu64_defconfig':
                continue
            newpath='/data1/zheng/'+repo+'/'+commit+'_'+configfile[:-10]
            if os.path.exists(newpath):
                print newpath,'already exists'
                continue
            print configfile
            string1='cd '+kernel+';make '+configfile+' O=output;rm output/vmlinux;rm output/arch/arm64/boot/Image;make -j30 O=output >compileresults'
            result=helper_zz.command(string1)
            #print result
            if os.path.exists(kernel+'output/vmlinux') and os.path.exists(kernel+'output/arch/arm64/boot/Image'):
                print 'compile success for',commit,configfile
                oldpath=kernel+'/output'
                #newpath='/data/zheng/msm-4.9/'+commit+'_'+configfile[:-10]
                os.mkdir(newpath)
                copyfile(oldpath+'/arch/arm64/boot/Image',newpath+'/boot')
                copyfile(oldpath+'/System.map',newpath+'/System.map')
                copyfile(oldpath+'/vmlinux',newpath+'/vmlinux')
                copyfile(oldpath+'/.config',newpath+'/.config')
            #string1='cp '+kernel+' -r /data/zheng/msm-4.9/'+commit+'_msm8953'
            #copyfile(oldpath+'/arch/arm64/boot/Image',newpath+'/boot')
            #copyfile(oldpath+'/System.map',newpath+'/System.map')
            #helper_zz.command(string1)
                #print 'copy done'
            else:
                print 'compile fail for',commit,configfile

def compile_4_9_msm8953():
    commitlist=['bd618d9d5201','83ca41f3fcc1','2c2400da9378','a023342c6f6c','d300d690ad61','78667dedc643','46838cf1ad7f','8f8b5140bd94','230f5ef8edc6','e7da47f2cfe8','2ba006048d4a','ded3533c0e75','d31e7c9af651','98ae89537923','696d37fc99f8','192abd85bbdd','e26d8b2c8093','34c5814e8243','e41d512953ef','f07a15734ce7','2502deacc774','38a1d53987e4','1f964e916d09','1a0bde7e83f2','1b473b19279a','d3f2e5c7d0ff','a8f191ba69f3','4661688f12cb','377343da9f80','3186af9f3ece','668263b017b5','32fbe87c43a6','74a7eba03f0a']
    #commitlist=['69e00cef97bb']
    kernel='/data/zheng/msm-4.9/'
    for commit in commitlist:
        print commit
        string1='cd '+kernel+';cp -r '+commit+' '+commit+'_msm8953'
        helper_zz.command(string1)
        print 'copy completed'
        kernelpath=kernel+commit+'_msm8953'
        configfile='msm8953_defconfig'
        string1='cd '+kernelpath+';make mrproper;make msm8953_defconfig O=output;rm output/vmlinux;rm tmp_o;rm output/arch/arm64/boot/Image;make -j32 O=output >compileresults'
        result=helper_zz.command(string1)
        print result
        if os.path.exists(kernelpath+'/output/vmlinux') and os.path.exists(kernelpath+'/output/arch/arm64/boot/Image'):
            print 'compile success for',commit
        else:
            print 'compile fail for',commit
def compile_4_4():
    #commitlist=os.listdir('/data/zheng/msm-4.4/')
    commitlist=['e130a419a73a','14efecefa760','23c20487892d','25c69bf35b1a','4049db73f1a3','1f9a2cdec9bc','a441ab05d2b7','1c7b64cd1038','74482c64afce','991119cca552','51568631aa42','726ce06fae16','41155385a0a2','601ae4876403','2d6cc4c81b1c','cfcc5dbf739f','4036bbe404a4','c44da670c287','03ef042130c9','a8c750891d8d','376782b887e1','3b8fc0b7a3fc','bbaf766c22fc','a66d8962f27e','869b2c41ea91','0fd6f3e2ecac','6844af58b62a','0b402f74a04f','1a66c5978621','361feeef4f86','c9c3923eb4c7','5e64690cac75','e2c952227890','fe1277ee048e','2d8f5e66d396','73b996d01780','406cc39b36ea']
    kernel='/home/zheng/fiberweiteng/msm-4.4/'
    print len(commitlist)
    for commit in commitlist:
        if os.path.exists('/data/zheng/msm-4.4/'+commit+'_msmcortex'):
            continue
        print commit
        string1='cd '+kernel+';git checkout -f '+commit
        helper_zz.command(string1)
        #kernel='/data/zheng/msm-4.4/'+commit+'/'
        configdir=kernel+'arch/arm64/configs/'
        #if os.path.exists(configdir+'msm_defconfig'):
        #    configfile='msm_defconfig'
        #else:
        #    print 'no suitable config file for',commit
        #    continue
        configfile='msmcortex_defconfig'
        string1='cd '+kernel+';make mrproper;make '+configfile+' O=output;rm output/vmlinux;rm output/arch/arm64/boot/Image;make -j32 O=output >compileresults'
        result=helper_zz.command(string1)
        #print result
        if os.path.exists(kernel+'output/vmlinux') and os.path.exists(kernel+'output/arch/arm64/boot/Image'):
            print 'compile success for',commit
            #string1='cd '+kernel+';python copy.py'
            string1='mkdir'+' /data/zheng/msm-4.4/'+commit+'_msmcortex;'
            string1 += 'cp '+kernel+'/output/vmlinux /data/zheng/msm-4.4/'+commit+'_msmcortex/vmlinux;'
            string1 += 'cp '+kernel+'/output/System.map /data/zheng/msm-4.4/'+commit+'_msmcortex/System.map;'
            string1 += 'cp '+kernel+'/output/arch/arm64/boot/Image /data/zheng/msm-4.4/'+commit+'_msmcortex/boot;'
            helper_zz.command(string1)
            print 'copy done'
        else:
            print 'compile fail for',commit
#compile_4_14()
#compile_4_9()
move_beforecommits('msm-4.9','kernel.lnx.4.9.r25-rel')
#compile_4_4()
#compile_4_9_msm8953()
