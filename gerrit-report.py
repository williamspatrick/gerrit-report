#!/bin/env python

import subprocess
import json

def changes():
    s = subprocess.getoutput("ssh openbmc.gerrit gerrit query " +
                             "--format json --all-reviewers " +
                             "--current-patch-set -- " +
                             "'age:1d status:open -is:draft " +
                             "label:Code-Review>=-1 " +
                             "-project:openbmc/openbmc-test-automation'")

    changes = list(map(json.loads, s.splitlines()))
    del changes[-1]

    return changes

username_map = {
    'jenkins-openbmc': "Jenkins",
    'williamspatrick': "@iawillia",
    'bradbishop': "@bradleyb"
}

def map_username(user, name):
    return username_map.get(user, "[%s: %s]" % (user, name))

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
    reviewers = map_reviewers(change['allReviewers'], owner)
    approvals = map_approvals(change['currentPatchSet']['approvals'])


#    print("----")
#    print(subject)
#    print(owner)
#    print(approvals)
#    print(reviewers)
#    print("----")

    if len(reviewers) < 2:
        return "%s has added insufficient reviewers." % owner

    if ('Verified' in approvals):
        verified = approvals['Verified']
        scores = list(filter(lambda x: verified[x] < 0, verified))
        if len(scores):
            return "%s should resolve verification failure." % owner

    if ('Code-Review' not in approvals):
        return "Missing code review by %s." % (", ".join(reviewers))

    reviewed = approvals['Code-Review']
    rejected_by = list(filter(lambda x: reviewed[x] < 0, reviewed))
    if len(rejected_by):
        return "%s should resolve code review comments." % owner

    reviewed_by = list(filter(lambda x: reviewed[x] > 0, reviewed))
    if len(reviewed_by) < 2:
        return "Missing code review by %s." % \
               (", ".join(set(reviewers) - set(reviewed_by)))

    if ('Verified' not in approvals):
        return "May be missing Jenkins verification."

    approved_by = list(filter(lambda x: reviewed[x] == 2, reviewed))
    if len(approved_by):
        return "Ready for merge by %s." % (", ".join(approved_by))
    else:
        return "Awaiting merge review."

for c in changes():
    print(c['subject'])
    print(c['url'])
    print(reason(c))
    print("----")

