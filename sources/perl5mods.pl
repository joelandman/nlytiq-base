#!/usr/bin/env perl
# install perl modules
use strict;
use CPAN;
use MCE::Loop;

my @mods=qw(
        Digest::SHA IO::Pty IPC::Cmd IO::Socket::SSL
	IPC::Run File::Spec File::PathConvert ZMQ::LibZMQ3
	Getopt::Lucid JSON::PP DBI DBD::SQLite Digest::SHA1
	File::ChangeNotify Data::Serializer Time::ParseDate Moo
	Text::ASCIITable Text::UnicodeTable::Simple Text::Table
	Module::Install Module::AutoInstall Module::Build Starman
	Mojolicious XML::Smart
	Math::Random::Secure
	Crypt::PRNG MCE MCE::Loop MCE::Flow
	MCE::Map MCE::Grep MCE::Queue MCE::Hobo MCE::Shared
	HTTP::Response HTML::Entities
	URI::Escape 
	ZMQ::FFI SVG::Sparkline
);

MCE::Loop->init(
  max_workers => 8, chunk_size => 1
);

mce_loop {
           my ($mce, $chunk_ref, $chunk_id) = @_;
           MCE->say("$chunk_id: $_");
           CPAN::Shell->install($_);
        } @mods;
