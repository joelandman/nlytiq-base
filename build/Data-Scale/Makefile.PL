use strict;
use warnings;
use ExtUtils::MakeMaker;

WriteMakefile(
    NAME                => 'Data::Scale',
    AUTHOR              => 'Joe Landman <joe.landman@gmail.com>',
    VERSION_FROM        => 'lib/Data/Scale.pm',
    ABSTRACT_FROM       => 'lib/Data/Scale.pm',
    PL_FILES            => {},
    PREREQ_PM => {
        'Test::More' => 0,
    },
    dist                => { COMPRESS => 'gzip -9f', SUFFIX => 'gz', },
    clean               => { FILES => 'Data-Scale-*' },
);
