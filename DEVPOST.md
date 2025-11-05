# Continuum: Version Control for Claude Conversations

## Inspiration

During a recent hackathon, our team hit a frustrating wall. Multiple developers were using Claude Code to build features, but when bugs appeared, we couldn't help each other efficiently. Every handoff meant:

- "Wait, what did you prompt it with?"
- "Let me explain what I was trying to do..."
- "Can you share your conversation history?"
- Re-prompting the same context, burning tokens
- Starting from scratch when someone disconnected

We were losing hours to context transfer. **That's when Continuum was born.**

## What It Does

Think of it as **Git for your LLM conversations**. Every commit now captures the exact Claude context at that moment, creating a shareable, branchable history of AI-assisted development.

### The Game-Changing Benefits

**1. Zero-Friction Team Handoffs**

```
Developer A: "I'm stuck on this auth bug, heading to lunch"
Developer B: *checks out commit* *has full context instantly*
Developer B: "Fixed it! The context showed you were mixing JWT patterns"
```

No explanations. No re-prompting. No downtime.

**2. Pure Context Branching**

Explore different approaches without contamination:
- Main branch: Building with Supabase
- Feature branch: "What if we used Postgres instead?"
- Another branch: "Let's try MongoDB"

Each branch maintains pure context. No more "wait, ignore what I said about Supabase earlier."

**3. Perfect State Preservation**

Know exactly what Claude knew when it generated that code. When a bug appears three weeks later, you can return to the exact context that created it.

**4. Massive Token Savings**

Stop re-prompting the same project context across your team. One developer builds the context, everyone else reuses it. We've seen 70%+ token reduction in team projects.

## How We Built It

### Architecture: Two Git Repos Working in Harmony

Continuum maintains two parallel Git repositories:

1. **Your Code Repository** (business as usual)
   - Contains your actual project files
   - Normal Git workflow: branch, commit, merge

2. **Claude Context Repository** (`~/.claude/projects/{project}/`)
   - Stores `.jsonl` conversation files
   - Mirrors your code repo's branch structure
   - Automatically syncs via Git hooks

### The Context Capture Flow

When you commit code, here's what happens under the hood:

```python
# post_commit.py - Triggered by Git hook
def capture_context():
    # 1. Get the commit you just made
    main_commit_sha = get_current_commit_sha()
    main_branch = get_main_repo_branch()

    # 2. Switch Claude repo to matching branch
    create_or_checkout_branch(main_branch)

    # 3. Stage all conversation files (.jsonl)
    add_session_files()

    # 4. Commit with reference to code commit
    commit_sessions(main_commit_sha)

    # 5. Async push to Supabase (non-blocking)
    push_to_remote_async()
```

**Key Technical Decisions:**

- **Git Hooks**: Automatic capture on every commit ensures you never lose context
- **Stash Management**: Preserves untracked files and working directory state
- **Clean State Tracking**: Maintains `.claude/` directory hygiene across checkouts
- **Branch Mirroring**: Claude context branches mirror your code branches exactly

### Context Storage: The Smart Way

Instead of bloating your code repo, we store context efficiently:

```
.claude/projects/{encoded-path}/
├── session-abc123.jsonl    # Current conversation
├── session-def456.jsonl    # Another conversation
└── .git/                   # Separate Git repo!
```

Each `.jsonl` file contains the complete conversation history with Claude, including:
- User messages
- Claude responses
- Tool calls and results
- Session metadata

When you checkout a commit, we:
1. Stash any uncommitted changes in Claude repo
2. Switch to the matching branch
3. Checkout the commit that corresponds to your code commit
4. Restore your exact conversation state

### Cross-Device Sync with Supabase

The real magic happens when you want to share context across devices or teammates:

```python
# sync_ops.py - Supabase integration
def sync_with_remote():
    # 1. Create Git bundle (object storage compatible)
    bundle = create_git_bundle()

    # 2. Upload to Supabase Storage
    upload_to_supabase(bundle)

    # 3. On other device: download and unbundle
    pull_from_remote()
```

We use **Git bundles** because Supabase Storage is object-based (like S3), not a Git server. Bundles give us:
- Complete repository state in a single file
- Compatible with any object storage
- Efficient compression
- Full Git history preservation

### The Frontend: Visualizing Context Flow

Built with **Next.js 16** and **React 19**, the Continuum dashboard provides:

**Interactive Git Graph**
```tsx
// GitGraphCanvas.tsx - Dual timeline visualization
<svg>
  {/* Blue timeline: Git commits */}
  {gitNodes.map(node => <GraphNode type="git" />)}

  {/* Orange timeline: Claude contexts */}
  {claudeNodes.map(node => <GraphNode type="claude" />)}

  {/* Connections: When contexts branch/merge */}
  {connections.map(edge => <GraphEdge />)}
</svg>
```

The graph shows:
- **Blue nodes (left)**: Your Git commits
- **Orange nodes (right)**: Claude conversation snapshots
- **Connecting edges**: Which conversation led to which code

This gives you a visual understanding of your AI-assisted development flow.

## Challenges We Ran Into

**1. Git Within Git**

Initially, we tried storing `.claude/` as a submodule. Disaster. Git submodules are notoriously painful, and users would have to manually update them. Instead:

- Separate repos, same branch structure
- Automatic sync via hooks
- No submodule complexity

**2. Race Conditions During Checkout**

When switching branches, we had to carefully orchestrate:
```
1. Stash Claude context changes
2. Switch code branch
3. Switch Claude branch
4. Restore Claude stash
```

Getting the order wrong would lose context or corrupt state.

**3. Handling Detached HEAD**

Claude Code sometimes runs in detached HEAD (viewing old commits). We had to:
- Detect detached state
- Skip context capture (can't commit to a detached HEAD)
- Provide clear user feedback

**4. Supabase Storage Limitations**

Supabase Storage isn't a Git server. We couldn't just `git push`. Solution:
- Create Git bundles (portable Git archives)
- Upload bundle files to Supabase Storage
- Unbundle on download

This works with any object storage (S3, GCS, Azure Blob, etc.)

## Accomplishments We're Proud Of

**Seamless Integration**

Users run three commands and never think about it again:
```bash
cc-init              # Initialize context tracking
cc-install-hook      # Set up automatic capture
cc-sync              # Sync with teammates
```

After that? It just works. Every commit captures context automatically.

**Performance Optimizations**

- **Async Push**: Context syncs to Supabase in background, doesn't slow commits
- **Lazy Loading**: Frontend only renders visible graph nodes (viewport culling)
- **Bundle Compression**: Git bundles are highly compressed

**Developer Experience**

The visual graph isn't just pretty - it's genuinely useful for understanding:
- "Which conversation led to this bug?"
- "What was I thinking when I wrote this?"
- "How did we explore different approaches?"

## What We Learned

**Git is Surprisingly Flexible**

We discovered Git bundles, learned about detached HEAD states, and mastered hook chaining. Git has tools for scenarios we never imagined.

**Context is Everything**

Having perfect conversation history transforms debugging. You're not just seeing the code - you're seeing the *reasoning* behind it.

**Simple Tools, Complex Outcomes**

Our entire stack:
- Git (battle-tested version control)
- Python scripts (simple automation)
- Supabase (managed database + storage)
- Next.js (modern React framework)

Nothing exotic. The magic is in how they combine.

## What's Next for Continuum

**1. Claude API Integration**

Currently works with Claude Code (CLI). We want to support:
- Claude Web UI (browser extension)
- Claude API (direct integration)
- Other LLMs (GPT-4, Gemini, etc.)

**2. Smart Context Compression**

Conversations get long. We're exploring:
- Automatic summarization of old context
- Semantic search within conversation history
- Context diff viewer (what changed between commits?)

**3. Team Features**

- Shared context pools: Multiple devs contribute to one conversation
- Context review workflow: "Approve" context before merging
- Analytics: Token usage, conversation patterns, productivity metrics

**4. Time-Travel Debugging**

Imagine:
```bash
git bisect start        # Find the commit that introduced a bug
cc-restore <commit>     # Load the exact Claude context from that commit
# Ask Claude: "Why did you suggest this approach?"
```

## Try It Yourself

**Installation:**

```bash
# Install the CLI tool
cd ccc
pip install -e .

# Initialize in your project
cc-init
cc-install-hook
```

**Optional: Enable cross-device sync**

Create a `.env` file:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_BUCKET=your-bucket-name
```

Then:
```bash
cc-sync
```

**Usage:**

Just work normally! Every time you commit code, your Claude context is automatically captured. Checkout old commits to see historical context.

**View the dashboard:**

```bash
cd Continuum
npm install
npm run dev
```

Visit `http://localhost:3000` to explore your conversation timeline.

## Built With

- **Python** - CLI tools and Git automation
- **Git** - Version control for code and context
- **Supabase** - Database and object storage for sync
- **Next.js 16** - Frontend framework
- **React 19** - UI library with React Compiler
- **Tailwind CSS** - Styling
- **Radix UI** - Accessible component primitives
- **react-zoom-pan-pinch** - Interactive graph canvas

## Repository

Frontend (Continuum Dashboard): `../Continuum`
Backend (cc-context CLI): This repository

## License

MIT
