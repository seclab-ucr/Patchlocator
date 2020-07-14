## Patchlocator

Open source patch presence test system. Given a patch commit in upstream repository, check if the patch is applied in downstream repository/source code snapshots.

If only binary image available, it can generate necessary inputs required by [E-Fiber](https://github.com/zhangzhenghsy/fiber-1/tree/E-Fiber), then we can make use of Fiber to generate binary signatures and match them with target binary image to get the results.

## 0x0 preparation

Collect patch commits (manually or with the help of crawler) and store them in 'patchdic', which is used as input of 0x1

Download kernel repository, including:
1) The original reference kernel where the patch commit exists, for example, linux. We can extract information of patch from it.
2) The reference/target kernel where we need to locate/track the patch. 
3) (optional) the target source code snapshot.
**Note**: Hardcode the repo paths in helper_zz.py get_repopath()

## 0x1 repository target
**required**: patchdic. patchdic should contains patch name (for example, CVE number), corresponding repository name (for example, linux), and corresponding commit number. We contain an example file which contains some CVEs in Android security bulletin. 
`~/Patchlocator$ python Patchlocator.py [repo] [branch]`

- *repo*: target repo name. For example, [msm-4.9](https://source.codeaurora.org/quic/la/kernel/msm-4.9/)
- *branch*: target branch name. For example, kernel.lnx.4.9.r25-rel. From the tag "LA.UM.8.3.r1", we know it corresponds [snapdragon 845, Android 10](https://wiki.codeaurora.org/xwiki/bin/QAEP/release). 

**output**:
~/Patchlocator/output/upstreamresults/repo/branch. For example, output/upstreamresults/msm-4.9/kernel.lnx.4.9.r25-rel

## 0x2 source code target
### step1:patch evolution in reference branch
**required**: upstreamresults/repo/branch
`~/Patchlocator$ python Patchevolution.py [repo] [branch]`

**output**:
1)cve_functioncontent_[branch+]_pickle. For example. output/cve_functioncontent_kernel.lnx.4.9.r25-rel_pickle.
used as input of step2
2)cve_commitelement_[branch+]_pickle. For example, output/cve_commitelement_kernel.lnx.4.9.r25-rel_pickle
used as input of 0x3

### step2:match with target source code snapshot
**required**: cve_functioncontent_[branch+]_pickle
`~/Patchlocator$ python Patchmatcher_src.py [branch] [targetkernel]`

- *targetkernel*: path to target source code kernel

**output**: 
[targetkernel]/matchresults

## 0x3 binary image target

If the target kernel is a binary image, we needs to make use of Fiber, please follow[E-Fiber](https://github.com/zhangzhenghsy/fiber-1/tree/E-Fiber). To make things easier for users, we prepare a script (Fiberinput.py) to generate inputs of E-Fiber (reference source code/binary image,debug info...) as well as the corresponding Fiber commands.

**required**: cve_commitelement_[branch+]_pickle
`~/Patchlocator$ python Fiberinput.py [repo] [branch] [target kernel path]`

**Note**: Hardcode [refsourcepath] [refkernelpath] [config] in Fiberinput.py
- *refsourcepath*:directory that stores reference kernel source code
- *refkernelpath*:directory that stores reference kernel binary/symbol table/vmlinux/debuginfo
- *config*:the config file name when compiling reference kernel

In Fiberinput.py there are 8 functions, you should execute them in order. [target kernel path] is only used in the last function.

- *get_refsources()*: used for getting patch-related source codes of reference kernel.
- *get_refkernels()*: used for getting binary image/symbol table/vmlinux of reference kernel. We will compile reference kernels here.
**Note**: Before execute get_refkernels(). Please execute the following command in advance.
`~/Patchlocator$ source ./environ.sh`
This command set environment variables required for compiling. You can use the provided GCC in [tools directory](https://drive.google.com/drive/folders/1AeoCTErs2ZuE9e-Ds88zOq57OqmB4RP2?usp=sharing) or download official GCC and hard-code the path in environ.sh.
- *Get_debuginfo()*: used for extracting debug info from vmlinux. You can use the provided addr2line in tools directory or download GCC by yourself and hard-code the path in environ.sh. 
- *get_patches()*: used for getting patch file. (for each CVE, each reference kernel).

- *generate_pickcommands()*: generate commands used in Fiber pick phase.

**output**: Fiberinputs/pickcommands
- *generate_extcommands()*: generate commands used in Fiber extract phase.

**output**: Fiberinputs/extcommands
- *generate_matchcommands_ref()*: generate match commands for reference kernels(mode 0 , 2 in Fiber).

**output**: Fiberinputs/matchcommands_ref
- *generate_matchcommands_target()*: generate match commands for target kernels(mode 0 , 2 in Fiber).

**output**: Fiberinputs/matchcommands_targetkernel

**Note**: when you have multiple target kernels with the same reference branch, you only need to execute generate_pickcommands()/generate_extcommands()/generate_matchcommands_ref once but execute generate_matchcommands_target() for each target.

Finally, you can execute the commands in E-Fiber directory, you can execute the commands in parallel to speed up the process. (For example, with the help of GNU Parallel) 
## 0x4 Notes for other files

**helper_zz.py**: stores some helper functions related to git repository.

**src_parser.py**: stores some helper functions related to source code parse.

**sym_table.py**: stores some helper functions related to symbol table.

**compilekernels.py**: stores some helper functions related to kernel compilation.

**ext_sym**: used for generating symbol tables. We get it from Fiber.

**get_debuginfo.py**: stores some helper functions related to extracting and storing debug info files.
