---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---
Review this Go function before I commit it:

```go
func GetUser(id string) (*User, error) {
    resp, err := http.Get("https://api.internal.example/users/" + id)
    if err != nil {
        return nil, err
    }
    var u User
    json.NewDecoder(resp.Body).Decode(&u)
    return &u, nil
}
```
