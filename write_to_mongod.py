__author__ = 'Florian Lier | fl@techfak.uni-bielefeld.de'

# DEFAULTS
import time
import json
import urllib3
import threading
from sys import exit
from optparse import OptionParser

# Jenkins
import jenkinsapi
from jenkinsapi.jenkins import Jenkins

# MONGO
from pymongo import MongoClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class JenkinsWrapper(threading.Thread):
    def __init__(self, _options):
        threading.Thread.__init__(self)
        self.jenkins_url = str(_options.jenkinsurl)
        self.server = Jenkins(self.jenkins_url, ssl_verify=False)
        self.job_info = {}
        self.should_run = True
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client.jenkins_stats
        print ">> Jenkins init done"

    def run(self):
        init_time = time.time()
        initial_send = False
        while self.should_run:
            try:
                if initial_send is False:
                    for job_name, job_instance in self.server.get_jobs():
                        last_build_nr = job_instance.get_last_buildnumber()
                        status = job_instance.get_build(last_build_nr).get_status()
                        self.job_info[job_name] = {"lastbuild": last_build_nr, "status": status}
                    self.db.insert_one(self.job_info)
                    initial_send = True
                if time.time() - init_time > 3600:
                    for job_name, job_instance in self.server.get_jobs():
                        last_build_nr = job_instance.get_last_buildnumber()
                        status = job_instance.get_build(last_build_nr).get_status()
                        self.job_info[job_name] = {"lastbuild": last_build_nr, "status": status}
                    self.db.insert_one(self.job_info)
                    init_time = time.time()
            except Exception, e:
                print "ERROR >> %s" % str(e)
            time.sleep(1)
            if self.should_run is False:
                return

    def print_results(self):
        print self.job_info


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-j", "--jenkinsurl", dest="jenkinsurl", help="jenkins url")

    (options, args) = parser.parse_args()

    j = None

    if options.jenkinsurl:
        try:
            j = JenkinsWrapper(options)
            j.start()
        except Exception, e:
            print "ERROR >> %s" % str(e)
    else:
        print "No Jenkins URL provided"
        sys.exit(1)

    try:
        print ">> Entering __main__ loop"
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if j is not None:
            j.should_run = False
        print ">> CTRL+C exiting ..."
