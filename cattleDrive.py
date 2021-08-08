#!/usr/bin/env python


import yaml
import subprocess as sp
import string
import random
import os
import re as regex
import sys

####
#   Functions
####

def pushd(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
    os.chdir(dir)

# WGET
def get_wget(src,dest):
    
    # generage a random (likely non-colliding) page name that we can reliably delete later
    pageName = ''.join(random.choice(string.ascii_letters) for i in range(10))
    
    # get number of dirs to cut
    cutDirs = src.count('/') - 2

    currDir = os.getcwd()
    pushd(dest)
    
    # TODO: check wget is installed
    sp.run(["wget", 
                "-e robots=off", 
                "-m", "-nH", "--no-parent", 
                "--cut-dirs=" + str(cutDirs), 
                "--default-page=" + pageName,
                "-R " + pageName + "*", "--relative",
                 src ])
    
    os.remove(pageName)     # cleanup random index page name

    os.chdir(currDir)

# RSYNC
def get_rsync(src,dest):
    currDir = os.getcwd()
    pushd(dest)

    # TODO: check rsync is installed
    sp.run(["rsync", 
                "-avzP", "--delete",
                src, dest ])
    
    os.chdir(currDir)

# OCI Image/Docker Image
'''
TODO: 
    - Check docker is installed
    - check docker daemon is running
'''
def get_oci(image,dest,compress=True):
    
    currDir=os.getcwd()
    pushd(dest)
    
    fileName = image.replace(':','_').replace('/','_')

    sp.run(["docker", "pull", image ])

    if compress is True:
        sp.Popen("docker save " + image + " | gzip > " + fileName + ".tar.gz" , stdin=sp.PIPE, shell=True)
    elif compress is False:
        sp.run(["docker", "save", "-o" + fileName + ".tar", image])
    
    os.chdir(currDir)


# Helm 3 charts
def get_helm(repo,chart,dest,cleanup):

    currDir=os.getcwd()
    pushd(dest)

    repoConfig = chart + ".yaml"
    sp.run("helm --repository-config " + repoConfig + " repo add cattleDrive " + repo, shell=True)
    sp.run("helm --repository-config " + repoConfig + " pull cattleDrive/" + chart, shell=True)
    
    os.remove(chart + ".lock")

    if cleanup is True:
        os.remove(repoConfig)

    os.chdir(currDir)

# Load config
# TODO: check if config exsist and is valid yaml
config = yaml.safe_load( open(sys.argv[1], 'r') )


## Main

for s in config.get("mirror"):
    
    # wget
    if s["type"] == "wget":
        get_wget(s["src"], s["dest"])
    
    #rsync
    elif s["type"] == "rsync":
        get_rsync(s["src"], s["dest"])

    #oci images
    elif s["type"] == "oci":
        if "compress" in s:
            compress = s["compress"]
        else:
            compress = True
        get_oci(s["src"], s["dest"], compress)
    
    # helm charts
    elif s["type"] == "helm":
        if "cleanup" in s:
            cleanup = s["cleanup"]
        else:
            cleanup = True

        get_helm(s["repo"], s["chart"],s["dest"], cleanup )

    else:
        print("We dont handle type:\'" + s["type"] + "\' yet. Maybe check your config file.")
    


