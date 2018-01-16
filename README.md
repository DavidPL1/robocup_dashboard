# Sandbox for a transport enabled dashboard for Redmine

## Installation

Tested on Ubuntu 16.04

Install rabbit-mq server as explained here: https://www.rabbitmq.com/install-debian.html

Then:

<pre>
sudo pip install pika
sudo pip install flatbuffers
</pre>

Finally, clone this repo:

<pre>
git clone https://github.com/warp1337/redmine_dashboard.git
</pre>

## Usage

<pre>
sudo service rabbitmq-server start
sudo /usr/lib/rabbitmq/bin/rabbitmq-plugins enable rabbitmq_web_stomp
sudo service rabbitmq-server stop
sudo service rabbitmq-server start
/usr/lib/rabbitmq/bin/rabbitmq-plugins list
cd redmine_dashboard
python main.py -u $TARGETURL -p $PROJECT -l $LOGIN -c PASSWORD
</pre>