#!/usr/bin/env python

# pulls a list of docker images used from a decompressed helm chart on disk


import yaml
import subprocess as sp
import sys

# from yaml.loader import SafeLoader - allows to call "SafeLoader" by itself


# get helm output
cmd = "helm template " + sys.argv[1]
p = sp.Popen(cmd, shell=True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.STDOUT, close_fds=True)
template, stderr = p.communicate()

#load yaml to python structure
config = yaml.load_all(template, Loader=yaml.SafeLoader)

#init list
imageList = []

# iterate through documents
for d in config:

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

# print out image list
for i in imageList:
    print(i)
