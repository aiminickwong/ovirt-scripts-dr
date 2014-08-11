ovirt-scripts-dr
=============
Python scripts to automate disaster recovery.

All python script use .authpass file to read engine user / password, and its hostname,
change it to point to your engine server.

First script to launch is ChangeVMCluster.py that change all VMs cluster
from source to destination; sample execution is:

python2 ChangeVMCluster.py --clustersource CLUSTER_PROD --clusterdestination CLUSTER_DR

Second script is StartAllVM.py that start all VMs down, and optionally use cloud-init
functionalities for rewriting /etc/resolv.conf file, disabling some services, and
attach VM to Disaster Recovery ipa server -> changing ipa_server parameter on sssd.conf
file.
Sample execution is:

python2 StartAllVM.py --cluster CLUSTER_DR --cloudinit yes

cloud-init
=============

cloud-init functionalities, at this time, is activated *only* on rhel6 and rhel7 VMs,
but for using it:

- install cloud-init package -> yum install cloud-init on CentOS6, on rhel host to
install add rhel-x86_64-server-rh-common-6 software channel;
- due to avoid timeout on normal boot, disable cloud-init on cloud.cfg by append on
cloud.cfg this:

datasource_list: ["NoCloud", "ConfigDrive"]

