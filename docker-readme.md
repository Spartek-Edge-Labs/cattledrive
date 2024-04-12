# Using cattleDrive in docker
Given some of the issues we've discovered with running some of the programs (especially `reposync`), we recommend running it in a docker container built from this repo.

## Building
```bash
# from the root of this repo
docker build -t cattledrive:0.1 .
```

## Pulling
We host a pre-built image available at:
> ghcr.io/spartek-edge-labs/cattledrive:latest

## Running

```bash
docker run -d --name dev9 -v $(pwd):/repo -v /home/mike/drop/cattleDrive:/home/mike/drop/cattleDrive -v /var/run/docker.sock:/var/run/docker.sock cattledrive:0.1 cattleDrive /repo/config.yml
```
A few things to note:
- it assumes you're running it from the current directory.  If you need to reference a config in another directory, edit the first `-v` call
- the 2nd `-v` call (to `/home/mike/drop/cattleDrive`) is so that when it downloads things, it pulls them to the right directory on the actual host
- the 3rd `-v` call is only needed if you plan to use the cattleDrive `oci` module to download docker containers.  Rather than trying to do anything tricky, we just use the host docker daemon.