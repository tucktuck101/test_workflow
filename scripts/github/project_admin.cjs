const fs = require('fs');

const CONFIG_PATH = '.github/project-admin.json';

function loadConfig() {
  return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
}

function labelNames(item) {
  return (item.labels || []).map((label) =>
    typeof label === 'string' ? label : label.name
  );
}

function hasLabel(item, label) {
  return labelNames(item).some((name) => name.toLowerCase() === label.toLowerCase());
}

function inferType(item, config) {
  const labels = labelNames(item).map((label) => label.toLowerCase());
  for (const type of config.types) {
    if (labels.includes(type.toLowerCase())) return type;
  }
  const title = item.title || '';
  if (/^TASK[-:]/i.test(title)) return 'Task';
  if (/^BUG[-:]/i.test(title)) return 'Bug';
  if (/^FEAT[-:]/i.test(title)) return 'Feature';
  if (/^EPIC[-:]/i.test(title)) return 'Epic';
  if (/^ADR[-:]/i.test(title)) return 'ADR';
  return null;
}

function parseIssueFormSections(body) {
  const sections = {};
  const parts = (body || '').split(/^###\s+/gm);
  for (const part of parts) {
    const lines = part.split('\n');
    const title = (lines.shift() || '').trim();
    if (!title) continue;
    sections[title] = lines.join('\n').trim();
  }
  return sections;
}

function sectionValue(sections, startsWith) {
  const key = Object.keys(sections).find((name) =>
    name.toLowerCase().startsWith(startsWith.toLowerCase())
  );
  if (!key) return '';
  return sections[key].replace(/_No response_/gi, '').trim();
}

function taskIsReady(issue, config) {
  const sections = parseIssueFormSections(issue.body || '');
  return config.taskRequiredSections.every((section) => Boolean(sectionValue(sections, section)));
}

function statusFromIssueBody(issue) {
  const sections = parseIssueFormSections(issue.body || '');
  return sectionValue(sections, 'Status').toLowerCase();
}

function boardColumnForIssue(issue, type, config) {
  if (type === 'Task') {
    if (!taskIsReady(issue, config)) return 'Backlog';
    return 'Ready';
  }
  const status = statusFromIssueBody(issue);
  if (type === 'Bug') {
    if (status === 'in progress') return 'In Progress';
    if (status.startsWith('fixed')) return 'Ready for Human Review';
    if (status === 'done') return 'Done';
    return 'Backlog';
  }
  if (type === 'ADR') {
    if (status === 'accepted') return 'Ready';
    if (['rejected', 'superseded', 'deprecated'].includes(status)) return 'Done';
    return 'Backlog';
  }
  return 'Backlog';
}

function inferComponentFromFiles(files, config) {
  for (const [component, patterns] of Object.entries(config.components)) {
    if (files.some((file) => patterns.some((pattern) => file.startsWith(pattern) || file.includes(pattern)))) {
      return component;
    }
  }
  return null;
}

function inferComponentFromIssue(issue, config) {
  const labels = labelNames(issue).map((label) => label.toLowerCase());
  for (const component of Object.keys(config.components)) {
    if (labels.includes(component.toLowerCase())) return component;
  }
  const text = `${issue.title || ''}\n${issue.body || ''}`.toLowerCase();
  for (const component of Object.keys(config.components)) {
    if (text.includes(component)) return component;
  }
  return null;
}

function linkedIssueNumbers(text) {
  const numbers = new Set();
  const regex = /\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)/gi;
  let match;
  while ((match = regex.exec(text || ''))) {
    numbers.add(Number(match[1]));
  }
  return [...numbers];
}

async function addLabels(github, context, issueNumber, labels) {
  const clean = labels.filter(Boolean);
  if (!clean.length) return;
  await github.rest.issues.addLabels({
    owner: context.repo.owner,
    repo: context.repo.repo,
    issue_number: issueNumber,
    labels: clean,
  });
}

async function removeLabel(github, context, issueNumber, label) {
  try {
    await github.rest.issues.removeLabel({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: issueNumber,
      name: label,
    });
  } catch (error) {
    if (error.status !== 404) throw error;
  }
}

async function getProject(github, context, config, core) {
  const projectNumberRaw = process.env[config.project.numberEnv] || config.project.number;
  if (!projectNumberRaw) {
    core.warning(`Project number not configured. Set repo variable ${config.project.numberEnv}.`);
    return null;
  }
  const owner = process.env.PROJECT_OWNER || config.project.owner || context.repo.owner;
  const number = Number(projectNumberRaw);
  const query = `
    query($login: String!, $number: Int!) {
      user(login: $login) { projectV2(number: $number) { id title } }
      organization(login: $login) { projectV2(number: $number) { id title } }
    }
  `;
  const result = await github.graphql(query, { login: owner, number });
  return result.user?.projectV2 || result.organization?.projectV2 || null;
}

async function getFields(github, projectId) {
  const query = `
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 50) {
            nodes {
              ... on ProjectV2Field {
                id
                name
                dataType
              }
              ... on ProjectV2SingleSelectField {
                id
                name
                dataType
                options { id name }
              }
            }
          }
        }
      }
    }
  `;
  const result = await github.graphql(query, { projectId });
  const fields = {};
  for (const field of result.node.fields.nodes) {
    fields[field.name] = field;
  }
  return fields;
}

async function findProjectItemId(github, projectId, contentId) {
  const query = `
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          items(first: 100) {
            nodes {
              id
              content {
                ... on Issue { id }
                ... on PullRequest { id }
              }
            }
          }
        }
      }
    }
  `;
  const result = await github.graphql(query, { projectId });
  return result.node.items.nodes.find((item) => item.content?.id === contentId)?.id || null;
}

async function ensureProjectItem(github, projectId, contentId) {
  const existing = await findProjectItemId(github, projectId, contentId);
  if (existing) return existing;
  const mutation = `
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: { projectId: $projectId, contentId: $contentId }) {
        item { id }
      }
    }
  `;
  const result = await github.graphql(mutation, { projectId, contentId });
  return result.addProjectV2ItemById.item.id;
}

async function updateField(github, projectId, itemId, fields, fieldName, value, core) {
  if (!value) return;
  const field = fields[fieldName];
  if (!field) {
    core.info(`Project field ${fieldName} not found; skipping.`);
    return;
  }
  if (field.options) {
    const option = field.options.find((candidate) => candidate.name.toLowerCase() === value.toLowerCase());
    if (!option) {
      core.info(`Option ${value} not found for ${fieldName}; skipping.`);
      return;
    }
    const mutation = `
      mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
        updateProjectV2ItemFieldValue(input: {
          projectId: $projectId,
          itemId: $itemId,
          fieldId: $fieldId,
          value: { singleSelectOptionId: $optionId }
        }) { projectV2Item { id } }
      }
    `;
    await github.graphql(mutation, { projectId, itemId, fieldId: field.id, optionId: option.id });
    return;
  }
  if (field.dataType === 'TEXT') {
    const mutation = `
      mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $text: String!) {
        updateProjectV2ItemFieldValue(input: {
          projectId: $projectId,
          itemId: $itemId,
          fieldId: $fieldId,
          value: { text: $text }
        }) { projectV2Item { id } }
      }
    `;
    await github.graphql(mutation, { projectId, itemId, fieldId: field.id, text: value });
  }
}

async function syncProjectItem(github, context, core, content, values) {
  const config = loadConfig();
  const project = await getProject(github, context, config, core);
  if (!project) return;
  const itemId = await ensureProjectItem(github, project.id, content.node_id);
  const fields = await getFields(github, project.id);
  for (const [fieldKey, value] of Object.entries(values)) {
    const fieldName = config.fields[fieldKey];
    if (fieldName) {
      await updateField(github, project.id, itemId, fields, fieldName, value, core);
    }
  }
}

async function syncIssue({ github, context, core, issue }) {
  const config = loadConfig();
  const type = inferType(issue, config);
  const component = inferComponentFromIssue(issue, config);
  const column = boardColumnForIssue(issue, type, config);
  const readyTask = type === 'Task' && taskIsReady(issue, config);

  if (type === 'Task') {
    if (readyTask) {
      await addLabels(github, context, issue.number, [config.labels.agentReady]);
      await removeLabel(github, context, issue.number, config.labels.needsInfo);
    } else {
      await addLabels(github, context, issue.number, [config.labels.needsInfo]);
      await removeLabel(github, context, issue.number, config.labels.agentReady);
    }
  }

  await syncProjectItem(github, context, core, issue, {
    boardColumn: column,
    type,
    component,
    environment: config.defaults.environment,
    risk: config.defaults.risk,
    agentStatus: readyTask ? config.defaults.agentStatus : undefined,
  });
}

async function syncPullRequest({ github, context, core, pullRequest }) {
  const config = loadConfig();
  const files = await github.paginate(github.rest.pulls.listFiles, {
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: pullRequest.number,
  });
  const component = inferComponentFromFiles(files.map((file) => file.filename), config);
  const closed = context.payload.action === 'closed';
  const merged = Boolean(pullRequest.merged);
  const column = closed ? 'Done' : 'In Review';

  await syncProjectItem(github, context, core, pullRequest, {
    boardColumn: column,
    component,
    environment: config.defaults.environment,
    humanReview: closed ? 'approved' : config.defaults.humanReview,
  });

  const linkedNumbers = linkedIssueNumbers(`${pullRequest.title}\n${pullRequest.body || ''}`);
  for (const number of linkedNumbers) {
    const { data: issue } = await github.rest.issues.get({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: number,
    });
    await syncProjectItem(github, context, core, issue, {
      boardColumn: merged ? 'Done' : 'In Review',
      humanReview: merged ? 'approved' : config.defaults.humanReview,
      component,
    });
  }
}

async function syncSuccessfulPrCi({ github, context, core }) {
  if (context.payload.workflow_run.conclusion !== 'success') return;
  const prs = context.payload.workflow_run.pull_requests || [];
  for (const prRef of prs) {
    const { data: pullRequest } = await github.rest.pulls.get({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prRef.number,
    });
    const linkedNumbers = linkedIssueNumbers(`${pullRequest.title}\n${pullRequest.body || ''}`);
    for (const number of linkedNumbers) {
      const { data: issue } = await github.rest.issues.get({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: number,
      });
      await syncProjectItem(github, context, core, issue, {
        boardColumn: 'Ready for Human Review',
        humanReview: 'needed',
      });
    }
  }
}

async function hygieneReport({ github, context }) {
  const searches = [
    ['Open agent-ready tasks', 'is:issue is:open label:agent-ready'],
    ['Issues needing information', 'is:issue is:open label:needs-info'],
    ['Open CI bugs', 'is:issue is:open label:"source: ci"'],
    ['Open deployment records', 'is:issue is:open label:deployment'],
  ];
  const lines = ['# Project Hygiene Report', ''];
  for (const [label, query] of searches) {
    const result = await github.rest.search.issuesAndPullRequests({
      q: `repo:${context.repo.owner}/${context.repo.repo} ${query}`,
      per_page: 10,
    });
    lines.push(`## ${label}: ${result.data.total_count}`);
    for (const item of result.data.items.slice(0, 5)) {
      lines.push(`- #${item.number} ${item.title}`);
    }
    lines.push('');
  }

  const body = lines.join('\n');
  const existing = await github.rest.search.issuesAndPullRequests({
    q: `repo:${context.repo.owner}/${context.repo.repo} "PROJECT HYGIENE REPORT" is:issue is:open`,
  });
  if (existing.data.total_count > 0) {
    await github.rest.issues.createComment({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: existing.data.items[0].number,
      body,
    });
    return;
  }
  await github.rest.issues.create({
    owner: context.repo.owner,
    repo: context.repo.repo,
    title: 'PROJECT HYGIENE REPORT',
    body,
    labels: ['project-admin'],
  });
}

async function run({ github, context, core, mode }) {
  if (mode === 'hygiene') {
    await hygieneReport({ github, context, core });
    return;
  }
  if (context.eventName === 'issues' && context.payload.issue) {
    await syncIssue({ github, context, core, issue: context.payload.issue });
    return;
  }
  if (context.eventName === 'pull_request' && context.payload.pull_request) {
    await syncPullRequest({ github, context, core, pullRequest: context.payload.pull_request });
    return;
  }
  if (context.eventName === 'workflow_run' && context.payload.workflow_run) {
    await syncSuccessfulPrCi({ github, context, core });
    return;
  }
  core.info(`No project-admin handler for ${context.eventName}.`);
}

module.exports = { run };
