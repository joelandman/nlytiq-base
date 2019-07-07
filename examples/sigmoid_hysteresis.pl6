#!/usr/bin/env perl6

# sigmoid function
my $s  = sub (Numeric $a,$x) {1/(1+exp(-$a*$x))}

# offset sigmoid
my $os = sub (Numeric $o,$a,$x) {$s($a,-$o + $x)}

#x  =  -5.0:0.1:5.0;
my @x = (-50 .. 50)  »*»  0.1;

my @s1 = map { $os( 0,5,$_) }, @x;
my @s2 = map { $os(-1,5,$_) }, @x;
my @s3 = map { $os( 1,5,$_) }, @x;

# plotting would go here, but P6 has a dearth of options for this.
# shelling out to gnuplot might make the most sense

#plot(x,s1,x,s2,x,s3)
#print (hf, "sfh.png", "-dpng");

#exit
