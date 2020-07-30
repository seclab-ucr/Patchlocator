## Patchlocator

Open source patch presence test system. Given a patch commit in upstream repository, check if the patch is applied in downstream kernels.

There are three kinds of kernels:

1. Repository. Patchlocator can make use of information of the patches (introduction message, commit date, changed lines, etc.) to locate the corresponding commit in target repository. If the target kernel is a repository, please read section 0x0 and 0x1.

2. Source code snapshots. Patchlocator can determine if a patch is applied in a source code snapshot. If the target kernel is a source code snapshot, please read section 0x0 and 0x2. 

3. Binary image snapshots. Patchlocator can determine if a patch is applied in a binary image with the helper of [E-Fiber](https://github.com/zhangzhenghsy/fiber-1/tree/E-Fiber). If the target kernel is a binary snapshot, please read section 0x0 and 0x3.

The key insights are:

1. The functions in downstream are usually similar with those in corresponding upstream kernels, thus we can extract information of patched functions in upstream kernels to determine if the function is patched in downstream kernels. 

2. (For source/binary snapshot targets) After a patch is applied in upstream kernel, the patched function may evolve with time. The patched function in target kernel may be similar to any version of patched function in upstream kernel. To achieve higher accuracy, we keep track of the patched functions in upstream kernel and extract information from multiple versions of patched functions. 

## 0x0 Environment Setup

The scripts are based on python2.7.

Pygments modules required. `sudo pip install Pygments` to install it.

## 0x1 Locating patches in a repository branch.

To locate a patch in target kernels, at first, we need to collect information of the patches. Specifically, this tool requires the corresponding patch commit number in upstream repository. We can get them from vulnerability/patch release websites (e.g., [Android security bulletin](https://source.android.com/security/bulletin) and [NATIONAL VULNERABILITY DATABASE](https://nvd.nist.gov/vuln/full-listing)). For each vulnerability there is usually a link to the patch commit in upstream kernel repository. 

With the commit number, we can extract useful information (e.g., introduction message) about the patch from upstream repository, then we can make use of them to locate the patch in a given target repository/branch. Note that this tool only requires the commit number. For any given patch commit, whether it is a security patch or other bug fix, we can locate it in target repository. 
 
**required**: 

1. [targetrepo]: The target repository where we want to locate patches (which may or may not be present).

2. [patch info file]: Patches info file contains basic information of patches we want to locate. Specifically, in each line of patch info file, there is a patch name (for example, CVE number), a corresponding upstream repository name (for example, Linux), and a corresponding commit number. We prepare an example file (./patches_info) which contains some CVEs in Android security bulletin.

3. The patch-related upstream repositories in Patches info file. We can extract information of patch from it.

**Note**: Please set the repo paths in repo_path.txt. With this file we can get the path to the repository directory.  The repo names in repo_path.txt should be consistent with those in patch info file.

**usage**:

`~/Patchlocator$ python Overall_patch_locator.py repo [targetrepo] [targetbranch] [patch info file]`

- *targetrepo*: Target repo name. For example, [msm-4.9](https://source.codeaurora.org/quic/la/kernel/msm-4.9/).
- *targetbranch*: Target branch name. For example, kernel.lnx.4.9.r25-rel. From the tag "LA.UM.8.3.r1", we know it corresponds [snapdragon 845, Android 10](https://wiki.codeaurora.org/xwiki/bin/QAEP/release). 
- *patch info file*: Path to required patch info file mentioned above.

**example**:
`~/Patchlocator$ python Overall_patch_locator.py repo msm-4.9 kernel.lnx.4.9.r25-rel patches_info`

**output**:
~/Patchlocator/output/upstreamresults/[targetrepo]/[targetbranch]. It is a file that stores the results of patch locating for target branch. For example, examples/output/upstreamresults/msm-4.9/kernel.lnx.4.9.r25-rel.

Here are some example lines in output file:

1) CVE-2019-2287 de6abb23dc05 (2019, 2, 22).

    CVE-2019-2287 is patched with commit de6abb23dc05. The commit date of de6abb23dc05 is 2/22/2019, thus we think CVE-2019-2287 is patched in target branch (kernel.lnx.4.9.r25-rel) on 2/22/2019.

2) CVE-2019-10499 None

    We do not find patch-related files of CVE-2019-10499 in the branch. (Thus, this patch is not applicable for the branch) 

3) CVE-2019-2331 []

    We find patch-related files of CVE-2019-2331 but we do not find the commit corresponding the patch in target branch. Thus, this patch may have not been applied to the branch. Note that it does not necessarily means that the target branch is vulnerable. Maybe the patch-related file won't be compiled, or is removed in the development of the branch.

4) CVE-2019-2328 ['dce0f8189f75',...]

    We do not find any commit that can be strictly matched with the original patch commit. But we get several commits that may be related to the patch. The users can check them manually or ignore this patch for the moment.

## 0x2 Locating patches in a source code snapshot

When target kernel is a source code snapshot, an intuitive method is doing string match of patched functions in target kernel. However, there are two difficulties: 1) Downstream target kernel may do adaptations thus the patch-related function may be different from that in upstream kernel 2) Patch-related functions may evolve after the patch applied, thus there are multiple versions of patched functions. If we only match the function just after the patching with target kernel, we may get false negative results.

To solve the above problems, 1) we choose a reference upstream repository which is similar to target kernel. We extract patched functions from the reference repository instead of the original upstream repository. 2) we track evolution of patched functions in reference repository to collect multiple versions of patched functions.

For example, we want to determine if a CVE is patched in a source code snapshot of OEM phone. The CVE is originally patched in Linux kernel (original upstream kernel), and then the patch is propagated to Qualcomm kernel which is the direct upstream kernel of the OEM kernel. We locate the patch in the corresponding Qualcomm branch (reference upstream kernel) and track the patch evolution on it. After that we extract all versions of patched functions in the Qualcomm branch and match them with target OEM source code snapshot. If any of them matches, we think the CVE is patched in the target source code snapshot.

**required**: 
1. [reference repo]: The repository where we want to track evolutions of the patch-related functions.

2. [patch info file]: It has been introduced in 0x1.

3. [target kernel]: Target source code kernel.

**usage**:

`~/Patchlocator$ python Overall_patch_locator.py source [reference repo] [reference branch] [patch info file] [target kernel1] [target kernel2] ...`

- *reference repo*: The name of reference repository.
- *reference branch*: The name of reference branch where we want to track evolutions of the patches.
- *patch info file*: The path to patch info file.
- *target kernel*: The path to target source code kernel. We can have multiple target kernels here. (match them one by one).

**example**:
`~/Patchlocator$ python Overall_patch_locator.py source msm-4.9 kernel.lnx.4.9.r25-rel patches_info ./examples/target_kernel_source/`

**output**:

[targetkernel]/matchresults where P means the related patch has been adopted, N means the related patch has not been adopted and None means the patch-related function is not found in targetkernel. (e.g. examples/target_kernel_source/matchresults)


## 0x3 Locating patches in a binary image

Like source code snapshot, when the target kernel is a binary image snapshot, we need to pick a reference repository/branch and track patch-related function evolutions on it. However, string matching is not feasible for a binary target, thus we make use of [E-Fiber](https://github.com/zhangzhenghsy/fiber-1/tree/E-Fiber) to transform source code change sites to binary signatures. To make things easier for users, we prepare a script (Fiber_input.py) to generate inputs for E-Fiber (reference source code/binary image, debug info...) as well as the corresponding E-Fiber commands.

**required**:
1. [reference repo]: The repository where we want to track evolutions of the patches.

2. [patch info file]: It has been introduced in 0x1.

3. [target kernel]: Target binary kernel. We can have multiple target kernels here.

4. Download GCC tools which are used in cross-compiling kernels and set up the environmental variables. Execute the following command to get them and checkout to a stable version.

`~/Patchlocator$ cd helpers;git clone https://android.googlesource.com/platform/prebuilts/gcc/linux-x86/aarch64/aarch64-linux-android-4.9;git checkout -f origin/ndk-release-r21;source environ.sh`

**usage**:

`~/Patchlocator$ python Overall_patch_locator.py binary [reference repo] [reference branch] [patch info file] [config] [target kernel1] [target kernel2] ...`

- *reference repo*: The name of reference.
- *reference branch*: The name of reference branch where we track the patches.
- *patch info file*: The path to patch info file.
- *config*: The name of config file used in compiling reference kernels. For example, sdm845-perf. It must exist in the arch/arm64/configs directory of reference repository.
- *target kernel*: The path to target binary code kernel. [target kernel]/boot (binary image) is the binary image. (e.g. examples/target_kernel_binary/).  We can have multiple target kernels here.

**example**:
`~/Patchlocator$ python Overall_patch_locator.py binary msm-4.9 kernel.lnx.4.9.r25-rel patches_info sdm845-perf ./examples/target_kernel_binary/`

**output**: 

Fiberinputs/pickcommands: commands used in Fiber pick phase. (e.g., examples/Fiberinputs/pickcommands)

Fiberinputs/extcommands: commands used in Fiber extract phase. (e.g., examples/Fiberinputs/extcommands)

Fiberinputs/matchcommands_ref. Commands in Fiber match phase (with reference kernel). (e.g., examples/Fiberinputs/matchcommands_ref)

Fiberinputs/matchcommands_target. Commands in Fiber match phase (with target kernel). (e.g., examples/Fiberinputs/matchcommands_target)


Finally, you can execute the commands in E-Fiber directory, the commands can be executed in parallel to speed up the process. (For example, with the help of GNU Parallel).

**Note**: Since we match target kernel with signatures generated from multiple reference kernels, for each patch there are multiple results in targetkernel/matchresults. If any of them is 'P', then we think it's adopted in targetkernel.


## 0x4 Notes for other files

**Patch_locator.py**: stores helper function that locates a patch in given branch.

**Patch_evolution.py**: stores helper function that tracks evolution of given patch-related function in the given branch.

**Fiber_inputs.py**: stores helper function that generates input of E-Fiber.

**Patch_matcher_src**: stores helper function that does string match between patch-related functions in reference kernel and those in target kernel.

**helpers/helper_zz.py**: stores some helper functions related to git repository.

**helpers/src_parser.py**: stores some helper functions related to source code parse.

**helpers/sym_table.py**: stores some helper functions related to symbol table.

**helpers/compile_kernels.py**: stores some helper functions related to kernel compilation.

**helpers/ext_sym**: used for generating symbol tables. We get it from Fiber.

**helpers/get_debuginfo.py**: stores some helper functions related to extracting and storing debug info files.
