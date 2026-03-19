# Shell absorption (v0.8 Open WebUI pass)

Place Open WebUI–derived layout, sidebar, upload, and transcript components under this tree (or colocated `components/shell/`).

Constraints:

- All data flows through existing `api.js` helpers and bearer auth.
- Do not embed Open WebUI backend routes or duplicate file/run models.
