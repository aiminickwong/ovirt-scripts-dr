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
        15-07-2014
        Change all VMs in a cluster if VM status is down
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
usage = "usage: %prog [options] CLUSTERSOURCE CLUSTERDESTINATION"

parser = OptionParser(usage="%prog --clustersource CLUSTER1 --clusterdestination CLUSTER2", version="%prog Version: " + VERSION)

parser.add_option("--clustersource", type="string",dest="CLUSTERSOURCE", 
                  help="Cluster name source")

parser.add_option("--clusterdestination", type="string", dest="CLUSTERDESTINATION", 
                  help="Cluster name destination")

(options, args) = parser.parse_args()

if options.CLUSTERSOURCE == "" or not options.CLUSTERSOURCE:
    parser.error("incorrect number of arguments")
    sys.exit(1)

if options.CLUSTERDESTINATION == "" or not options.CLUSTERDESTINATION:
    parser.error("incorrect number of arguments")
    sys.exit(1)

CLUSTERSOURCE = options.CLUSTERSOURCE
CLUSTERDESTINATION = options.CLUSTERDESTINATION

if( DEBUG > 0 ):
    print "Cluster source: '" + CLUSTERSOURCE + "'"
    print "Cluster destination: '" + CLUSTERDESTINATION + "'"

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

def checkSameDataCenter( clusterName1, clusterName2 ):
    if( DEBUG > 0 ):
        print "Check if two cluster '" + clusterName1 + "' e '" + clusterName2 + "' " + \
        "sono nello stesso DataCenter"
    cn1 = api.clusters.get(name=clusterName1)
    cn2 = api.clusters.get(name=clusterName2)
    dc1 = cn1.get_data_center()
    dc2 = cn2.get_data_center()
    if dc1 == None or dc2 == None:
        print "Error: one of two cluster provided isn't associated to a DataCenter...Exit"
        sys.exit(1) 
    if( DEBUG > 0 ):
        print "Cluster " + clusterName1 + " is on DC with id: " + dc1.get_id()
        print "Cluster " + clusterName2 + " is on DC with id: " + dc2.get_id()
    if dc1.get_id() != dc2.get_id():
        print "Error: clusters " + clusterName1 + " and " + clusterName2 + " " + \
        "aren't on the same DataCenter...Exit"
        sys.exit(1)
    else:
        if( DEBUG > 0 ):
            print "Clusters " + clusterName1 + " and " + clusterName2 + " " + \
            "are on the same DataCenter"

# connect to engine
try:
    if( DEBUG > 0):
        print 'Now try to connect to the engine: ' + ENGINE_CONN
    
    api = None
    api = API(ENGINE_CONN, insecure=True, username=SUSERNAME, password=SPASSWORD)
    if( DEBUG > 0):
        print 'Connection established to the engine: ' + ENGINE_CONN
    
    EXIT_ON = 'checkClusterExist'
    checkClusterExist(CLUSTERSOURCE)
    checkClusterExist(CLUSTERDESTINATION)
    
    EXIT_ON = 'checkSameDataCenter'
    checkSameDataCenter(CLUSTERSOURCE, CLUSTERDESTINATION)
    
    EXIT_ON = 'ListVMs'
    vmlist = api.vms.list("cluster=" + CLUSTERSOURCE, max=10000)
    for vm in vmlist:
        vmstat = vm.get_status().state
        if vmstat == 'down':
            print "Change cluster " + CLUSTERDESTINATION + " for VM " + vm.name
            try:
                vm.set_cluster( api.clusters.get(name=CLUSTERDESTINATION))
                vm.update()
            except Exception, err:
                print Exception, err
                print "##############################################################################"
                print "Error on update VM: " + vm.get_name()
                print "Probably domain is '' and not null, try to apply WA at: "
                print ""
                print ""
                print "https://bugzilla.redhat.com/show_bug.cgi?id=1113571"
                print "update vm_init set domain = null where domain=''"
                print "##############################################################################"
                sleep(1)
        else:
            print "VM " + vm.name + " state is: '" + vmstat + "'...no change to cluster destination: " + CLUSTERDESTINATION
    
except:
    if EXIT_ON == '':
        print 'Error: Connection failed to server: ' + ENGINE_CONN
        sys.exit(1)
    else:
        print 'Error on ' + EXIT_ON
finally:
    if api != None:
        api.disconnect()