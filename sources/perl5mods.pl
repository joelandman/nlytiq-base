#!/usr/bin/env perl
# install perl modules
use strict;
use CPAN;
use MCE::Loop;

my @mods=qw(
        Digest::SHA
	Digest::SHA1
	Module::Install
	Module::AutoInstall 
	Module::Build 
	MCE 
	MCE::Queue 
	MCE::Shared 
	Moo
	HTTP::Response 
	HTML::Entities
	URI::Escape 
	Starman
	Mojolicious 
	Data::Serializer
	IO::Pty 
	IPC::Cmd 
	IO::Socket::SSL
	IPC::Run 
	File::Spec 
	File::PathConvert 
	Getopt::Lucid
	JSON::PP
	DBI
	DBD::SQLite	
	File::ChangeNotify
	Time::ParseDate
	Text::ASCIITable 
	Text::UnicodeTable::Simple 
	Text::Table
	Math::Random::Secure 
	Crypt::PRNG 	
	ZMQ::LibZMQ3	
	ZMQ::FFI
	SVG::Sparkline
);

# This used to run mce_loop with 8 workers and chunk_size 3, and pass $_ to
# CPAN::Shell->install.  Inside an mce_loop block $_ is the chunk -- an array
# reference -- not one module name, so every install call got a reference and
# died with:
#
#     1: ARRAY(0x55d3...)
#     Can't call method "color_cmd_tmps" on unblessed reference
#         at CPAN/Shell.pm line 1751
#
# Nothing in this list was ever installed by this script; the modules that did
# turn up came in as dependencies of something else.  That is also what the
# "run it twice, the second pass fixes a dependency error" comment in
# Makefile.perl5mods was really working around.
#
# The loop is also serial now.  CPAN takes a single global lock on its build
# directory, so concurrent CPAN::Shell->install calls do not proceed in
# parallel anyway: they queue on the lock, and a blocked one can stop to ask
# whether to break it, which hangs a non-interactive build.  MCE stays in the
# module list above -- it is worth having -- it just cannot drive CPAN.

foreach my $mod (@mods) {
    printf("installing %s\n", $mod);
    CPAN::Shell->install($mod);
}
