class eventlog {

	package { 'netcat-openbsd': ensure => 'latest' }

	file { '/opt/eventlog':
		owner => 'root',
		group => 'root',
		mode => 755,
		ensure => 'directory'
	}
	
	file { "/opt/eventlog/testconnection.ignorentp":
		ensure => "present",
		owner => "root",
		group => "root",
		mode => 755
	}
	
	file { '/opt/eventlog/events.py':
		ensure => 'present',
		owner => 'root',
		group => 'root',
		mode => 755,
		source => ['puppet:///modules/eventlog/events.py']
	}
	
	file { '/opt/eventlog/eventlog':
		ensure => 'present',
		owner => 'root',
		group => 'root',
		mode => 755,
		recurse => true,
		source => ['puppet:///modules/eventlog/eventlog']
	}

	file { '/opt/eventlog/events.conf':
		ensure => 'present',
		owner => 'root',
		group => 'root',
		mode => 755,
		source => ["puppet:///modules/eventlog/${domain}-events.conf"]
	}

	file { '/opt/eventlog/eventlog_post.sh':
		ensure => 'present',
		owner => 'root',
		group => 'root',
		mode => 755,
		source => ['puppet:///modules/eventlog/eventlog_post.sh']
	}
	
	file { '/opt/eventlog/testconnection.py':
		ensure => 'present',
		owner => 'root',
		group => 'root',
		mode => 755,
		content => template('eventlog/testconnection.py.erb')
	}
	
	file { '/opt/eventlog/testconnection.sh':
		ensure => 'present',
		owner => 'root',
		group => 'root',
		mode => 755,
		source => ['puppet:///modules/eventlog/testconnection.sh']
	}

	file { '/opt/eventlog/lock.py':
		ensure => 'present',
		owner => 'root',
		group => 'root',
		mode => 755,
		source => ['puppet:///modules/eventlog/lock.py']
	}
	
	file { '/etc/rc3.d/S80connection-test':
		ensure => 'link',
		owner => 'root',
		group => 'root',
		mode => 744,
		target => '/opt/eventlog/eventlog_post.sh'
	}
	
	cron { 'Check connection and upload event log':
		command => '(/usr/local/bin/random-delay.sh 1100; /opt/eventlog/eventlog_post.sh) >> /var/log/cronjobs/eventlog_post.log 2>&1',
		user => 'root',
		hour  => '*',
		minute => [0, 20, 40]
	}
	
	cron { 'Check connection and log':
		ensure => absent,
		user => root
	}
}
