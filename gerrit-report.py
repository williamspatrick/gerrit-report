#!/bin/env python3

import argparse
import subprocess
import json

option_age = ""
option_owner = None

query_cache = {}

def query(*args):
    s = subprocess.getoutput("ssh openbmc.gerrit gerrit query " +
                             "--format json --all-reviewers " +
                             "--dependencies --current-patch-set -- '" +
                             " ".join(args) + "'")
    results = list(map(json.loads, s.splitlines()))
    del results[-1]

    for r in results:
        query_cache[r['id']] = r

    return results

def changes():
    args= "age:{}".format(option_age)
    if option_owner:
        args += " ( {} )".format(option_owner)
    return query(args,
                 "status:open", "-is:draft", "-label:Code-Review=-2",
                 "-project:openbmc/openbmc-test-automation")

def change_by_id(change_id):
    if change_id in query_cache:
        return query_cache[change_id]
    c = query(change_id)
    if len(c):
        return c[0]
    return None

username_map = {
    'adamliyi': "@shyili",
    'amboar': "@arj",
    'anoo1': "@anoo",
    'bradbishop': "@bradleyb",
    'chinaridinesh': "@chinari",
    'dhruvibm': "@dhruvaraj",
    'dkodihal': "@dkodihal",
    'geissonator': "@andrewg",
    'gtmills': "@gmills",
    'jenkins-openbmc': "Jenkins",
    'JoshDKing': "@jdking",
    'mine260309': "@shyulei",
    'msbarth': "@msbarth",
    'mtritz': "@mtritz",
    'ojayanth': "@ojayanth",
    'ratagupt': "@ratagupt",
    'saqibkh': "@khansa",
    'shenki': "@jms",
    'spinler': "@spinler",
    'tomjoseph83': "@tomjoseph",
    'vishwabmc': "@vishwanath",
    'williamspatrick': "@iawillia",
}

def map_username(user, name):
    return username_map.get(user, "[{}: {}]".format(user, name))

def map_approvals(approvals):
    mapped = {}
    for a in approvals:
        approval_type = a['type']
        approval_owner = map_username(a['by']['username'], a['by']['name'])
        approval_score = int(a['value'])

        if approval_type not in mapped:
            mapped[approval_type] = {}

        mapped[approval_type][approval_owner] = approval_score

    return mapped

def map_reviewers(reviewers, owner):
    mapped = []
    for r in reviewers:
        reviewer_user = r['username']
        reviewer_name = r['name']

        if reviewer_user == 'jenkins-openbmc':
            continue

        reviewer_username = map_username(r['username'], r['name'])

        if reviewer_username == owner:
            continue

        mapped.append(reviewer_username)

    return mapped


def reason(change):
    subject = change['subject']
    owner = map_username(change['owner']['username'], change['owner']['name'])
    if 'allReviewers' in change:
        reviewers = map_reviewers(change['allReviewers'], owner)
    else:
        reviewers = []
    if 'approvals' in change['currentPatchSet']:
        approvals = map_approvals(change['currentPatchSet']['approvals'])
    else:
        approvals = {}

    if len(reviewers) < 2:
        return "{0} has added insufficient reviewers.".format(owner)

    if ('Verified' in approvals):
        verified = approvals['Verified']
        scores = list(filter(lambda x: verified[x] < 0, verified))
        if len(scores):
            return "{0} should resolve verification failure.".format(owner)

    if ('Code-Review' not in approvals):
        return "Missing code review by {0}.".format(", ".join(reviewers))

    reviewed = approvals['Code-Review']
    rejected_by = list(filter(lambda x: reviewed[x] < 0, reviewed))
    if len(rejected_by):
        return "{0} should resolve code review comments.".format(owner)

    reviewed_by = list(filter(lambda x: reviewed[x] > 0, reviewed))
    if len(reviewed_by) < 2:
        return "Missing code review by {0}.".\
               format(", ".join(set(reviewers) - set(reviewed_by)))

    if ('Verified' not in approvals):
        return "May be missing Jenkins verification ({0}).".format(owner)

    if ('dependsOn' in change) and (len(change['dependsOn'])):
        for dep in change['dependsOn']:
            if not dep['isCurrentPatchSet']:
                return "Depends on out of date patch set {1} ({0}).".\
                       format(owner, dep['id'])
            dep_info = change_by_id(dep['id'])
            if not dep_info:
                continue
            if dep_info['status'] != "MERGED":
                return "Depends on unmerged patch set {1} ({0}).".\
                       format(owner, dep['id'])

    approved_by = list(filter(lambda x: reviewed[x] == 2, reviewed))
    if len(approved_by):
        return "Ready for merge by {0}.".format(", ".join(approved_by))
    else:
        return "Awaiting merge review."

def do_report(args):
    for c in changes():
        print("{} - {}".format(c['url'], c['id']))
        print(c['subject'])
        print(reason(c))
        print("----")

parser = argparse.ArgumentParser()
parser.add_argument('--age', help='Change age since last modified', type=str,
                    default="1d")
parser.add_argument('--owner', help='Change owner', type=str,
                    action='append')
subparsers = parser.add_subparsers()

report = subparsers.add_parser('report', help='Generate report')
report.set_defaults(func=do_report)

args = parser.parse_args()

if 'age' in args:
    option_age = args.age;
if ('owner' in args) and args.owner:
    option_owner = " OR ".join(map(lambda x: "owner:" + x,
                                   args.owner));

if 'func' in args:
    args.func(args)
else:
    parser.print_help()
