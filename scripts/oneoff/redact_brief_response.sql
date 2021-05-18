/*
This script is to redact a brief response and also all related audit messages.

This is very dangerous - you should only run it after testing on non-production environments, and with the agreement of
IA.

To apply this script, target the correct environment with `cf target -s <desired environment>`, then run
`cf conduit digitalmarketplace_api_db -- psql --set=id=<brief response ID> < ./scripts/oneoff/redact_brief_response.sql`
*/

UPDATE brief_responses
SET data = data::jsonb
    || '{"respondToEmailAddress": "<REMOVED>"}'::jsonb
    || '{"essentialRequirements": [{"evidence": "<REMOVED>"}, {"evidence": "<REMOVED>"}, {"evidence": "<REMOVED>"}, {"evidence": "<REMOVED>"}, {"evidence": "<REMOVED>"}, {"evidence": "<REMOVED>"}]}'::jsonb
    || '{"niceToHaveRequirements": [{"yesNo": false}, {"yesNo": false}]}'::jsonb
WHERE id=:id;

UPDATE audit_events
SET data = data::jsonb
        || '{"briefResponseData":"<REMOVED>"}'::jsonb
        || ('{"redaction": {"reason": "Security - see Zendesk ticket https://govuk.zendesk.com/agent/tickets/4540337", "timestamp": "' || now() || '"}}')::jsonb
WHERE object_id=:id and object_type='BriefResponse' and type='update_brief_response';

INSERT INTO
   audit_events (type, created_at, "user", data, object_type, object_id, acknowledged, acknowledged_by, acknowledged_at)
VALUES (
  'update_brief_response',
  now(),
  'DM Developers',
  '{"what": "Redacted respondToEmailAddress, essentialRequirements, and niceToHaveRequirements", "reason": "Security - see Zendesk ticket https://govuk.zendesk.com/agent/tickets/4540337"}'::json,
  'BriefResponse',
  :id,
  't',
  'DM Developers',
  now()
);
