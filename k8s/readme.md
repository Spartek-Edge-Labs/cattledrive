# Running cattledrive on Kubernetes
cattleDrive is well suited to be run as a Kubernetes `CronJob` and then hosted up via a web server.  This directory contains the necessary manifests to stand up a cattleDrive backed http mirror in Kubernetes.

## Assumptions/requirements
The resources make a couple of assumptions:
1. You have a working Kubernetes cluster, kubectl installed, and can run kubectl commands against the cluster.
2. You have a StorageClass with at least 100GB of storage.  You can adjust the size of the PVC in `cattledrive.yaml` as needed.
3. You have a functioning Ingress Controller

## Installation

1. Setup the config
   1. Edit `config.yaml` to reflect the cattledrive config you'd like to run. and run `kubectl apply -f config.yaml`  
    **or**
   2. Create a configmap based on an existing config: 
    ```bash
    kubectl create configmap cattledrive-config --from-file=config.yaml=/path/to/cattledrive/config.yaml
    ```
2. Apply the other manifests:
   ```bash
   kubectl apply -f cattledrive.yaml webserver.yaml
   ```

It should be noted that the webserver is only provided as an example on how to expose the data.  The core of this is building a Kubernetes PV filled with your cattleDrive runs.  What you do with it after that is up to you!

## Logs
By default, kubernetes keeps the last three pods from the executions of a `CronJob`.  

```bash
# kubectl get pods -n cattledrive-mirror

NAME                                     READY   STATUS      RESTARTS       AGE
cattledrive-28195320-zmvvq               0/1     Completed   0              135m
cattledrive-28195380-wbbpw               0/1     Completed   0              75m
cattledrive-28195440-ssp8z               0/1     Completed   0              15m
mirror-sparteklabs-io-695ccc778b-xzsm2   1/1     Running     0              12d
```

You can simply view those logs like you would any other container:

```bash
# kubectl logs cattledrive-28195320-zmvvq

...
drpms/rust-indicatif+vt100-devel-0.17.5-1.el9_0.17.6-1.el9.noarch.drpm
drpms/rust-indicatif-devel-0.17.5-1.el9_0.17.6-1.el9.noarch.drpm
drpms/rust-termbg+default-devel-0.4.1-2.el9_0.4.3-1.el9.noarch.drpm
drpms/rust-termbg-devel-0.4.1-2.el9_0.4.3-1.el9.noarch.drpm
drpms/termbg-0.4.1-2.el9_0.4.3-1.el9.x86_64.drpm
repodata/
repodata/065a1e1cdf0a73962b630bfddb97e32d13500ed19330c9c6b2dc3b37cc2f4058-primary.xml.gz
repodata/09af5705255cb9cb6c98d9e2458856f59e9abc3ac89cdc1044535d0f95b86962-filelists.sqlite.bz2
repodata/0ba91ded344ea0f61cd965927a3a1a0d108620caf481d35e6027363af0665e8b-other.xml.gz
repodata/1396cfb89f57496a39cc35c79df444462204f1049cf46a665c5d08c296be4631-primary.sqlite.bz2
repodata/16c4c7b5f6a2d6c380d355943b22d53d36dfa0cbe7c533814a8af6fcf07a8686-comps-Everything.x86_64.xml.gz
repodata/338c5f1c404c34683ae36931c11b4a0c271dee1c62e5535c7f664497464cbac4-updateinfo.xml.bz2
repodata/4ec0ae1bc2c5baa2d1e390e68ed92033cb05deea86333bd01351e8f73615e404-comps-Everything.x86_64.xml
repodata/c4da9532ee36076bb287ad28c130d91aba53a288bf7234d0601de30d35fe97b9-filelists.xml.gz
repodata/c7d3f09f66d0245aaf16895eea672a5f149187c3e1899f79810c6bbe6b08c684-other.sqlite.bz2
repodata/c9f52f4e4e5cc3233ba721b47237b19b55dab5586e8cb64bad60f4c6bb08086a-prestodelta.xml.gz
repodata/repomd.xml

sent 5,230 bytes  received 109,477,277 bytes  5,614,487.54 bytes/sec
total size is 33,358,355,923  speedup is 304.69

receiving incremental file list

sent 24 bytes  received 135 bytes  318.00 bytes/sec
total size is 989,266,123  speedup is 6,221,799.52

receiving incremental file list

sent 24 bytes  received 134 bytes  316.00 bytes/sec
total size is 1,010,172,106  speedup is 6,393,494.34
```