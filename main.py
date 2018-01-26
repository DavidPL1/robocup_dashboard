__author__ = 'Florian Lier | fl@techfak.uni-bielefeld.de'

# DEFAULTS
import time
import pika
import json
import base64
import urllib3
import threading
import flatbuffers
from sys import exit
from threading import Lock
from redminelib import Redmine
from optparse import OptionParser


# FLATBUF
import RedmineIssues.Issue
import RedmineIssues.Issues

# MQTT
import paho.mqtt.client as mqtt

# Jenkins
import jenkinsapi
from jenkinsapi.jenkins import Jenkins

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RedmineAdapter:
    def __init__(self, _options):
        # Defaults
        self.lock = Lock()
        self.url = _options.url
        self.project = _options.project
        self.username = _options.login
        self.password = _options.credentials
        self.redmine_instance = None
        self.project_instance = None
        self.current_byte_buf = None
        self.current_json_issues = None
        # RabbitMQ
        self.mqttw = MQTTWrapper()
        print ">> Redmine init done"

    def connect(self):
        try:
            self.redmine_instance = Redmine(self.url, username=self.username, password=self.password)
        except Exception, e:
            print "ERROR >> %s" % str(e)
            exit(1)

    def refresh(self):
        try:
            self.lock.acquire()
            self.project_instance = self.redmine_instance.project.get(self.project)
            self.lock.release()
        except Exception, e:
            print "ERROR >> %s" % str(e)
            self.lock.release()

    def serialize_issues(self, _filter="[task]"):
        issues_collection = []
        builder = flatbuffers.Builder(1024)
        for item in self.project_instance.issues:
            try:
                if _filter in str(item.subject).lower():
                    title = builder.CreateString(str(item.subject))
                    if "assigned_to" in item:
                        asignee = builder.CreateString(str(item.assigned_to))
                    else:
                        asignee = builder.CreateString("Not Assigned")
                    RedmineIssues.Issue.IssueStart(builder)
                    RedmineIssues.Issue.IssueAddTitle(builder, title)
                    RedmineIssues.Issue.IssueAddAsignee(builder, asignee)
                    RedmineIssues.Issue.IssueAddPercentDone(builder, int(item.done_ratio))
                    issue = RedmineIssues.Issue.IssueEnd(builder)
                    issues_collection.append(issue)
            except Exception, e:
                print "ERROR >> %s" % str(e)
        RedmineIssues.Issues.IssuesStartIssuesVector(builder, len(issues_collection))
        for item in issues_collection:
            builder.PrependUOffsetTRelative(item)
        issues = builder.EndVector(len(issues_collection))
        RedmineIssues.Issues.IssuesStart(builder)
        RedmineIssues.Issues.IssuesAddIssues(builder, issues)
        final_issues = RedmineIssues.Issues.IssuesEnd(builder)
        builder.Finish(final_issues)
        self.lock.acquire()
        self.current_byte_buf = builder.Output()
        self.lock.release()

    def json_builder_issues(self, _filter="[task]"):
        self.refresh()
        issues = []
        for item in self.project_instance.issues:
            try:
                if _filter in str(item.subject).lower():
                    single_issue = {"subject": str(item.subject)}
                    if "assigned_to" in item:
                        single_issue['assignee'] = str(item.assigned_to)
                    else:
                        single_issue['assignee'] = "Not Assigned"
                        single_issue['done'] = str(item.done_ratio)
                        issues.append(single_issue)
            except Exception, e:
                print "ERROR >> %s" % str(e)
        self.lock.acquire()
        self.current_json_issues = issues
        self.lock.release()

    def print_issues_flatbuf(self):
        self.lock.acquire()
        if self.current_byte_buf is not None:
            issues = RedmineIssues.Issues.Issues.GetRootAsIssues(self.current_byte_buf, 0)
            for x in range(issues.IssuesLength()):
                issue = issues.Issues(x)
                print ">> Title: ", issue.Title(), "| Assignee: ", issue.Asignee(), "| Percent Done: ", issue.PercentDone()
        self.lock.release()

    def print_json_issues(self):
        self.lock.acquire()
        print json.dumps(self.current_json_issues)
        self.lock.release()

    def send_issues(self):
        self.lock.acquire()
        self.mqttw.publish(self.current_json_issues)
        self.lock.release()


# class RabbitMQWrapper:
#     def __init__(self):
#         self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
#         self.channel = self.connection.channel()
#         self.channel.exchange_declare(exchange='dashboard.issues', exchange_type='topic')
#         self.routing_key = "dashboard.issues.now"
#
#     def publish(self, _message):
#         encoded_m = base64.b64encode(_message)
#         self.channel.basic_publish(exchange='dashboard.issues', routing_key=self.routing_key, body=encoded_m)


class MQTTWrapper:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.connect("127.0.0.1", 1883, 60)
        self.client.subscribe('dashboard.issues')
        print ">> MQTT init done"

    def publish(self, _message, topic='dashboard.issues'):
        # encoded_m = base64.b64encode(_message)
        self.client.publish(topic, json.dumps(_message), 0, False)
        print ">> Publishing on %s" % topic

    def disconnect(self):
        self.client.disconnect()


class JenkinsWrapper(threading.Thread):
    def __init__(self, _options):
        threading.Thread.__init__(self)
        self.jenkins_url = str(_options.jenkinsurl)
        self.server = Jenkins(self.jenkins_url, ssl_verify=False)
        self.job_info = {}
        self.lock = Lock()
        self.should_run = True
        self.mqttw = MQTTWrapper()
        print ">> Jenkins init done"

    def run(self):
        init_time = time.time()
        initial_send = False
        while self.should_run:
            try:
                if initial_send is False:
                    self.lock.acquire()
                    for job_name, job_instance in self.server.get_jobs():
                        last_build_nr = job_instance.get_last_buildnumber()
                        status = job_instance.get_build(last_build_nr).get_status()
                        self.job_info[job_name] = {"lastbuild": last_build_nr, "status": status}
                    self.lock.release()
                    self.mqttw.publish(self.job_info, topic='dashboard.jobinfo')
                    initial_send = True
                if time.time() - init_time > 3600:
                    self.lock.acquire()
                    for job_name, job_instance in self.server.get_jobs():
                        last_build_nr = job_instance.get_last_buildnumber()
                        status = job_instance.get_build(last_build_nr).get_status()
                        self.job_info[job_name] = {"lastbuild": last_build_nr, "status": status}
                    self.lock.release()
                    self.mqttw.publish(self.job_info, topic='dashboard.jobinfo')
                    init_time = time.time()
            except Exception, e:
                self.lock.release()
                print "ERROR >> %s" % str(e)
            time.sleep(1)
            if self.should_run is False:
                return

    def print_results(self):
        print self.job_info


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-u", "--url", dest="url", help="redmine url")
    parser.add_option("-p", "--project", dest="project", help="redmine project")
    parser.add_option("-l", "--login", dest="login", help="redmine user/login")
    parser.add_option("-c", "--credentials", dest="credentials", help="redmine password/credentials")
    parser.add_option("-j", "--jenkinsurl", dest="jenkinsurl", help="jenkins url")

    (options, args) = parser.parse_args()

    j = None

    if options.jenkinsurl:
        try:
            j = JenkinsWrapper(options)
            j.start()
        except Exception, e:
            print "ERROR >> %s" % str(e)

    ra = RedmineAdapter(options)
    ra.connect()

    start_time = time.time()

    try:
        print ">> Entering __main__ loop"
        while True:
            ra.json_builder_issues()
            ra.send_issues()
            time.sleep(360)
            print ">> Updating..."
    except KeyboardInterrupt:
        ra.mqttw.disconnect()
        if j is not None:
            j.should_run = False
        print ">> CTRL+C exiting ..."
