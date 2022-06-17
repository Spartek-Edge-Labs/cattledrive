# cattleDrive
System provisioning artifact aggregator.

A tool designed to declaratively pull artifacts needed (yum repos, web directories, docker containers, helm charts, etc.) needed for green field or air-gapped deployments.  Inspired by:

- [Rancher Federal's Hauler](https://github.com/rancherfederal/hauler)
- [Pulp](https://pulpproject.org/)
- A variation of ever script I've ever written on every project I've ever been on

The script should be generally idempotent, but recommend you test on a fresh folder before using it as a mirror script. See [TODO](./TODO.md) for things that could use improvement.

## Usage
```bash
$ ./cattleDrive.py config.yml
```

## Config
The config file in this repo has examples of every type of "mirror" protocol thats currently implemented. See it for examples and modify to suit.

## Mirror Protocols

### `wget`
Requires the `wget` command in your `$PATH`.  Does a recursive download of the path specified to the directory specified, stripping out all of the dirs in the `source` path.  Good for any directory listing on a web server or similar.

**Example**
```yaml
mirror:
  - type: wget
    src: https://mirrors.rit.edu/centos/7/os/x86_64/repodata/ # web url that you want to download. Note that:
    dest: /home/mike/drop/wget/ #Local folder path where you want the files copied
    # if you omit the trailing "/" at the end, you'll get the html file that is the directory listing or the web page
```


### `rsync`
Requires the `rsync` command in your `$PATH`.  Does an rysnc copy from `src` to `dest` with the following arguments:
```bash
$ rsync -avzP --delete $src $dest
```

`src` or `dest` can be *any* RSYNC supported URI (as the script is just passing those values whole-hog); `rsync://`, local file, or `user@server:/file` SSH formats are all supported.  We do not support passing passwords at this time.  Setup SSH keys with the user you'll be running this script as if needed.

**Example - Remote file**
```yaml
mirror:
  - type: rsync
    src: rsync://mirrors.rit.edu/centos/7/os/x86_64/repodata/
    dest: /home/mike/drop/rsync/
```

**Example - Local file**
```yaml
mirror:
  - type: rsync
    src: /srv/pub/centos/7/os/x86_64/repodata/
    dest: /home/mike/drop/rsync/
```

**Example - SSH/SFTP copy**
```yaml
mirror:
  - type: rsync
    src: root@myserver.example.com:/srv/pub/centos/7/os/x86_64/repodata/
    dest: /home/mike/drop/rsync/
```

### `oci`
Pulls down docker images. Requires `docker` to be in your `$PATH`.

```yaml
mirror:
  - type: oci
    src: hello-world:latest
    dest: /home/mike/drop/docker/
    compress: false # OPTIONAL - If omitted, defaults to true.
```

### `helm`
Pulls down helm chart and optionally the OCI/Docker images it depends on.  Only tested for latest version


**Example**
```yaml
mirror:
  - type: helm
    repo: https://helm.traefik.io/traefik 
    chart: traefik
    dest: /home/mike/drop/helm/traefik/
    cleanup: false # OPTIONAL - Remove the temporary helm repository-config 
                   # (useful to know when/where the chart was pulled). If omitted, defaults to true.
    pullImages: true # OPTIONAL - pulls docker images that the helm chart depends on.
```

### `reposync`
When `wget` and `rsync` are not options, you can use `reposync`.  This utilizes `reposync` from your path and pulls the repo down based on a baseurl definition.  

This is also useful when you're pulling from a location where you want to validate the metadata.  `createrepo --update .` is run at the end to generate repodata.

**Example**
```yaml
mirror:
  - type: reposync
    src: https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64/
    dest: /home/mike/drop/cattleDrive/kick/working/os/kubernetes/el7/x86_64/
    gpgkey: https://packages.cloud.google.com/yum/doc/yum-key.gpg
```

## Disclaimer/Warranty
TL;DR - Caveat Emptor.  There is no warranty express or implied of fitness for a particular purpose.
