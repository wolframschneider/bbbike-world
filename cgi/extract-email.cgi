#!/usr/local/bin/perl -T
# Copyright (c) 2011-2013 Wolfram Schneider, https://bbbike.org
#
# extract-email.cgi - email REST wrapper
#

use CGI qw/-utf8 unescape escapeHTML/;
use CGI::Carp;
use IO::File;
use JSON;
use Data::Dumper;
use Encode qw/encode_utf8/;
use Email::Valid;
use Digest::MD5 qw(md5_hex);
use Net::SMTP;
use HTTP::Date;

use strict;
use warnings;

# group writable file
umask(002);

binmode \*STDOUT, ":utf8";
binmode \*STDERR, ":utf8";
$ENV{PATH} = "/bin:/usr/bin";

our $option = {
    'script_homepage' => 'https://extract.bbbike.org',
    'request_method'  => 'POST',
    'debug'           => 1,
    'bcc'             => 'bbbike@bbbike.org',
    'bcc_rest'        => 'bbbike@bbbike.org',
    'email_from'      => 'bbbike@bbbike.org',
};

###
# global variables
#
my $language       = $option->{'language'};
my $extract_dialog = '/extract-dialog';

#
# Parse user config file.
# This allows to override standard config values
#
my $config_file = "../.bbbike-extract.rc";
if ( CGI->new->url( -full => 1 ) =~ m,^https?://extract[1-9]?-pro[1-9]?\., ) {
    $config_file = '../.bbbike-extract-pro.rc';
    warn "Use extract pro config file $config_file\n"
      if $option->{"debug"} >= 2;
}

if ( -e $config_file ) {
    warn "Load config file: $config_file\n" if $option->{"debug"} >= 2;
    require $config_file;
}
else {
    warn "config file: $config_file not found, ignored\n"
      if $option->{"debug"} >= 2;
}

######################################################################
# global functions
#
my $request_method = $option->{request_method};  # use "GET" or "POST" for forms
my $debug          = $option->{'debug'};
my $q;

######################################################################
# helper functions
#

sub check_input {
    my %args = @_;

    our $error         = 0;
    our $error_message = "";

    sub error {
        my $text      = shift;
        my $no_escape = shift;

        $error++;
        warn "Error: $text\n";
        $error_message .= "$text;";
    }

    my $obj = {};

    my $to      = $q->param("to")      || "";
    my $subject = $q->param("subject") || "";
    my $message = $q->param("message") || "";
    my $token   = $q->param("token")   || "";
    my $bcc = $option->{"bcc_rest"} || $option->{"bcc"} || "";

    error("no to: to given")  if $to eq "";
    error("no subject given") if $subject eq "";
    error("no message given") if $message eq "";
    error("no token given")   if $token eq "";

    error("wrong token '$token' given") if $token ne $option->{'email_token'};
    error( "wrong request method given: " . $q->request_method() )
      if $option->{'request_method'} ne $q->request_method();

    $obj = {
        "error"         => $error,
        "to"            => $to,
        "subject"       => $subject,
        "message"       => $message,
        "error_message" => $error_message,
        "bcc"           => $bcc,
    };

    return $obj;
}

sub sent_email_rest {
    my %args = @_;

    my $obj = &check_input( 'q' => $q );
    if ( $obj->{'error'} ) {
        return fatal_error( $obj->{'error_message'} );
    }

    eval {
        send_email(
            $obj->{'to'},      $obj->{'subject'},
            $obj->{'message'}, $obj->{'bcc'}
        );
    };

    if ($@) {
        return fatal_error("sent email: $@");
    }

    out_message( -error => 0, -message => 'ok' );
}

sub fatal_error {
    my $message = shift;

    warn "fatal: $message\n";
    out_message( -error => 1, -message => $message, -q => $q );
}

sub out_message {
    my %args    = @_;
    my $message = $args{-message};
    my $error   = $args{-error};

    $error = 0 if !defined $error || $error <= 0;

    print $q->header(
        -charset      => 'utf-8',
        -content_type => 'application/json'
    );

    my $json_text =
      encode_json( { "status" => $error, 'message' => $message } );
    print "$json_text\n\n";
}

# SMTP wrapper
sub send_email {
    my ( $to, $subject, $message, $bcc ) = @_;
    my $mail_server = "localhost";
    my @to = split /,/, $to;

    my $from         = $option->{'email_from'};
    my @bcc          = split /,/, $bcc;
    my $content_type = "Content-Type: text/plain; charset=UTF-8\n"
      . "Content-Transfer-Encoding: binary";

    my $data =
      "From: $from\nTo: $to\nSubject: $subject\n" . "$content_type\n\n$message";
    warn "send email to $to\nbcc: $bcc\n$subject\n" if $debug >= 1;
    warn "$message\n"                               if $debug >= 2;

    my $smtp = new Net::SMTP( $mail_server, Hello => "localhost" )
      or die "can't make SMTP object";

    $smtp->mail($from) or die "can't send email from $from";
    $smtp->to(@to)     or die "can't use SMTP recipient '$to'";
    if ($bcc) {
        $smtp->bcc(@bcc) or die "can't use SMTP recipient '$bcc'";
    }
    $smtp->data($data) or die "can't email data to '$to'";
    $smtp->quit() or die "can't send email to '$to'";

    warn "\n$data\n" if $debug >= 3;
}

######################################################################
# main
$q = new CGI;
&sent_email_rest();

1;
