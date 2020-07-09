## Patchlocator

Open source patch presence test system. Given a patch commit in upstream repository, check if the patch is applied in downstream repository/source code snapshots.

If only binary image available, it can generate necessary inputs required by Fiber(https://github.com/fiberx/fiber),then we can make use of Fiber to generate binary signatures.

## 0x0 preparation

Collect patch commits (manually or with the help of crawler) and store them in 'patchdic', which is used as input of 0x1

Download kernel repository, including:
1) The original reference kernel where the patch commit exists, for example, linux. We can extract information of patch from it.
2) The reference/target kernel where we need to locate/track the patch. 
3) (optional) the target source code snapshot.
**Note**: Hardcode the repo paths in helper_zz.py get_repopath()

## 0x1 repository target
**required**: patchdic
`~/Patchlocator$ python Patchlocator.py [repo] [branch]`

- *repo*: target repo name. 
- *branch*: target branch name.

**output**:
~/Patchlocator/upstreamresults/repo/branch

## 0x2 source code target
# step1:patch evolution in reference branch
**required**: upstreamresults/repo/branch
`~/Patchlocator$ python Patchevolution.py [repo] [branch]`

**output**:
1)cve_functioncontent_[branch+]_pickle
used as input of step2
2)cve_commitelement_[branch+]_pickle
used as input of 0x3

## step2:match with target source code snapshot
**required**: cve_functioncontent_[branch+]_pickle
`~/Patchlocator$ python Patchmatcher_src.py [branch] [targetkernel]`

- *targetkernel*: path to target source code kernel

**output**: 
[targetkernel]/matchresults

## 0x3 binary image target
**required**: cve_commitelement_[branch+]_pickle
`~/Patchlocator$ python Fiberinput.py [repo] [branch]`

**Note**: Hardcode [refsourcepath] [refkernelpath] [config] in Fiberinput.py
- *refsourcepath*:directory that stores reference kernel source code
- *refkernelpath*:directory that stores reference kernel binary/symbol table/vmlinux/debuginfo
- *config*:the config file name when compiling reference kernel

