__author__ = 'Florian Lier | fl@techfak.uni-bielefeld.de'

# DEFAULTS
import time
import pika
import base64
import flatbuffers
from sys import exit
from threading import Lock
from redminelib import Redmine
from optparse import OptionParser

# FLATBUF
import RedmineIssues.Issue
import RedmineIssues.Issues


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
        # RabbitMQ
        self.rmq = RabbitMQWrapper()

    def connect(self):
        try:
            self.redmine_instance = Redmine(self.url, username=self.username, password=self.password)
            self.project_instance = self.redmine_instance.project.get(self.project)
        except Exception, e:
            print "ERROR >> %s" % str(e)
            exit(1)

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

    def print_issues(self):
        if self.current_byte_buf is not None:
            issues = RedmineIssues.Issues.Issues.GetRootAsIssues(self.current_byte_buf, 0)
            for x in range(issues.IssuesLength()):
                issue = issues.Issues(x)
                print ">> Title: ", issue.Title(), "| Assignee: ", issue.Asignee(), "| Percent Done: ", issue.PercentDone()

    def send_issues(self):
        self.lock.acquire()
        self.rmq.publish(self.current_byte_buf)
        self.lock.release()


class RabbitMQWrapper:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='dashboard.issues', exchange_type='topic')
        self.routing_key = "dashboard.issues"

    def publish(self, _message):
        encoded_m = base64.b64encode(_message)
        self.channel.basic_publish(exchange='dashboard.issues', routing_key=self.routing_key, body=encoded_m)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-u", "--url", dest="url", help="redmine url")
    parser.add_option("-p", "--project", dest="project", help="redmine project")
    parser.add_option("-l", "--login", dest="login", help="redmine user/login")
    parser.add_option("-c", "--credentials", dest="credentials", help="redmine password/credentials")

    (options, args) = parser.parse_args()
    
    ra = RedmineAdapter(options)
    ra.connect()

    try:
        import paho.mqtt.client as mqtt

        # The callback for when the client receives a CONNACK response from the server.
        def on_connect(client, userdata, flags, rc):
            print("Connected with result code " + str(rc))

            # Subscribing in on_connect() means that if we lose the connection and
            # reconnect then subscriptions will be renewed.
            # client.subscribe("$SYS/#")
            client.subscribe('/dashboard/issues')
            client.publish('/dashboard/issues', "something", 0, False)

        # The callback for when a PUBLISH message is received from the server.
        def on_message(client, userdata, msg):
            print(msg.topic + " " + str(msg.payload))


        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        # client.connect('15.xx.xx.xx', 1883, 60)
        # client.connect("iot.eclipse.org", 1883, 60)
        client.connect("127.0.0.1", 1883, 60)

        # client.publish('SEEDQ', 111, 0, False)

        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        client.loop_forever()
        while True:
            ra.serialize_issues()
            ra.print_issues()
            ra.send_issues()
            time.sleep(30)
    except KeyboardInterrupt:
        print ">> CTRL+C exiting ..."
