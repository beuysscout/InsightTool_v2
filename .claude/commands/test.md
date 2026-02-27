Run the full test and type-check suite for InsightTool_v2.

## Backend Tests
1. Run pytest from the backend directory:
   ```
   cd /home/user/InsightTool_v2/backend && python -m pytest tests/ -v
   ```
2. Report pass/fail counts.

## Frontend Type Check
1. Run the TypeScript compiler in check mode:
   ```
   cd /home/user/InsightTool_v2/frontend && npx tsc --noEmit
   ```
2. Report any type errors found.

## Summary
After both checks complete, provide a summary:
- Backend: X/Y tests passed
- Frontend: clean compile or list of errors
- Overall: PASS or FAIL

If anything fails, suggest fixes. $ARGUMENTS
