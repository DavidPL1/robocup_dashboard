# Sandbox for a transport enabled dashboard for RoboCup

## The looks

<img src="https://github.com/warp1337/robocup_dashboard/raw/master/screen_1.jpg"/>
<br/>
<img src="https://github.com/warp1337/robocup_dashboard/raw/master/screen_2.jpg"/>

## Installation

Tested on Ubuntu 16.04

Install a recent version of Erlang (remove existing versions first)

<pre>
sudo apt-get update && sudo apt-get -y upgrade
wget https://packages.erlang-solutions.com/erlang-solutions_1.0_all.deb
sudo dpkg -i erlang-solutions_1.0_all.deb
sudo apt-get update
sudo apt-get install esl-erlang
</pre>

Install a recent version of rabbitmq

<pre>
echo "deb https://dl.bintray.com/rabbitmq/debian xenial main" | sudo tee /etc/apt/sources.list.d/bintray.rabbitmq.list
wget -O- https://dl.bintray.com/rabbitmq/Keys/rabbitmq-release-signing-key.asc | sudo apt-key add -
sudo apt-get update
sudo apt-get install rabbitmq-server
</pre>

Then:

<pre>
sudo pip install pika
sudo pip install flatbuffers
sudo pip install python-redmine
sudo pip install paho-mqtt
</pre>

Finally, clone this repo:

<pre>
git clone https://github.com/warp1337/redmine_dashboard.git
</pre>

## Usage

<pre>
sudo service rabbitmq-server start
sudo rabbitmq-plugins enable rabbitmq_management rabbitmq_web_mqtt rabbitmq_mqtt
sudo service rabbitmq-server stop
sudo service rabbitmq-server start
cd redmine_dashboard
python main.py -u $TARGETURL -p $PROJECT -l $LOGIN -c PASSWORD
</pre>
