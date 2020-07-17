## Patchlocator

Open source patch presence test system. Given a patch commit in upstream repository, check if the patch is applied in downstream repository/source code snapshots.

If only binary image available, it can generate necessary inputs required by [E-Fiber](https://github.com/zhangzhenghsy/fiber-1/tree/E-Fiber), then we can make use of Fiber to generate binary signatures and match them with target binary image to get the results.

## 0x0 preparation

1. Environment Setup

The scripts are based on python2.7.

Pygments modules required. `sudo pip install Pygments` to install it.

2. Input file

patches info file: collect patch commits (manually or with the help of crawler) and store them in a file (eg, patches_info), which is used as input of 0x1. Patches info file should contains basic information of patches we want to locate. Specifically, in each line of patches file, there is a patch name (for example, CVE number), a corresponding repository name (for example, linux), and a corresponding commit number. We prepare an example file (./patches_info) which contains some CVEs in Android security bulletin.

3. Download kernel repositories.

1) The original reference kernels in patches info file, for example, linux. We can extract information of patch from it.

2) The reference/target reposotory where we want to locate/track the patches.

**Note**: Please set the repo paths in helper_zz.py get_repopath() function. With this function we can get the path to repository directory with the repo name.  The repo names in get_repopath() shoud be consistent with the names in patches info file.

4. Download target kernel snapshots (source code or binary inage) where we want to locate patches.

The target source code snapshot/binary image where we want to locate the patches.

## 0x1 Locating patches in a repository branch.
**required**: patches info file. It has been introduced in 0x0 section.

`~/Patchlocator$ python Patch_locator.py [repo] [branch] [patches info file]`

- *repo*: target repo name. For example, [msm-4.9](https://source.codeaurora.org/quic/la/kernel/msm-4.9/). Note that the repo name should be 
- *branch*: target branch name. For example, kernel.lnx.4.9.r25-rel. From the tag "LA.UM.8.3.r1", we know it corresponds [snapdragon 845, Android 10](https://wiki.codeaurora.org/xwiki/bin/QAEP/release). 
- *patches info file*: Path to required patches info file mentioned above.

**output**:
~/Patchlocator/output/upstreamresults/repo/branch. For example, output/upstreamresults/msm-4.9/kernel.lnx.4.9.r25-rel. It stores the results of patch locating.

Here are some examples of lines in output file:

1) CVE-2019-2287 f920e8539ff2 de6abb23dc05 (2019, 2, 22).

CVE-2019-2287 is patched with commit f920e8539ff2, which is in the upstream of target branch. Then f920e8539ff2 is merged into target branch with the merge commit de6abb23dc05. The commit date of de6abb23dc05 is 2/22/2019, thus we think CVE-2019-2287 is patched in target branch (kernel.lnx.4.9.r25-rel) at 2/22/2019.

2) CVE-2019-2328 None

We don't find patch-related files of CVE-2019-2328 in the branch. 

3) CVE-2019-2331 [] []

We find patch-related files of CVE-2019-2331 but we don't find the commit corresponding the patch in target branch.

## 0x2 Patch evolution tracker
**required**: output/upstreamresults/repo/branch. It's the output file of 0x1. Thus 0x1 should be executed in advance. This file will be imported automatically thus the user doesn't need to set the path manually.

`~/Patchlocator$ python Patch_evolution.py [repo] [branch] [patches info file]`

**output**:

Patch_evolution_[branch]_pickle. It's a file containing results of patch evolutions. (eg, output/Patch_evolution_kernel.lnx.4.9.r25-rel_pickle)


## 0x3.1 Locating patches in a source code snapshot

If the target kernel is a source code snapshot, it tries to match each patched function  version (identified  by  the  patch evolution tracker) to the target function.

**required**: output/Patch_evolution_[branch]_pickle file. It's the output file of 0x2. Thus 0x1, 0x2 should be executed in advance. This file will be imported automatically thus the user doesn't need to set the path manually.

`~/Patchlocator$ python Patch_matcher_src.py [branch] [targetkernel]`

- *targetkernel*: path to target source code kernel

**output**: 

[targetkernel]/matchresults where P means the related patch has been adopted, NE means the related patch has not been adopted and None means the patch-related function is not found in targetkernel.

## 0x3.2 Locating patches in a binary image

If the target kernel is a binary image, we need to make use of Fiber, please follow[E-Fiber](https://github.com/zhangzhenghsy/fiber-1/tree/E-Fiber) to install Fiber. To make things easier for users, we prepare a script (Fiberinput.py) to generate inputs of E-Fiber (reference source code/binary image,debug info...) as well as the corresponding E-Fiber commands.

**required**: Patch_evolution_[branch]_pickle file. It's the output file of 0x2. Thus 0x1, 0x2 should be executed in advance. This file will be imported automatically thus the user doesn't need to set the path manually.

`~/Patchlocator$ python Fiberinput.py [repo] [branch] [targetkernel]`

- *targetkernel*: path to target binary kernel. targetkernel/boot (binary image) is the binary image.

**Note**: The user needs to set [refsourcepath] [refkernelpath] [config] in Fiberinput.py. 
- *refsourcepath*: directory where we want to store reference kernel source code.
- *refkernelpath*: directory where we want to store reference kernel binary/symbol table/vmlinux/debuginfo.
- *config*: the config file name when compiling reference kernel. For example, sdm845-perf.

In Fiberinput.py there are 8 functions, you should execute them in order. [targetkernel] is only used in the last function.

- *get_refsources()*: used for getting patch-related source codes of reference kernel.
- *get_refkernels()*: used for getting binary image/symbol table/vmlinux of reference kernel. We will compile reference kernels here.

**Note**: Before execute get_refkernels(). Please execute the following command in advance.

`~/Patchlocator$ source environ.sh`

This command set environment variables required for compiling. You can use the provided GCC in shared [tools directory](https://drive.google.com/drive/folders/1AeoCTErs2ZuE9e-Ds88zOq57OqmB4RP2?usp=sharing) or download official GCC and hard-code the path in environ.sh.
- *Get_debuginfo()*: used for extracting debug info from vmlinux. You can use the provided addr2line in tools directory or download GCC by yourself and hard-code the path in environ.sh. 
- *get_patches()*: used for getting patch file. (for each CVE, each reference kernel, there is a patchfile).

- *generate_pickcommands()*: generate commands used in Fiber pick phase.

    **output**: Fiberinputs/pickcommands
- *generate_extcommands()*: generate commands used in Fiber extract phase.

    **output**: Fiberinputs/extcommands
- *generate_matchcommands_ref()*: generate match commands for reference kernels(mode 0 , 2 in Fiber).

    **output**: Fiberinputs/matchcommands_ref
- *generate_matchcommands_target()*: generate match commands for target kernels(mode 0 , 2 in Fiber).

    **output**: Fiberinputs/matchcommands_targetkernel

**Note**: when you have multiple target kernels with the same reference branch, you only need to execute generate_pickcommands()/generate_extcommands()/generate_matchcommands_ref once but execute generate_matchcommands_target() for each target.

Finally, you can execute the commands in E-Fiber directory, you can execute the commands in parallel to speed up the process. (For example, with the help of GNU Parallel).

**Note**: Since we match target kernel with signatures generated from multiple reference kernels, for each patch there are multiple results in targetkernel/matchresults. If one of them is 'P', then we think it's adopted in targetkernel.

## 0x4 Notes for other files

**helper_zz.py**: stores some helper functions related to git repository.

**src_parser.py**: stores some helper functions related to source code parse.

**sym_table.py**: stores some helper functions related to symbol table.

**compilekernels.py**: stores some helper functions related to kernel compilation.

**ext_sym**: used for generating symbol tables. We get it from Fiber.

**get_debuginfo.py**: stores some helper functions related to extracting and storing debug info files.
