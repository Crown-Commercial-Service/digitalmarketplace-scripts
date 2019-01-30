# Test scripts/generate-framework-agreement-signature-pages.py

`generate-framework-agreement-signature-pages.py` requires suppliers with a
framework interest and at least one completed draft service. Additionally, to
be able to generate a signature page certain parts of the framework declaration
must be present.

These tests pass against the latest database dump, `cleaned-production-201901270300.sql.gz`.

Alternatively, please ensure the following data is present in your database:

Table "supplier_frameworks"

| supplier_id | framework_id | on_framework | declaration            |
|-------------|--------------|--------------|------------------------|
|      710024 | 9            | true         | {"status": "complete"} |
|      710026 | 9            | false        | {"status": "complete"} |
|      710028 | 9            | true         | {"status": "complete"} |
|      710029 | 9            | true         | {"status": "complete"} |
|      710038 | 9            | true         | {"status": "complete"} |
|      710056 | 9            | true         | {"status": "complete"} |

Table "draft_services"

| id     | supplier_id | framework_id | lot_id | status        |
|--------|-------------|--------------|--------|---------------|
|  98120 |      710024 |            9 |     11 | submitted     |
|  98491 |      710028 |            9 |     10 | submitted     |
|  99662 |      710038 |            9 |     11 | submitted     |
|  99941 |      710029 |            9 |     10 | submitted     |
| 101516 |      710056 |            9 |     11 | submitted     |
| 101783 |      710038 |            9 |     11 | submitted     |
| 101834 |      710038 |            9 |     11 | submitted     |
| 101886 |      710038 |            9 |     11 | submitted     |
| 101920 |      710038 |            9 |     11 | submitted     |
| 101939 |      710038 |            9 |     11 | submitted     |
| 102411 |      710056 |            9 |     11 | not-submitted |