import os,sys
import helper_zz
from shutil import copyfile
def compile_kernel(repo,commitlist,config,refkernelpath):
    kernel=helper_zz.get_repopath(repo)

    for commit in commitlist:
        print 'compile kernel',repo,commit,'with config',config
        string1='cd '+kernel+';git checkout -f '+commit
        helper_zz.command(string1)
        configdir=kernel+'/arch/arm64/configs/'
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
            if os.path.exists(kernel+'/output/vmlinux') and os.path.exists(kernel+'/output/arch/arm64/boot/Image'):
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

if __name__ == '__main__':
    repo=sys.argv[1]
    commitlist = [sys.argv[2]]
    config = sys.argv[3]
    refkernelpath = sys.argv[4]
    compile_kernel(repo,commitlist,config,refkernelpath)
