
  $ cd $TESTDIR/../..

Usage:

  $ ./scripts/notify-suppliers-whether-application-made-for-framework.py
  Usage:
      scripts/notify-suppliers-whether-application-made-for-framework.py [options]
           [--supplier-id=<id> ... | --supplier-ids-from=<file>]
           <stage> <framework> <notify_api_key>
  [1]


Invalid arguments:

  $ ./scripts/notify-suppliers-whether-application-made-for-framework.py --do-the-thing garbage
  Usage:
      scripts/notify-suppliers-whether-application-made-for-framework.py [options]
           [--supplier-id=<id> ... | --supplier-ids-from=<file>]
           <stage> <framework> <notify_api_key>
  [1]

Detailed help:

  $ ./scripts/notify-suppliers-whether-application-made-for-framework.py -h
  Email all suppliers who registered interest in applying to a framework about whether or not they made an application.
  
  Uses the Notify API to send emails. This script *should not* resend emails.
  
  Usage:
      scripts/notify-suppliers-whether-application-made-for-framework.py [options]
           [--supplier-id=<id> ... | --supplier-ids-from=<file>]
           <stage> <framework> <notify_api_key>
  
  Example:
      scripts/notify-suppliers-whether-application-made-for-framework.py --dry-run preview g-cloud-9 my-awesome-key
  
  Options:
      <stage>                     Environment to run script against.
      <framework>                 Slug of framework to run script against.
      <notify_api_key>            API key for GOV.UK Notify.
  
      --supplier-id=<id>          ID(s) of supplier(s) to email.
      --supplier-ids-from=<file>  Path to file containing supplier ID(s), one per line.
  
      -n, --dry-run               Run script without sending emails.
  
      -h, --help                  Show this screen
