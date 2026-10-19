from typing import Optional
from backend.models.pr_model import PRMetadata


class PromptBuilder:
    @staticmethod
    def build_summary_prompt(pr: PRMetadata, custom_notes: Optional[str] = None) -> str:
        files_summary = "\n".join(
            [f"- {f.path} (+{f.additions}/-{f.deletions})" for f in pr.files[:35]]
        )
        if len(pr.files) > 35:
            files_summary += f"\n- ... and {len(pr.files) - 35} more files."

        commits_summary = "\n".join([f"- {c}" for c in pr.commits[:25]])
        if len(pr.commits) > 25:
            commits_summary += f"\n- ... and {len(pr.commits) - 25} more commits."

        extra_notes_section = ""
        if custom_notes and custom_notes.strip():
            extra_notes_section = f"\nAdditional Context / User Notes:\n{custom_notes.strip()}\n"

        prompt = f"""You are an expert senior software engineer and technical reviewer.
Analyze the following GitHub Pull Request details, commit messages, and file diffs.
Write a clear, concise, and professional Pull Request description strictly in English.

PR Information:
- Title: {pr.title}
- Repository: {pr.owner}/{pr.repo}
- Author: {pr.author}
- Branch: {pr.head_branch} -> {pr.base_branch}
- Original PR Body: {pr.body or '(None)'}

Files Changed ({len(pr.files)} files, +{pr.total_additions}/-{pr.total_deletions}):
{files_summary}

Commit Messages:
{commits_summary}
{extra_notes_section}

Code Diff:
```diff
{pr.diff_text}
```

CRITICAL INSTRUCTIONS:
1. You MUST follow the EXACT Markdown template below. Do not omit any heading or comment structure.
2. In "## Types of changes", check `[x]` for all categories that accurately apply based on your code diff analysis (e.g. Bugfix, Feature, Performance, Security, Database changes, BREAKING CHANGE, Both FE and BE). Unselected categories must stay as `- [ ]`.
3. In "## How to QA?", write realistic, step-by-step verification checklist items tailored to the code changes, and MUST preserve the exact item: `- [ ] After merging to master, I'll make sure it's good and not locking production release`.
4. In "## Automation tests:", MUST preserve the exact sentence "If I have time, I would add tests for the following:" followed by concrete automated test scenarios (e.g., unit tests, integration tests, edge cases) derived from the changes.
5. In "## What", write clear, concise bullet points explaining what was changed and why it was modified.
6. In "## Why", explain the root problem or business requirement being solved.
7. Only output the markdown text itself. Do NOT include markdown code fences (like ```markdown ... ```) around the entire output. Do NOT include introductory or conversational filler.

REQUIRED MARKDOWN TEMPLATE:
## What

<!-- Describe your changes in detail. -->
<!-- If frontend, specific Figma link or screenshot of the page helps. -->

## Why

<!-- Why is this change required? What problem does it solve? -->
<!-- If it fixes an open issue, please link to the issue here. -->

## How to QA?

<!-- Share a checklist how you tested and will test your changes. -->
<!-- Mention how your change affects the rest of the system. -->

- [ ] After merging to master, I'll make sure it's good and not locking production release

## Any screenshots or loom video?

<!-- It really helps!! Sometimes while making screenshots or videos, we realize we need to test or explain better. -->
<!-- Frontend: help us see your changes visually please. Backend: when screenshots can't tell the story, loom video has been awesome so far -->

## Types of changes

- [ ] Bugfix
- [ ] Feature
- [ ] Performance
- [ ] Security
- [ ] Database changes
- [ ] BREAKING CHANGE
- [ ] Both FE and BE (note different deployment time)

## Automation tests:

If I have time, I would add tests for the following:

<!-- Share a list of useful test cases you think can be automated but you don't have time or experience to do so -->
"""
        return prompt
