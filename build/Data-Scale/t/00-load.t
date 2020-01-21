#!perl -T

use Test::More qw(no_plan);
BEGIN {
	use_ok( 'Data::Scale' );
}

diag( "Testing Data::Scale $Data::Scale::VERSION, Perl $], $^X" );

my $x1 = Data::Scale->size_to_bytes("1.23GiB",{debug => 1});
eval {diag("x1=".$x1)};
if ($x1 == 1320702443.52)
   { 
    pass("x1 = ".$x1);
   }
  else
   { 
    fail("x1 != ".$x1);
   }

my $x2 = Data::Scale->size_to_bytes("1.23 GB",{debug => 1});
eval {diag("x2=".$x2)};
if ($x2 == 1230000000)
   {
    pass("x2 = ".$x2);
   }
  else
   { 
    fail("x2 != ".$x2);
   }
   
my $x3 = Data::Scale->bytes_to_size(1024,{debug => 1});
eval {diag("x3=".$x3)};
if ($x3 =~ "0.001 MB")
   {
    pass("x3 = ".$x3);
   }
  else
   { 
    fail("x3 != ".$x3);
   }
   
my $x4 = Data::Scale->bytes_to_size(1024*1024,{debug => 1,digits=>2});
eval {diag("x4=".$x4)};
if ($x4 =~ "1.05 MB")
   {
    pass("x4 = ".$x4);
   }
  else
   { 
    fail("x4 != ".$x4);
   }
   
my $x5 = Data::Scale->bytes_to_size(1024*1024,{debug => 1,digits=>1,scale=>"MiB"});
eval {diag("x5=".$x5)};
if ($x5 =~ "1.0 MiB")
   {
    pass("x5 = ".$x5);
   }
  else
   { 
    fail("x5 != ".$x5);
   }

$x1 = Data::Scale->rescale(1000*1024,{debug => 1,digits=>1,scale=>"KiB"});
eval {diag("x1=".$x1)};
if ($x1 =~ "1000.0 KiB")
   {
    pass("x1 = ".$x1);
   }
  else
   { 
    fail("x1 != ".$x1);
   }

$x1 = Data::Scale->autoscale(1024*1024*1024*1024,{debug => 1,units=>'SI'});
eval {diag("x1=".$x1)};
if ($x1 =~ "1.100 TB")
   {
    pass("x1 = ".$x1);
   }
  else
   { 
    fail("x1 != ".$x1);
   }
