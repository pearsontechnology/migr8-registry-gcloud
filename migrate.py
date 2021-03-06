#!/usr/bin/env python
# Must have python 2.7 installed
# This script assumes you have gcloud sdk installed and
# the sdk has already be authenticated to gcloud
# It also assumes access to your private repository through the REG_URL

import requests
import json
import logging
import ast
import subprocess
import os

os.path.abspath('/')

##########################################
#  Examples for GCLOUD_URL AND REG_URL
# export GCLOUD_URL="gcr.io/<project-name>/"
# export REG_URL="docker-registry.example.com:5000/"
# export GCLOUDPATH = "/usr/bin/gcloud"
# export DOCKERPATH = "/usr/bin/docker"
# Make sure you have these env vars set
os.environ.get('GCLOUD_URL')
os.environ.get('REG_URL')
os.environ.get('GCLOUDPATH')
os.environ.get('DOCKERPATH')


class MigrateToGcloud():
    # Init some urls and paths for migration then call _get_catalog
    def __init__(self):
        self.REG_URL = os.environ.get('REG_URL')
        self.GCLOUD_URL = os.environ.get('GCLOUD_URL')
        self.dockerpath = os.environ.get('DOCKERPATH')
        self.gcloudpath = os.environ.get('GCLOUDPATH')
        self._get_catalog()

    # Get a catalog of repos from your existing repository
    def _get_catalog(self):
        r = requests.get('https://' + self.REG_URL + '/v2/_catalog')
        logging.debug("Test get Catalog: %r", r)
        io = json.dumps(r.text)
        n = json.loads(io)
        line = ast.literal_eval(n)
        mylist = line['repositories']
        self._log = logging.debug("Test run: %r", mylist)
        self._run(mylist)

    # primary run function to execute every thing else
    def _run(self, mylist):
        for line in mylist:
            print(line)
            command = self.gcloudpath + ' alpha container images list-tags ' + self.GCLOUD_URL + '/' + line
            checktags = subprocess.check_output(command, shell=True)
            taglist = self._get_tags(line)
            for tag in taglist:
                tagvalue = self._check_tag(line, tag, checktags)
                if tagvalue is False:
                    self._download_images(line, tag)
                    self._set_tag(line, tag)
                    self._upload_image(line, tag)
                else:
                    print("Found " + line + ' ' + tag +
                          " is already uploaded to Gcloud. Skipping")
                    continue

    # Get version tags from existing repository so we can migrate all of them
    def _get_tags(self, line):
        command = 'https://' + self.REG_URL + '/v2/' + line + '/tags/list'
        checktags = requests.get(command)
        io = json.dumps(checktags.text)
        n = json.loads(io)
        tagline = ast.literal_eval(n)
        try:
            taglist = tagline['tags']
        except:
            taglist = tagline['tags'] = 'null'
        return taglist

    # Check if the version tag exists in new repository
    def _check_tag(self, line, tag, checktags):
        if tag in checktags:
            return True
        else:
            return False

    # Download images from existing registry
    def _download_images(self, line, tag):
        print ("######### Downloading " + line + ':' + tag +
               " image from bitesize registry ##########################")
        try:
            command = (self.dockerpath + ' pull ' +
                       self.REG_URL + '/' + line + ':' + tag)
            subprocess.check_output(command, shell=True)
        except:
            return

# Tag image for new registry
    def _set_tag(self, line, tag):
        print ("######### TAGGING " + line + ':' + tag +
               " IMAGE FOR UPLOAD ################")
        try:
            command = (self.gcloudpath + ' docker tag ' + self.REG_URL + '/' + line +
                       ':' + tag + ' ' + self.GCLOUD_URL + '/' + line + ':' + tag)
            print(command)
            subprocess.check_output(command, shell=True)
        except:
            return

# Upload image to new registry
    def _upload_image(self, line, tag):
        print ("############### STARTING " + line + ':' + tag +
               " IMAGE UPLOAD TO NEW REPO ###################")
        try:
            command = (self.gcloudpath + ' docker push ' +
                       self.GCLOUD_URL + '/' + line + ':' + tag)
            subprocess.check_output(command, shell=True)
        except:
            return


MigrateToGcloud()
