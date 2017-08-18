#!/bin/bash

function show_usage {
	echo "mtu-discover.sh [-h|--help] -i|--interface INTERFACE [-r|recheck]"
	echo "  [-a|--apply] [-x|--maxMtu max-mtu] [-n|--minMtu min-mtu]"
	echo ""
	echo "  -h, --help                 Show this help message and exit."
	echo "  -i, --interface INTERFACE  Required. Network interface to use, such as eth0."
	echo "  -r, --recheck              Recheck for MTU size that is larger than currently applied."
	echo "  -a, --apply                Apply the discovered MTU size to the interface"
	echo "  -x --maxMtu MAX-MTU        Maximum MTU size to test. Default is 1500."
	echo "  -n --minMtu MIN-MTU        Minimum MTU size to test. Default is 576."
	exit
}

# default values
INTERFACE="none"
MAX_MTU=1500
MIN_MTU=576
DEST="seeder.basechord.com"
MAX_RETRIES=1
APPLY=false
RECHECK_MAX=false

# get settings from the config file
SCRIPT_PATH="`dirname \"$0\"`"
source "$SCRIPT_PATH/mtu-discover.conf"

# get settings from command-line parameters
while [[ $# > 0 ]]
do
    key="$1"
    shift
    case $key in
	    -i|--interface)
			INTERFACE="$1"
			shift
			;;
        -r|--recheck)
			RECHECK_MAX=true
			;;
        -a|--apply)
			APPLY=true
			;;
        -x|--maxMtu)
			MAX_MTU="$1"
			shift
			;;
        -n|--minMtu)
			MIN_MTU="$1"
			shift
			;;
        -h|--help|*)
			show_usage
			;;
    esac
done

if [ "$INTERFACE" == "none" ]
then
    echo "Interface is required. Please specify an interface using --interface"
	show_usage
fi

# if recheck is not specified, then the current MTU will be used.
# get the system's original MTU setting
old_mtu_setting=$(ip link show $INTERFACE | grep -oP '(?<=mtu )[0-9]+')
if [ "$RECHECK_MAX" == "true" ]
then
    # apply the specified maximum MTU to allow testing packets up to that size
	ifconfig $INTERFACE mtu $MAX_MTU
else
    # use the system's original MTU setting to test only for a reduced MTU
	MAX_MTU=$old_mtu_setting
fi

low=$((MIN_MTU - 28))
high=$((MAX_MTU - 28))
retries=0
while [ $high -gt $low ]
do
    # find the midpoint rounded up to the nearest integer
    mid=$(bc -l <<< "scale=0;($low+$high+1)/2")
	echo "Testing packet size of $mid between $low and $high"
	# test for fragmentation with a packet size of the midpoint
    result=$(ping -c 1 -s $mid -I $INTERFACE -M do $DEST)
	echo $result
    if [[ $result == *"Frag needed"* ]]
	then
        # packet size too large
		high=$((mid - 1))
	elif [[ $result == *"0 received"* ]]
	then
	    # packet lost
		if [ $retries -eq $MAX_RETRIES ]
		then
		    # assume packet size is too large
			high=$((mid - 1))
		    retries=0
		else
		    # try again (leave the low, mid, and high values as-is)
			retries=$((retries + 1))
		fi
	else
	    # packet size is less than or equal to actual MTU
		low=$mid
    fi
done

mtu=$((low + 28))
if [ $mtu -eq $MAX_MTU ]
then
    if [ $MAX_MTU -eq $old_mtu_setting ]
	then
	    echo "Path MTU is greater than or equal to the system's current MTU of $MAX_MTU"
	else
        echo "Path MTU is greater than or equal to the specified maximum MTU of $MAX_MTU"
	fi
else
    echo "Path MTU is discovered to be $mtu"
fi

if [ "$APPLY" == "true" ]
then
    # Call ifconfig to set MTU size
    ifconfig $INTERFACE mtu $mtu
	
	# Add if-up.d script so MTU is automatically set when the interface is brought up
	echo "#!/bin/bash" > /etc/network/if-up.d/000mtu
	echo "ifconfig $INTERFACE mtu $mtu" >> /etc/network/if-up.d/000mtu
	echo  >> /etc/network/if-up.d/000mtu
	
	echo "MTU for $INTERFACE is now set at $mtu"
else
    # revert to the system's original MTU setting
	ifconfig $INTERFACE mtu $old_mtu_setting
fi