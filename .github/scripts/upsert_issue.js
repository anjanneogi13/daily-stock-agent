/**
 * Bug #19 (2026-05-05): Upsert workflow report issues instead of duplicating.
 *
 * GitHub Actions report workflows can re-run. Creating a new issue on every
 * run floods the repo with duplicate Daily Picks / Performance / Execution
 * Report issues. This helper makes report delivery idempotent:
 *   - exact-match open issue title
 *   - update body/labels/assignees if found
 *   - create if absent
 */
async function upsertIssue({ github, context, core = console, title, body, labels = [], assignees = [] }) {
  const { owner, repo } = context.repo;

  const issues = await github.paginate(github.rest.issues.listForRepo, {
    owner,
    repo,
    state: 'open',
    per_page: 100,
    labels: labels.length ? labels.join(',') : undefined,
  });

  const existing = issues.find((i) => i.title === title && !i.pull_request);

  if (existing) {
    await github.rest.issues.update({
      owner,
      repo,
      issue_number: existing.number,
      title,
      body,
      labels,
      assignees,
    });
    core.info(`Updated existing issue #${existing.number}: ${title}`);
    return { action: 'updated', number: existing.number, url: existing.html_url };
  }

  const created = await github.rest.issues.create({
    owner,
    repo,
    title,
    body,
    labels,
    assignees,
  });
  core.info(`Created issue #${created.data.number}: ${title}`);
  return { action: 'created', number: created.data.number, url: created.data.html_url };
}

module.exports = { upsertIssue };
