/*
This script is to fix the results of accidentally publishing some draft services for some suppliers who were not
awarded `on_framework` for G10. The issue was with the publishing script, and the fix to prevent this happening again is
here: https://github.com/alphagov/digitalmarketplace-scripts/pull/256

To apply this script run the below command
Targe the correct environment with `cf target -s <desired environment>`
`cf conduit digitalmarketplace_api_db -- psql < ./scripts/oneoff/fix_accidentially_published_g10_services.sql`
*/

START transaction;
SELECT
   services.service_id,
   ds.id AS draft_id INTO TEMP TABLE naughty_services
FROM
   services
   LEFT JOIN
      draft_services AS ds
      ON services.service_id = ds.service_id
   LEFT JOIN
      supplier_frameworks AS sf
      ON services.supplier_id = sf.supplier_id
WHERE
   services.framework_id = (SELECT id FROM frameworks WHERE slug = 'g-cloud-10')
   AND sf.on_framework = 'f'
   AND sf.framework_id = (SELECT id FROM frameworks WHERE slug = 'g-cloud-10')
;

UPDATE
   draft_services
SET
   service_id = NULL
WHERE
   id IN (SELECT draft_id FROM naughty_services)
;

DELETE
FROM
   archived_services
WHERE
   service_id IN (SELECT service_id FROM naughty_services)
;

DELETE
FROM
   services
WHERE
   service_id IN (SELECT service_id FROM naughty_services)
;

INSERT INTO
   audit_events (type, created_at, "user", data, object_type, object_id, acknowledged, acknowledged_by, acknowledged_at) (
   SELECT
      'update_service',
      now(),
      'DM Developers',
      '{"what": "Deleted service and archived service with ./scripts/oneoff/fix_accidentially_published_g10_services.sql", "reason": "Draft services accidentally published for suppliers not on framework"}'::json,
      'Service',
      service_id::BIGINT,
      't',
      'DM Developers',
      now()
   FROM
      naughty_services)
;

INSERT INTO
   audit_events (type, created_at, "user", data, object_type, object_id, acknowledged, acknowledged_by, acknowledged_at) (
   SELECT
      'update_draft_service',
      now(),
      'DM Developers',
      '{"what": "Removed service_id from draft_service with ./scripts/oneoff/fix_accidentially_published_g10_services.sql", "reason": "Draft services accidentally published for suppliers not on framework"}'::json,
      'DraftService',
      draft_id::BIGINT,
      't',
      'DM Developers',
      now()
   FROM
      naughty_services)
;

DROP TABLE naughty_services;

COMMIT;
