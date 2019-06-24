
  $ cd $TESTDIR/../..

Usage:

  $ ./scripts/framework-applications/notify-successful-suppliers-for-framework.py
  Usage:
      scripts/framework-applications/notify-successful-suppliers-for-framework.py [options]
           [--supplier-id=<id> ... | --supplier-ids-from=<file>]
           <stage> <framework> <notify_api_key> <notify_template_id>
  [1]


Invalid arguments:

  $ ./scripts/framework-applications/notify-successful-suppliers-for-framework.py --do-the-thing garbage
  Usage:
      scripts/framework-applications/notify-successful-suppliers-for-framework.py [options]
           [--supplier-id=<id> ... | --supplier-ids-from=<file>]
           <stage> <framework> <notify_api_key> <notify_template_id>
  [1]

Detailed help:

  $ ./scripts/framework-applications/notify-successful-suppliers-for-framework.py -h
  Email suppliers who have at least one successful lot entry on the given framework.
  
  Uses the Notify API to inform suppliers of success result. This script *should not* resend emails.
  
  Usage:
      scripts/framework-applications/notify-successful-suppliers-for-framework.py [options]
           [--supplier-id=<id> ... | --supplier-ids-from=<file>]
           <stage> <framework> <notify_api_key> <notify_template_id>
  
  Example:
      scripts/framework-applications/notify-successful-suppliers-for-framework.py preview g-cloud-11 api-key template-id
  
  Options:
      <stage>                     Environment to run script against.
      <framework>                 Slug of framework to run script against.
      <notify_api_key>            API key for GOV.UK Notify.
  
      --supplier-id=<id>          ID(s) of supplier(s) to email.
      --supplier-ids-from=<file>  Path to file containing supplier ID(s), one per line.
  
      -n, --dry-run               Run script without sending emails.
  
      -h, --help                  Show this screen.
