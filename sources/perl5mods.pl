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

MCE::Loop->init(
  max_workers => 8, chunk_size => 3
);

mce_loop {
           my ($mce, $chunk_ref, $chunk_id) = @_;
           MCE->say("$chunk_id: $_");
           CPAN::Shell->install($_);
        } @mods;
