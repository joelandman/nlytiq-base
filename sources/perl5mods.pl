#!/usr/bin/env perl
# install perl modules
use strict;
use CPAN;
use MCE::Loop;

my @mods=qw(
  Digest::SHA IO::Pty IPC::Cmd
	IPC::Run File::Spec File::PathConvert Sys::Hostname ZMQ::LibZMQ3
	Getopt::Lucid JSON::PP DBI DBD::SQLite Digest::SHA1
	File::ChangeNotify Data::Serializer Time::ParseDate Moo
	Text::ASCIITable Text::UnicodeTable::Simple Text::Table
	Module::Install Module::AutoInstall Module::Build Starman
	Net::Server::PreFork HTML::Mason Mojolicious
	Mojolicious::Plugin::Mason1Renderer XML::Smart
	Config::General Config::IniFiles Config::JSON Math::Random::Secure
	Crypt::PRNG MCE MCE::Loop MCE::Flow
	MCE::Map MCE::Grep MCE::Queue MCE::Hobo MCE::Shared
	HTML::TreeBuilder Params::Validate
	Mojolicious::Plugin::RemoteAddr HTTP::Response HTML::Entities
	Config::Scoped  FFI::Platypus  FFI::CheckLib  FFI::Raw
	FFI::Platypus::Declare FFI::Platypus::Memory
	FFI::Platypus::API FFI::Platypus::Type
	URI::Escape  IO::Socket::Netlink::Taskstats
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
