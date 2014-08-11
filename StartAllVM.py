#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
        Autore: Amedeo Salvati
        email: amedeo@linux.com
        
        
        Copyright (C) 2014 Amedeo Salvati.  All rights reserved.
        
        This program is free software; you can redistribute it and/or
        modify it under the terms of the GNU General Public License
        as published by the Free Software Foundation; either version 2
        of the License, or (at your option) any later version.
        
        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.
        
        You should have received a copy of the GNU General Public License
        along with this program; if not, write to the Free Software
        Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
        
        Amedeo Salvati
        17-07-2014
        Start all VMs that are down on cluster parameter
"""

from ovirtsdk.xml import params
from ovirtsdk.api import API
from time import sleep
import os, sys
from optparse import OptionParser
from string import count
import ConfigParser

# Set > 0 if you whant print terminal information
DEBUG = 1

VERSION = "0.3"

SHOSTNAME = ''
SPORT = ''
SPROTOCOL = ''
ENGINE_CONN = ''
SUSERNAME = ''
SPASSWORD = ''

#FIXME: make this variable parameter
AUTH_FILE = '/home/amedeo/DR/.authpass'

EXIT_ON = ''

parser = OptionParser()
usagestr = "usage: %prog [options] --cluster CLUSTERNAME [--cloudinit yes|no]"

parser = OptionParser(usage=usagestr, version="%prog Version: " + VERSION)

parser.add_option("--cluster", type="string",dest="CLUSTER", 
                  help="Cluster name where start VMs")

parser.add_option("--cloudinit", type="string",dest="CLOUDINIT", 
                  help="Start VM with cloud-init options")

(options, args) = parser.parse_args()

if options.CLUSTER == "" or not options.CLUSTER:
    parser.error("incorrect number of arguments")
    sys.exit(1)

if options.CLOUDINIT == "" or not options.CLOUDINIT:
    options.CLOUDINIT = "no"
elif options.CLOUDINIT != "yes":
    options.CLOUDINIT = "no"

CLUSTER = options.CLUSTER
CLOUDINIT = options.CLOUDINIT

if( DEBUG > 0 ):
    print "Cluster source: '" + CLUSTER + "'"
    print "cloud-init: '" + CLOUDINIT + "'" 

# get auth user / pass
try:
    Config = ConfigParser.ConfigParser()
    Config.read(AUTH_FILE)
    if len( Config.sections() ) == 0:
        print "Error: Wrong auth file: " + AUTH_FILE + ", now try to use default /root/DR/.authpass"
        AUTH_FILE = '/root/DR/.authpass'
        Config.read(AUTH_FILE)
        if len( Config.sections() ) == 0:
            print "Error: Wrong auth file: " + AUTH_FILE + ", now exit"
            sys.exit(1)
    print "Try to read Username from " + AUTH_FILE
    SUSERNAME = Config.get("Auth", "Username")
    print "Found Username: " + SUSERNAME
    print "Try to read Password from " + AUTH_FILE
    SPASSWORD = Config.get("Auth", "Password")
    print "Found Password: ***********"
    print "Try to read Hostname from " + AUTH_FILE
    SHOSTNAME = Config.get("Auth", "Hostname")
    print "Found Hostname: " + SHOSTNAME
    print "Try to read protocol from " + AUTH_FILE
    SPROTOCOL = Config.get("Auth", "Protocol")
    print "Found Protocol: " + SPROTOCOL
    print "Try to read Port from " + AUTH_FILE
    SPORT = Config.get("Auth", "Port")
    print "Found Port: " + SPORT
    ENGINE_CONN = SPROTOCOL + '://' + SHOSTNAME + ':' + SPORT
    print "Connection string: " + ENGINE_CONN
except:
    print "Error on reading auth file: " + AUTH_FILE
    sys.exit(1)

def checkClusterExist ( clusterName ):
    if( DEBUG > 0 ):
        print "Check if exist cluster: '" + clusterName + "'"
    cn = api.clusters.get(name=clusterName)
    if cn == None:
        print "Error: cluster " + clusterName + " doesn't exist... Exit"
        sys.exit(1)

def buildYamlFile():
    str1 = "write_files:\n-   content: |\n"
    str1 = str1 + "        search example.com\n"
    str1 = str1 + "        nameserver 10.10.10.1\n"
    str1 = str1 + "        nameserver 10.10.10.2\n"
    str1 = str1 + "    path: /etc/resolv.conf\n\n"
    str1 = str1 + "runcmd:\n"
    str1 = str1 + "- [ sh, -c, \"/sbin/chkconfig postfix off\" ]\n"
    str1 = str1 + "- [ sh, -c, \"/bin/cp -p -f /etc/sssd/sssd.conf /etc/sssd/sssd.conf.predr\" ]\n"
    str1 = str1 + "- [ sh, -c, \"/bin/sed -e s/^ipa_server.*/ipa_server=ipaserverdr.example.com/g /etc/sssd/sssd.conf > /etc/sssd/sssd.conf.tmp\" ]\n"
    str1 = str1 + "- [ sh, -c, \"/bin/mv -f /etc/sssd/sssd.conf.tmp /etc/sssd/sssd.conf\" ]\n"
    str1 = str1 + "- [ sh, -c, \"/bin/chmod 600 /etc/sssd/sssd.conf\" ]\n"
    str1 = str1 + "- [ sh, -c, \"/sbin/service sssd restart\" ]"
    return str1

# connect to rhevm
try:
    if( DEBUG > 0):
        print 'Now try to connect to the engine: ' + ENGINE_CONN
    
    api = None
    api = API(ENGINE_CONN, insecure=True, username=SUSERNAME, password=SPASSWORD)
    if( DEBUG > 0):
        print 'Connection established to the engine: ' + ENGINE_CONN
    
    EXIT_ON = 'checkClusterExist'
    checkClusterExist(CLUSTER)
    
    EXIT_ON = 'ListVMs'
    vmlist = api.vms.list("cluster=" + CLUSTER, max=10000)
    for vm in vmlist:
        vmstat = vm.get_status().state
        if vmstat == 'down':
            
            try:
                osVersion = vm.get_os().get_type()
                if (osVersion == "rhel_6x64" or osVersion == "rhel_6" or osVersion == "rhel_7x64") and CLOUDINIT == "yes":
                    print "Starting VM: " + vm.name + " with cloud-init options"
                    scontent = buildYamlFile()
                    action = params.Action(
                        vm=params.VM(
                            initialization=params.Initialization(
                                cloud_init=params.CloudInit(
                                    #host=params.Host(address="rheltest029"),
                                    users=params.Users(
                                        user=[params.User(user_name="root", password="SECRET")]
                                        ),
                                    files=params.Files(
                                        file=[params.File(name="/etc/resolv.conf", content=scontent, type_="PLAINTEXT")]
                                        )
                                    )
                                )
                            )
                        )
                    vm.start( action )
                else:
                    print "Starting VM " + vm.name
                    vm.start()
                while vmstat != 'down':
                    sleep(1)
                    vmstat = vm.get_status().state
            except Exception, err:
                print "Error on starting VM"
                print err
        else:
            print "VM " + vm.name + " state is: '" + vmstat + "'...no start is required..." 
    
except:
    if EXIT_ON == '':
        print 'Error: Connection failed to server: ' + ENGINE_CONN
    else:
        print 'Error on ' + EXIT_ON
finally:
    if api != None:
        api.disconnect()
