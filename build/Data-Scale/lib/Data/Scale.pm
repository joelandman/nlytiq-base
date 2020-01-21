package Data::Scale;

use warnings;
use strict;
require Exporter;
our @ISA    = qw( Exporter );
our @EXPORT = qw( true false );


=head1 NAME

Data::Scale - Data Scaling Constants and Utility functions

=head1 VERSION

Version 1.00

=cut

our $VERSION = '1.00';


=head1 SYNOPSIS

    use strict;
    use Data::Scale;
    my ($x,$y,$v);

    $x = true; 
    $y = false;
    $v = Data::Scale->size_to_bytes("2.34GB");

    ...


=cut


=head1 FUNCTIONS

=head2 function1

=cut


sub units {
    my $self	= shift;
    my $units;
    $units ->{SI} = {
	  order => [qw(B KB MB GB TB PB EB ZB YB)],
	  B   => 1,
	  KB  => 1000,
	  MB  => 1000*1000,
	  GB  => 1000*1000*1000,
	  TB  => 1000*1000*1000*1000,
	  PB  => 1000*1000*1000*1000*1000,
	  EB  => 1000*1000*1000*1000*1000*1000,
	  ZB  => 1000*1000*1000*1000*1000*1000*1000,
	  YB  => 1000*1000*1000*1000*1000*1000*1000*1000
	 };
    
    $units ->{IEC} = {
	  order => [qw(B KiB MiB GiB TiB PiB EiB ZiB YiB)],
	  B   => 1,
	  KiB => 1024,
	  MiB => 1024*1024,
	  GiB => 1024*1024*1024,
	  TiB => 1024*1024*1024*1024,
	  PiB => 1024*1024*1024*1024*1024,
	  EiB => 1024*1024*1024*1024*1024*1024,
	  ZiB => 1024*1024*1024*1024*1024*1024*1024,
	  YiB => 1024*1024*1024*1024*1024*1024*1024*1024,
	 };
    return $units;
}

sub size_to_bytes {
    my ($self,$string,$attr)  = @_;
    my $rv = undef;
    
    # %attrs => {debug => true} will turn on debugging
    my $debug;
    $debug	= $attr->{'debug'} if (defined($attr->{'debug'}));
    
    # input string in the form (\d+\.{0,1}\d{0,})\s{0,}([kKMGTPEZY]{0,1}i{0,1}B)
    # return the size in bytes of this string
    my $units	= $self->units();
    if ($string) {
    if ($string =~ /(\d+\.{0,1}\d{0,})\s{0,}([kKMGTPEZY]{0,1}i{0,1}B)/)
       {
	my $scale	= $2;
	$scale 		=~ s/^k/K/; # force K to be upper case if it is there
	my $value	= $1;
	my $type	= 'SI';
	$type	= 'IEC' if ($scale =~ /.iB/i);
	printf STDERR "D[%i] Data::Scale::size_to_bytes value,scale,type=%s, %s, %s\n",$$,$value,$scale,$type if ($debug);
	$rv	= $value * $units->{$type}->{$scale};
       }
      elsif ($string =~ /(\d+\.{0,1}\d{0,})/)
       {
	$rv	= $string;
       }
     }
    return $rv;
}

sub bytes_to_size {
    my ($self,$value,$attrs)  = @_;
    my ($rv,$type,$debug);
    # input value in bytes
    # if $scale is not defined, then set scale to MB
    # if $digits is not defined, then set digits to 3
    $debug	= $attrs->{'debug'} if (defined($attrs->{'debug'}));
    
    $attrs->{digits}	= 3 	if (!$attrs->{digits});
    $attrs->{scale}	= "MB"	if (!$attrs->{scale});
    $type	= "SI";
    $type	= "IEC" if ($attrs->{scale} =~ /.iB/);
    
    my $units	= $self->units();
    my $tmp_rv 	= ($value ? $value/$units->{$type}->{$attrs->{scale}} : 0);
    my $fmt	= "%.".(sprintf '%i',$attrs->{digits})."f %s";
    printf STDERR "D[%i] Data::Scale::bytes_to_size tmp_rv,units,fmt=\'%s\', %s, %s\n",$$,$tmp_rv,$attrs->{scale},$fmt if ($debug);
    $rv		= sprintf $fmt,$tmp_rv,$attrs->{scale};
    return $rv;
}


=head2 rescale

=cut

sub rescale {
    my ($self,$string,$attrs)  = @_;
    my ($rv,$actual);
    # input string in the form (\d+\.{0,1}\d{0,})\s{0,}([kKMGTPEZY]{0,1}i{0,1}B)
    # return the size in bytes of this string
    my $units	= $self->units();
    
    # %attrs => {debug => true} will turn on debugging
    my $debug;
    $debug	= $attrs->{'debug'} if (defined($attrs->{'debug'}));
    $actual	= $self->size_to_bytes($string,$attrs);
    $rv		= $self->bytes_to_size($actual,$attrs);
    printf STDERR "D[%i] Data::Scale::rescale string,actual,units = %s, %s, %s\n",$$,$string,$actual,$attrs->{scale} if ($debug);
    return $rv;
}

=head2 autoscale

=cut

sub autoscale {
    my ($self,$string,$attrs)  = @_;
    my ($rv,$actual,$scale,$type,$digits,$tmp_rv,$q);
    # input string in the form (\d+\.{0,1}\d{0,})\s{0,}([kKMGTPEZY]{0,1}i{0,1}B)
    # return the size in bytes of this string
    my $units	= $self->units();
    
    # %attrs => {debug => true} will turn on debugging
    my $debug;
    $debug	= $attrs->{'debug'} if (defined($attrs->{'debug'}));
    $actual	= $self->size_to_bytes($string,$attrs);
    $attrs->{digits}	= 3 	if (!$attrs->{digits});
    $type	= "SI";
    $type	= "IEC" if (
			    ($attrs->{scale} && ($attrs->{scale} =~ /.iB/)) ||
			    ($attrs->{scale} && ($attrs->{units}=~/IEC/i))
			   );
    printf STDERR "D[%i] Data::Scale::autoscale string,actual,type = %s, %s, %s\n",$$,$string,$actual,$type if ($debug);
   
    # now progressively divide actual by $units->{$type}->{$scale} until we have no more than 3 digits
    # before the decimal
    my @order	= @{$units->{$type}->{order}};
    printf STDERR "D[%i] Data::Scale::autoscale order = %s\n",$$,join(",",@order) if ($debug);
    foreach $scale (@order)
      {
        printf STDERR "D[%i]  Data::Scale::autoscale loop actual,scale, units = %s, %s, %s\n",$$,$actual,$units->{$type}->{$scale},$scale if ($debug);
	$tmp_rv	= ($actual ? $actual / $units->{$type}->{$scale} : 0);
        printf STDERR "D[%i]  Data::Scale::autoscale loop tmp_rv = %s\n",$$,$tmp_rv if ($debug);
	$q	= int($tmp_rv);
        printf STDERR "D[%i]  Data::Scale::autoscale loop q = %s\n",$$,$q if ($debug);
	if (
	    (length($q) >= 1) &&
	    (length($q) <= 3) &&
	    int($q) >= 1
	   )
	   {
	    my $fmt	= '%.'.(sprintf '%i',$attrs->{digits})."f %s";
	    printf STDERR "D[%i]  Data::Scale::autoscale final format fmt=\'%s\', tmp_rv=%s, scale=%s\n",$$,$fmt,$tmp_rv,$scale if ($debug);
            $q  	= sprintf $fmt,$tmp_rv,$scale;
	    $tmp_rv	= $q;
	    last;
	   }
      }
    $rv		= $tmp_rv;
    return $rv;
}

=head1 AUTHOR

Joe Landman, C<< <joe.landman at gmail.com> >>

=head1 BUGS

Please report any bugs or feature requests to C<bug-si-utils at rt.cpan.org>, or through
the web interface at L<http://rt.cpan.org/NoAuth/ReportBug.html?Queue=Data-Scale>.  I will be notified, and then you'll
automatically be notified of progress on your bug as I make changes.




=head1 SUPPORT

You can find documentation for this module with the perldoc command.

    perldoc Data::Scale


You can also look for information at:

=over 4

=item * RT: CPAN's request tracker

L<http://rt.cpan.org/NoAuth/Bugs.html?Dist=Data-Scale>

=item * AnnoCPAN: Annotated CPAN documentation

L<http://annocpan.org/dist/Data-Scale>

=item * CPAN Ratings

L<http://cpanratings.perl.org/d/Data-Scale>

=item * Search CPAN

L<http://search.cpan.org/dist/Data-Scale>

=back


=head1 ACKNOWLEDGEMENTS


=head1 COPYRIGHT & LICENSE

Copyright 2017 Joe Landman, all rights reserved.

This program is free software; you can redistribute it and/or modify it
under the same terms as Perl itself.


=cut

1; # End of Data::Scale
