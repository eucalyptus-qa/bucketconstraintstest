#!/usr/bin/perl
use strict;
use warnings;
use Cwd qw(abs_path);
use Data::Dumper;
use lib abs_path("../share/perl_lib/EucaTest/lib");
use EucaTest;


my $ALLOWALLPOLICY = "./policy/allowall.policy";
### Pass in the path to the input file and a password if keys have not been exchanged between the tester and DU
my $clc_connection = EucaTest->new( );
my $local = EucaTest->new({ host => "local"});
$clc_connection->sync_keys();
my @walrii =  $clc_connection->get_machines("ws");
my $walrus_ip = $walrii[0]->{"ip"};

print "Walrus IPs:\n " . Dumper(@walrii);

my $time = time();

my $account1 = "bucket-constraint1-" . $time;
my $user1 = "user1-" . $time;
my $user2 = "user2-" . $time;
my @clcs =  $clc_connection->get_machines("clc");
my $clc_ip = $clcs[0]->{"ip"};
$local->sys( "scp -o StrictHostKeyChecking=no -r policy root\@" . $clc_ip . ":" );
$clc_connection->euare_create_account($account1);
$clc_connection->euare_create_user( $user1, $account1 );
$clc_connection->euare_create_user( $user2, $account1 );
$clc_connection->euare_attach_policy_user( $user1, "allowall", $ALLOWALLPOLICY, $account1 );

my $user1_cred = $clc_connection->get_cred($account1, $user1);
my $user2_cred = $clc_connection->get_cred($account1, $user2);

## GET ACCESS AND SECRET KEYS
my $user1_access = $clc_connection->get_access_key($user1_cred);
my $user2_access = $clc_connection->get_access_key($user2_cred);
my $user1_secret = $clc_connection->get_secret_key($user1_cred);
my $user2_secret = $clc_connection->get_secret_key($user2_cred);

chomp($user1_access);
chomp($user2_access);
chomp($user1_secret);
chomp($user2_secret);



$clc_connection->modify_property("walrus.storagemaxbucketsizeinmb",500);
$local->sys( "scp -o StrictHostKeyChecking=no -r bucketconstraintstest.py root\@" . $clc_ip . ":" );
$local->sys( "scp -o StrictHostKeyChecking=no -r dummyobj root\@" . $clc_ip . ":" );

my $cmd = "./bucketconstraintstest.py --url $walrus_ip --user1-access $user1_access --user1-secret $user1_secret --user2-access $user2_access --user2-secret $user2_secret";

### IF we are using RHEL or CENTOS 5
if ( ($clcs[0]->{"distro"} =~ /rhel/i || $clcs[0]->{"distro"} =~ /centos/i) && $clcs[0]->{"distro_ver"} =~ /5/i )  {
	if($clcs[0]->{"source"} =~ /BZR/){
	   $cmd = "python2.5 " . $cmd;
	}else{
	   $cmd = "python2.6 " . $cmd;
	}
	
}
if( ! $clc_connection->found($cmd,qr/Successfully received exception/)){
	$clc_connection->fail("Found error in python script");
}


$clc_connection->euare_delete_account($account1);


### The fail count gets incremented everytime the fail function is called
$clc_connection->do_exit();