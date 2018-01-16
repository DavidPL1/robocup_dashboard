# Sandbox for a transport enabled dashboard for Redmine

## Installation

Tested on Ubuntu 16.04

<pre>
sudo apt-get install rabbitmq-server
sudo pip install pika
sudo pip install flatbuffers
</pre>

Clone this:

<pre>
git clone https://github.com/warp1337/redmine_dashboard.git
</pre>

## Usage

<pre>
sudo service rabbitmq-server start
sudo /usr/lib/rabbitmq/bin/rabbitmq-plugins enable rabbitmq_web_stomp
cd redmine_dashboard
python main.py -u $TARGETURL -p $PROJECT -l $LOGIN -c PASSWORD
</pre>