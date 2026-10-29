#!/usr/bin/env bash
# Quick check of the day 74 data API (instructor, before class): releases, policy, gates, prompt fault switch.
set -u
B=localhost:8800
show() { echo "\$ $1"; shift; "$@"; echo; }
show "GET /releases/helpdesk" curl -s $B/releases/helpdesk
show "policy on" curl -s -XPOST $B/releases/helpdesk/policy -d '{"require_gate":true}'
show "deploy 1.1.0 without a gate record (409)" curl -s -XPOST $B/releases/helpdesk -d '{"active":"1.1.0"}'
show "gate record 1.1.0 promote" curl -s -XPOST $B/gates/helpdesk -d '{"release":"1.1.0","verdict":"promote","passed":6,"total":6,"source":"check"}'
show "deploy 1.1.0 again (200)" curl -s -XPOST $B/releases/helpdesk -d '{"active":"1.1.0"}'
show "fault prompts error" curl -s -XPOST $B/admin/fault -d '{"prompts":"error"}'
show "GET /prompts/helpdesk/p1 (500)" curl -s $B/prompts/helpdesk/p1
show "fault prompts ok" curl -s -XPOST $B/admin/fault -d '{"prompts":"ok"}'
show "GET /prompts/helpdesk/p9 (404)" curl -s $B/prompts/helpdesk/p9
show "reset" curl -s -XPOST $B/releases/helpdesk/reset
show "gates clear" curl -s -XPOST $B/gates/helpdesk/clear
show "GET /audit (day 73 endpoint still there)" curl -s $B/audit
