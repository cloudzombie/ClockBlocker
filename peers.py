#!/usr/bin/env python

################
# dependencies #
################

import os
import urllib2
import json
import bitcoinAuth
import ipInfoAuth
from bitcoinrpc import AuthServiceProxy, JSONRPCException


#############
# constants #
#############

peerFile = '/home/pi/pybits/data/peer_list.txt'


##############
# initialize #
##############

# initialize bitcoin RPC connection and gather info
rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:8332"%(bitcoinAuth.USER,bitcoinAuth.PW))


#############
# functions #
#############

# refresh the peers list --  TODO ONLY LOOKUP IP for new peers
def refreshPeers():
	# open file or create new
	p = open(peerFile, 'a')
	p.close()
	p = open(peerFile, 'r+')
	
	# read data from file
	oldPeerData = p.read()
	if oldPeerData:
		peerDataJson = json.loads(oldPeerData)
	else:
		peerDataJson = json.loads("{}")
	
	# move file pointer back to top
	p.seek(0)

	# get peerinfo from bitcoind
	updatedPeers = []
	newPeerInfo = rpc_connection.getpeerinfo()
	newPeers = 0
	totalPeers = 0
	
	# request location from IP info server and fill out info for display
	for peer in newPeerInfo:
		totalPeers += 1
		thisPeer = {}
		thisPeer['addr'] = peer['addr']
		thisPeer['inbound'] = peer['inbound']
		thisPeer['subver'] = peer['subver']
		
		# do we need to reload this IP info? Check for per, then check we have its info
		checkForOld = next((item for item in peerDataJson if item["addr"] == thisPeer['addr']), False)
		if checkForOld:
			if ('country' in checkForOld and checkForOld['country']):
				updatedPeers.append(checkForOld)
				continue
		
		# get the location info from IP API
		thisIP = thisPeer['addr'].split(':')[0]
		
		try:
			response = urllib2.urlopen('http://api.ipinfodb.com/v3/ip-city/?key=' + ipInfoAuth.api_key   + '&format=json&ip=' + thisIP)
		except urllib2.URLError:
			#print "Get IP Info error"
			response = False	
		
		if response:
			responseJson = json.load(response)	
		else:
			responseJson = False
		
		thisPeer['country'] = responseJson['countryName'] if response else ''
		thisPeer['region'] = responseJson['regionName'] if response else ''
		thisPeer['city'] = responseJson['cityName'] if response else ''
		
		newPeers += 1
		updatedPeers.append(thisPeer)
	
	# write json of peer info and close
	peerJson = json.dumps(updatedPeers)	
	p.write(peerJson)
	p.close()
	return "Peers list refreshed: " + str(newPeers) + " updated, " + str(totalPeers) + " total"