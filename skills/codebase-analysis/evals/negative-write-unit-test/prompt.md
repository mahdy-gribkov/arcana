---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Write a table-driven Go unit test for this function.

```go
func Clamp(v, lo, hi int) int {
    if v < lo { return lo }
    if v > hi { return hi }
    return v
}
```
