---
name: safety_policy_blocks_rm_rf
description: Execution environment blocks dangerous commands like rm -rf
type: memory
---

Attempts to run `rm -rf` are blocked with 'Dangerous command has been blocked!'. Use non-recursive or scoped cleanup instead. `rmdir project/tmp` failed because the directory was not empty.
