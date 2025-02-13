# -*- coding: future_fstrings -*-

import os
import requests
import urllib3
import warnings
from configparser import ConfigParser
from datetime import datetime

##
## Omada API calls expect a timestamp in milliseconds.
##
def timestamp():
	return int( datetime.utcnow().timestamp() * 1000 )

##
## Display errorCode and optional message returned from Omada API.
##
class OmadaError(Exception):

	def __init__(self, json):
		self.errorCode = 0
		self.msg = None
		
		if json is None:
			raise TypeError('json cannot be None')
		
		if 'errorCode' in json:
			self.errorCode = json['errorCode']
		
		if 'msg' in json:
			self.msg = '"' + json['msg'] + '"'

	def __str__(self):
		return f"errorCode={self.errorCode}, msg={self.msg}"

##
## The main Omada API class.
##
class Omada:

	##
	## Initialize a new Omada API instance.
	##
	def __init__(self, config='omada.cfg', baseurl=None, site='Default', verify=True, warnings=True):
		
		self.config = None
		self.token  = None
		
		if baseurl is not None:
			# use the provided configuration
			self.baseurl  = baseurl
			self.site     = site
			self.verify   = verify
			self.warnings = warnings
		elif os.path.isfile( config ):
			# read from configuration file
			self.config = ConfigParser()
			try:
				self.config.read( config )
				self.baseurl  = self.config['omada'].get('baseurl')
				self.site     = self.config['omada'].get('site', 'Default')
				self.verify   = self.config['omada'].getboolean('verify', True)
				self.warnings = self.config['omada'].getboolean('warnings', True)
			except:
				raise
		else:
			# could not find configuration
			raise FileNotFoundError(config)
		
		# create a new session to hold cookies
		self.session = requests.Session()
		self.session.verify = self.verify
		
		# hide warnings about insecure SSL requests
		if self.verify == False and self.warnings == False:
			urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

	##
	## Current API path.
	##
	ApiPath = '/api/v2'

	##
	## Build a URL for the provided path.
	##
	def url_for(self, path):
		return self.baseurl + Omada.ApiPath + path

	##
	## Perform a GET request and return the result.
	##
	def get(self, path, params=None, data=None, json=None):
		
		if params is None and self.token is not None:
			params = {'token':self.token,'_':timestamp()}
		
		response = self.session.get( self.url_for(path), params=params, data=data, json=json )
		response.raise_for_status()
		
		json = response.json()
		if json['errorCode'] == 0:
			return json['result'] if 'result' in json else None
		
		raise OmadaError(json)

	##
	## Perform a POST request and return the result.
	##
	def post(self, path, params=None, data=None, json=None):
		
		if params is None and self.token is not None:
			params = {'token':self.token,'_':timestamp()}
		
		response = self.session.post( self.url_for(path), params=params, data=data, json=json )
		response.raise_for_status()
		
		json = response.json()
		if json['errorCode'] == 0:
			return json['result'] if 'result' in json else None
		
		raise OmadaError(json)

	##
	## Perform a PATCH request and return the result.
	##
	def patch(self, path, params=None, data=None, json=None):
		
		if params is None and self.token is not None:
			params = {'token':self.token,'_':timestamp()}
		
		response = self.session.patch( self.url_for(path), params=params, data=data, json=json )
		response.raise_for_status()
		
		json = response.json()
		if json['errorCode'] == 0:
			return json['result'] if 'result' in json else None
		
		raise OmadaError(json)

	##
	## Log in with the provided credentials and return the result.
	##
	def login(self, username=None, password=None):
		
		if username is None and password is None:
			if self.config is None:
				raise TypeError('username and password cannot be None')
			try:
				username = self.config['omada'].get('username')
				password = self.config['omada'].get('password')
			except:
				raise
		
		result = self.post( '/login', json={'username':username,'password':password} )
		self.token = result['token']
		return result

	##
	## Log out of the current session. Return value is always None.
	##
	def logout(self):
		return self.post( '/logout' )

	##
	## Returns the current login status.
	##
	def getLoginStatus(self):
		return self.get( '/loginStatus' )

	##
	## Returns the current user information.
	##
	def getCurrentUser(self):
		return self.get( '/users/current' )

		## Group Types
	IPGroup   = 0 # "IP Group"
	PortGroup = 1 # "IP-Port Group"
	MACGroup  = 2 # "MAC Group"

	##
	## Returns the list of groups for the given site.
	##
	def getSiteGroups(self, site=None, type=None):
		
		if site is None:
			site = self.site
		
		if type is None:
			result = self.get( f'/sites/{site}/setting/profiles/groups' )
		else:
			result = self.get( f'/sites/{site}/setting/profiles/groups/{type}' )
		
		return result['data']

	##
	## Returns the list of portal candidates for the given site.
	##
	## This is the "SSID & Network" list on Settings > Authentication > Portal > Basic Info.
	##
	def getPortalCandidates(self, site=None):
		
		if site is None:
			site = self.site
		
		return self.get( f'/sites/{site}/setting/portal/candidates' )

	##
	## Returns the list of RADIUS profiles for the given site.
	##
	def getRadiusProfiles(self, site=None):
		
		if site is None:
			site = self.site
		
		return self.get( f'/sites/{site}/setting/radiusProfiles' )

	##
	## Returns the list of scenarios.
	##
	def getScenarios(self):
		return self.get( '/scenarios' )

	##
	## Returns the list of devices for given site.
	##
	def getSiteDevices(self, site=None):
		
		if site is None:
			site = self.site
		
		return self.get( f'/sites/{site}/devices' )
	
	##
	## Returns the list of active Clients for given site.
	##
	def getSiteClients(self, site=None):
	if site is None:
		site = self.site
	return self.get( f'/sites/{site}/clients?currentPageSize=999&currentPage=1&filters.active=true')

	##
	## Returns the list of settings for the given site.
	##
	def getSiteSettings(self, site=None):
		
		if site is None:
			site = self.site
		
		result = self.get( f'/sites/{site}/setting' )
		
		# work-around for error when sending PATCH for site settings (see below)
		if 'beaconControl' in result:
			if self.warnings:
				warnings.warn( "settings['beaconControl'] was removed as it causes an error", stacklevel=2 )
			del result['beaconControl']
		
		return result

	##
	## Push back the settings for the site.
	##
	def setSiteSettings(self, settings, site=None):
		
		if site is None:
			site = self.site
		
		# not sure why but setting 'beaconControl' here does not work, returns {'errorCode': -1001}
		if 'beaconControl' in settings:
			if self.warnings:
				warnings.warn( "settings['beaconControl'] was removed as it causes an error", stacklevel=2 )
			del settings['beaconControl']
		
		return self.patch( f'/sites/{site}/setting', json=settings )

	##
	## Returns the list of timerange profiles for the given site.
	##
	def getTimeRanges(self, site=None):
		
		if site is None:
			site = self.site
		
		return self.get( f'/sites/{site}/setting/profiles/timeranges' )

	##
	## Returns the list of wireless network groups.
	##
	## This is the "WLAN Group" list on Settings > Wireless Networks.
	##
	def getWirelessGroups(self, site=None):
		
		if site is None:
			site = self.site
		
		result = self.get( f'/sites/{site}/setting/wlans' )
		
		return result['data']

	##
	## Returns the list of wireless networks for the given group.
	##
	## This is the main SSID list on Settings > Wireless Networks.
	##
	def getWirelessNetworks(self, group, site=None):
		
		if site is None:
			site = self.site
		
		result = self.get( f'/sites/{site}/setting/wlans/{group}/ssids' )
		
		return result['data']

