#!/usr/bin/env python3


from genericpath import exists
from jinja2 import Template as j2
import yaml
import subprocess as sp
import string
import random
import os
import re as regex
import sys
import tarfile
import shutil
import glob


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
    cutDirs = src.count('/') - 3

    currDir = os.getcwd()
    pushd(dest)
    
    # TODO: check wget is installed
    sp.run(["wget", 
                "-e robots=off", 
                "-m", "-nH", "--no-parent", 
                "--cut-dirs=" + str(cutDirs), 
                "--relative",
                 src ])
    
    #os.remove(pageName)     # cleanup random index page name

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
def get_oci(image,dest,compress):
    
    currDir=os.getcwd()
    pushd(dest)
    
    fileName = image.replace('/','_')

    sp.run(["docker", "pull", image ])

    if compress is True:
        sp.Popen("docker save " + image + " | gzip > " + fileName + ".tar.gz" , stdin=sp.PIPE, shell=True)
    elif compress is False:
        sp.run(["docker", "save", "-o" + fileName + ".tar", image])
    
    os.chdir(currDir)


# Helm 3 charts
def get_helm(**args):
    currDir=os.getcwd()
    pushd(args['dest'])

    if 'version' in args:
        repoConfig = args['chart'] + "-" + args['version'] + ".yaml"
    else:
        repoConfig = args['chart'] + ".yaml"
    
    sp.run("helm --repository-config " + repoConfig + " repo add cattleDrive-"+ args['chart'] + " " + args['repo'], shell=True)
    sp.run("helm --repository-config " + repoConfig + " repo update", shell=True)

    helmSave = "helm --repository-config " + repoConfig + " pull cattleDrive-" + args['chart'] +"/" + args['chart']
    if 'version' in args:
        helmSave += " --version " + args['version']
    sp.run(helmSave, shell=True)
    
    os.remove(repoConfig[:-5] + ".lock")

    if args['cleanup'] is True:
        os.remove(repoConfig)

    
    if args['pullImages'] is True:

        # TODO: This is ugly, get a better way to find the tarball path - will fail at pulling docker images for older helm charts. need to get the filename created from the 'helm pull' command
        helmList = glob.glob(args['chart'] + '-*.tgz')
        tarballPath = sorted(helmList,reverse=True)[0]  # get the latest tarball's path

        pull_helm_images(tarballPath,args['chart'],args['dest'])
    
    os.chdir(currDir)


# pull oci images based on helm chart
def pull_helm_images(tarball,chartName,dest):

    # decompress helm tarball to temp dir
    randStr = ''.join(random.choice(string.ascii_letters) for i in range(10))
    tempDir = '/tmp/cattleDriveHelm-' + randStr #TODO: make global var for temp working dir
    file = tarfile.open(tarball)
    file.extractall(tempDir)
    file.close()


    # get helm template output
    cmd = "helm template " + tempDir + '/' + chartName
    p = sp.Popen(cmd, shell=True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.STDOUT, close_fds=True)
    template, stderr = p.communicate()
    
    #load yaml to python structure
    helmChart = yaml.load_all(template, Loader=yaml.SafeLoader)
    
    #init list
    imageList = []
    
    # iterate through documents
    for d in helmChart:
    
        # get k8s manifest kind
        kind = d["kind"]
        
        # most k8s manifests
        if kind in ["Deployment","ReplicaSet","StatefulSet","DaemonSet","Job","CronJob","ReplicationController"]:
            
            # just in case its a multi container-pod
            for c in d["spec"]["template"]["spec"]["containers"]:
                imageList.append(c["image"])
        
        # of course pods have to be special
        if kind == "Pod":
            
            # just in case its a multi container-pod
            for c in d["spec"]["spec"]["containers"]:
                imageList.append(c["image"])

    # remove temdir
    try:
       shutil.rmtree(tempDir)
    except:
       print('Error while deleting directory ' + tempDir)

    # pull images from imageList to dest
    #TODO: make compression a global setting ala global.CompressPulledHelmImages
    #TODO: make `dest` configurable per call of type:helm - store images seperate from helm charts

    imgDir = dest + '/images'

    if not os.path.exists(imgDir):
        os.makedirs(imgDir)

    for img in imageList:
        get_oci(img,imgDir,True) 

## do reposync on yum repos
def get_reposync (**args ):
    
    currDir=os.getcwd()
    pushd(args['dest'])

    repoFile = "cattledrive.repo"
    t = j2("""[cattledrive]
name=cattledrive repo
baseurl={{ src }}
enabled=1
{% if gpgkey is defined %}gpgcheck=1
gpgkey={{ gpgkey }}
{% else %}gpgcheck=0
{% endif %}""")

    # render repofile
    renderedRepo = t.render(**args)
    
    # write repofile to disk
    f = open(repoFile, "w")
    f.write(renderedRepo)
    f.close()

    # reposync the file
    sp.run(f'reposync -c {repoFile} --repo cattledrive --norepopath', shell=True)
    sp.run('createrepo --update .', shell=True)
    if 'gpgkey' in args and args['gpgkey']:
        get_wget(src=args['gpgkey'], dest='.')
    os.chdir(currDir)

## Main

# Load config
# TODO: check if config exsist and is valid yaml
config = yaml.safe_load( open(sys.argv[1], 'r') )

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
        thisObj = s
        # default 'cleanup' val
        if "cleanup" not in thisObj:
            thisObj["cleanup"] = True
        
        # default 'pullImage' val
        if "pullImages" not in thisObj:
            thisObj["pullImages"] = False

        del thisObj['type']

        get_helm(**thisObj)
    elif s["type"] == "reposync":
        get_reposync(**s)
    else:
        print("We dont handle type:\'" + s["type"] + "\' yet. Maybe check your config file.")
    


