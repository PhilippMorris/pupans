#! /bin/sh
DEFAULT_IP=127.0.0.1

case "$1" in
  add)
    IP=${3:-$DEFAULT_IP}
	sed -i -e "/\b$2\b/d" /etc/hosts
	echo "$IP $2"  >> /etc/hosts
        ;;
  remove)
        sed -i -e "/\b$2\b/d" /etc/hosts
        ;;

  *)
        echo "Usage: "
        echo "hosts.sh [add|remove] [hostname] [ip]"
        echo 
        echo "Ip defaults to 127.0.0.1"
        echo "Examples:"
        echo "hosts.sh add testing.com"
        echo "hosts.sh remove testing.com 192.168.1.1"
        exit 1
        ;;
esac

exit 0
