#!/usr/local/bin/perl
# Copyright (c) 2009-2016 Wolfram Schneider, https://bbbike.org
#
# livesearch.cgi - bbbike.org live routing search

use CGI qw/-utf-8 escapeHTML/;
use CGI::Carp;
use IO::File;
use IO::Dir;
use Encode;
use Data::Dumper;

use strict;
use warnings;

binmode \*STDOUT, ":utf8";
$ENV{PATH} = "/bin:/usr/bin";

my $q = new CGI;

my $dir         = "msg";
my $master_lang = "de";
my $debug       = 1;

sub get_languages_list {
    my $dir = shift;

    my $fh = IO::Dir->new($dir);
    if ( !defined $fh ) {
        warn "opendir $dir: $!\n";
        return;

    }

    my @list;
    while ( defined( $_ = $fh->read ) ) {
        push( @list, $_ ) if /^[a-z][a-z]$/;
    }

    return sort @list;
}

sub footer {
    return <<EOF;
<div id="footer">
<div id="footer_top">
<a href="../">home</a>
</div>
</div>
<hr/>

<div id="copyright" style="text-align: center; font-size: x-small; margin-top: 1em;" >
(&copy;) 2008-2012 <a href="http://www.rezic.de/eserte">Slaven Rezi&#x107;</a> &amp; <a href="https://wolfram.schneider.org">Wolfram Schneider</a> // <a href="http://www.bbbike.de">http://www.bbbike.de</a> <br />
<div id="footer_community">
</div>
</div>
EOF
}

sub css {

    return <<EOF;
    <style type="text/css">

tr.en { color: green; }
tr.de td { color: black; border-top: 1px solid black }

tr.even { background-color: #FFF; }
tr.odd { background-color: #EEE; }
tr.odd:hover, tr.even:hover {  background-color:silver; }

div#main { padding: 1em; }
table { border: 1px solid black; }

    </style>

EOF

}

sub display_table {
    my %args = @_;

    my $dir       = $args{'dir'};
    my $lang      = $args{'lang'};
    my $languages = $args{'languages'};
    my $q         = $args{'q'};

    my $hash;
    my @languages = sort @$languages;

    @languages = grep { $_ eq $lang } @languages if $lang;

    # "en" first
    @languages = grep { $_ ne "en" } @languages;
    unshift @languages, "en";

    foreach my $l ( sort @languages ) {
        $hash->{$l} = require "$dir/$l";
    }

    my $counter = 0;
    print "<table>\n";
    foreach my $key ( sort keys %{ $hash->{"en"} } ) {
        my $key = Encode::decode( "iso-8859-1", $key );

        $counter++;
        my $odd = $counter % 2 ? "odd" : "even";
        print qq{<tr class="de $odd"><td>$counter</td><td>de</td><td>},
          escapeHTML($key), qq{</td></tr>\n};
        foreach my $l (@languages) {
            my $val =
              Encode::decode( "utf8", $hash->{$l}->{$key} || "!!!UNKNOWN!!!" );

            print qq|<tr class="$l $odd"><td></td><td>$l</td><td>|,
              escapeHTML($val), qq|</td></tr>\n|;
        }
    }

    print "</table>\n";
}

# debugging
sub is_tainted {
    local $@;    # Don't pollute caller's value.
    return !eval { eval( "#" . substr( join( "", @_ ), 0, 0 ) ); 1 };
}

##############################################################################################
#
# main
#

print $q->header( -charset => 'utf-8' );

print $q->start_html(
    -title => 'BBBike @ World languages',
    -head  => $q->meta(
        {
            -http_equiv => 'Content-Type',
            -content    => 'text/html; charset=utf-8'
        }
    ),
);

my @languages = &get_languages_list($dir);
my $lang = $q->param('lang') || "";
if ( $lang =~ /^([a-z]+$)/ ) {
    $lang = $1;
}
else {
    $lang = "";
}

print &css;

print $q->h1('BBBike @ World languages'), "\n";
print qq{<div id="main">\n};
&display_table(
    'dir'       => $dir,
    'lang'      => $lang,
    'languages' => \@languages,
    'q'         => $q
);
print "</div>\n";
print &footer;

print $q->end_html;

1;
