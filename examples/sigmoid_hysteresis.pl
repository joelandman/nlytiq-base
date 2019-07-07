#!/usr/bin/env perl
use Chart::Gnuplot;

# note, you may need to add
#
# <policy domain="coder" rights="read|write" pattern="PNG" />
#
# to your /etc/ImageMagick-6/policy.xml

my (@ds,@s1,@s2,@s3,@x);

# sigmoid function
sub s {
    my ($a,$x) = @_;
    return 1/(1+exp(-$a*$x));
}

# offset sigmoid
sub os {
   my ($o,$a,$x) = @_;
   return &s($a,-$o + $x)
}

#x  =  -5.0:0.1:5.0;
@x  = map { $_/10 }(-50 .. 50);

@s1 = map { &os( 0,5,$_) } @x;
@s2 = map { &os(-1,5,$_) } @x;
@s3 = map { &os( 1,5,$_) } @x;



#plot(x,s1,x,s2,x,s3)
my $chart = Chart::Gnuplot->new(
    output => "sfh_p5.png",
    title  => "Sigmoid Hysteresis with offset",
    xlabel => "x",
    ylabel => "y",
);

$ds[1] = Chart::Gnuplot::DataSet->new(
    xdata => \@x,
    ydata => \@s1,
    title => "s1",
    style => "linespoints",
);
$ds[2] = Chart::Gnuplot::DataSet->new(
    xdata => \@x,
    ydata => \@s2,
    title => "s2",
    style => "linespoints",
);
$ds[3] = Chart::Gnuplot::DataSet->new(
    xdata => \@x,
    ydata => \@s3,
    title => "s3",
    style => "linespoints",
);

$chart->plot2d($ds[1],$ds[2],$ds[3]);
