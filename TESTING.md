# Jarvis-Termux AI – Final Integration Test Structure

This document defines the complete end-to-end integration test checklist before production deployment in Termux.

---

## 1. Environment Setup Test

### 1.1 API Key
Ensure environment variable is set:

```
export BLUESMINDS_API_KEY=your_key_here
```

Verify:

```
echo $BLUESMINDS_API_KEY
```

---

## 2. Installation Test

Run:

```
bash install.sh
```

Verify:

```
which ai
```

Expected:

```
$PREFIX/bin/ai
```

---

## 3. Basic Chat Test

```
ai hello
```

✅ Expect GPT response.

---

## 4. Memory System Tests

### 4.1 Store Memory
```
ai remember Project=TMail
```

### 4.2 View Memory
```
ai memory
```

✅ Should display stored key-value.

### 4.3 Remove Memory
```
ai forget Project
```

---

## 5. History + Auto Summary Test

Send 50+ short messages:

```
ai test1
ai test2
...
```

Expected:

- history.json resets
- summary.json updated

Check:

```
cat ~/.jarvis/data/summary.json
```

---

## 6. Shell Execution Test

```
ai run "ls"
```

✅ Must ask confirmation before execution.

---

## 7. Git Workflow Tests

Inside a Git project:

### 7.1 Status
```
ai status
```

### 7.2 Diff
```
ai diff
```

### 7.3 Commit (AI-generated message)
```
ai commit
```

✅ Must:
- Analyze staged changes
- Suggest message
- Ask confirmation

### 7.4 Push
```
ai push
```

✅ Must request confirmation.

---

## 8. AI Doctor Test (Laravel Project)

Inside Laravel project:

```
ai doctor
```

✅ Should:
- Collect git status
- Read composer.json
- Read package.json
- Return structured diagnosis

---

## 9. Storage Size Verification

Ensure:

- history.json < 50KB
- memory.json < 20KB
- summary.json < 20KB

Check:

```
du -h ~/.jarvis/data/
```

---

## 10. Failure Handling Tests

- Remove API key → should throw clear error.
- Run outside Git repo → Git commands should not crash.
- Run shell with invalid command → graceful error.

---

# ✅ Integration Pass Criteria

Jarvis is production-ready if:

- All commands execute without crashing
- Auto-summary triggers correctly
- Memory persists across sessions
- Git workflow works safely
- Shell execution requires confirmation
- No uncontrolled file growth

---

# Deployment Status

If all checks pass:

Jarvis-Termux AI = ✅ Production Ready
