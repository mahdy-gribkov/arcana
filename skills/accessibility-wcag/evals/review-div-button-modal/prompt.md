---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Review this React component for accessibility before we ship it. We need to meet WCAG AA.

```tsx
export function DeleteDialog({ open, onConfirm, onClose }) {
  if (!open) return null;
  return (
    <div className="modal">
      <div className="title">Delete project?</div>
      <input autoFocus placeholder="Type the project name" />
      <div className="btn red" onClick={onConfirm}>Delete</div>
      <div className="btn" onClick={onClose}>Cancel</div>
      <span style={{ color: 'red' }}>This cannot be undone</span>
    </div>
  );
}
```
