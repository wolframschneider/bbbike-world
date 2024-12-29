#!/usr/local/bin/perl -T
# Copyright (c) 2012-2025 Wolfram Schneider, https://bbbike.org
#
# download.cgi - extract.bbbike.org live extracts

use CGI qw/-utf-8 unescape escapeHTML/;
use CGI::Carp;
use URI;
use URI::QueryParam;
use IO::File;
use JSON;
use Data::Dumper;
use File::stat;
use File::Basename;
use HTTP::Date;

use lib qw[../world/lib ../lib];
use Extract::Config;
use Extract::Utils;
use Extract::Locale;
use BBBike::Analytics;

use strict;
use warnings;

###########################################################################
# config

binmode \*STDOUT, ":utf8";
binmode \*STDERR, ":utf8";

$ENV{PATH} = "/bin:/usr/bin";

our $option = {
    'debug' => "0",

    'download_homepage' => 'https://download.bbbike.org/osm/',

    'extract_homepage'     => 'https://extract.bbbike.org',
    'extract_homepage_pro' => 'https://extract-pro.bbbike.org',

    'message_path' => "../world/etc/extract",
    'pro'          => 0,

    # spool directory. Should be at least 100GB large
    'spool_dir'     => '/opt/bbbike/extract',
    'spool_dir_pro' => '/opt/bbbike/extract',

    'download'     => '/osm/extract/',
    'download_pro' => '/osm/extract/',

    # cut to long city names
    'max_city_length' => 38,

    'show_heading' => 0,

    'enable_google_analytics' => 1,

    'auto_refresh' => {
        'enabled'       => 1,
        'max'           => 20,
        'delay_seconds' => 30,
    },
};

###########################################################################
my $q            = new CGI;
my $max_extracts = 2000;

my $default_date      = "12h";    # 24h: today
my $default_date_json = "3h";     # less data for json output
my $filter_format     = "";       # all formats

my $debug = $option->{'debug'};
if ( defined $q->param('debug') ) {
    $debug = int( $q->param('debug') );
}
if ( defined $q->param('format') ) {
    $filter_format = $q->param('format');
}

my $extract_utils = new Extract::Utils;
my $extract       = Extract::Config->new( 'q' => $q, 'option' => $option );

$extract->load_config;
$extract->check_extract_pro;
my $formats = $Extract::Config::formats;
my $spool   = $Extract::Config::spool;
my $spool_dir =
  $option->{'pro'} ? $option->{'spool_dir_pro'} : $option->{'spool_dir'};

# EOF config
###########################################################################

sub M { return Extract::Locale::M(@_); };    # wrapper

# extract areas from trash can
sub extract_areas {
    my %args = @_;

    my $log_dir       = $args{'log_dir'};
    my $max           = $args{'max'};
    my $devel         = $args{'devel'} || 0;
    my $sort_by       = $args{'sort_by'} || "time";
    my $date          = $args{'date'} || "";
    my $email         = $args{'email'} || "";
    my $filter_format = $args{'filter_format'} || "";

    my $max_days = 6;

    warn
"download: log dir: $log_dir, max: $max, devel: $devel, date: '$date', format='$filter_format', max days=$max_days\n"
      if $debug;

    my %hash;
    foreach my $f (`find $log_dir/ -name '*.json' -mtime -${max_days} -print`) {
        chomp $f;

        my $st = stat($f);
        if ( !$st ) {

            # already gone?
            warn "stat $f: $!\n";
        }
        else {
            $hash{$f} = $st->mtime;
        }
    }

    # newest first
    my @list = reverse sort { $hash{$a} <=> $hash{$b} } keys %hash;

    warn "download number of objects: @{[ scalar(@list) ]}\n" if $debug;

    my @area;
    my $download_dir = "$spool_dir/" . $spool->{"download"};
    my $time         = time();

    my %unique;
    for ( my $i = 0 ; $i < scalar(@list) && $i < $max ; $i++ ) {
        my $file = $list[$i];
        my $obj  = $extract_utils->parse_json_file( $file, 1 );

        next if !exists $obj->{'date'};

        # show only my extracts
        if ( $email && $obj->{'email'} ne $email ) {
            next;
        }

        my $pbf_file = $download_dir . "/" . basename( $obj->{"pbf_file"} );
        my $format   = $obj->{"format"};

        my $download_file = $pbf_file;
        $download_file =~ s/\.pbf$//;
        my $format_display = $format;

        # handle osm.pbf and srtm.osm.pbf etc.
        $format_display =~
          s/^(osm|srtm\.osm|srtm-europe\.osm|srtm|srtm-europe)\.//;
        $download_file .= "." . $format_display;

        # other languages ?
        my $lang = $obj->{"lang"};
        if ( $lang ne "en" && $lang ne "" ) {
            if ( $format eq 'bbbike-perltk.zip' && $lang ne 'de' ) {

                # only "de" and "en" is supported for perltk
            }
            else {
                $download_file =~ s/\.zip$/.${lang}.zip/;
            }
        }

        if ( !-e $download_file ) {
            warn "ignore missing $download_file format=$format\n"
              if $debug >= 2;
            next;
        }

        if ( $unique{$download_file} ) {
            warn "ignore duplicated $download_file\n" if $debug >= 2;
            next;
        }
        $unique{$download_file} = 1;

        $obj->{"download_file"} = basename($download_file);

        my $st = stat($download_file) or die "stat $download_file: $!\n";
        $obj->{"extract_time"} = $st->mtime;
        $obj->{"extract_size"} = $st->size;

        if ( $date =~ /^(\d+)h$/ ) {
            my $hours = $1;
            if ( $obj->{"extract_time"} + $hours * 3600 < $time ) {
                warn "filtered by $hours: $download_file\n" if $debug >= 2;
                next;
            }
        }

        if ( $filter_format ne "" ) {
            if ( index( $obj->{"format"}, $filter_format ) != 0 ) {
                warn
"filtered by $format: $download_file, $obj->{'format'} != $filter_format\n"
                  if $debug >= 2;
                next;
            }
        }

        warn "found download file $download_file\n" if $debug >= 3;

        push @area, $obj;
    }

    return sort_extracts( $sort_by, @area );
}

sub sort_extracts {
    my $sort_by = shift;
    my @area    = @_;

    # newest first, or otherwise
    if ( $sort_by eq 'name' ) {
        return sort { $a->{"city"} cmp $b->{"city"} } @area;
    }
    elsif ( $sort_by eq 'format' ) {
        return sort {
                $a->{"format"} cmp $b->{"format"}
              ? $a->{"format"} cmp $b->{"format"}
              : ( $a->{"extract_size"} <=> $b->{"extract_size"} ) * -1
        } @area;
    }
    elsif ( $sort_by eq 'size' ) {
        return
          reverse sort { $a->{"extract_size"} <=> $b->{"extract_size"} } @area;
    }
    else {
        return
          reverse sort { $a->{"extract_time"} <=> $b->{"extract_time"} } @area;
    }
}

# running or ready to run
sub running_extract_areas {
    my %args = @_;

    my $log_dir       = $args{'log_dir'};
    my $max           = $args{'max'};
    my $devel         = $args{'devel'} || 0;
    my $sort_by       = $args{'sort_by'} || "time";
    my $filter_format = $args{'filter_format'} || "";
    my $email         = $args{'email'} || "";

    warn "download: log dir: $log_dir, max: $max, devel: $devel\n" if $debug;

    my %hash;
    foreach my $f ( glob("$log_dir/*.json"), glob("$log_dir/*/*.json") ) {
        my $st = stat($f);
        if ( !$st ) { warn "stat $f: $!\n"; }
        else {
            $hash{$f} = $st->mtime;
        }
    }

    # newest first
    my @list = reverse sort { $hash{$a} <=> $hash{$b} } keys %hash;

    my @area;
    my $json         = new JSON;
    my $download_dir = "$spool_dir/" . $spool->{"download"};

    my %unique;
    for ( my $i = 0 ; $i < scalar(@list) && $i < $max ; $i++ ) {
        my $file = $list[$i];
        my $fh   = new IO::File $file, "r" or die "open $file: $!\n";
        binmode $fh, ":utf8";

        my $data = "";
        while (<$fh>) {
            $data .= $_;
        }

        my $obj;
        eval { $obj = $json->decode($data); };
        if ($@) {
            warn "Cannot parse json file $file: $@\n";
            next;
        }

        next if !exists $obj->{'date'};
        if ( $email && $obj->{'email'} ne $email ) {
            next;
        }

        if ( $filter_format ne "" ) {
            if ( index( $obj->{"format"}, $filter_format ) != 0 ) {
                warn
"filtered by format: $file, $obj->{'format'} != $filter_format\n"
                  if $debug >= 2;
                next;
            }
        }

        my $script_url = $obj->{"script_url"};

        if ( $unique{$script_url} ) {
            warn "ignore duplicated $script_url\n" if $debug >= 2;
            next;
        }
        $unique{$script_url} = 1;

        push @area, $obj;
    }

    return reverse sort { $a->{"time"} <=> $b->{"time"} } @area;
}

sub footer {
    my %args = @_;
    my $date = $args{'date'};

    my $extract_homepage = $option->{'extract_homepage'};
    return <<EOF;

<p align="center"><a href="$extract_homepage/community.html"><img src="/images/btn_donateCC_LG.gif" alt="donate" /></a></p>

<div id="bottom">
<p>
@{[ M("Last update") ]}: $date
</p>

<div id="footer">
<div id="footer_top">
<a href="@{[ $option->{'download_homepage'} ]}">home</a> |
<a href="$extract_homepage/extract.html">@{[ M("help") ]}</a> |
<a href="$extract_homepage/garmin.html">@{[ M("garmin") ]}</a> |
<a href="$extract_homepage/community.html">@{[ M("donate") ]}</a> |
<a href="$extract_homepage/support.html">commercial support</a>
<hr/>
</div> <!-- footer_top -->

<div id="copyright">
(&copy;) 2008-2025 <a href="https://www.bbbike.org">BBBike.org</a> // Map data (&copy;) <a href="https://www.openstreetmap.org/copyright" title="OpenStreetMap License">OpenStreetMap.org</a> contributors
</div> <!-- copyright -->

</div> <!-- footer -->

</div> <!-- bottom -->
</div> <!-- nomap -->
EOF
}

sub load_javascript_libs {
    my @js = qw(
      jquery/jquery-1.8.3.min.js
      OpenLayers/2.12/OpenLayers-min.js
      OpenLayers/2.12/OpenStreetMap.js
      extract-download.js
    );

    my $javascript = join "\n",
      map { qq{<script src="/html/$_" type="text/javascript"></script>} } @js;

    my $dom_ready = <<'EOF';

<script type="text/javascript">
$(document).ready(function () {
    download_init_map();

    // non-blocking delay
    setTimeout(function() { parse_areas_from_links(); }, 10);

    if (_auto_refresh_start) {
        auto_refresh();
    }
});
</script>
EOF

    return $javascript . $dom_ready;
}

sub css_map {
    return <<EOF;
EOF
}

# osm.pbf -> format_osm_pbf
sub class_format {
    my $format = shift;

    $format =~ s/[\.\-]/_/g;

    return "format_" . $format;
}

sub statistic {
    my %args = @_;

    my $files     = $args{'files'};
    my $summary   = $args{'summary'};
    my @downloads = @$files;

    print qq{<h3>@{[ M("Statistic") ]}</h3>\n\n};

    if ( !@downloads ) {
        print qq{<p>@{[ M("none") ]}</p>\n};
        print "<hr/>\n\n";
        return;
    }

    print qq{<p>@{[ M("Number of extracts") ]}: }
      . scalar(@downloads)
      . qq{</p>\n};

    sub strip_format {
        my $f = shift;
        $f =~ s/\-.*//;
        $f =~ s/\..*//;

        # osmium
        $f =~ s/geojsonseq/geojson/;
        $f =~ s/sqlite/sql/;
        return $f;
    }

    my %format_counter;
    my %format_counter_all;
    foreach my $download (@downloads) {
        $format_counter{ $download->{"format"} } += 1;
        $format_counter_all{ strip_format( $download->{"format"} ) } += 1;
    }

    foreach my $f (
        reverse sort { $format_counter{$a} <=> $format_counter{$b} }
        keys %format_counter
      )
    {
        print qq{<span class="}
          . class_format($f)
          . qq{" title="}
          . sprintf( "%2.2f", $format_counter{$f} * 100 / scalar(@downloads) )
          . qq{%">};
        print $formats->{$f} . " (" . $format_counter{$f} . ")";
        print "</span><br/>\n";
    }
    print "<hr/>\n\n";

    return if !$summary;
    foreach my $f (
        reverse sort { $format_counter_all{$a} <=> $format_counter_all{$b} }
        keys %format_counter_all
      )
    {
        # filter results by format
        my $q = new CGI;
        $q->param( "format", $f );
        my $url = $q->url( -query => 1, -relative => 1 );

        print qq{<span title="} . $format_counter_all{$f} . qq{">};
        printf( "<a href='%s'>%s</a> (%2.2f%%)",
            $url, $f, $format_counter_all{$f} * 100 / scalar(@downloads) );
        print "</span><br/>\n";
    }
    print "<hr/>\n\n";
}

sub result {
    my %args = @_;

    my $type     = $args{'type'};
    my $name     = $args{'name'};
    my $files    = $args{'files'};
    my $message  = $args{'message'};
    my $callback = $args{'callback'};

    my @downloads = @$files;

    my $sub_title = "";
    if ( !@downloads ) {
        warn "Nothing todo for $type\n" if $debug >= 2;
        $sub_title = ": " . M("none");
    }
    elsif ($message) {
        $sub_title = ": " . M($message);
    }

    print qq{<h4 title="}
      . scalar(@downloads)
      . qq{ extracts">@{[ M($name) ]}$sub_title</h4>\n\n};

    if ( defined $callback ) {
        &$callback;
        print "<hr/>\n";
    }

    # no waiting or running extracts - done
    return if !@downloads;

    print qq{<table id="$type">\n};
    print qq{<thead>\n<tr>\n};

    table_head( $type, 'name',   M("Name of area") );
    table_head( $type, 'format', M("Format") );
    table_head( $type, 'size',   M("Size") );

    print qq{<th>Link</th>\n<th>@{[ M("Map") ]}</th>\n} . qq{</tr>\n</thead>\n};
    print qq{<tbody>\n};

    foreach my $download (@downloads) {
        print "<tr>\n";

        my $date = time2str( $download->{"extract_time"} );
        my $city = $download->{"city"};

        # name of area
        print "<td>";
        print qq{<span title="}
          . escapeHTML($city) . qq{">}
          . escapeHTML( substr( $city, 0, $option->{"max_city_length"} ) )
          . qq{</span>};
        print "</td>\n";

        # Format
        print "<td>";
        print qq{<span class="}
          . class_format( $download->{"format"} ) . qq{">};
        print escapeHTML( $formats->{ $download->{"format"} } );
        print "</span>";
        print "</td>\n";

        # size (in MB)
        print "<td>";
        if ( $download->{"extract_size"} ) {
            print kb_to_mb( $download->{"extract_size"} ) . " MB";
        }
        else {
            print "-";
        }
        print "</td>\n";

        # download link if available
        print "<td>";
        if ( $download->{"download_file"} ) {
            my $prefix =
                $option->{'pro'}
              ? $option->{"download_pro"}
              : $option->{"download"};

            print qq{<a title="$date" href="$prefix}
              . escapeHTML( $download->{"download_file"} )
              . qq{">download</a>};
        }
        else {
            print "-";
        }
        print "</td>\n";

        print "<td>";
        my @coords = @{ $download->{"coords"} };

        # protocol independent links
        my $script_url = $download->{"script_url"};
        my $uri        = URI->new($script_url);
        $uri->query_param( "ref", "download" );
        $script_url = $uri->as_string;
        $script_url =~ s,^https?:,,;

        print qq{<a class="polygon}
          . ( scalar(@coords) ? 1 : 0 )
          . qq{" title="}
          . ( scalar(@coords) ? "polygon" : "rectangle" )
          . qq{" href="}
          . escapeHTML($script_url)
          . qq{">map</a>};
        print "</td>\n";

        print "</tr>\n";
    }
    print "</tbody>\n";
    print "</table>\n";
    print "<hr/>\n\n";
}

sub result_json {
    my %args = @_;

    my $files = $args{'files'};
    my $appid = $args{'appid'} // "";

    my @downloads = @$files;

    # no waiting or running extracts - done
    return if !@downloads;

    my @data;
    my $homepage = $option->{download_homepage};
    $homepage =~ s,/osm/$,,;

    foreach my $download (@downloads) {
        my $obj = {
            "time" => $download->{"extract_time"},
            "size" => $download->{"extract_size"},
            "name" => $download->{"city"},
        };

        # download link if available
        if ( $download->{"download_file"} ) {
            my $prefix =
                $option->{'pro'}
              ? $option->{"download_pro"}
              : $option->{"download"};

            $obj->{"url"} = $homepage . $prefix . $download->{"download_file"};
        }

        # ignore all which are not matching the appid
        if ( $appid ne "" ) {
            if ( $download->{"appid"} ne $appid ) {
                next;
            }
        }

        push @data, $obj;
    }
    return \@data;
}

sub uniqe_users {
    my @extracts_trash = @_;

    my %hash;
    foreach my $download (@extracts_trash) {
        $hash{ $download->{"email"} } += 1;
    }

    return scalar( keys %hash );
}

# sort table by name, size, format
sub table_head {
    my ( $type, $sort_by, $name ) = @_;

    my $q = new CGI;

    print "<th>";

    my $sort_by_param = $q->param("sort_by") || "";
    if ( $type eq 'download' && $sort_by ne $sort_by_param ) {
        $q->param( "sort_by", $sort_by );
        print $q->a(
            {
                href  => $q->url( -query => 1, -relative => 1 ),
                title => "Sort by $name"
            },
            $name
        );
    }
    else {
        print $name;
    }

    print "</th>";
}

sub download_header {
    my $q = shift;

    print $q->header( -charset => 'UTF-8', -expires => '+0s' );

    print $q->start_html(
        -title => 'BBBike extracts ready to download',
        -head  => [
            $q->meta(
                {
                    -http_equiv => 'Content-Type',
                    -content    => 'text/html; charset=UTF-8'
                }
            ),
            $q->meta( { -name => "robots", -content => "nofollow,noarchive" } ),
            $q->Link(
                { -rel => "shortcut icon", -href => "/images/srtbike16.gif" }
            )
        ],

        -style => {
            'src' => ["/html/extract-download.css"],
            -code => &css_map
        },

        #-script => [
        #    { 'src' => "/html/bbbike.js" },
        #    { 'src' => "/html/jquery/jquery-1.8.3.min.js " }
        #],
    );

# print qq{<noscript><p>}, qq{You must enable JavaScript and CSS to run this application!}, qq{</p>\n</noscript>\n};
    print qq{<div id="all">\n};
}

sub filter_date {
    my %args = @_;

    my $filter_date    = $args{'filter_date'};
    my $current_filter = $args{'date'};

    sub display_filter {
        my $filter = shift;
        return $filter =~ /^d+/ ? $filter : M($filter);
    }

    my $q    = new CGI;
    my $data = "";

    foreach my $filter (@$filter_date) {
        $q->param( "date", $filter );
        $data .= " |\n" if $data;
        $data .=
            $filter eq $current_filter
          ? &display_filter($filter)
          : $q->a( { href => $q->url( -query => 1, -relative => 1 ) },
            &display_filter($filter) );
    }

    print M("Limit to date") . ": $data\n\n";
}

###########################################################################
#
sub download_json {
    my $q   = shift;
    my $max = $max_extracts;

    my @filter_date = qw/1h 3h 6h 12h 24h 36h 48h 72h all/;
    print $q->header(
        -charset => 'UTF-8',
        -expires => '+0s',
        -type    => 'application/json',
    );

    if ( $q->param('max') ) {
        my $m = $q->param('max');
        $max = $m if $m > 0 && $m <= 5_000;
    }

    my $date = $q->param('date') || $default_date_json;
    if ( $date ne "" && !grep { $date eq $_ } @filter_date ) {
        warn "Reset date: '$date'\n" if $debug;
        $date = "";
    }

    my $current_date     = time2str(time);
    my $extract_homepage = $option->{'extract_homepage'};

    my @extracts = ();

    my $sort_by        = $q->param('sort_by') || $q->param("sort");
    my @extracts_trash = &extract_areas(
        'log_dir'       => "$spool_dir/" . $spool->{"trash"},
        'max'           => $max,
        'sort_by'       => $sort_by,
        'filter_format' => $filter_format,
        'date'          => $date
    );

    #@extracts = &running_extract_areas(
    #    'log_dir'       => "$spool_dir/" . $spool->{"confirmed"},
    #    'filter_format' => $filter_format,
    #    'max'           => $max
    #);
    #
    #result(
    #    'type'    => 'confirmed',
    #    'files'   => \@extracts,
    #    'name'    => 'Waiting extracts',
    #    'message' => 'Will start in the next 1-5 minutes',
    #);
    #
    #@extracts = &running_extract_areas(
    #    'log_dir'       => "$spool_dir/" . $spool->{"running"},
    #    'filter_format' => $filter_format,
    #    'max'           => $max
    #);
    #
    #result(
    #    'type'    => 'running',
    #    'files'   => \@extracts,
    #    'name'    => 'Running extracts',
    #    'message' => 'Will be ready in the next 2-7 minutes',
    #);

    @extracts = @extracts_trash;
    my $appid      = $q->param('appid') // "";
    my $trash_perl = result_json(
        'appid' => $appid,
        'files' => \@extracts
    );
    my $perl = {
        "copyright" =>
          "Copyright (c) 2025 Wolfram Schneider, https://extract.bbbike.org",
        "ready" => $trash_perl
    };

    print JSON->new->pretty(1)->canonical->encode($perl);
}

sub current_user {
    my $q = shift;

    # limit to current user
    my $email = $q->cookie('email') // "";
    $email .= '@bbbike.org' if $email eq 'nobody';

    return $email;
}

sub download_html {
    my $q      = shift;
    my $locale = Extract::Locale->new( 'q' => $q );
    my $max    = $max_extracts;

    download_header($q);
    my @filter_date = qw/1h 3h 6h 12h 24h 36h 48h 72h all/;

    if ( $q->param('max') ) {
        my $m = $q->param('max');
        $max = $m if $m > 0 && $m <= 5_000;
    }

    my $date = $q->param('date') || $default_date;
    if ( $date ne "" && !grep { $date eq $_ } @filter_date ) {
        warn "Reset date: '$date'\n" if $debug;
        $date = "";
    }

    print qq{<div id="map_area">\n};
    print $q->h2( qq{<a href="}
          . $q->url( -relative => 1 )
          . qq{">OpenStreetMap extracts ready to download</a>} )
      if $option->{'show_heading'};

    print <<EOF;
<span id="noscript"><noscript>Please enable JavaScript in your browser. Thanks!</noscript></span>
<div id="map" style="height:480px"></div> <!-- map -->
<div id="map_after">
<span id="debug"></span>

EOF
    my $fullscreen =
      qq{ | <a href="#" onclick="toggle_fullscreen()">fullscreen</a>\n};

    print $locale->language_links(
        'with_separator' => 1,
        'postfix'        => $fullscreen
    );

    my $current_date     = time2str(time);
    my $extract_homepage = $option->{'extract_homepage'};

    my @extracts = ();

    my $sort_by = $q->param('sort_by') || $q->param("sort");
    my $email   = &current_user($q);
    my $me      = $q->param("me") || 0;

    my @extracts_trash = &extract_areas(
        'log_dir'       => "$spool_dir/" . $spool->{"trash"},
        'max'           => $max,
        'sort_by'       => $sort_by,
        'filter_format' => $filter_format,
        'email'         => $me ? $email : "",
        'date'          => $date
    );

    my ( $count, $max_count, $time ) = &activate_auto_refresh($q);

    print <<EOF;

<table id="donate">
<tr>
<td>
 <span title='@{[ M("Number of extracts") . ': ' .  scalar(@extracts_trash) ]}, @{[ M("uniqe users") . ': ' . &uniqe_users(@extracts_trash) ]}'>
   @{[ M("Newest extracts are first") ]}
 </span>
 -
 <span>@{[ M("Last update") ]}: $current_date</span>
EOF

    if ($email) {
        my $qq = new CGI($q);
        if ( !$me ) {
            $qq->param( "me", "1" );
            my $url = $qq->url( -query => 1, -absolute => 1 );
            print qq|<a href="$url">|, M("only my extracts"), qq|</a>|;
        }
        else {
            $qq->delete("me");
            my $url = $qq->url( -query => 1, -absolute => 1 );
            print qq|<a href="$url">|, M("all extracts"), qq|</a>|;
        }
        print " - \n";
    }

    if ( $option->{'auto_refresh'}->{'enabled'} ) {
        print <<EOF;
<a title="enable/disable auto refresh every $time seconds" onclick="javascript:auto_refresh($count);"
style="display: inline;"> 
@{[ $count == 0 || $count >= $max_count ? M("enable auto refresh") : M("disable auto refresh") ]}</a>
EOF
    }

    print <<EOF;
</td>
<td><a href="$extract_homepage/community.html"><img src="/images/btn_donateCC_LG.gif" alt="donate" /></a></td>
</tr>
</table>

EOF

    print <<EOF;
<p>
</p>

</div> <!-- map_after -->
</div> <!-- map_area -->
<div id="nomap">
EOF

    @extracts = &running_extract_areas(
        'log_dir'       => "$spool_dir/" . $spool->{"confirmed"},
        'filter_format' => $filter_format,
        'email'         => $me ? $email : "",
        'max'           => $max
    );

    result(
        'type'    => 'confirmed',
        'files'   => \@extracts,
        'name'    => 'Waiting extracts',
        'message' => 'Will start in the next 1-5 minutes',
    );

    @extracts = &running_extract_areas(
        'log_dir'       => "$spool_dir/" . $spool->{"running"},
        'filter_format' => $filter_format,
        'email'         => $me ? $email : "",
        'max'           => $max
    );

    result(
        'type'    => 'running',
        'files'   => \@extracts,
        'name'    => 'Running extracts',
        'message' => 'Will be ready in the next 2-7 minutes',
    );

    @extracts = @extracts_trash;
    result(
        'callback' => sub {
            filter_date( 'filter_date' => \@filter_date, 'date' => $date );
        },
        'type'  => 'download',
        'name'  => 'Ready extracts',
        'files' => \@extracts
    );

    filter_date( 'filter_date' => \@filter_date, 'date' => $date );
    statistic( 'files' => \@extracts, 'summary' => 1 );

    print &footer( 'date' => $current_date );

    #print qq{    </div> <!-- main -->\n};
    #print qq{  </div> <!-- border -->\n};
    print qq{</div> <!-- all -->\n};

    # load javascript code late
    print &load_javascript_libs;
    print $option->{"enable_google_analytics"}
      ? BBBike::Analytics->new( 'q' => $q )->google_analytics
      : "";

    print $q->end_html;
}

sub activate_auto_refresh {
    my $q = shift;

    my $max  = $option->{'auto_refresh'}->{'max'};
    my $time = $option->{'auto_refresh'}->{'delay_seconds'};

    my $count = $q->param("count") || 0;
    $count = int($count);
    if ( $count >= $max ) {
        $count = 0;
    }

    my $qq = CGI->new($q);
    $qq->param( "count", $count + 1 );

    my $url  = $qq->url( -query => 1, -path => 1 );
    my $url2 = $q->url( -query => 0, -path => 1 );

    print <<EOF;
<script type="text/javascript">
function auto_refresh (flag) {
    if (flag) {
        clearTimeout(auto_refresh_timer)
        _auto_refresh (0, $max, $time, "$url2");
    } else {
        _auto_refresh ($count, $max, $time, "$url");
    }
}

var _auto_refresh_start = $count;
</script>
EOF
    return ( $count, $max, $time );
}

##############################################################################################
#
# main
#
my $ns = $q->param("ns") // "";
if ( $ns eq 'json' ) {
    &download_json($q);
}
else {
    &download_html($q);
}
