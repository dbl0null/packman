#!/usr/bin/env bash

function state_error
{
	echo "ERROR: ${1:-UNKNOWN} (status $?)" 1>&2
	exit 1
}

function check_pkg
{
	echo "checking to see if package $1 is installed..."
	dpkg -s $1 || state_error "package $1 is not installed"
	echo "package $1 is installed"
}

function check_user
{
	echo "checking to see if user $1 exists..."
	id -u $1 || state_error "user $1 doesn't exists"
	echo "user $1 exists"
}

function check_port
{
	echo "checking to see if port $1 is opened..."
	nc -z $1 $2 || state_error "port $2 is closed"
	echo "port $2 on $1 is opened"
}

function check_dir
{
	echo "checking to see if dir $1 exists..."
	if [ -d $1 ]; then
		echo "dir $1 exists"
	else
		state_error "dir $1 doesn't exist"
	fi
}

function check_file
{
	echo "checking to see if file $1 exists..."
	if [ -f $1 ]; then
		echo "file $1 exists"
		# if [ -$2 $1 ]; then
			# echo "$1 exists and contains the right attribs"
		# else
			# state_error "$1 exists but does not contain the right attribs"
		# fi
	else
		state_error "file $1 doesn't exists"
	fi
}

function check_upstart
{
	echo "checking to see if $1 daemon is running..."
	sudo status $1 || state_error "daemon $1 is not running"
	echo "daemon $1 is running"
}

function check_service
{
    echo "checking to see if $1 service is running..."
    sudo service $1 status || state_error "service $1 is not running"
    echo "service $1 is running"
}


PKG_NAME="logstash"
PKG_DIR="/sources/logstash"
BOOTSTRAP_LOG="/var/log/cloudify3-bootstrap.log"

BASE_DIR="/opt"
HOME_DIR="${BASE_DIR}/${PKG_NAME}"

LOG_DIR="/var/log"

PKG_INIT_DIR="${PKG_DIR}/config/init"
INIT_DIR="/etc/init"
INIT_FILE="logstash.conf"

PKG_CONF_DIR="${PKG_DIR}/config/conf"
CONF_DIR="/etc"
CONF_FILE="logstash.conf"


echo "creating ${PKG_NAME} application dir..."
sudo mkdir -p ${HOME_DIR}
check_dir "${HOME_DIR}"

echo "creating ${PKG_NAME} home dir..."
sudo mkdir -p /home/logstash
check_dir "/home/logstash"

echo "placing jar file..."
sudo cp ${PKG_DIR}/logstash-*-flatjar.jar ${HOME_DIR}
check_file "${HOME_DIR}/logstash-*-flatjar.jar"

echo "moving some stuff around..."
sudo cp ${PKG_INIT_DIR}/${INIT_FILE} ${INIT_DIR}
check_file "${INIT_DIR}/${INIT_FILE}"

sudo cp ${PKG_CONF_DIR}/${CONF_FILE} ${CONF_DIR}
check_file "${CONF_DIR}/${CONF_FILE}"

echo "creating logstash user..."
sudo useradd --shell /usr/sbin/nologin --create-home --home-dir ${HOME_DIR} --groups adm logstash
check_user "logstash"

echo "pwning ${PKG_NAME} file by logstash user..."
sudo chown logstash:logstash ${HOME_DIR}/logstash-*-flatjar.jar
echo "creating ${PKG_NAME} file link..."
sudo ln -sf ${HOME_DIR}/logstash-*-flatjar.jar ${HOME_DIR}/logstash.jar
#TODO: check if file link exists
# echo "creating ${PKG_NAME} logfile..."
# sudo touch ${LOG_DIR}/logstash.out
# echo "pwning logstash logfile by ${PKG_NAME} user..."
# sudo chown logstash:adm ${LOG_DIR}/logstash.out

echo "starting ${PKG_NAME}..."
sudo start logstash
check_upstart "logstash"