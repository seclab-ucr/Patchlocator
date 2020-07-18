## Patchlocator

Open source patch presence test system. Given a patch commit in upstream repository, check if the patch is applied in downstream kernels.

There are three kinds of kernels:

1. Repository. Patchlocator can make use of information of the patches (introduction message, commit date, changed lines, etc) to locate the corresponding commit in target repository. If the target kernel is a repository, please read section 0x0 and 0x1.

2. Source code snapshots. Patchlocator can determine if a patch is applied in a source code snapshot. If the target kernel is a source code snapshot, please read section 0x0 and 0x1, 0x2 and 0x3.1. 

3. Binary image snapshots. Patchlocator can determine if a patch is applied in a binary image with the helper of [E-Fiber](https://github.com/zhangzhenghsy/fiber-1/tree/E-Fiber). If the target kernel is a binary snapshot, please read section 0x0 and 0x1, 0x2 and 0x3.2.

The key insight is that 1) The functions in downstream are usually similar with those in corresponding upstream kernels, thus we can extract information of patched functions in upstream kernels to determine if the function is patched in downstream kernels. 2)(For source/binary snapshot targets) After a patch is applied in upstream kernel, the patched function may evolve with time. The patched function in target kernel may be similar to any version of patched function in upstream.  To achieve higher accuracy we keep track of the patched functions in upstream kernel and extract information from multiple versions of patched functions. 

## 0x0 Environment Setup

The scripts are based on python2.7.

Pygments modules required. `sudo pip install Pygments` to install it.

## 0x1 Locating patches in a repository branch.
**required**: 
1. Patches info file. Patches info file contains basic information of patches we want to locate. Specifically, in each line of patches file, there is a patch name (for example, CVE number), a corresponding repository name (for example, linux), and a corresponding commit number. We prepare an example file (./patches_info) which contains some CVEs in Android security bulletin.

2. The patch-related repositories in Patches info file. We can extract information of patch from it.

3. The repository where we want to locate patches.

**Note**: Please set the repo paths in helper_zz.py get_repopath() function. With this function we can get the path to the repository directory.  The repo names in get_repopath() should be consistent with those in patches info file.

`~/Patchlocator$ python Patch_locator.py [repo] [branch] [patches info file]`

- *repo*: target repo name. For example, [msm-4.9](https://source.codeaurora.org/quic/la/kernel/msm-4.9/).
- *branch*: target branch name. For example, kernel.lnx.4.9.r25-rel. From the tag "LA.UM.8.3.r1", we know it corresponds [snapdragon 845, Android 10](https://wiki.codeaurora.org/xwiki/bin/QAEP/release). 
- *patches info file*: Path to required patches info file mentioned above.

**output**:
~/Patchlocator/output/upstreamresults/repo/branch. It's a file that stores the results of patch locating for target branch. For example, examples/output/upstreamresults/msm-4.9/kernel.lnx.4.9.r25-rel.

Here are some examples of lines in output file:

1) CVE-2019-2287 f920e8539ff2 de6abb23dc05 (2019, 2, 22).

    CVE-2019-2287 is patched with commit f920e8539ff2, which is in the upstream of target branch. Then f920e8539ff2 is merged into target branch with the merge commit de6abb23dc05. The commit date of de6abb23dc05 is 2/22/2019, thus we think CVE-2019-2287 is patched in target branch (kernel.lnx.4.9.r25-rel) at 2/22/2019.

2) CVE-2019-10499 None

    We don't find patch-related files of CVE-2019-10499 in the branch. (Thus this patch may be not applicable for the branch) 

3) CVE-2019-2331 [] []

    We find patch-related files of CVE-2019-2331 but we don't find the commit corresponding the patch in target branch. (Thus this patch may have not been applied to the branch)

4) CVE-2019-2328 [] ['dce0f8189f75',...]

    We don't find the commit that can be strictly matched with the original patch commit. But we get several commits that may be related to the patch. The users can check them manually or ignore this patch for the moment.

## 0x2 Patch evolution tracker
**required**: 
1. output/upstreamresults/repo/branch. It's the output file of 0x1. Thus 0x1 should be executed in advance. This file will be imported automatically thus the user doesn't need to set the path manually.

2. The repository where we want to track evolutions of the patches. It should be the target repo in 0x1. (Only after we locate the patch we can keep track of it).

`~/Patchlocator$ python Patch_evolution.py [repo] [branch] [patches info file]`

**output**:

output/Patch_evolution_[branch]_pickle. It's a file containing results of patch evolutions. (eg, examples/output/Patch_evolution_kernel.lnx.4.9.r25-rel_pickle)


## 0x3.1 Locating patches in a source code snapshot

If the target kernel is a source code snapshot, we try to match each version of patch function (identified by the patch evolution tracker) with the target function. If any of them matches, we think the patch has been applied to target source code snapshot.

**required**: 
1. output/Patch_evolution_[branch]_pickle file. It's the output file of 0x2. Thus 0x1, 0x2 should be executed in advance. This file will be imported automatically thus the user doesn't need to set the path manually.

2. Target source code snapshot.

`~/Patchlocator$ python Patch_matcher_src.py [branch] [targetkernel1] [targetkernel2] ...`

- *targetkernel*: path to target source code kernel. We can have multiple target kernels here. (match them one by one)

**output**: 

[targetkernel]/matchresults where P means the related patch has been adopted, N means the related patch has not been adopted and None means the patch-related function is not found in targetkernel. (eg, examples/target_kernel_source/matchresults)

## 0x3.2 Locating patches in a binary image

If the target kernel is a binary image, we need to make use of [E-Fiber](https://github.com/zhangzhenghsy/fiber-1/tree/E-Fiber). To make things easier for users, we prepare a script (Fiber_input.py) to generate inputs for E-Fiber (reference source code/binary image,debug info...) as well as the corresponding E-Fiber commands.

**required**: 
1. Patch_evolution_[branch]_pickle file. It's the output file of 0x2. Thus 0x1, 0x2 should be executed in advance. This file will be imported automatically thus the user doesn't need to set the path manually.

2. The reference repository where we track the patches. We should have downloaded it in 0x1.

3. GCC tools which are used in compiling kernels. You can get the provided GCC by downloading provided [tools directory](https://drive.google.com/drive/folders/1AeoCTErs2ZuE9e-Ds88zOq57OqmB4RP2?usp=sharing) and copy the directory to ~/Patchlocator/tools. Or you can download GCC from official websites and set the path to GCC directory in environ.sh which sets environment variables required for compiling.

4. Target binary image.

`~/Patchlocator$ source environ.sh`

`~/Patchlocator$ python Fiber_input.py [repo] [branch] [targetkernel1] [targetkernel2] ...`

- *targetkernel*: path to target binary kernel. targetkernel/boot (binary image) is the binary image. We can have multiple target kernels here.

**Note**: The user can change the setting of [refsourcepath] [refkernelpath] [config] in Fiber_input.py.

- *refsourcepath*: directory where we want to store reference kernel source code.
- *refkernelpath*: directory where we want to store reference kernel binary/symbol table/vmlinux/debuginfo.
- *config*: the name of config file used in compiling reference kernels. For example, sdm845-perf. It must exists in the arch/arm64/configs directory of reference repository.


**output**: 

Fiberinputs/refsources: patch-related source codes of reference kernels. (eg. examples/Fiberinputs/refsources)

Fiberinputs/refkernels: binary image/symbol table/vmlinux of reference kernels. (eg. examples/Fiberinputs/refkernels. Due to the oversize of vmlinux/debug info file, we don't include them in example directory)

Fiberinputs/pickcommands: commands used in Fiber pick phase. (eg. examples/Fiberinputs/pickcommands)

Fiberinputs/extcommands: commands used in Fiber extract phase. (eg. examples/Fiberinputs/extcommands)

Fiberinputs/matchcommands_ref. Commands in Fiber match phase (with reference kernel). (eg. examples/Fiberinputs/matchcommands_ref)

Fiberinputs/matchcommands_target. Commands in Fiber match phase (with target kernel). (eg. examples/Fiberinputs/matchcommands_target)


Finally, you can execute the commands in E-Fiber directory, the commands can be executed in parallel to speed up the process. (For example, with the help of GNU Parallel).

**Note**: Since we match target kernel with signatures generated from multiple reference kernels, for each patch there are multiple results in targetkernel/matchresults. If any of them is 'P', then we think it's adopted in targetkernel.

## 0x4 Overall patch locator

To make things easier for users, we prepare a script that combines all steps above.

**required**:
1. Patches info file.

2. The patch-related repositories in Patches info file.

3. The repository where we want to locate/keep track of patches.

4. The target source code/binary snapshots.

5. Downloading provided [tools directory](https://drive.google.com/drive/folders/1AeoCTErs2ZuE9e-Ds88zOq57OqmB4RP2?usp=sharing) and copy the directory to ~/Patchlocator/tools

All of them have been introduced above.

`~/Patchlocator$ source environ.sh`

`~/Patchlocator$ python Overall_patch_locator.py [mode] [repo] [branch] [patches info file] [target kernel1] [target kernel2] ...`

- *mode*: 'repo', 'source', 'binary'. Each corresponds a target type

## 0x5 Notes for other files

**helper_zz.py**: stores some helper functions related to git repository.

**src_parser.py**: stores some helper functions related to source code parse.

**sym_table.py**: stores some helper functions related to symbol table.

**compile_kernels.py**: stores some helper functions related to kernel compilation.

**ext_sym**: used for generating symbol tables. We get it from Fiber.

**get_debuginfo.py**: stores some helper functions related to extracting and storing debug info files.
