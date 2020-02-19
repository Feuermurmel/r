# r

Not to be confused with R from the [R Project](https://www.r-project.org).


## Introduction

`r` allows command to be executed on a remote host while giving it access to the contents of a local directory. This works by synchronizing the local directory's contents to the remote host before running the command and back after running the command.

`r` currently support linking a local directory with a directory on a single remote host through an `r.toml` file. The directory containing that file is used as the root for synchronization. Whenever `r` run, it will look for an `r.toml` file in the current directory and all its parents, using the closest one found.

`r` uses [Unison](https://www.cis.upenn.edu/~bcpierce/unison/index.html) to synchronize the local directory and the corresponding directory on the remote host. The same version of Unison needs to be available on `$PATH` on both the local and remote host.



## Example

Create an `r.toml` file via `r --init`:

```
$ r --init
Please enter the address of the remote directory in the form <hostname>:<path>:
? apu:test
r: Saving configuration to r.toml ...
```

Run a command locally and remotely:

```
$ uname
Darwin
$ r uname
r: Copying  from /Users/michi/test to //apu//home/michi/test
Linux
```

Create a script file locally and run it remotely. The script creates a file, which is synchronized back to the local directory:

```
$ cat > test.sh
#! /usr/bin/env bash
uname > uname.txt
$ chmod a+x test.sh 
$ r ./test.sh 
r: Copying test.sh from /Users/michi/test to //apu//home/michi/test
r: Copying uname.txt from //apu//home/michi/test to /Users/michi/test
$ cat uname.txt 
Linux
```

Running `r` from a subdirectory still uses the directory containing the `r.toml` file as the root for synchronization, but runs the command with the same working directory relative to that root:

```
$ mkdir foo
$ cd foo
$ r ls ..
r: Copying foo from /Users/michi/test to //apu//home/michi/test
foo
r.toml
test.sh
uname.txt
```
